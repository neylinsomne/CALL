"""
Spanish TTS Service
Text-to-Speech synthesis supporting F5-TTS and Kokoro backends.

Backends:
  - f5:     F5-TTS (high quality, zero-shot cloning, heavier)
  - kokoro: Kokoro-82M (lightweight, 210x realtime, evolved voice tensors)

Set TTS_BACKEND=kokoro and KOKORO_VOICE_PATH to use evolved voices.
"""

import os
import io
import base64
import uuid
import hashlib
from typing import Optional, Dict
from pathlib import Path
from collections import OrderedDict

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
import torch
import soundfile as sf
import numpy as np
from loguru import logger

# Configure logging
logger.add(
    "logs/tts_{time}.log",
    rotation="100 MB",
    retention="7 days",
    level="INFO"
)

# ===========================================
# Backend Selection
# ===========================================
TTS_BACKEND = os.getenv("TTS_BACKEND", "f5")  # "f5" | "kokoro"
KOKORO_VOICE_PATH = os.getenv("KOKORO_VOICE_PATH", "")
KOKORO_VOICE_STYLE = os.getenv("KOKORO_VOICE_STYLE", "ef_dora")
KOKORO_LANG = os.getenv("KOKORO_LANG", "e")  # "e" = Spanish

# F5-TTS imports
F5TTS = None
if TTS_BACKEND == "f5":
    try:
        from f5_tts.api import F5TTS
    except ImportError:
        try:
            from f5_tts.infer.utils_infer import load_model, infer_process
        except ImportError:
            logger.warning("F5-TTS not installed, only Kokoro backend available")

# Kokoro imports
KPipeline = None
if TTS_BACKEND == "kokoro":
    try:
        from kokoro import KPipeline
    except ImportError:
        logger.error("Kokoro not installed. Install with: pip install kokoro>=0.9.4")


# ===========================================
# Configuration
# ===========================================
DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.getenv("TTS_MODEL", "jpgallegoar/F5-Spanish")
AUDIO_OUTPUT_DIR = Path("/app/audio")
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True)
VOICE_REFERENCES_DIR = AUDIO_OUTPUT_DIR / "voice_references"
VOICE_REFERENCES_DIR.mkdir(exist_ok=True)

# Reference audio for voice cloning (optional)
REFERENCE_AUDIO_PATH = os.getenv("REFERENCE_AUDIO", None)

# Cache configuration
CACHE_MAX_SIZE = int(os.getenv("TTS_CACHE_SIZE", "100"))


# ===========================================
# LRU Cache for Synthesis
# ===========================================
class LRUCache:
    """Simple LRU cache for TTS synthesis results"""
    
    def __init__(self, max_size: int = 100):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            self.cache.move_to_end(key)
            logger.debug(f"Cache hit for key: {key[:16]}...")
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Dict):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                logger.debug(f"Cache evicted oldest: {oldest[:16]}...")
            self.cache[key] = value
    
    def make_key(self, text: str, ref_path: Optional[str] = None) -> str:
        """Generate cache key from text and reference audio path"""
        content = f"{text}:{ref_path or 'default'}"
        return hashlib.md5(content.encode()).hexdigest()


synthesis_cache = LRUCache(max_size=CACHE_MAX_SIZE)


# ===========================================
# App Initialization
# ===========================================
app = FastAPI(
    title="Spanish TTS Service",
    description=f"Text-to-Speech synthesis (backend: {TTS_BACKEND})",
    version="1.1.0"
)


# ===========================================
# Model Loading
# ===========================================
tts_model = None
kokoro_pipeline = None
kokoro_voice_tensor = None

@app.on_event("startup")
async def load_tts_model():
    """Load TTS model on startup based on TTS_BACKEND setting."""
    global tts_model, kokoro_pipeline, kokoro_voice_tensor

    if TTS_BACKEND == "kokoro":
        logger.info(f"Loading Kokoro TTS on {DEVICE}...")
        if KPipeline is None:
            raise RuntimeError("Kokoro not installed. pip install kokoro>=0.9.4")

        kokoro_pipeline = KPipeline(lang_code=KOKORO_LANG)
        logger.info(f"Kokoro pipeline loaded (lang={KOKORO_LANG})")

        # Load evolved voice tensor if specified
        if KOKORO_VOICE_PATH and Path(KOKORO_VOICE_PATH).exists():
            kokoro_voice_tensor = torch.load(
                KOKORO_VOICE_PATH, map_location=DEVICE, weights_only=True
            )
            logger.info(f"Loaded evolved voice tensor: {KOKORO_VOICE_PATH}")
        else:
            # Use built-in Kokoro voice
            kokoro_voice_tensor = kokoro_pipeline.load_voice(KOKORO_VOICE_STYLE)
            logger.info(f"Using built-in Kokoro voice: {KOKORO_VOICE_STYLE}")

        logger.info("Kokoro TTS ready!")

    else:
        logger.info(f"Loading F5-TTS model on {DEVICE}...")
        try:
            if F5TTS is not None:
                tts_model = F5TTS(device=DEVICE)
            else:
                tts_model = load_model(MODEL_PATH, device=DEVICE)
            logger.info("F5-TTS model loaded successfully!")
        except Exception as e:
            logger.error(f"Error loading TTS model: {e}")
            raise


# ===========================================
# Pydantic Models
# ===========================================
class SynthesizeRequest(BaseModel):
    text: str
    reference_audio: Optional[str] = None  # Base64 encoded or path
    reference_text: Optional[str] = None   # Transcript of reference audio
    speed: float = 1.0
    return_bytes: bool = False

class SynthesizeResponse(BaseModel):
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    duration_seconds: float


# ===========================================
# Endpoints
# ===========================================
@app.get("/health")
async def health():
    """Health check"""
    if TTS_BACKEND == "kokoro":
        model_loaded = kokoro_pipeline is not None
    else:
        model_loaded = tts_model is not None

    return {
        "status": "healthy",
        "backend": TTS_BACKEND,
        "model_loaded": model_loaded,
        "device": DEVICE,
    }


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """
    Synthesize speech from text.

    Dispatches to F5-TTS or Kokoro depending on TTS_BACKEND.
    """
    if TTS_BACKEND == "kokoro":
        return await _synthesize_kokoro(request)
    return await _synthesize_f5(request)


async def _synthesize_kokoro(request: SynthesizeRequest):
    """Synthesize using Kokoro TTS backend."""
    if kokoro_pipeline is None:
        raise HTTPException(status_code=503, detail="Kokoro model not loaded")

    try:
        # Cache check
        cache_ref = f"kokoro:{KOKORO_VOICE_STYLE}"
        if not request.return_bytes and request.speed == 1.0:
            cache_key = synthesis_cache.make_key(request.text, cache_ref)
            cached = synthesis_cache.get(cache_key)
            if cached:
                return SynthesizeResponse(**cached)

        logger.info(f"Kokoro synthesizing: {request.text[:50]}...")

        # Generate audio chunks and concatenate
        audio_chunks = []
        for chunk in kokoro_pipeline(
            request.text,
            voice=kokoro_voice_tensor,
            speed=request.speed,
        ):
            if chunk.audio is not None:
                audio_chunks.append(chunk.audio.numpy())

        if not audio_chunks:
            raise HTTPException(status_code=500, detail="Kokoro produced no audio")

        audio = np.concatenate(audio_chunks)
        sample_rate = 24000  # Kokoro native sample rate

        duration = len(audio) / sample_rate

        if request.return_bytes:
            buffer = io.BytesIO()
            sf.write(buffer, audio, sample_rate, format='WAV')
            return Response(content=buffer.getvalue(), media_type="audio/wav")

        # Save to file
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_OUTPUT_DIR / f"{audio_id}.wav"
        sf.write(str(audio_path), audio, sample_rate)

        # Encode to base64
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV')
        audio_base64 = base64.b64encode(buffer.getvalue()).decode()

        response_data = {
            "audio_url": f"/audio/{audio_id}.wav",
            "audio_base64": audio_base64,
            "duration_seconds": duration,
        }

        if request.speed == 1.0:
            cache_key = synthesis_cache.make_key(request.text, cache_ref)
            synthesis_cache.set(cache_key, response_data)

        return SynthesizeResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _synthesize_f5(request: SynthesizeRequest):
    """Synthesize using F5-TTS backend."""
    if tts_model is None:
        raise HTTPException(status_code=503, detail="TTS model not loaded")

    try:
        ref_path = request.reference_audio or REFERENCE_AUDIO_PATH

        # Check cache
        if not request.return_bytes and request.speed == 1.0:
            cache_key = synthesis_cache.make_key(request.text, ref_path)
            cached = synthesis_cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for text: {request.text[:30]}...")
                return SynthesizeResponse(**cached)

        # Handle reference audio
        ref_audio = None
        ref_text = request.reference_text or ""

        if request.reference_audio:
            if request.reference_audio.startswith("data:"):
                audio_data = base64.b64decode(
                    request.reference_audio.split(",")[1]
                )
                ref_audio = io.BytesIO(audio_data)
            elif os.path.exists(request.reference_audio):
                ref_audio = request.reference_audio
        elif REFERENCE_AUDIO_PATH and os.path.exists(REFERENCE_AUDIO_PATH):
            ref_audio = REFERENCE_AUDIO_PATH

        logger.info(f"F5 synthesizing: {request.text[:50]}...")

        # Generate speech
        if F5TTS is not None:
            audio, sample_rate = tts_model.infer(
                text=request.text,
                ref_audio=ref_audio,
                ref_text=ref_text,
                speed=request.speed
            )
        else:
            audio, sample_rate = infer_process(
                model=tts_model,
                text=request.text,
                ref_audio=ref_audio,
                ref_text=ref_text
            )

        duration = len(audio) / sample_rate

        if request.return_bytes:
            buffer = io.BytesIO()
            sf.write(buffer, audio, sample_rate, format='WAV')
            return Response(content=buffer.getvalue(), media_type="audio/wav")

        # Save to file
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_OUTPUT_DIR / f"{audio_id}.wav"
        sf.write(str(audio_path), audio, sample_rate)

        # Encode to base64
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV')
        audio_base64 = base64.b64encode(buffer.getvalue()).decode()

        response_data = {
            "audio_url": f"/audio/{audio_id}.wav",
            "audio_base64": audio_base64,
            "duration_seconds": duration,
        }

        if request.speed == 1.0:
            cache_key = synthesis_cache.make_key(request.text, ref_path)
            synthesis_cache.set(cache_key, response_data)

        return SynthesizeResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize_stream")
async def synthesize_stream(request: SynthesizeRequest):
    """
    Synthesize speech and stream audio chunks.
    Useful for real-time applications.
    """
    try:
        if TTS_BACKEND == "kokoro":
            if kokoro_pipeline is None:
                raise HTTPException(status_code=503, detail="Kokoro model not loaded")

            audio_chunks = []
            for chunk in kokoro_pipeline(
                request.text,
                voice=kokoro_voice_tensor,
                speed=request.speed,
            ):
                if chunk.audio is not None:
                    audio_chunks.append(chunk.audio.numpy())

            if not audio_chunks:
                raise HTTPException(status_code=500, detail="Kokoro produced no audio")

            audio = np.concatenate(audio_chunks)
            sample_rate = 24000
        else:
            if tts_model is None:
                raise HTTPException(status_code=503, detail="TTS model not loaded")

            if F5TTS is not None:
                audio, sample_rate = tts_model.infer(
                    text=request.text,
                    speed=request.speed
                )
            else:
                audio, sample_rate = infer_process(
                    model=tts_model,
                    text=request.text
                )

        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV')

        return Response(
            content=buffer.getvalue(),
            media_type="audio/wav"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/set_reference")
async def set_reference(
    audio: UploadFile = File(...),
    transcript: str = ""
):
    """
    Upload a reference audio for voice cloning
    This will be used as the default voice for synthesis
    """
    global REFERENCE_AUDIO_PATH
    
    # Save reference audio
    ref_path = AUDIO_OUTPUT_DIR / "reference.wav"
    content = await audio.read()
    
    with open(ref_path, "wb") as f:
        f.write(content)
    
    REFERENCE_AUDIO_PATH = str(ref_path)
    
    # Save transcript if provided
    if transcript:
        with open(AUDIO_OUTPUT_DIR / "reference.txt", "w") as f:
            f.write(transcript)
    
    return {"status": "Reference audio saved", "path": REFERENCE_AUDIO_PATH}


@app.post("/set_voice")
async def set_voice(style: str = "neutral"):
    """
    Switch the active Kokoro voice tensor (only available with kokoro backend).

    Args:
        style: Voice style name. Loads the tensor from
               /data/distillation/evolved_voices/{style}.pt
    """
    global kokoro_voice_tensor

    if TTS_BACKEND != "kokoro":
        raise HTTPException(
            status_code=400,
            detail="Voice switching only available with TTS_BACKEND=kokoro",
        )

    tensor_path = Path(f"/data/distillation/evolved_voices/{style}.pt")
    if not tensor_path.exists():
        raise HTTPException(status_code=404, detail=f"Voice tensor not found: {style}")

    kokoro_voice_tensor = torch.load(str(tensor_path), map_location=DEVICE, weights_only=True)
    logger.info(f"Switched to voice style: {style}")

    return {"status": "ok", "style": style, "tensor_path": str(tensor_path)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
