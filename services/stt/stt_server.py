"""
Whisper STT Service
Speech-to-Text using Faster Whisper optimized for Spanish
Enhanced with clarification system and error correction
"""

import os
import io
import json
import base64
import tempfile
from typing import Optional, List, Dict

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from faster_whisper import WhisperModel
from loguru import logger

# Import enhanced features
try:
    from clarification_system import get_clarification_system
    from error_correction_bank import get_error_bank
    ENHANCED_FEATURES_AVAILABLE = True
    logger.info("Enhanced STT features loaded")
except ImportError as e:
    logger.warning(f"Enhanced features not available: {e}")
    ENHANCED_FEATURES_AVAILABLE = False


# ===========================================
# Configuration
# ===========================================
MODEL_SIZE = os.getenv("STT_MODEL", "large-v3")
DEVICE = os.getenv("DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "float16")  # or "int8" for less VRAM
LANGUAGE = os.getenv("LANGUAGE", "es")

# Triton Inference Server configuration
USE_TRITON = os.getenv("USE_TRITON", "false").lower() == "true"
TRITON_URL = os.getenv("TRITON_URL", "http://triton:8010")
TRITON_MODEL_NAME = os.getenv("TRITON_MODEL_NAME", "whisper_stt")


# ===========================================
# App Initialization
# ===========================================
app = FastAPI(
    title="Whisper STT Service",
    description="Speech-to-Text transcription using Faster Whisper",
    version="1.0.0"
)


# ===========================================
# Triton Inference Helper
# ===========================================
_triton_client = None


async def _get_triton_client() -> httpx.AsyncClient:
    """Get or create a persistent HTTP client for Triton."""
    global _triton_client
    if _triton_client is None or _triton_client.is_closed:
        _triton_client = httpx.AsyncClient(timeout=30.0)
    return _triton_client


async def triton_transcribe(
    audio_bytes: bytes,
    language: str = "es",
    word_timestamps: bool = False,
) -> dict:
    """Call Triton Inference Server for transcription."""
    client = await _get_triton_client()

    # Triton V2 inference protocol with BYTES input
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
    payload = {
        "inputs": [
            {
                "name": "audio_bytes",
                "shape": [1],
                "datatype": "BYTES",
                "data": [audio_b64],
            },
            {
                "name": "language",
                "shape": [1],
                "datatype": "BYTES",
                "data": [language],
            },
        ],
        "outputs": [{"name": "result_json"}],
    }

    if word_timestamps:
        payload["inputs"].append({
            "name": "word_timestamps",
            "shape": [1],
            "datatype": "BOOL",
            "data": [True],
        })

    response = await client.post(
        f"{TRITON_URL}/v2/models/{TRITON_MODEL_NAME}/infer",
        json=payload,
    )
    response.raise_for_status()

    result = response.json()
    result_json_str = result["outputs"][0]["data"][0]
    return json.loads(result_json_str)


# ===========================================
# Model Loading
# ===========================================
whisper_model = None
_triton_available = False


@app.on_event("startup")
async def load_model():
    """Load Whisper model on startup, or connect to Triton."""
    global whisper_model, _triton_available

    if USE_TRITON:
        logger.info(f"Triton mode enabled, connecting to {TRITON_URL}...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{TRITON_URL}/v2/health/ready")
                if resp.status_code == 200:
                    logger.info("Triton server is ready - using Triton backend")
                    _triton_available = True
                    whisper_model = "TRITON"
                    return
                else:
                    logger.warning(
                        f"Triton returned status {resp.status_code}, "
                        "will retry on first request"
                    )
                    _triton_available = True
                    whisper_model = "TRITON"
                    return
        except Exception as e:
            logger.warning(
                f"Cannot reach Triton at startup: {e}. "
                "Falling back to local model."
            )

    # Local model loading (original behavior or Triton fallback)
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
        print("Falling back to CPU...")
        whisper_model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            download_root="/app/models"
        )


def _is_triton_mode() -> bool:
    """Check if we should use Triton for inference."""
    return USE_TRITON and whisper_model == "TRITON"


async def _fallback_to_local():
    """Load local model if Triton fails."""
    global whisper_model, _triton_available
    logger.warning("Falling back from Triton to local Whisper model...")
    _triton_available = False
    try:
        whisper_model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            download_root="/app/models"
        )
        logger.info("Local Whisper model loaded as fallback")
    except Exception:
        whisper_model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            download_root="/app/models"
        )
        logger.info("Local Whisper model loaded on CPU as fallback")


# ===========================================
# Pydantic Models
# ===========================================
class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float
    segments: list


class EnhancedTranscriptionResponse(BaseModel):
    text: str
    corrected_text: str
    language: str
    confidence: float
    segments: list
    word_confidences: list
    corrections_made: list
    needs_clarification: bool
    clarification_prompt: Optional[str] = None
    clarification_type: Optional[str] = None
    intent_detected: Optional[str] = None
    normalized_entities: dict


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
        "device": DEVICE,
        "triton_mode": _is_triton_mode(),
        "triton_url": TRITON_URL if _is_triton_mode() else None,
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
        content = await audio.read()
        lang = language or LANGUAGE

        # --- Triton path ---
        if _is_triton_mode():
            try:
                triton_result = await triton_transcribe(content, lang)
                if "error" in triton_result:
                    raise RuntimeError(triton_result["error"])
                return TranscriptionResponse(
                    text=triton_result.get("text", ""),
                    language=triton_result.get("language", lang),
                    confidence=triton_result.get("confidence", 0.0),
                    segments=triton_result.get("segments", []),
                )
            except Exception as e:
                logger.warning(f"Triton inference failed: {e}, falling back")
                await _fallback_to_local()

        # --- Local model path ---
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        segments, info = whisper_model.transcribe(
            tmp_path,
            language=lang if lang != "auto" else None,
            task=task,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            )
        )

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

        os.unlink(tmp_path)

        return TranscriptionResponse(
            text=" ".join(full_text).strip(),
            language=info.language,
            confidence=info.language_probability,
            segments=segments_list
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe/enhanced", response_model=EnhancedTranscriptionResponse)
async def transcribe_enhanced(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    conversation_id: Optional[str] = Form(None),
    enable_correction: bool = Form(True),
    enable_clarification: bool = Form(True)
):
    """
    Enhanced transcription with error correction and clarification detection

    Args:
        audio: Audio file (WAV, MP3, etc.)
        language: Language code (e.g., 'es', 'en')
        conversation_id: ID for tracking clarification history
        enable_correction: Apply automatic error correction
        enable_clarification: Detect when clarification is needed

    Returns:
        Enhanced response with corrections, confidence scores, and clarification needs
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="STT model not loaded")

    if not ENHANCED_FEATURES_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Enhanced features not available. Install sentence-transformers and faiss-cpu."
        )

    try:
        content = await audio.read()
        lang = language or LANGUAGE

        segments_list = []
        full_text = []
        word_confidences = []
        detected_language = lang
        detected_confidence = 0.0

        # --- Triton path ---
        triton_ok = False
        if _is_triton_mode():
            try:
                triton_result = await triton_transcribe(
                    content, lang, word_timestamps=True
                )
                if "error" in triton_result:
                    raise RuntimeError(triton_result["error"])

                detected_language = triton_result.get("language", lang)
                detected_confidence = triton_result.get("confidence", 0.0)

                for seg in triton_result.get("segments", []):
                    segments_list.append(seg)
                    full_text.append(seg.get("text", ""))
                    for w in seg.get("words", []):
                        word_confidences.append({
                            "word": w.get("word", "").strip(),
                            "confidence": w.get("probability", 0.0),
                        })
                triton_ok = True
            except Exception as e:
                logger.warning(f"Triton enhanced failed: {e}, falling back")
                await _fallback_to_local()

        # --- Local model path ---
        if not triton_ok:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            segments, info = whisper_model.transcribe(
                tmp_path,
                language=lang if lang != "auto" else None,
                task="transcribe",
                vad_filter=True,
                word_timestamps=True,
                beam_size=5,
                temperature=0.0,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6
            )

            for segment in segments:
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "confidence": segment.avg_logprob
                }
                if hasattr(segment, 'words') and segment.words:
                    segment_data["words"] = [
                        {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability
                        }
                        for word in segment.words
                    ]
                    for word in segment.words:
                        word_confidences.append({
                            "word": word.word.strip(),
                            "confidence": word.probability
                        })
                segments_list.append(segment_data)
                full_text.append(segment.text)

            os.unlink(tmp_path)
            detected_language = info.language
            detected_confidence = info.language_probability

        original_text = " ".join(full_text).strip()
        corrected_text = original_text
        corrections_made = []

        # Apply error correction if enabled
        if enable_correction:
            error_bank = get_error_bank()
            corrected_text, corrections_made = error_bank.correct_transcription(
                original_text,
                confidence_scores=word_confidences
            )

        # Check if clarification is needed
        needs_clarification = False
        clarification_prompt = None
        clarification_type = None

        if enable_clarification and conversation_id:
            clarification_system = get_clarification_system()
            clarification_result = clarification_system.should_ask_clarification(
                corrected_text,
                word_confidences,
                conversation_id
            )

            if clarification_result:
                needs_clarification = True
                clarification_prompt = clarification_result.get("prompt")
                clarification_type = clarification_result.get("type")

        # Detect intent (basic patterns)
        intent_detected = _detect_intent(corrected_text)

        # Normalize entities (numbers, emails, etc.)
        normalized_entities = _normalize_entities(corrected_text)

        return EnhancedTranscriptionResponse(
            text=original_text,
            corrected_text=corrected_text,
            language=detected_language,
            confidence=detected_confidence,
            segments=segments_list,
            word_confidences=word_confidences,
            corrections_made=corrections_made,
            needs_clarification=needs_clarification,
            clarification_prompt=clarification_prompt,
            clarification_type=clarification_type,
            intent_detected=intent_detected,
            normalized_entities=normalized_entities
        )

    except Exception as e:
        logger.error(f"Error in enhanced transcription: {e}")
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
        content = await audio.read()
        lang = language or LANGUAGE

        # --- Triton path ---
        if _is_triton_mode():
            try:
                triton_result = await triton_transcribe(content, lang)
                if "error" not in triton_result:
                    return {
                        "language": triton_result.get("language", lang),
                        "segments": [
                            {"start": s["start"], "end": s["end"], "text": s["text"]}
                            for s in triton_result.get("segments", [])
                        ],
                    }
            except Exception as e:
                logger.warning(f"Triton stream failed: {e}, falling back")
                await _fallback_to_local()

        # --- Local model path ---
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

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
        content = await audio.read()

        # --- Triton path ---
        if _is_triton_mode():
            try:
                triton_result = await triton_transcribe(content, "auto")
                if "error" not in triton_result:
                    return {
                        "language": triton_result.get("language", ""),
                        "probability": triton_result.get("confidence", 0.0),
                    }
            except Exception as e:
                logger.warning(f"Triton detect_language failed: {e}, falling back")
                await _fallback_to_local()

        # --- Local model path ---
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        _, info = whisper_model.transcribe(tmp_path)
        os.unlink(tmp_path)

        return {
            "language": info.language,
            "probability": info.language_probability
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learn_correction")
async def learn_correction(
    original_text: str = Form(...),
    corrected_text: str = Form(...)
):
    """
    Learn from user corrections to improve error correction bank

    Args:
        original_text: The original transcription
        corrected_text: The user's corrected version
    """
    if not ENHANCED_FEATURES_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Enhanced features not available"
        )

    try:
        error_bank = get_error_bank()
        error_bank.learn_from_clarification(original_text, corrected_text)

        return {
            "status": "success",
            "message": "Correction learned successfully",
            "original": original_text,
            "corrected": corrected_text
        }

    except Exception as e:
        logger.error(f"Error learning correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================
# Helper Functions
# ===========================================

def _detect_intent(text: str) -> Optional[str]:
    """
    Detect user intent from transcribed text

    Returns:
        Intent label or None
    """
    text_lower = text.lower()

    # Common intents in call center
    intent_patterns = {
        "greeting": ["hola", "buenos días", "buenas tardes", "buenas noches"],
        "question": ["¿", "cómo", "cuándo", "dónde", "qué", "cuál", "quién", "por qué"],
        "complaint": ["queja", "problema", "no funciona", "mal servicio", "molesto"],
        "request_info": ["información", "saber", "conocer", "consultar"],
        "request_transfer": ["transferir", "hablar con", "supervisor", "gerente"],
        "request_callback": ["llamar", "devolver la llamada", "callback"],
        "cancel": ["cancelar", "dar de baja", "eliminar", "cerrar"],
        "update": ["cambiar", "modificar", "actualizar", "editar"],
        "payment": ["pagar", "pago", "factura", "cobro", "tarjeta"],
        "farewell": ["adiós", "gracias", "chao", "hasta luego"]
    }

    for intent, keywords in intent_patterns.items():
        if any(keyword in text_lower for keyword in keywords):
            return intent

    return None


def _normalize_entities(text: str) -> Dict:
    """
    Extract and normalize entities from text

    Returns:
        Dict with normalized entities (numbers, emails, dates, etc.)
    """
    import re

    entities = {
        "numbers": [],
        "emails": [],
        "phones": [],
        "dates": [],
        "amounts": []
    }

    # Extract numbers (account numbers, IDs, etc.)
    number_patterns = re.findall(r'\b\d{4,}\b', text)
    entities["numbers"] = number_patterns

    # Extract emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    entities["emails"] = re.findall(email_pattern, text)

    # Extract phone numbers (various formats)
    phone_pattern = r'\b(?:\+?34)?[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{3}\b'
    entities["phones"] = re.findall(phone_pattern, text)

    # Extract monetary amounts
    amount_pattern = r'\b\d+(?:[.,]\d{1,2})?\s*(?:euros?|€|dolares?|\$|pesos?)\b'
    entities["amounts"] = re.findall(amount_pattern, text, re.IGNORECASE)

    # Extract dates (basic patterns)
    date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
    entities["dates"] = re.findall(date_pattern, text)

    return entities


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
