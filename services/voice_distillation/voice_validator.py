"""
Voice Validator - Stage 3
==========================
Validates evolved voice tensors by generating test audio and
analyzing prosody, speaker similarity, and style differentiation.
Reuses the existing prosody_analyzer from audio_preprocess service.
"""

import io
import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import soundfile as sf
from loguru import logger

from config import (
    STYLES, EVOLVED_DIR, VALIDATION_DIR, SAMPLE_RATE,
    KOKORO_LANG, KOKORO_MODEL, RESEMBLYZER_THRESHOLD,
)


# Test phrases for validation (different from training phrases)
VALIDATION_PHRASES = [
    "Buenos dias, gracias por comunicarse con nosotros.",
    "Permita me verificar la informacion en nuestro sistema.",
    "Su solicitud sera procesada en las proximas veinticuatro horas.",
    "Hay algo mas en lo que pueda ayudarle el dia de hoy.",
    "Le agradecemos su paciencia y comprension.",
]


class VoiceValidator:
    """
    Validates evolved voice tensors with multiple quality checks.
    """

    def __init__(self, reference_dir: Path, evolved_dir: Path = EVOLVED_DIR):
        """
        Args:
            reference_dir: Directory with F5-TTS target audio per style.
            evolved_dir: Directory with evolved .pt tensors.
        """
        self.reference_dir = reference_dir
        self.evolved_dir = evolved_dir

        # Late imports for optional dependencies
        self._speech_gen = None
        self._prosody_analyzer = None
        self._resemblyzer_encoder = None

    def _get_speech_gen(self):
        if self._speech_gen is None:
            from voice_evolver import SpeechGenerator
            self._speech_gen = SpeechGenerator()
        return self._speech_gen

    def _get_prosody_analyzer(self):
        """Load prosody analyzer from audio_preprocess service."""
        if self._prosody_analyzer is None:
            try:
                import sys
                sys.path.insert(0, "/app/audio_preprocess")
                from prosody_analyzer import ProsodyAnalyzer
                self._prosody_analyzer = ProsodyAnalyzer(sample_rate=SAMPLE_RATE)
            except ImportError:
                logger.warning("prosody_analyzer not available, using basic analysis")
                self._prosody_analyzer = _BasicProsodyAnalyzer(sample_rate=SAMPLE_RATE)
        return self._prosody_analyzer

    def _get_resemblyzer(self):
        if self._resemblyzer_encoder is None:
            from resemblyzer import VoiceEncoder, preprocess_wav
            self._resemblyzer_encoder = VoiceEncoder()
            self._preprocess_wav = preprocess_wav
        return self._resemblyzer_encoder

    def validate_style(self, style: str) -> Dict:
        """
        Validate a single evolved voice tensor against its target.

        Returns:
            Validation report dict with scores and analysis.
        """
        tensor_path = self.evolved_dir / f"{style}.pt"
        target_path = self.reference_dir / style / "target.wav"

        if not tensor_path.exists():
            return {"style": style, "valid": False, "error": "Tensor not found"}
        if not target_path.exists():
            return {"style": style, "valid": False, "error": "Target audio not found"}

        logger.info(f"Validating style '{style}'...")

        import torch
        voice_tensor = torch.load(tensor_path, map_location="cpu", weights_only=True)
        speech_gen = self._get_speech_gen()

        # Generate test audio with all validation phrases
        generated_audios = []
        for phrase in VALIDATION_PHRASES:
            audio = speech_gen.generate(phrase, voice_tensor)
            if audio is not None:
                generated_audios.append({"phrase": phrase, "audio": audio})

        if not generated_audios:
            return {"style": style, "valid": False, "error": "All synthesis failed"}

        # 1. Speaker similarity vs F5-TTS target
        speaker_scores = self._evaluate_speaker_similarity(
            generated_audios, str(target_path)
        )

        # 2. Prosody analysis of generated audio
        prosody_profiles = self._analyze_prosody(generated_audios)

        # 3. Consistency check (self-similarity across phrases)
        consistency = self._evaluate_consistency(generated_audios)

        # 4. Audio quality checks
        quality = self._evaluate_quality(generated_audios)

        # Overall validity
        avg_speaker_sim = np.mean(speaker_scores) if speaker_scores else 0.0
        is_valid = (
            avg_speaker_sim >= RESEMBLYZER_THRESHOLD
            and consistency >= 0.80
            and quality["avg_duration"] >= 1.0
        )

        report = {
            "style": style,
            "valid": is_valid,
            "speaker_similarity": {
                "mean": float(avg_speaker_sim),
                "scores": [float(s) for s in speaker_scores],
                "threshold": RESEMBLYZER_THRESHOLD,
            },
            "prosody": prosody_profiles,
            "consistency": float(consistency),
            "quality": quality,
            "phrases_generated": len(generated_audios),
            "phrases_total": len(VALIDATION_PHRASES),
        }

        logger.info(
            f"  Style '{style}': valid={is_valid}, "
            f"speaker_sim={avg_speaker_sim:.3f}, "
            f"consistency={consistency:.3f}"
        )

        return report

    def _evaluate_speaker_similarity(
        self,
        generated: List[Dict],
        target_path: str,
    ) -> List[float]:
        """Compare each generated audio against the F5-TTS target embedding."""
        try:
            encoder = self._get_resemblyzer()
            target_wav = self._preprocess_wav(target_path)
            target_emb = encoder.embed_utterance(target_wav)

            scores = []
            for item in generated:
                buf = io.BytesIO()
                sf.write(buf, item["audio"], SAMPLE_RATE, format="WAV")
                buf.seek(0)
                gen_wav = self._preprocess_wav(buf)
                if len(gen_wav) > SAMPLE_RATE * 0.3:
                    gen_emb = encoder.embed_utterance(gen_wav)
                    sim = float(np.inner(target_emb, gen_emb))
                    scores.append(max(0.0, sim))
            return scores
        except Exception as e:
            logger.warning(f"Speaker similarity evaluation failed: {e}")
            return []

    def _analyze_prosody(self, generated: List[Dict]) -> Dict:
        """Analyze prosody of generated audio using the prosody analyzer."""
        analyzer = self._get_prosody_analyzer()
        profiles = []

        for item in generated:
            # Convert to bytes for prosody analyzer
            buf = io.BytesIO()
            sf.write(buf, item["audio"], SAMPLE_RATE, format="WAV")
            audio_bytes = buf.getvalue()

            result = analyzer.analyze_audio(audio_bytes)
            profiles.append({
                "phrase": item["phrase"][:50],
                "pitch_mean": result.get("pitch_mean", 0),
                "pitch_std": result.get("pitch_std", 0),
                "energy_level": result.get("energy_level", 0),
                "speech_rate": result.get("speech_rate", 0),
                "emotional_tone": result.get("emotional_tone", "unknown"),
            })

        # Aggregate statistics
        if profiles:
            return {
                "samples": profiles,
                "avg_pitch_mean": float(np.mean([p["pitch_mean"] for p in profiles])),
                "avg_pitch_std": float(np.mean([p["pitch_std"] for p in profiles])),
                "avg_energy": float(np.mean([p["energy_level"] for p in profiles])),
                "avg_speech_rate": float(np.mean([p["speech_rate"] for p in profiles])),
                "dominant_tone": _most_common([p["emotional_tone"] for p in profiles]),
            }
        return {}

    def _evaluate_consistency(self, generated: List[Dict]) -> float:
        """Check that the same voice sounds consistent across phrases."""
        if len(generated) < 2:
            return 1.0

        try:
            encoder = self._get_resemblyzer()
            embeddings = []
            for item in generated:
                buf = io.BytesIO()
                sf.write(buf, item["audio"], SAMPLE_RATE, format="WAV")
                buf.seek(0)
                wav = self._preprocess_wav(buf)
                if len(wav) > SAMPLE_RATE * 0.3:
                    embeddings.append(encoder.embed_utterance(wav))

            if len(embeddings) < 2:
                return 0.0

            # Average pairwise similarity
            sims = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = float(np.inner(embeddings[i], embeddings[j]))
                    sims.append(max(0.0, sim))

            return float(np.mean(sims)) if sims else 0.0
        except Exception as e:
            logger.warning(f"Consistency check failed: {e}")
            return 0.0

    def _evaluate_quality(self, generated: List[Dict]) -> Dict:
        """Basic audio quality checks."""
        durations = []
        clipping_count = 0

        for item in generated:
            audio = item["audio"]
            durations.append(len(audio) / SAMPLE_RATE)
            if np.max(np.abs(audio)) > 0.99:
                clipping_count += 1

        return {
            "avg_duration": float(np.mean(durations)),
            "min_duration": float(np.min(durations)),
            "max_duration": float(np.max(durations)),
            "clipping_samples": clipping_count,
        }

    def validate_all(
        self,
        output_dir: Path = VALIDATION_DIR,
    ) -> Dict[str, Dict]:
        """
        Validate all evolved styles and compare them.

        Returns:
            Dict of style → validation report.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        reports = {}
        for style in STYLES:
            report = self.validate_style(style)
            reports[style] = report

        # Cross-style differentiation check
        differentiation = self._check_style_differentiation(reports)

        # Summary
        valid_count = sum(1 for r in reports.values() if r.get("valid"))
        summary = {
            "styles_validated": len(reports),
            "styles_valid": valid_count,
            "style_differentiation": differentiation,
            "reports": reports,
        }

        # Save report
        report_path = output_dir / "validation_report.json"
        report_path.write_text(json.dumps(summary, indent=2, default=str))
        logger.info(f"Validation report saved: {report_path}")
        logger.info(f"Valid styles: {valid_count}/{len(reports)}")

        return reports

    def _check_style_differentiation(self, reports: Dict) -> Dict:
        """
        Verify that different styles actually produce different-sounding voices.
        Compares prosody profiles between styles.
        """
        style_prosodies = {}
        for style, report in reports.items():
            prosody = report.get("prosody", {})
            if prosody:
                style_prosodies[style] = {
                    "pitch_mean": prosody.get("avg_pitch_mean", 0),
                    "pitch_std": prosody.get("avg_pitch_std", 0),
                    "energy": prosody.get("avg_energy", 0),
                    "speech_rate": prosody.get("avg_speech_rate", 0),
                }

        if len(style_prosodies) < 2:
            return {"differentiated": False, "reason": "Not enough styles to compare"}

        # Check if prosody metrics differ meaningfully between styles
        pitch_means = [p["pitch_mean"] for p in style_prosodies.values()]
        speech_rates = [p["speech_rate"] for p in style_prosodies.values()]

        pitch_variation = np.std(pitch_means) / (np.mean(pitch_means) + 1e-10)
        rate_variation = np.std(speech_rates) / (np.mean(speech_rates) + 1e-10)

        is_differentiated = pitch_variation > 0.05 or rate_variation > 0.05

        return {
            "differentiated": bool(is_differentiated),
            "pitch_variation_pct": float(pitch_variation * 100),
            "rate_variation_pct": float(rate_variation * 100),
            "per_style": style_prosodies,
        }


class _BasicProsodyAnalyzer:
    """Fallback prosody analyzer when the full one isn't available."""

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate

    def analyze_audio(self, audio_bytes: bytes) -> Dict:
        try:
            import librosa
            audio_buf = io.BytesIO(audio_bytes)
            audio, sr = librosa.load(audio_buf, sr=self.sample_rate, mono=True)

            f0 = librosa.yin(
                audio,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
                sr=self.sample_rate,
            )
            f0_valid = f0[f0 > 0]
            rms = librosa.feature.rms(y=audio)[0]
            rms_db = librosa.amplitude_to_db(rms, ref=np.max)

            return {
                "pitch_mean": float(np.mean(f0_valid)) if len(f0_valid) > 0 else 0.0,
                "pitch_std": float(np.std(f0_valid)) if len(f0_valid) > 0 else 0.0,
                "energy_level": float(np.mean(rms_db)),
                "speech_rate": 150.0,  # Default
                "emotional_tone": "neutral",
            }
        except Exception:
            return {
                "pitch_mean": 0.0,
                "pitch_std": 0.0,
                "energy_level": -60.0,
                "speech_rate": 0.0,
                "emotional_tone": "unknown",
            }


def _most_common(items: list) -> str:
    """Return most frequent item in a list."""
    if not items:
        return "unknown"
    from collections import Counter
    return Counter(items).most_common(1)[0][0]


def run_stage(
    reference_dir: Path,
    evolved_dir: Path = EVOLVED_DIR,
    output_dir: Path = VALIDATION_DIR,
) -> Dict[str, Dict]:
    """Entry point for Stage 3."""
    validator = VoiceValidator(reference_dir, evolved_dir)
    return validator.validate_all(output_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stage 3: Validate evolved voices")
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--evolved-dir", type=Path, default=EVOLVED_DIR)
    parser.add_argument("--output-dir", type=Path, default=VALIDATION_DIR)
    args = parser.parse_args()

    reports = run_stage(args.reference_dir, args.evolved_dir, args.output_dir)
    for style, report in reports.items():
        status = "PASS" if report.get("valid") else "FAIL"
        sim = report.get("speaker_similarity", {}).get("mean", 0)
        print(f"  [{status}] {style}: speaker_sim={sim:.3f}")
