"""
Reference Generator - Stage 1
==============================
Uses the existing F5-TTS service to generate high-quality target audio
for each voice style. These clips become the optimization target for
the Kokoro voice evolution stage.
"""

import asyncio
import base64
import io
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import numpy as np
import soundfile as sf
from loguru import logger

from config import (
    STYLES, TTS_URL, REFERENCE_DIR,
    SAMPLE_RATE, TARGET_LUFS,
)


class ReferenceGenerator:
    """
    Generates target reference audio using F5-TTS for each style.
    Communicates with the existing TTS Docker service via HTTP.
    """

    def __init__(
        self,
        tts_url: str = TTS_URL,
        source_reference_audio: Optional[str] = None,
        source_reference_text: Optional[str] = None,
    ):
        self.tts_url = tts_url.rstrip("/")
        self.source_reference_audio = source_reference_audio
        self.source_reference_text = source_reference_text

    async def check_tts_health(self) -> bool:
        """Verify TTS service is running."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.tts_url}/health")
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"TTS service unreachable at {self.tts_url}: {e}")
            return False

    async def set_reference_voice(
        self,
        audio_path: str,
        transcript: str,
    ) -> bool:
        """
        Upload a voice reference to the TTS service.
        This sets the voice identity that F5-TTS will clone.
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                with open(audio_path, "rb") as f:
                    files = {"audio": ("reference.wav", f, "audio/wav")}
                    data = {"transcript": transcript}
                    resp = await client.post(
                        f"{self.tts_url}/set_reference",
                        files=files,
                        data=data,
                    )
                    if resp.status_code == 200:
                        logger.info(f"Reference voice set from: {audio_path}")
                        return True
                    logger.error(f"Failed to set reference: {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"Error setting reference voice: {e}")
            return False

    async def synthesize_phrase(
        self,
        text: str,
        speed: float = 1.0,
        reference_audio: Optional[str] = None,
    ) -> Optional[np.ndarray]:
        """
        Synthesize a single phrase using F5-TTS.
        Returns audio as numpy array (24kHz mono float32).
        """
        payload = {
            "text": text,
            "speed": speed,
            "return_bytes": True,
        }

        if reference_audio:
            # Send as base64 if it's a file path
            if Path(reference_audio).exists():
                with open(reference_audio, "rb") as f:
                    audio_b64 = base64.b64encode(f.read()).decode()
                payload["reference_audio"] = f"data:audio/wav;base64,{audio_b64}"

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.tts_url}/synthesize",
                    json=payload,
                )
                if resp.status_code != 200:
                    logger.error(f"Synthesis failed: {resp.text}")
                    return None

                data = resp.json()

                # Decode audio from base64
                if "audio_base64" in data and data["audio_base64"]:
                    audio_bytes = base64.b64decode(data["audio_base64"])
                    audio, sr = sf.read(io.BytesIO(audio_bytes))
                    if sr != SAMPLE_RATE:
                        # Basic resampling via librosa if needed
                        import librosa
                        audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)
                    return audio.astype(np.float32)

                logger.error("No audio data in response")
                return None

        except Exception as e:
            logger.error(f"Synthesis error for '{text[:50]}...': {e}")
            return None

    async def generate_style_reference(
        self,
        style: str,
        output_dir: Path,
        max_retries: int = 3,
    ) -> Optional[Path]:
        """
        Generate a concatenated reference clip for one style.
        Synthesizes all reference phrases and joins them with short pauses.
        """
        style_config = STYLES.get(style)
        if not style_config:
            logger.error(f"Unknown style: {style}")
            return None

        phrases = style_config["reference_phrases"]
        speed = style_config["f5_speed"]

        logger.info(f"Generating reference for style '{style}' ({len(phrases)} phrases, speed={speed})")

        audio_segments = []
        # Short silence between phrases (0.5s)
        silence_gap = np.zeros(int(SAMPLE_RATE * 0.5), dtype=np.float32)

        for i, phrase in enumerate(phrases):
            audio = None
            for attempt in range(max_retries):
                audio = await self.synthesize_phrase(
                    text=phrase,
                    speed=speed,
                    reference_audio=self.source_reference_audio,
                )
                if audio is not None:
                    break
                logger.warning(f"  Retry {attempt + 1}/{max_retries} for phrase {i + 1}")
                await asyncio.sleep(2 ** attempt)

            if audio is None:
                logger.error(f"  Failed to synthesize phrase {i + 1}: {phrase[:50]}...")
                continue

            audio_segments.append(audio)
            audio_segments.append(silence_gap)
            logger.info(f"  Phrase {i + 1}/{len(phrases)}: {len(audio) / SAMPLE_RATE:.1f}s")

        if not audio_segments:
            logger.error(f"No audio generated for style '{style}'")
            return None

        # Concatenate all segments
        full_audio = np.concatenate(audio_segments)

        # LUFS normalization
        try:
            full_audio = _normalize_lufs(full_audio, SAMPLE_RATE, TARGET_LUFS)
        except Exception as e:
            logger.warning(f"LUFS normalization failed, using raw audio: {e}")

        # Save
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "target.wav"
        sf.write(str(output_path), full_audio, SAMPLE_RATE, subtype="PCM_16")

        duration = len(full_audio) / SAMPLE_RATE
        logger.info(f"Reference saved: {output_path} ({duration:.1f}s)")

        # Save metadata
        metadata = {
            "style": style,
            "phrases": phrases,
            "speed": speed,
            "duration_seconds": duration,
            "sample_rate": SAMPLE_RATE,
            "source_reference": self.source_reference_audio,
        }
        meta_path = output_dir / "metadata.json"
        meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

        return output_path

    async def generate_all_references(
        self,
        output_base: Path = REFERENCE_DIR,
    ) -> Dict[str, Path]:
        """
        Generate reference audio for all styles.
        Returns dict of style → path to generated wav.
        """
        if not await self.check_tts_health():
            raise ConnectionError(f"TTS service not available at {self.tts_url}")

        # Set source voice reference if provided
        if self.source_reference_audio and self.source_reference_text:
            success = await self.set_reference_voice(
                self.source_reference_audio,
                self.source_reference_text,
            )
            if not success:
                logger.warning("Could not set source reference, using TTS default voice")

        results = {}
        for style in STYLES:
            style_dir = output_base / style
            path = await self.generate_style_reference(style, style_dir)
            if path:
                results[style] = path
            else:
                logger.error(f"Failed to generate reference for style '{style}'")

        logger.info(f"Generated {len(results)}/{len(STYLES)} style references")
        return results


def _normalize_lufs(audio: np.ndarray, sample_rate: int, target_lufs: float) -> np.ndarray:
    """
    Simple LUFS normalization. Uses the audio_processor module if available,
    otherwise falls back to RMS-based approximation.
    """
    try:
        # Try to use the existing training module
        import sys
        sys.path.insert(0, "/app/training_utils")
        from audio_processor import normalize_lufs
        return normalize_lufs(audio, sample_rate, target_lufs)
    except ImportError:
        pass

    # Fallback: RMS-based gain adjustment
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 1e-10:
        return audio

    # Approximate LUFS from RMS (simplified)
    current_lufs_approx = 20 * np.log10(rms) - 0.691
    gain_db = target_lufs - current_lufs_approx
    gain_linear = 10 ** (gain_db / 20)

    normalized = audio * gain_linear

    # Soft clip to prevent clipping
    peak = np.max(np.abs(normalized))
    if peak > 0.95:
        normalized = normalized * (0.95 / peak)

    return normalized


async def run_stage(
    source_audio: Optional[str] = None,
    source_text: Optional[str] = None,
    tts_url: str = TTS_URL,
    output_dir: Path = REFERENCE_DIR,
) -> Dict[str, Path]:
    """Entry point for Stage 1."""
    generator = ReferenceGenerator(
        tts_url=tts_url,
        source_reference_audio=source_audio,
        source_reference_text=source_text,
    )
    return await generator.generate_all_references(output_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stage 1: Generate F5-TTS reference audio")
    parser.add_argument("--reference-audio", help="Source voice audio file")
    parser.add_argument("--reference-text", help="Transcript of source audio")
    parser.add_argument("--tts-url", default=TTS_URL, help="TTS service URL")
    parser.add_argument("--output-dir", type=Path, default=REFERENCE_DIR)
    args = parser.parse_args()

    results = asyncio.run(run_stage(
        source_audio=args.reference_audio,
        source_text=args.reference_text,
        tts_url=args.tts_url,
        output_dir=args.output_dir,
    ))
    print(f"\nGenerated references: {list(results.keys())}")
