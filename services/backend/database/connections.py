"""
Dual Database Connection Management
====================================
Manages two independent PostgreSQL connections:
  - Platform (Supabase): organizational/management data
  - Local: agent operational data (existing docker postgres)
"""

import os
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from loguru import logger


# =============================================
# Separate Base classes for each database
# =============================================

class PlatformBase(DeclarativeBase):
    """Base class for all Supabase/platform models"""
    pass


class LocalBase(DeclarativeBase):
    """Base class for all local PostgreSQL models"""
    pass


# =============================================
# Connection Configuration
# =============================================

def _get_local_url() -> str:
    """Build local PostgreSQL connection URL from env vars"""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "callcenter")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    db = os.getenv("POSTGRES_DB", "callcenter")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def _get_platform_url() -> str:
    """
    Build Supabase connection URL.

    Supports two modes:
    1. Full connection string via SUPABASE_DB_URL
    2. Constructed from SUPABASE_DB_HOST + SUPABASE_DB_PASSWORD + defaults
    """
    direct_url = os.getenv("SUPABASE_DB_URL")
    if direct_url:
        if direct_url.startswith("postgresql://"):
            return direct_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if direct_url.startswith("postgres://"):
            return direct_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return direct_url

    host = os.getenv("SUPABASE_DB_HOST")
    port = os.getenv("SUPABASE_DB_PORT", "5432")
    user = os.getenv("SUPABASE_DB_USER", "postgres")
    password = os.getenv("SUPABASE_DB_PASSWORD", "")
    db = os.getenv("SUPABASE_DB_NAME", "postgres")

    if not host:
        return ""

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


# =============================================
# Engine and Session Factories
# =============================================

_local_engine: Optional[AsyncEngine] = None
_local_session_factory: Optional[async_sessionmaker] = None

_platform_engine: Optional[AsyncEngine] = None
_platform_session_factory: Optional[async_sessionmaker] = None


def get_local_engine() -> AsyncEngine:
    """Get or create local database engine"""
    global _local_engine
    if _local_engine is None:
        _local_engine = create_async_engine(
            _get_local_url(),
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
    return _local_engine


def get_platform_engine() -> Optional[AsyncEngine]:
    """Get or create platform database engine. Returns None if not configured."""
    global _platform_engine
    url = _get_platform_url()
    if not url:
        return None
    if _platform_engine is None:
        ssl_mode = os.getenv("SUPABASE_DB_SSL", "prefer")
        _platform_engine = create_async_engine(
            url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"ssl": ssl_mode} if ssl_mode != "disable" else {},
        )
    return _platform_engine


def get_local_session_factory() -> async_sessionmaker:
    """Get local session factory"""
    global _local_session_factory
    if _local_session_factory is None:
        _local_session_factory = async_sessionmaker(
            get_local_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _local_session_factory


def get_platform_session_factory() -> Optional[async_sessionmaker]:
    """Get platform session factory. Returns None if not configured."""
    global _platform_session_factory
    engine = get_platform_engine()
    if engine is None:
        return None
    if _platform_session_factory is None:
        _platform_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _platform_session_factory


# =============================================
# Context Managers for Sessions
# =============================================

@asynccontextmanager
async def get_local_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a local database session with automatic cleanup"""
    factory = get_local_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_platform_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a platform database session with automatic cleanup"""
    factory = get_platform_session_factory()
    if factory is None:
        raise RuntimeError(
            "Platform database (Supabase) is not configured. "
            "Set SUPABASE_DB_URL or SUPABASE_DB_HOST environment variables."
        )
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =============================================
# Shutdown helpers
# =============================================

async def dispose_all_engines():
    """Dispose both engines on application shutdown"""
    global _local_engine, _platform_engine
    global _local_session_factory, _platform_session_factory

    if _local_engine:
        await _local_engine.dispose()
        _local_engine = None
        _local_session_factory = None

    if _platform_engine:
        await _platform_engine.dispose()
        _platform_engine = None
        _platform_session_factory = None

    logger.info("All database engines disposed")
