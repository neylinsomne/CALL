"""
Schema de Metadata para Grabaciones de Call Center
Define la estructura completa de metadata que se guarda con cada grabación
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class CallDirection(Enum):
    """Dirección de la llamada"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallOutcome(Enum):
    """Resultado de la llamada"""
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CALLBACK_SCHEDULED = "callback_scheduled"
    ABANDONED = "abandoned"
    TRANSFERRED = "transferred"
    NO_RESOLUTION = "no_resolution"


class SentimentLabel(Enum):
    """Sentimiento del cliente"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"
    FRUSTRATED = "frustrated"


# ==========================================
# Schema de Audio
# ==========================================

class AudioMetadata(BaseModel):
    """Metadata técnica del audio"""
    format: str = Field(..., description="Formato: wav, mp3, etc.")
    sample_rate: int = Field(16000, description="Sample rate en Hz")
    channels: int = Field(1, description="Número de canales")
    duration_seconds: float = Field(..., description="Duración en segundos")
    bitrate: Optional[int] = Field(None, description="Bitrate en kbps")
    codec: Optional[str] = Field(None, description="Codec utilizado")
    file_size_bytes: int = Field(..., description="Tamaño del archivo")
    checksum: str = Field(..., description="SHA-256 checksum")


# ==========================================
# Schema de Transcripción
# ==========================================

class WordConfidence(BaseModel):
    """Confianza por palabra"""
    word: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    start: float = Field(..., description="Timestamp inicio (segundos)")
    end: float = Field(..., description="Timestamp fin (segundos)")


class TranscriptionSegment(BaseModel):
    """Segmento de transcripción"""
    start: float
    end: float
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    words: Optional[List[WordConfidence]] = []


class TranscriptionMetadata(BaseModel):
    """Metadata de transcripción STT"""
    text: str = Field(..., description="Transcripción completa")
    corrected_text: Optional[str] = Field(None, description="Texto después de corrección")
    language: str = Field("es", description="Idioma detectado")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza global")
    segments: List[TranscriptionSegment] = []
    word_confidences: List[WordConfidence] = []

    # Métricas de calidad
    estimated_wer: Optional[float] = Field(None, description="Word Error Rate estimado")
    low_confidence_words_count: int = Field(0, description="Palabras con confianza <0.7")

    # Correcciones aplicadas
    corrections_made: List[Dict] = Field(default_factory=list, description="Correcciones aplicadas")
    correction_method: Optional[str] = Field(None, description="Método: online, offline, hybrid")

    # Modelo utilizado
    stt_model: str = Field("whisper-large-v3", description="Modelo STT utilizado")
    stt_processing_time_ms: Optional[float] = Field(None, description="Tiempo de procesamiento")


# ==========================================
# Schema de Análisis
# ==========================================

class SentimentAnalysis(BaseModel):
    """Análisis de sentimiento"""
    label: SentimentLabel = Field(..., description="Etiqueta de sentimiento")
    score: float = Field(..., ge=-1.0, le=1.0, description="Score de sentimiento")
    confidence: float = Field(..., ge=0.0, le=1.0)

    # Análisis avanzado
    emotional_tone: Optional[str] = Field(None, description="Tono emocional: calm, nervous, etc.")
    keywords_detected: List[str] = Field(default_factory=list)


class IntentAnalysis(BaseModel):
    """Análisis de intención"""
    primary_intent: str = Field(..., description="Intención principal")
    secondary_intents: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)


class EntityExtraction(BaseModel):
    """Entidades extraídas"""
    account_numbers: List[str] = Field(default_factory=list)
    amounts: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    product_ids: List[str] = Field(default_factory=list)


class TopicAnalysis(BaseModel):
    """Análisis de tópicos"""
    topics: List[str] = Field(default_factory=list, description="Tópicos detectados")
    keywords: List[str] = Field(default_factory=list, description="Keywords principales")
    coherence_score: float = Field(..., ge=0.0, le=1.0, description="Coherencia del texto")


# ==========================================
# Schema de Conversación
# ==========================================

class ConversationTurn(BaseModel):
    """Un turno de conversación (usuario o agente)"""
    turn_number: int
    speaker: str = Field(..., description="user o agent")
    text: str
    timestamp: float = Field(..., description="Timestamp relativo al inicio (segundos)")
    duration: float = Field(..., description="Duración del turno (segundos)")

    # Análisis del turno
    sentiment: Optional[SentimentAnalysis] = None
    intent: Optional[IntentAnalysis] = None


class ConversationMetrics(BaseModel):
    """Métricas de la conversación"""
    total_duration_seconds: float
    total_turns: int
    user_turns: int
    agent_turns: int

    # Tiempos
    avg_response_time_seconds: float = Field(..., description="Tiempo promedio de respuesta")
    silence_duration_seconds: float = Field(0.0, description="Tiempo total de silencio")

    # Interrupciones
    interruptions_count: int = Field(0)
    user_interrupted_agent: int = Field(0)
    agent_interrupted_user: int = Field(0)

    # Sentiment evolution
    sentiment_trend: List[float] = Field(default_factory=list, description="Evolución de sentiment")
    final_sentiment: Optional[SentimentLabel] = None


# ==========================================
# Schema de Performance
# ==========================================

class ProcessingMetrics(BaseModel):
    """Métricas de procesamiento"""
    stt_latency_ms: float
    llm_latency_ms: float
    tts_latency_ms: float
    total_latency_ms: float

    # Audio preprocessing
    target_extraction_ms: Optional[float] = None
    prosody_analysis_ms: Optional[float] = None
    denoise_ms: Optional[float] = None


# ==========================================
# Schema Completo de Recording
# ==========================================

class RecordingMetadata(BaseModel):
    """
    Schema completo de metadata para una grabación
    Este es el objeto principal que se guarda en metadata.json
    """

    # Identificadores
    recording_id: str = Field(..., description="ID único de la grabación")
    conversation_id: str = Field(..., description="ID de la conversación")
    call_id: Optional[str] = Field(None, description="ID externo de la llamada (CRM)")

    # Timestamps
    timestamp: datetime = Field(..., description="Timestamp de creación")
    call_started_at: Optional[datetime] = None
    call_ended_at: Optional[datetime] = None

    # Información de la llamada
    direction: CallDirection = Field(..., description="Dirección de la llamada")
    outcome: Optional[CallOutcome] = None
    caller_phone: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None

    # Audio
    audio: AudioMetadata

    # Transcripción
    transcription: Optional[TranscriptionMetadata] = None

    # Análisis
    sentiment: Optional[SentimentAnalysis] = None
    intent: Optional[IntentAnalysis] = None
    entities: Optional[EntityExtraction] = None
    topics: Optional[TopicAnalysis] = None

    # Conversación completa
    turns: List[ConversationTurn] = Field(default_factory=list)
    conversation_metrics: Optional[ConversationMetrics] = None

    # Performance
    processing_metrics: Optional[ProcessingMetrics] = None

    # Almacenamiento
    storage_backend: str = Field("local", description="local, s3, both")
    local_path: Optional[str] = None
    s3_path: Optional[str] = None

    # Flags
    processed: bool = Field(False, description="¿Procesado completamente?")
    processing_mode: str = Field("online", description="online o offline")
    deleted: bool = Field(False, description="Soft delete flag")
    deleted_at: Optional[datetime] = None

    # Notas y etiquetas
    tags: List[str] = Field(default_factory=list, description="Tags personalizados")
    notes: Optional[str] = Field(None, description="Notas del agente")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de calidad")

    # Versión del schema
    schema_version: str = Field("1.0", description="Versión del schema")


# ==========================================
# Utilidades
# ==========================================

def create_recording_metadata(
    recording_id: str,
    conversation_id: str,
    audio_data: bytes,
    direction: CallDirection = CallDirection.INBOUND,
    **kwargs
) -> RecordingMetadata:
    """
    Helper para crear metadata inicial de una grabación

    Args:
        recording_id: ID único
        conversation_id: ID de conversación
        audio_data: Bytes del audio (para calcular size/checksum)
        direction: Dirección de la llamada
        **kwargs: Campos adicionales

    Returns:
        RecordingMetadata inicializada
    """
    import hashlib

    # Metadata de audio básica
    audio_metadata = AudioMetadata(
        format=kwargs.get("format", "wav"),
        sample_rate=kwargs.get("sample_rate", 16000),
        channels=kwargs.get("channels", 1),
        duration_seconds=kwargs.get("duration_seconds", 0.0),
        file_size_bytes=len(audio_data),
        checksum=hashlib.sha256(audio_data).hexdigest()
    )

    # Crear metadata completa
    metadata = RecordingMetadata(
        recording_id=recording_id,
        conversation_id=conversation_id,
        timestamp=datetime.utcnow(),
        direction=direction,
        audio=audio_metadata,
        **{k: v for k, v in kwargs.items() if k not in [
            "format", "sample_rate", "channels", "duration_seconds"
        ]}
    )

    return metadata


def update_with_transcription(
    metadata: RecordingMetadata,
    transcription_result: Dict
) -> RecordingMetadata:
    """
    Actualiza metadata con resultados de transcripción

    Args:
        metadata: Metadata existente
        transcription_result: Resultado de STT enhanced

    Returns:
        Metadata actualizada
    """
    # Crear TranscriptionMetadata
    transcription = TranscriptionMetadata(
        text=transcription_result.get("text", ""),
        corrected_text=transcription_result.get("corrected_text"),
        language=transcription_result.get("language", "es"),
        confidence=transcription_result.get("confidence", 0.0),
        segments=[
            TranscriptionSegment(**seg)
            for seg in transcription_result.get("segments", [])
        ],
        word_confidences=[
            WordConfidence(**w)
            for w in transcription_result.get("word_confidences", [])
        ],
        corrections_made=transcription_result.get("corrections_made", []),
        correction_method=transcription_result.get("processing_mode", "online"),
        stt_processing_time_ms=transcription_result.get("processing_time_ms")
    )

    metadata.transcription = transcription
    metadata.processed = True

    return metadata


# ==========================================
# Ejemplo de Uso
# ==========================================

if __name__ == "__main__":
    # Crear metadata de ejemplo
    metadata = create_recording_metadata(
        recording_id="rec_12345",
        conversation_id="conv_67890",
        audio_data=b"fake audio data",
        direction=CallDirection.INBOUND,
        duration_seconds=120.5,
        agent_id="agent_001",
        caller_phone="+34612345678"
    )

    # Actualizar con transcripción
    transcription_result = {
        "text": "Hola necesito ayuda con mi cuenta",
        "corrected_text": "Hola necesito ayuda con mi cuenta",
        "language": "es",
        "confidence": 0.95,
        "segments": [],
        "word_confidences": [],
        "processing_mode": "online",
        "processing_time_ms": 450.0
    }

    metadata = update_with_transcription(metadata, transcription_result)

    # Serializar a JSON
    print(metadata.model_dump_json(indent=2))
