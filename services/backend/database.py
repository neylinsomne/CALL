"""
Database Layer
PostgreSQL connection and models for conversation management
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import create_engine, Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.future import select


# ===========================================
# Configuration
# ===========================================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "callcenter")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "callcenter")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


# ===========================================
# SQLAlchemy Setup
# ===========================================
Base = declarative_base()


class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True)
    caller_id = Column(String(50), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    metadata = Column(JSON, nullable=True)


class Message(Base):
    """Message model"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    role = Column(String(10))  # 'user' or 'assistant'
    content = Column(Text)
    audio_path = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class CallLog(Base):
    """Call log model for analytics with quality metrics"""
    __tablename__ = "call_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    event_type = Column(String(50))
    details = Column(JSON, nullable=True)  # Stores metrics: stt_latency_ms, llm_latency_ms, tts_latency_ms, sentiment_score, etc.
    created_at = Column(DateTime, default=datetime.utcnow)


# ===========================================
# Database Class
# ===========================================
class Database:
    """Async database handler"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        
    async def connect(self):
        """Initialize database connection"""
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
    async def disconnect(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            
    async def create_conversation(
        self, 
        conversation_id: str,
        caller_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Create a new conversation"""
        async with self.async_session() as session:
            conversation = Conversation(
                id=conversation_id,
                caller_id=caller_id,
                metadata=metadata or {}
            )
            session.add(conversation)
            await session.commit()
            return conversation_id
            
    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation by ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return {
                    "id": conversation.id,
                    "caller_id": conversation.caller_id,
                    "started_at": conversation.started_at.isoformat() if conversation.started_at else None,
                    "ended_at": conversation.ended_at.isoformat() if conversation.ended_at else None,
                    "status": conversation.status,
                    "metadata": conversation.metadata
                }
            return None
            
    async def end_conversation(self, conversation_id: str):
        """End a conversation"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.ended_at = datetime.utcnow()
                conversation.status = "ended"
                await session.commit()
                
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        audio_path: Optional[str] = None
    ) -> str:
        """Add a message to a conversation"""
        async with self.async_session() as session:
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                audio_path=audio_path
            )
            session.add(message)
            await session.commit()
            return message.id
            
    async def get_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.timestamp)
            )
            messages = result.scalars().all()
            return [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "audio_path": msg.audio_path,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in messages
            ]
            
    async def log_event(
        self,
        conversation_id: str,
        event_type: str,
        details: Optional[dict] = None
    ):
        """Log a call event"""
        async with self.async_session() as session:
            log = CallLog(
                conversation_id=conversation_id,
                event_type=event_type,
                details=details or {}
            )
            session.add(log)
            await session.commit()

    async def get_conversation_metrics(self, conversation_id: str) -> Dict:
        """Get aggregated metrics for a conversation"""
        async with self.async_session() as session:
            result = await session.execute(
                select(CallLog)
                .where(CallLog.conversation_id == conversation_id)
                .where(CallLog.event_type.in_(["turn_completed", "turn_completed_streaming"]))
                .order_by(CallLog.created_at)
            )
            logs = result.scalars().all()

            if not logs:
                return {}

            # Aggregate metrics
            total_turns = len(logs)
            stt_latencies = []
            llm_latencies = []
            tts_latencies = []
            total_latencies = []
            sentiment_scores = []
            interruptions = 0

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

            # Count interruptions
            interruption_result = await session.execute(
                select(CallLog)
                .where(CallLog.conversation_id == conversation_id)
                .where(CallLog.event_type == "interruption")
            )
            interruptions = len(interruption_result.scalars().all())

            return {
                "conversation_id": conversation_id,
                "total_turns": total_turns,
                "avg_stt_latency_ms": sum(stt_latencies) // len(stt_latencies) if stt_latencies else 0,
                "avg_llm_latency_ms": sum(llm_latencies) // len(llm_latencies) if llm_latencies else 0,
                "avg_tts_latency_ms": sum(tts_latencies) // len(tts_latencies) if tts_latencies else 0,
                "avg_total_latency_ms": sum(total_latencies) // len(total_latencies) if total_latencies else 0,
                "avg_sentiment_score": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                "interruptions_count": interruptions
            }

    async def get_all_metrics(self, limit: int = 100) -> List[Dict]:
        """Get metrics for all recent conversations"""
        async with self.async_session() as session:
            # Get recent conversations
            result = await session.execute(
                select(Conversation)
                .order_by(Conversation.started_at.desc())
                .limit(limit)
            )
            conversations = result.scalars().all()

            metrics_list = []
            for conv in conversations:
                metrics = await self.get_conversation_metrics(conv.id)
                if metrics:
                    metrics["started_at"] = conv.started_at.isoformat() if conv.started_at else None
                    metrics["ended_at"] = conv.ended_at.isoformat() if conv.ended_at else None
                    metrics["status"] = conv.status
                    metrics_list.append(metrics)

            return metrics_list
