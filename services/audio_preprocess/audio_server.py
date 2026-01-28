"""
Audio Preprocessing Service
Noise suppression using DeepFilterNet + Speaker Identification with SpeechBrain
"""

import os
import io
import uuid
import hashlib
from typing import Optional, Dict, Tuple
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel
import torch
import numpy as np
import soundfile as sf
from loguru import logger

# Configure logging
logger.add(
    "logs/audio_preprocess_{time}.log",
    rotation="100 MB",
    retention="7 days",
    level="INFO"
)


# ===========================================
# Configuration
# ===========================================
DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
SPEAKER_DB_PATH = Path("/app/data/speakers")
SPEAKER_DB_PATH.mkdir(parents=True, exist_ok=True)

# Model selection
DENOISE_MODEL = os.getenv("DENOISE_MODEL", "deepfilternet")  # or "rnnoise"


# ===========================================
# App Initialization
# ===========================================
app = FastAPI(
    title="Audio Preprocessing Service",
    description="Noise suppression and speaker identification for call center audio",
    version="1.0.0"
)


# ===========================================
# Model Loading
# ===========================================
df_model = None
df_state = None
speaker_model = None


@app.on_event("startup")
async def load_models():
    """Load noise suppression and speaker identification models"""
    global df_model, df_state, speaker_model
    
    logger.info(f"Loading audio preprocessing models on {DEVICE}...")
    
    # Load DeepFilterNet for noise suppression
    try:
        from df.enhance import init_df, enhance
        df_model, df_state, _ = init_df()
        logger.info("DeepFilterNet loaded successfully!")
    except ImportError:
        logger.warning("DeepFilterNet not available, trying noisereduce fallback")
        df_model = None
    except Exception as e:
        logger.error(f"Error loading DeepFilterNet: {e}")
        df_model = None
    
    # Load SpeechBrain for speaker identification
    try:
        from speechbrain.inference import SpeakerRecognition
        speaker_model = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="/app/models/speaker_recognition",
            run_opts={"device": DEVICE}
        )
        logger.info("SpeechBrain speaker recognition loaded successfully!")
    except Exception as e:
        logger.error(f"Error loading speaker model: {e}")
        speaker_model = None


# ===========================================
# Pydantic Models
# ===========================================
class DenoiseResponse(BaseModel):
    audio_base64: Optional[str] = None
    duration_seconds: float
    noise_reduced: bool


class SpeakerEnrollResponse(BaseModel):
    speaker_id: str
    status: str


class SpeakerVerifyResponse(BaseModel):
    speaker_id: Optional[str] = None
    score: float
    is_match: bool
    threshold: float


# ===========================================
# Noise Suppression Functions
# ===========================================
def denoise_with_deepfilter(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """Apply DeepFilterNet noise suppression"""
    global df_model, df_state
    
    if df_model is None:
        return audio
    
    from df.enhance import enhance
    
    # DeepFilterNet expects specific format
    if len(audio.shape) == 1:
        audio = audio.reshape(1, -1)
    
    # Convert to torch tensor
    audio_tensor = torch.from_numpy(audio).float()
    
    # Enhance (denoise)
    enhanced = enhance(df_model, df_state, audio_tensor)
    
    return enhanced.squeeze().numpy()


def denoise_with_noisereduce(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """Fallback noise reduction using noisereduce library"""
    try:
        import noisereduce as nr
        return nr.reduce_noise(y=audio, sr=sample_rate, prop_decrease=0.8)
    except ImportError:
        logger.warning("noisereduce not available")
        return audio


def apply_noise_suppression(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """Apply the configured noise suppression method"""
    if DENOISE_MODEL == "deepfilternet" and df_model is not None:
        logger.debug("Using DeepFilterNet for noise suppression")
        return denoise_with_deepfilter(audio, sample_rate)
    else:
        logger.debug("Using noisereduce fallback for noise suppression")
        return denoise_with_noisereduce(audio, sample_rate)


# ===========================================
# Speaker Identification Functions
# ===========================================
def get_speaker_embedding(audio_path: str) -> Optional[np.ndarray]:
    """Extract speaker embedding from audio file"""
    if speaker_model is None:
        return None
    
    try:
        embedding = speaker_model.encode_batch(
            torch.tensor(sf.read(audio_path)[0]).unsqueeze(0)
        )
        return embedding.squeeze().cpu().numpy()
    except Exception as e:
        logger.error(f"Error extracting speaker embedding: {e}")
        return None


def compare_embeddings(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings"""
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    return float(similarity)


def find_matching_speaker(embedding: np.ndarray, threshold: float = 0.7) -> Tuple[Optional[str], float]:
    """Find matching speaker from enrolled speakers"""
    best_match = None
    best_score = 0.0
    
    for speaker_file in SPEAKER_DB_PATH.glob("*.npy"):
        speaker_id = speaker_file.stem
        stored_embedding = np.load(speaker_file)
        score = compare_embeddings(embedding, stored_embedding)
        
        if score > best_score:
            best_score = score
            if score >= threshold:
                best_match = speaker_id
    
    return best_match, best_score


# ===========================================
# Endpoints
# ===========================================
@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "denoise_model": DENOISE_MODEL,
        "deepfilter_loaded": df_model is not None,
        "speaker_model_loaded": speaker_model is not None,
        "device": DEVICE
    }


@app.post("/denoise", response_model=DenoiseResponse)
async def denoise_audio(
    audio: UploadFile = File(...),
    return_bytes: bool = Form(False)
):
    """
    Apply noise suppression to audio
    
    Args:
        audio: Audio file (WAV format recommended)
        return_bytes: If True, return raw audio bytes instead of base64
    """
    try:
        # Read audio
        content = await audio.read()
        audio_data, sample_rate = sf.read(io.BytesIO(content))
        
        logger.info(f"Processing audio: {len(audio_data)/sample_rate:.2f}s at {sample_rate}Hz")
        
        # Apply noise suppression
        denoised = apply_noise_suppression(audio_data, sample_rate)
        
        # Calculate duration
        duration = len(denoised) / sample_rate
        
        if return_bytes:
            buffer = io.BytesIO()
            sf.write(buffer, denoised, sample_rate, format='WAV')
            return Response(
                content=buffer.getvalue(),
                media_type="audio/wav"
            )
        
        # Encode to base64
        import base64
        buffer = io.BytesIO()
        sf.write(buffer, denoised, sample_rate, format='WAV')
        audio_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return DenoiseResponse(
            audio_base64=audio_base64,
            duration_seconds=duration,
            noise_reduced=True
        )
        
    except Exception as e:
        logger.error(f"Denoise error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/denoise_bytes")
async def denoise_audio_bytes(audio: UploadFile = File(...)):
    """Denoise and return raw audio bytes (optimized for pipeline)"""
    try:
        content = await audio.read()
        audio_data, sample_rate = sf.read(io.BytesIO(content))
        
        denoised = apply_noise_suppression(audio_data, sample_rate)
        
        buffer = io.BytesIO()
        sf.write(buffer, denoised, sample_rate, format='WAV')
        
        return Response(
            content=buffer.getvalue(),
            media_type="audio/wav"
        )
        
    except Exception as e:
        logger.error(f"Denoise bytes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/speakers/enroll", response_model=SpeakerEnrollResponse)
async def enroll_speaker(
    audio: UploadFile = File(...),
    speaker_id: str = Form(None),
    speaker_name: str = Form(None)
):
    """
    Enroll a new speaker for identification
    
    Args:
        audio: Reference audio (5-30 seconds of clean speech)
        speaker_id: Custom speaker ID (generated if not provided)
        speaker_name: Human-readable name for the speaker
    """
    if speaker_model is None:
        raise HTTPException(status_code=503, detail="Speaker model not loaded")
    
    try:
        # Generate speaker ID if not provided
        if not speaker_id:
            speaker_id = f"spk_{uuid.uuid4().hex[:8]}"
        
        # Save audio temporarily
        content = await audio.read()
        temp_path = f"/tmp/{speaker_id}_enroll.wav"
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Extract embedding
        embedding = get_speaker_embedding(temp_path)
        
        if embedding is None:
            raise HTTPException(status_code=500, detail="Failed to extract speaker embedding")
        
        # Save embedding
        np.save(SPEAKER_DB_PATH / f"{speaker_id}.npy", embedding)
        
        # Save metadata
        if speaker_name:
            with open(SPEAKER_DB_PATH / f"{speaker_id}.txt", "w") as f:
                f.write(speaker_name)
        
        logger.info(f"Enrolled speaker: {speaker_id} ({speaker_name or 'unnamed'})")
        
        # Cleanup
        os.remove(temp_path)
        
        return SpeakerEnrollResponse(
            speaker_id=speaker_id,
            status="enrolled"
        )
        
    except Exception as e:
        logger.error(f"Enrollment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/speakers/identify", response_model=SpeakerVerifyResponse)
async def identify_speaker(
    audio: UploadFile = File(...),
    threshold: float = Form(0.7)
):
    """
    Identify speaker from audio
    
    Args:
        audio: Audio to identify speaker from
        threshold: Minimum similarity score for a match (0.0-1.0)
    """
    if speaker_model is None:
        raise HTTPException(status_code=503, detail="Speaker model not loaded")
    
    try:
        # Save audio temporarily
        content = await audio.read()
        temp_path = f"/tmp/identify_{uuid.uuid4().hex[:8]}.wav"
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Extract embedding
        embedding = get_speaker_embedding(temp_path)
        
        if embedding is None:
            raise HTTPException(status_code=500, detail="Failed to extract speaker embedding")
        
        # Find matching speaker
        speaker_id, score = find_matching_speaker(embedding, threshold)
        
        # Cleanup
        os.remove(temp_path)
        
        logger.info(f"Speaker identification: {speaker_id or 'unknown'} (score: {score:.3f})")
        
        return SpeakerVerifyResponse(
            speaker_id=speaker_id,
            score=score,
            is_match=speaker_id is not None,
            threshold=threshold
        )
        
    except Exception as e:
        logger.error(f"Identification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/speakers")
async def list_speakers():
    """List all enrolled speakers"""
    speakers = []
    
    for emb_file in SPEAKER_DB_PATH.glob("*.npy"):
        speaker_id = emb_file.stem
        name_file = SPEAKER_DB_PATH / f"{speaker_id}.txt"
        name = name_file.read_text() if name_file.exists() else None
        
        speakers.append({
            "speaker_id": speaker_id,
            "name": name
        })
    
    return {"speakers": speakers, "count": len(speakers)}


@app.delete("/speakers/{speaker_id}")
async def delete_speaker(speaker_id: str):
    """Delete an enrolled speaker"""
    emb_file = SPEAKER_DB_PATH / f"{speaker_id}.npy"
    name_file = SPEAKER_DB_PATH / f"{speaker_id}.txt"
    
    if not emb_file.exists():
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    emb_file.unlink()
    if name_file.exists():
        name_file.unlink()
    
    logger.info(f"Deleted speaker: {speaker_id}")
    
    return {"status": "deleted", "speaker_id": speaker_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
