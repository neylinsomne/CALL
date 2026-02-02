"""
Local PostgreSQL ORM Models - Level 2
=======================================
Agent operational data. These tables live in the local docker postgres.
Includes migrated versions of the existing Conversation, Message, CallLog models.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Text, Boolean, Integer, Float, DateTime, ForeignKey, VARCHAR,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .connections import LocalBase


# =============================================
# AUTH MODELS (local copy for self-contained operation)
# =============================================

class OrganizationLocal(LocalBase):
    """Local organization record"""
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    plan_type: Mapped[str] = mapped_column(Text, nullable=False, default="basic")
    max_agents: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tokens: Mapped[List["ApiTokenLocal"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class ApiTokenLocal(LocalBase):
    """Local API token for authentication"""
    __tablename__ = "api_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    token_prefix: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(
        Text, nullable=False, default="agent:read,agent:write,calls:read,qa:read"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    organization: Mapped["OrganizationLocal"] = relationship(back_populates="tokens")


# =============================================
# MIGRATED EXISTING MODELS (now with UUID PKs)
# =============================================

class Conversation(LocalBase):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    caller_id: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(VARCHAR(20), default="active")
    call_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    call_logs: Mapped[List["CallLog"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    process_metadata_entries: Mapped[List["ProcessMetadata"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(LocalBase):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(VARCHAR(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    audio_path: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class CallLog(LocalBase):
    __tablename__ = "call_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="call_logs")


# =============================================
# NEW MODELS
# =============================================

class VoiceProfile(LocalBase):
    __tablename__ = "voice_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(VARCHAR(10), nullable=False, default="es")
    sample_audio_path: Mapped[Optional[str]] = mapped_column(Text)
    parameters: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class ContextProfile(LocalBase):
    __tablename__ = "context_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE", use_alter=True),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False, default="default")
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    personality: Mapped[Optional[str]] = mapped_column(Text)
    greeting_message: Mapped[Optional[str]] = mapped_column(Text)
    fallback_message: Mapped[Optional[str]] = mapped_column(Text)
    max_context_turns: Mapped[int] = mapped_column(Integer, default=10)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    parameters: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Agent(LocalBase):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Logical FK to Supabase organizations -- NOT a DB-level FK
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # Logical FK to Supabase agent_registrations
    agent_registration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True)
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="idle")
    sip_port: Mapped[Optional[int]] = mapped_column(Integer)
    ws_port: Mapped[Optional[int]] = mapped_column(Integer)
    assigned_voice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("voice_profiles.id", ondelete="SET NULL"),
    )
    context_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("context_profiles.id", ondelete="SET NULL"),
    )
    config: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    voice_assignments: Mapped[List["VoiceAssignment"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    rag_batches: Mapped[List["RagBatch"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        foreign_keys=[Conversation.agent_id]
    )


class VoiceAssignment(LocalBase):
    __tablename__ = "voice_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    voice_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("voice_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    sip_port: Mapped[Optional[int]] = mapped_column(Integer)
    ws_sub_port: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    agent: Mapped["Agent"] = relationship(back_populates="voice_assignments")
    voice_profile: Mapped["VoiceProfile"] = relationship()


class RagBatch(LocalBase):
    __tablename__ = "rag_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text, nullable=False, default="file")
    source_path: Mapped[Optional[str]] = mapped_column(Text)
    embedding_model: Mapped[str] = mapped_column(
        Text, default="all-MiniLM-L6-v2"
    )
    vector_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    agent: Mapped["Agent"] = relationship(back_populates="rag_batches")
    documents: Mapped[List["RagDocument"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class RagDocument(LocalBase):
    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(Text)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    doc_metadata: Mapped[Optional[dict]] = mapped_column("doc_metadata", JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    batch: Mapped["RagBatch"] = relationship(back_populates="documents")
    chunks: Mapped[List["RagChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class RagCategory(LocalBase):
    """Knowledge domain categories for categorized RAG retrieval"""
    __tablename__ = "rag_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    retrieval_config: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    chunks: Mapped[List["RagChunk"]] = relationship(back_populates="category")


class RagChunk(LocalBase):
    """Embedded text fragments with pgvector for similarity search"""
    __tablename__ = "rag_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_categories.id", ondelete="SET NULL"),
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding = mapped_column(Vector(384), nullable=True)
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    document: Mapped["RagDocument"] = relationship(back_populates="chunks")
    category: Mapped[Optional["RagCategory"]] = relationship(back_populates="chunks")


class RagForbiddenTopic(LocalBase):
    """Explicit topic blocklist per agent"""
    __tablename__ = "rag_forbidden_topics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text, nullable=False, default="block")
    redirect_message: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class QaCriterion(LocalBase):
    """Scoring rubrics for call quality evaluation"""
    __tablename__ = "qa_criteria"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text, nullable=False, default="general")
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_automated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    automation_config: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    scores: Mapped[List["QaScore"]] = relationship(back_populates="criterion")


class QaEvaluation(LocalBase):
    """One QA evaluation per conversation"""
    __tablename__ = "qa_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
    )
    evaluator_type: Mapped[str] = mapped_column(
        Text, nullable=False, default="auto"
    )
    evaluator_id: Mapped[Optional[str]] = mapped_column(Text)
    overall_score: Mapped[Optional[float]] = mapped_column(Float)
    max_possible_score: Mapped[Optional[float]] = mapped_column(Float)
    percentage: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    evaluation_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    scores: Mapped[List["QaScore"]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan"
    )


class QaScore(LocalBase):
    """Individual criterion score within an evaluation"""
    __tablename__ = "qa_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("qa_evaluations.id", ondelete="CASCADE"),
        nullable=False,
    )
    criterion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("qa_criteria.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=10)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    evidence: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    evaluation: Mapped["QaEvaluation"] = relationship(back_populates="scores")
    criterion: Mapped["QaCriterion"] = relationship(back_populates="scores")


class ProcessMetadata(LocalBase):
    __tablename__ = "process_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    input_hash: Mapped[Optional[str]] = mapped_column(Text)
    output_hash: Mapped[Optional[str]] = mapped_column(Text)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    model_used: Mapped[Optional[str]] = mapped_column(Text)
    parameters: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="process_metadata_entries"
    )
