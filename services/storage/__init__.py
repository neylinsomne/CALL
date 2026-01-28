"""
Storage Module - Sistema de almacenamiento de grabaciones y metadata
"""

from .audio_storage import AudioStorage, get_audio_storage, StorageBackend
from .metadata_schema import (
    RecordingMetadata,
    AudioMetadata,
    TranscriptionMetadata,
    SentimentAnalysis,
    IntentAnalysis,
    EntityExtraction,
    ConversationMetrics,
    CallDirection,
    CallOutcome,
    SentimentLabel,
    create_recording_metadata,
    update_with_transcription
)

__all__ = [
    "AudioStorage",
    "get_audio_storage",
    "StorageBackend",
    "RecordingMetadata",
    "AudioMetadata",
    "TranscriptionMetadata",
    "SentimentAnalysis",
    "IntentAnalysis",
    "EntityExtraction",
    "ConversationMetrics",
    "CallDirection",
    "CallOutcome",
    "SentimentLabel",
    "create_recording_metadata",
    "update_with_transcription"
]
