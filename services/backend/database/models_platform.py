"""
Platform (Supabase) ORM Models - Level 1
==========================================
Organizational / management plane data.
These tables live in the remote Supabase PostgreSQL.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Text, Boolean, Integer, DateTime, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .connections import PlatformBase


class Organization(PlatformBase):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    plan_type: Mapped[str] = mapped_column(
        Text, nullable=False, default="basic"
    )
    max_agents: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    servers: Mapped[List["OrganizationServer"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    tokens: Mapped[List["ApiToken"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    agent_registrations: Mapped[List["AgentRegistration"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    training_configs: Mapped[List["TrainingConfig"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class OrganizationServer(PlatformBase):
    __tablename__ = "organization_servers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    ip_address: Mapped[str] = mapped_column(INET, nullable=False)
    hostname: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[str] = mapped_column(Text, default="default")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    server_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization: Mapped["Organization"] = relationship(back_populates="servers")


class ApiToken(PlatformBase):
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
        Text, nullable=False, default="agent:read,agent:write"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    organization: Mapped["Organization"] = relationship(back_populates="tokens")


class AgentRegistration(PlatformBase):
    __tablename__ = "agent_registrations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(
        Text, nullable=False, default="inbound"
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="registered"
    )
    server_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization_servers.id", ondelete="SET NULL"),
    )
    config_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="agent_registrations"
    )


class TrainingConfig(PlatformBase):
    __tablename__ = "training_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    model_type: Mapped[str] = mapped_column(
        Text, nullable=False, default="tts"
    )
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    dataset_reference: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="training_configs"
    )
