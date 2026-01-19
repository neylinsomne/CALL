"""
Whisper STT Service
Speech-to-Text using Faster Whisper optimized for Spanish
"""

import os
import io
import tempfile
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from faster_whisper import WhisperModel


# ===========================================
# Configuration
# ===========================================
MODEL_SIZE = os.getenv("STT_MODEL", "large-v3")
DEVICE = os.getenv("DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "float16")  # or "int8" for less VRAM
LANGUAGE = os.getenv("LANGUAGE", "es")


# ===========================================
# App Initialization
# ===========================================
app = FastAPI(
    title="Whisper STT Service",
    description="Speech-to-Text transcription using Faster Whisper",
    version="1.0.0"
)


# ===========================================
# Model Loading
# ===========================================
whisper_model = None

@app.on_event("startup")
async def load_model():
    """Load Whisper model on startup"""
    global whisper_model
    print(f"Loading Whisper {MODEL_SIZE} on {DEVICE}...")
    
    try:
        whisper_model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            download_root="/app/models"
        )
        print("Whisper model loaded successfully!")
    except Exception as e:
        print(f"Error loading Whisper: {e}")
        # Try CPU fallback
        print("Falling back to CPU...")
        whisper_model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            download_root="/app/models"
        )


# ===========================================
# Pydantic Models
# ===========================================
class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float
    segments: list


# ===========================================
# Endpoints
# ===========================================
@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "model_loaded": whisper_model is not None,
        "model_size": MODEL_SIZE,
        "device": DEVICE
    }


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    task: str = Form("transcribe")  # or "translate"
):
    """
    Transcribe audio to text
    
    Args:
        audio: Audio file (WAV, MP3, etc.)
        language: Language code (e.g., 'es', 'en'). Auto-detect if not provided
        task: 'transcribe' or 'translate' (to English)
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="STT model not loaded")
    
    try:
        # Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Transcribe
        lang = language or LANGUAGE
        segments, info = whisper_model.transcribe(
            tmp_path,
            language=lang if lang != "auto" else None,
            task=task,
            vad_filter=True,  # Voice Activity Detection
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            )
        )
        
        # Collect results
        segments_list = []
        full_text = []
        
        for segment in segments:
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "confidence": segment.avg_logprob
            })
            full_text.append(segment.text)
        
        # Cleanup temp file
        os.unlink(tmp_path)
        
        return TranscriptionResponse(
            text=" ".join(full_text).strip(),
            language=info.language,
            confidence=info.language_probability,
            segments=segments_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe_stream")
async def transcribe_stream(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Transcribe audio with streaming response
    Returns segments as they are processed
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="STT model not loaded")
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        lang = language or LANGUAGE
        segments, info = whisper_model.transcribe(
            tmp_path,
            language=lang if lang != "auto" else None,
            vad_filter=True
        )
        
        results = []
        for segment in segments:
            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
        
        os.unlink(tmp_path)
        
        return {
            "language": info.language,
            "segments": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect_language")
async def detect_language(audio: UploadFile = File(...)):
    """Detect language from audio sample"""
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="STT model not loaded")
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Use first 30 seconds for language detection
        _, info = whisper_model.transcribe(tmp_path)
        
        os.unlink(tmp_path)
        
        return {
            "language": info.language,
            "probability": info.language_probability
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
