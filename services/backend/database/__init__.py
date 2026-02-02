"""
Database Package
=================
Dual-database architecture: Local PostgreSQL + Supabase (remote).

Usage (backwards compatible):
    from database import Database, Conversation, Message
    db = Database()
    await db.connect()
"""

# Connections
from .connections import (
    PlatformBase,
    LocalBase,
    get_local_session,
    get_platform_session,
    get_local_engine,
    get_platform_engine,
    dispose_all_engines,
)

# Manager
from .manager import DatabaseManager

# Local models (Level 2 - operational)
from .models_local import (
    OrganizationLocal,
    ApiTokenLocal,
    Conversation,
    Message,
    CallLog,
    Agent,
    VoiceProfile,
    VoiceAssignment,
    ContextProfile,
    RagBatch,
    RagDocument,
    RagCategory,
    RagChunk,
    RagForbiddenTopic,
    QaCriterion,
    QaEvaluation,
    QaScore,
    ProcessMetadata,
)

# Platform models (Level 1 - organizational)
from .models_platform import (
    Organization,
    OrganizationServer,
    ApiToken,
    AgentRegistration,
    TrainingConfig,
)

# Backwards-compatible alias
Database = DatabaseManager

__all__ = [
    # Connections
    "PlatformBase",
    "LocalBase",
    "get_local_session",
    "get_platform_session",
    "get_local_engine",
    "get_platform_engine",
    "dispose_all_engines",
    # Manager
    "DatabaseManager",
    "Database",
    # Local models
    "Conversation",
    "Message",
    "CallLog",
    "Agent",
    "VoiceProfile",
    "VoiceAssignment",
    "ContextProfile",
    "RagBatch",
    "RagDocument",
    "RagCategory",
    "RagChunk",
    "RagForbiddenTopic",
    "QaCriterion",
    "QaEvaluation",
    "QaScore",
    "ProcessMetadata",
    # Platform models
    "Organization",
    "OrganizationServer",
    "ApiToken",
    "AgentRegistration",
    "TrainingConfig",
]
