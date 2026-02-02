"""
Database Manager
=================
Unified interface for dual-database operations.
Provides the same methods as the existing Database class for backwards compatibility,
plus new methods for platform and cross-database operations.
"""

import uuid
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import text
from sqlalchemy.future import select
from loguru import logger

from .connections import (
    get_local_engine,
    get_platform_engine,
    get_local_session,
    get_platform_session,
    get_local_session_factory,
    dispose_all_engines,
)
from .models_local import (
    Conversation,
    Message,
    CallLog,
    Agent,
    VoiceProfile,
    ContextProfile,
    VoiceAssignment,
    RagBatch,
    RagDocument,
    ProcessMetadata,
)


def _to_uuid(value) -> uuid.UUID:
    """Convert string or UUID to uuid.UUID"""
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


class DatabaseManager:
    """
    Unified database manager with dual-connection support.

    Maintains backwards compatibility with the existing Database class API
    while adding platform (Supabase) database access.
    """

    def __init__(self):
        self._local_engine = None
        self._platform_engine = None

    # =========================================
    # Lifecycle
    # =========================================

    async def connect(self):
        """Initialize both database connections"""
        self._local_engine = get_local_engine()
        logger.info("Local database engine initialized")

        self._platform_engine = get_platform_engine()
        if self._platform_engine:
            logger.info("Platform database (Supabase) engine initialized")
        else:
            logger.warning(
                "Platform database not configured - operating in local-only mode"
            )

    async def disconnect(self):
        """Close all database connections"""
        await dispose_all_engines()
        self._local_engine = None
        self._platform_engine = None

    @property
    def platform_available(self) -> bool:
        """Check if the platform (Supabase) database is configured"""
        return self._platform_engine is not None

    # =========================================
    # Backwards-compatible methods (local DB)
    # =========================================

    async def create_conversation(
        self,
        conversation_id: str,
        caller_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        agent_id: Optional[str] = None,
    ) -> str:
        """Create a new conversation"""
        async with get_local_session() as session:
            conversation = Conversation(
                id=_to_uuid(conversation_id),
                caller_id=caller_id,
                agent_id=_to_uuid(agent_id) if agent_id else None,
                call_metadata=metadata or {},
            )
            session.add(conversation)
        return conversation_id

    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation by ID"""
        async with get_local_session() as session:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == _to_uuid(conversation_id)
                )
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return {
                    "id": str(conversation.id),
                    "caller_id": conversation.caller_id,
                    "agent_id": str(conversation.agent_id) if conversation.agent_id else None,
                    "started_at": conversation.started_at.isoformat() if conversation.started_at else None,
                    "ended_at": conversation.ended_at.isoformat() if conversation.ended_at else None,
                    "status": conversation.status,
                    "metadata": conversation.call_metadata,
                }
            return None

    async def end_conversation(self, conversation_id: str):
        """End a conversation"""
        async with get_local_session() as session:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == _to_uuid(conversation_id)
                )
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.ended_at = datetime.utcnow()
                conversation.status = "ended"

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        audio_path: Optional[str] = None,
    ) -> str:
        """Add a message to a conversation"""
        msg_id = uuid.uuid4()
        async with get_local_session() as session:
            message = Message(
                id=msg_id,
                conversation_id=_to_uuid(conversation_id),
                role=role,
                content=content,
                audio_path=audio_path,
            )
            session.add(message)
        return str(msg_id)

    async def get_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation"""
        async with get_local_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == _to_uuid(conversation_id))
                .order_by(Message.timestamp)
            )
            messages = result.scalars().all()
            return [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "audio_path": msg.audio_path,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in messages
            ]

    async def log_event(
        self,
        conversation_id: str,
        event_type: str,
        details: Optional[dict] = None,
    ):
        """Log a call event"""
        async with get_local_session() as session:
            log = CallLog(
                conversation_id=_to_uuid(conversation_id),
                event_type=event_type,
                details=details or {},
            )
            session.add(log)

    async def get_conversation_metrics(self, conversation_id: str) -> Dict:
        """Get aggregated metrics for a conversation"""
        conv_uuid = _to_uuid(conversation_id)
        async with get_local_session() as session:
            result = await session.execute(
                select(CallLog)
                .where(CallLog.conversation_id == conv_uuid)
                .where(CallLog.event_type.in_(["turn_completed", "turn_completed_streaming"]))
                .order_by(CallLog.created_at)
            )
            logs = result.scalars().all()

            if not logs:
                return {}

            total_turns = len(logs)
            stt_latencies = []
            llm_latencies = []
            tts_latencies = []
            total_latencies = []
            sentiment_scores = []

            for log in logs:
                details = log.details or {}
                if "stt_latency_ms" in details:
                    stt_latencies.append(details["stt_latency_ms"])
                if "llm_latency_ms" in details:
                    llm_latencies.append(details["llm_latency_ms"])
                if "tts_latency_ms" in details:
                    tts_latencies.append(details["tts_latency_ms"])
                if "total_latency_ms" in details:
                    total_latencies.append(details["total_latency_ms"])
                if "sentiment_score" in details:
                    sentiment_scores.append(details["sentiment_score"])

            interruption_result = await session.execute(
                select(CallLog)
                .where(CallLog.conversation_id == conv_uuid)
                .where(CallLog.event_type == "interruption")
            )
            interruptions = len(interruption_result.scalars().all())

            return {
                "conversation_id": str(conversation_id),
                "total_turns": total_turns,
                "avg_stt_latency_ms": sum(stt_latencies) // len(stt_latencies) if stt_latencies else 0,
                "avg_llm_latency_ms": sum(llm_latencies) // len(llm_latencies) if llm_latencies else 0,
                "avg_tts_latency_ms": sum(tts_latencies) // len(tts_latencies) if tts_latencies else 0,
                "avg_total_latency_ms": sum(total_latencies) // len(total_latencies) if total_latencies else 0,
                "avg_sentiment_score": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                "interruptions_count": interruptions,
            }

    async def get_all_metrics(self, limit: int = 100) -> List[Dict]:
        """Get metrics for all recent conversations"""
        async with get_local_session() as session:
            result = await session.execute(
                select(Conversation)
                .order_by(Conversation.started_at.desc())
                .limit(limit)
            )
            conversations = result.scalars().all()

            metrics_list = []
            for conv in conversations:
                metrics = await self.get_conversation_metrics(str(conv.id))
                if metrics:
                    metrics["started_at"] = conv.started_at.isoformat() if conv.started_at else None
                    metrics["ended_at"] = conv.ended_at.isoformat() if conv.ended_at else None
                    metrics["status"] = conv.status
                    metrics_list.append(metrics)

            return metrics_list

    # =========================================
    # Raw query methods (for vocabulary.py compatibility)
    # =========================================

    async def execute(self, query: str, *args):
        """Execute a raw SQL query on the local database"""
        async with get_local_session() as session:
            converted_query, params = self._convert_asyncpg_params(query, args)
            await session.execute(text(converted_query), params)

    async def fetch(self, query: str, *args) -> List[Dict]:
        """Fetch multiple rows from local database"""
        async with get_local_session() as session:
            converted_query, params = self._convert_asyncpg_params(query, args)
            result = await session.execute(text(converted_query), params)
            rows = result.mappings().all()
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args) -> Optional[Dict]:
        """Fetch single row from local database"""
        async with get_local_session() as session:
            converted_query, params = self._convert_asyncpg_params(query, args)
            result = await session.execute(text(converted_query), params)
            row = result.mappings().first()
            return dict(row) if row else None

    async def fetchval(self, query: str, *args):
        """Fetch single value from local database"""
        async with get_local_session() as session:
            converted_query, params = self._convert_asyncpg_params(query, args)
            result = await session.execute(text(converted_query), params)
            row = result.first()
            return row[0] if row else None

    @staticmethod
    def _convert_asyncpg_params(query: str, args: tuple) -> tuple:
        """Convert asyncpg $1, $2 style params to SQLAlchemy :p1, :p2 style"""
        params = {}
        converted = query
        # Replace in reverse order to avoid $1 matching in $10, $11, etc.
        for i in range(len(args), 0, -1):
            param_name = f"p{i}"
            converted = converted.replace(f"${i}", f":{param_name}")
            params[param_name] = args[i - 1]
        return converted, params

    # =========================================
    # Platform (Supabase) operations
    # =========================================

    async def get_organization(self, org_id: str) -> Optional[Dict]:
        """Fetch organization from Supabase"""
        if not self.platform_available:
            return None
        from .models_platform import Organization
        async with get_platform_session() as session:
            result = await session.execute(
                select(Organization).where(
                    Organization.id == _to_uuid(org_id)
                )
            )
            org = result.scalar_one_or_none()
            if org:
                return {
                    "id": str(org.id),
                    "name": org.name,
                    "domain": org.domain,
                    "plan_type": org.plan_type,
                    "max_agents": org.max_agents,
                    "is_active": org.is_active,
                    "settings": org.settings,
                }
            return None

    async def validate_api_token(
        self, token_prefix: str, token_hash: str
    ) -> Optional[Dict]:
        """Validate an API token against Supabase"""
        if not self.platform_available:
            return None
        from .models_platform import ApiToken
        async with get_platform_session() as session:
            result = await session.execute(
                select(ApiToken).where(
                    ApiToken.token_prefix == token_prefix,
                    ApiToken.token_hash == token_hash,
                    ApiToken.is_active == True,
                )
            )
            token = result.scalar_one_or_none()
            if token:
                if token.expires_at and token.expires_at < datetime.utcnow():
                    return None
                token.last_used_at = datetime.utcnow()
                return {
                    "org_id": str(token.org_id),
                    "scope": token.scope,
                    "token_id": str(token.id),
                }
            return None

    async def get_agent_registrations(self, org_id: str) -> List[Dict]:
        """Fetch agent registrations for an organization from Supabase"""
        if not self.platform_available:
            return []
        from .models_platform import AgentRegistration
        async with get_platform_session() as session:
            result = await session.execute(
                select(AgentRegistration).where(
                    AgentRegistration.org_id == _to_uuid(org_id)
                )
            )
            regs = result.scalars().all()
            return [
                {
                    "id": str(r.id),
                    "org_id": str(r.org_id),
                    "agent_name": r.agent_name,
                    "agent_type": r.agent_type,
                    "status": r.status,
                    "server_id": str(r.server_id) if r.server_id else None,
                }
                for r in regs
            ]
