"""
Spanish F5-TTS Service
Text-to-Speech synthesis using F5 model fine-tuned for Spanish
"""

import os
import io
import base64
import uuid
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
import torch
import soundfile as sf
import numpy as np

# F5-TTS imports (installed via git+https://github.com/jpgallegoar/Spanish-F5)
try:
    from f5_tts.api import F5TTS
except ImportError:
    from f5_tts.infer.utils_infer import load_model, infer_process
    F5TTS = None


# ===========================================
# Configuration
# ===========================================
DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.getenv("TTS_MODEL", "jpgallegoar/F5-Spanish")
AUDIO_OUTPUT_DIR = Path("/app/audio")
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True)

# Reference audio for voice cloning (optional)
REFERENCE_AUDIO_PATH = os.getenv("REFERENCE_AUDIO", None)


# ===========================================
# App Initialization
# ===========================================
app = FastAPI(
    title="Spanish F5-TTS Service",
    description="Text-to-Speech synthesis using F5 Spanish model",
    version="1.0.0"
)


# ===========================================
# Model Loading
# ===========================================
tts_model = None

@app.on_event("startup")
async def load_tts_model():
    """Load TTS model on startup"""
    global tts_model
    print(f"Loading F5-TTS model on {DEVICE}...")
    
    try:
        if F5TTS is not None:
            tts_model = F5TTS(device=DEVICE)
        else:
            # Fallback loading method
            tts_model = load_model(MODEL_PATH, device=DEVICE)
        print("F5-TTS model loaded successfully!")
    except Exception as e:
        print(f"Error loading TTS model: {e}")
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
    return {
        "status": "healthy",
        "model_loaded": tts_model is not None,
        "device": DEVICE
    }


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """
    Synthesize speech from text
    
    Args:
        text: Text to synthesize
        reference_audio: Optional reference audio for voice cloning
        reference_text: Transcript of reference audio
        speed: Speech speed multiplier
        return_bytes: If True, return raw audio in response
    """
    if tts_model is None:
        raise HTTPException(status_code=503, detail="TTS model not loaded")
    
    try:
        # Handle reference audio
        ref_audio = None
        ref_text = request.reference_text or ""
        
        if request.reference_audio:
            if request.reference_audio.startswith("data:"):
                # Base64 encoded
                audio_data = base64.b64decode(
                    request.reference_audio.split(",")[1]
                )
                ref_audio = io.BytesIO(audio_data)
            elif os.path.exists(request.reference_audio):
                # File path
                ref_audio = request.reference_audio
        elif REFERENCE_AUDIO_PATH and os.path.exists(REFERENCE_AUDIO_PATH):
            ref_audio = REFERENCE_AUDIO_PATH
        
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
        
        # Calculate duration
        duration = len(audio) / sample_rate
        
        if request.return_bytes:
            # Return raw audio bytes
            buffer = io.BytesIO()
            sf.write(buffer, audio, sample_rate, format='WAV')
            return Response(
                content=buffer.getvalue(),
                media_type="audio/wav"
            )
        
        # Save to file
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_OUTPUT_DIR / f"{audio_id}.wav"
        sf.write(str(audio_path), audio, sample_rate)
        
        # Encode to base64
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV')
        audio_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return SynthesizeResponse(
            audio_url=f"/audio/{audio_id}.wav",
            audio_base64=audio_base64,
            duration_seconds=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize_stream")
async def synthesize_stream(request: SynthesizeRequest):
    """
    Synthesize speech and stream audio chunks
    Useful for real-time applications
    """
    if tts_model is None:
        raise HTTPException(status_code=503, detail="TTS model not loaded")
    
    try:
        # For now, generate full audio and return
        # TODO: Implement true streaming when F5-TTS supports it
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
        
        # Convert to bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV')
        
        return Response(
            content=buffer.getvalue(),
            media_type="audio/wav"
        )
        
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
