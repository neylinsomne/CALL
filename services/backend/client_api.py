"""
Client API - Tenant-Scoped Endpoints
======================================
Endpoints available to authenticated clients (organizations).
Every query is automatically filtered by the tenant's org_id.

Scopes:
    - agent:read    → View their agents and configuration
    - agent:write   → Configure agents (voice, context, RAG)
    - calls:read    → View call history and metrics
    - qa:read       → View QA evaluations
    - qa:write      → Create manual QA evaluations
"""

import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from loguru import logger

from database import (
    get_local_session,
    Agent,
    VoiceProfile,
    ContextProfile,
    Conversation,
    Message,
    CallLog,
    QaCriterion,
    QaEvaluation,
    QaScore,
)
from auth import TenantContext, get_current_tenant, require_scope

router = APIRouter(prefix="/api/v1", tags=["Client API"])


# =============================================
# Pydantic Schemas
# =============================================

class AgentSummary(BaseModel):
    id: str
    name: str
    status: str
    sip_port: Optional[int]
    ws_port: Optional[int]


class AgentDetail(AgentSummary):
    config: Optional[dict]
    voice_name: Optional[str] = None
    context_name: Optional[str] = None
    created_at: str


class AgentConfigUpdate(BaseModel):
    assigned_voice_id: Optional[str] = None
    context_profile_id: Optional[str] = None
    config: Optional[dict] = None


class ConversationSummary(BaseModel):
    id: str
    agent_id: Optional[str]
    caller_id: Optional[str]
    started_at: Optional[str]
    ended_at: Optional[str]
    status: str


class ConversationDetail(ConversationSummary):
    messages: List[dict]
    metrics: Optional[dict] = None


class QaEvaluationSummary(BaseModel):
    id: str
    conversation_id: str
    agent_id: Optional[str]
    evaluator_type: str
    overall_score: Optional[float]
    percentage: Optional[float]
    created_at: str


class QaManualScore(BaseModel):
    criterion_id: str
    score: float = Field(..., ge=0)
    notes: Optional[str] = None
    evidence: Optional[str] = None


class QaManualEvaluation(BaseModel):
    conversation_id: str
    scores: List[QaManualScore]
    notes: Optional[str] = None


# =============================================
# Agent Endpoints (agent:read / agent:write)
# =============================================

@router.get("/agents")
async def list_my_agents(
    tenant: TenantContext = Depends(require_scope("agent:read")),
):
    """List all agents belonging to the authenticated organization"""
    async with get_local_session() as session:
        result = await session.execute(
            select(Agent)
            .where(Agent.org_id == uuid.UUID(tenant.org_id))
            .order_by(Agent.name)
        )
        agents = result.scalars().all()
        return [
            AgentSummary(
                id=str(a.id),
                name=a.name,
                status=a.status,
                sip_port=a.sip_port,
                ws_port=a.ws_port,
            )
            for a in agents
        ]


@router.get("/agents/{agent_id}")
async def get_my_agent(
    agent_id: str,
    tenant: TenantContext = Depends(require_scope("agent:read")),
):
    """Get detailed agent information"""
    async with get_local_session() as session:
        agent = await _get_tenant_agent(session, agent_id, tenant.org_id)

        voice_name = None
        if agent.assigned_voice_id:
            voice_result = await session.execute(
                select(VoiceProfile).where(VoiceProfile.id == agent.assigned_voice_id)
            )
            voice = voice_result.scalar_one_or_none()
            if voice:
                voice_name = voice.name

        context_name = None
        if agent.context_profile_id:
            ctx_result = await session.execute(
                select(ContextProfile).where(ContextProfile.id == agent.context_profile_id)
            )
            ctx = ctx_result.scalar_one_or_none()
            if ctx:
                context_name = ctx.name

        return AgentDetail(
            id=str(agent.id),
            name=agent.name,
            status=agent.status,
            sip_port=agent.sip_port,
            ws_port=agent.ws_port,
            config=agent.config,
            voice_name=voice_name,
            context_name=context_name,
            created_at=agent.created_at.isoformat() if agent.created_at else "",
        )


@router.put("/agents/{agent_id}/config")
async def update_my_agent_config(
    agent_id: str,
    data: AgentConfigUpdate,
    tenant: TenantContext = Depends(require_scope("agent:write")),
):
    """Update agent configuration (voice, context, settings)"""
    async with get_local_session() as session:
        agent = await _get_tenant_agent(session, agent_id, tenant.org_id)

        if data.assigned_voice_id is not None:
            # Verify voice profile exists
            voice_result = await session.execute(
                select(VoiceProfile).where(
                    VoiceProfile.id == uuid.UUID(data.assigned_voice_id)
                )
            )
            if not voice_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Voice profile not found")
            agent.assigned_voice_id = uuid.UUID(data.assigned_voice_id)

        if data.context_profile_id is not None:
            ctx_result = await session.execute(
                select(ContextProfile).where(
                    ContextProfile.id == uuid.UUID(data.context_profile_id)
                )
            )
            if not ctx_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Context profile not found")
            agent.context_profile_id = uuid.UUID(data.context_profile_id)

        if data.config is not None:
            agent.config = data.config

        agent.updated_at = datetime.utcnow()

        logger.info(f"Agent config updated by tenant {tenant.org_name}: {agent.name}")
        return {"status": "updated", "agent_id": str(agent.id)}


# =============================================
# Calls / Conversations Endpoints (calls:read)
# =============================================

@router.get("/calls")
async def list_my_calls(
    tenant: TenantContext = Depends(require_scope("calls:read")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """List call history for the tenant's agents"""
    async with get_local_session() as session:
        # Get all agent IDs for this org
        agent_ids = await _get_org_agent_ids(session, tenant.org_id)

        if not agent_ids:
            return []

        query = (
            select(Conversation)
            .where(Conversation.agent_id.in_(agent_ids))
            .order_by(Conversation.started_at.desc())
        )
        if status_filter:
            query = query.where(Conversation.status == status_filter)
        query = query.offset(skip).limit(limit)

        result = await session.execute(query)
        conversations = result.scalars().all()

        return [
            ConversationSummary(
                id=str(c.id),
                agent_id=str(c.agent_id) if c.agent_id else None,
                caller_id=c.caller_id,
                started_at=c.started_at.isoformat() if c.started_at else None,
                ended_at=c.ended_at.isoformat() if c.ended_at else None,
                status=c.status,
            )
            for c in conversations
        ]


@router.get("/calls/{conversation_id}")
async def get_my_call(
    conversation_id: str,
    tenant: TenantContext = Depends(require_scope("calls:read")),
):
    """Get detailed call information with messages"""
    async with get_local_session() as session:
        conv = await _get_tenant_conversation(session, conversation_id, tenant.org_id)

        # Get messages
        msg_result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.timestamp)
        )
        messages = msg_result.scalars().all()

        # Get metrics from call logs
        log_result = await session.execute(
            select(CallLog)
            .where(
                CallLog.conversation_id == conv.id,
                CallLog.event_type.in_(["turn_completed", "turn_completed_streaming"]),
            )
        )
        logs = log_result.scalars().all()

        metrics = None
        if logs:
            total_latencies = [
                log.details.get("total_latency_ms", 0)
                for log in logs if log.details
            ]
            metrics = {
                "total_turns": len(logs),
                "avg_total_latency_ms": (
                    sum(total_latencies) // len(total_latencies)
                    if total_latencies else 0
                ),
            }

        return ConversationDetail(
            id=str(conv.id),
            agent_id=str(conv.agent_id) if conv.agent_id else None,
            caller_id=conv.caller_id,
            started_at=conv.started_at.isoformat() if conv.started_at else None,
            ended_at=conv.ended_at.isoformat() if conv.ended_at else None,
            status=conv.status,
            messages=[
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                }
                for m in messages
            ],
            metrics=metrics,
        )


@router.get("/calls/metrics/summary")
async def get_my_call_metrics(
    tenant: TenantContext = Depends(require_scope("calls:read")),
    days: int = Query(7, ge=1, le=90),
):
    """Get aggregated call metrics for the tenant"""
    async with get_local_session() as session:
        agent_ids = await _get_org_agent_ids(session, tenant.org_id)
        if not agent_ids:
            return {"total_calls": 0, "agents": 0}

        since = datetime.utcnow() - __import__("datetime").timedelta(days=days)

        total_calls = (await session.execute(
            select(func.count(Conversation.id)).where(
                Conversation.agent_id.in_(agent_ids),
                Conversation.started_at >= since,
            )
        )).scalar()

        active_calls = (await session.execute(
            select(func.count(Conversation.id)).where(
                Conversation.agent_id.in_(agent_ids),
                Conversation.status == "active",
            )
        )).scalar()

        ended_calls = (await session.execute(
            select(func.count(Conversation.id)).where(
                Conversation.agent_id.in_(agent_ids),
                Conversation.started_at >= since,
                Conversation.status == "ended",
            )
        )).scalar()

        return {
            "period_days": days,
            "total_calls": total_calls,
            "active_calls": active_calls,
            "ended_calls": ended_calls,
            "agents_count": len(agent_ids),
        }


# =============================================
# QA Endpoints (qa:read / qa:write)
# =============================================

@router.get("/qa/evaluations")
async def list_my_qa_evaluations(
    tenant: TenantContext = Depends(require_scope("qa:read")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    agent_id: Optional[str] = Query(None),
):
    """List QA evaluations for the tenant's agents"""
    async with get_local_session() as session:
        agent_ids = await _get_org_agent_ids(session, tenant.org_id)
        if not agent_ids:
            return []

        query = (
            select(QaEvaluation)
            .where(QaEvaluation.agent_id.in_(agent_ids))
            .order_by(QaEvaluation.created_at.desc())
        )
        if agent_id:
            if uuid.UUID(agent_id) not in agent_ids:
                raise HTTPException(status_code=403, detail="Agent does not belong to your organization")
            query = query.where(QaEvaluation.agent_id == uuid.UUID(agent_id))
        query = query.offset(skip).limit(limit)

        result = await session.execute(query)
        evaluations = result.scalars().all()

        return [
            QaEvaluationSummary(
                id=str(e.id),
                conversation_id=str(e.conversation_id),
                agent_id=str(e.agent_id) if e.agent_id else None,
                evaluator_type=e.evaluator_type,
                overall_score=e.overall_score,
                percentage=e.percentage,
                created_at=e.created_at.isoformat() if e.created_at else "",
            )
            for e in evaluations
        ]


@router.get("/qa/evaluations/{evaluation_id}")
async def get_my_qa_evaluation(
    evaluation_id: str,
    tenant: TenantContext = Depends(require_scope("qa:read")),
):
    """Get detailed QA evaluation with individual scores"""
    async with get_local_session() as session:
        agent_ids = await _get_org_agent_ids(session, tenant.org_id)

        result = await session.execute(
            select(QaEvaluation).where(QaEvaluation.id == uuid.UUID(evaluation_id))
        )
        evaluation = result.scalar_one_or_none()

        if not evaluation or (evaluation.agent_id and evaluation.agent_id not in agent_ids):
            raise HTTPException(status_code=404, detail="Evaluation not found")

        # Get scores
        scores_result = await session.execute(
            select(QaScore).where(QaScore.evaluation_id == evaluation.id)
        )
        scores = scores_result.scalars().all()

        # Get criterion names
        score_details = []
        for score in scores:
            criterion_result = await session.execute(
                select(QaCriterion).where(QaCriterion.id == score.criterion_id)
            )
            criterion = criterion_result.scalar_one_or_none()
            score_details.append({
                "criterion_name": criterion.name if criterion else "Unknown",
                "criterion_category": criterion.category if criterion else "general",
                "score": score.score,
                "max_score": score.max_score,
                "notes": score.notes,
                "evidence": score.evidence,
            })

        return {
            "id": str(evaluation.id),
            "conversation_id": str(evaluation.conversation_id),
            "agent_id": str(evaluation.agent_id) if evaluation.agent_id else None,
            "evaluator_type": evaluation.evaluator_type,
            "overall_score": evaluation.overall_score,
            "max_possible_score": evaluation.max_possible_score,
            "percentage": evaluation.percentage,
            "notes": evaluation.notes,
            "scores": score_details,
            "created_at": evaluation.created_at.isoformat() if evaluation.created_at else "",
        }


@router.post("/qa/evaluations")
async def create_manual_qa_evaluation(
    data: QaManualEvaluation,
    tenant: TenantContext = Depends(require_scope("qa:write")),
):
    """Create a manual QA evaluation for a conversation"""
    async with get_local_session() as session:
        # Verify the conversation belongs to this org
        conv = await _get_tenant_conversation(session, data.conversation_id, tenant.org_id)

        # Create evaluation
        evaluation = QaEvaluation(
            conversation_id=conv.id,
            agent_id=conv.agent_id,
            evaluator_type="human",
            evaluator_id=tenant.token_id,
            notes=data.notes,
        )
        session.add(evaluation)
        await session.flush()

        # Add scores
        total_score = 0.0
        total_max = 0.0
        for score_data in data.scores:
            criterion_result = await session.execute(
                select(QaCriterion).where(
                    QaCriterion.id == uuid.UUID(score_data.criterion_id)
                )
            )
            criterion = criterion_result.scalar_one_or_none()
            if not criterion:
                raise HTTPException(
                    status_code=400,
                    detail=f"Criterion {score_data.criterion_id} not found",
                )

            qa_score = QaScore(
                evaluation_id=evaluation.id,
                criterion_id=criterion.id,
                score=min(score_data.score, criterion.max_score),
                max_score=criterion.max_score,
                notes=score_data.notes,
                evidence=score_data.evidence,
            )
            session.add(qa_score)
            total_score += qa_score.score * criterion.weight
            total_max += criterion.max_score * criterion.weight

        # Update evaluation totals
        evaluation.overall_score = total_score
        evaluation.max_possible_score = total_max
        evaluation.percentage = (total_score / total_max * 100) if total_max > 0 else 0

        logger.info(
            f"Manual QA evaluation created by {tenant.org_name}: "
            f"{evaluation.percentage:.1f}% for conversation {data.conversation_id}"
        )

        return {
            "id": str(evaluation.id),
            "overall_score": evaluation.overall_score,
            "max_possible_score": evaluation.max_possible_score,
            "percentage": evaluation.percentage,
        }


@router.get("/qa/criteria")
async def list_qa_criteria(
    tenant: TenantContext = Depends(require_scope("qa:read")),
):
    """List QA criteria available for the organization"""
    async with get_local_session() as session:
        result = await session.execute(
            select(QaCriterion).where(
                QaCriterion.org_id == uuid.UUID(tenant.org_id),
                QaCriterion.is_active == True,
            ).order_by(QaCriterion.category, QaCriterion.name)
        )
        criteria = result.scalars().all()
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "category": c.category,
                "max_score": c.max_score,
                "weight": c.weight,
                "is_automated": c.is_automated,
            }
            for c in criteria
        ]


# =============================================
# Tenant Info
# =============================================

@router.get("/me")
async def get_my_info(tenant: TenantContext = Depends(get_current_tenant)):
    """Get information about the authenticated organization"""
    async with get_local_session() as session:
        agent_count = (await session.execute(
            select(func.count(Agent.id)).where(
                Agent.org_id == uuid.UUID(tenant.org_id)
            )
        )).scalar()

        return {
            "org_id": tenant.org_id,
            "org_name": tenant.org_name,
            "plan_type": tenant.plan_type,
            "scopes": tenant.scopes,
            "agents_count": agent_count,
        }


# =============================================
# Internal Helpers
# =============================================

async def _get_org_agent_ids(session, org_id: str) -> List[uuid.UUID]:
    """Get all agent IDs for an organization"""
    result = await session.execute(
        select(Agent.id).where(Agent.org_id == uuid.UUID(org_id))
    )
    return [row[0] for row in result.all()]


async def _get_tenant_agent(session, agent_id: str, org_id: str) -> "Agent":
    """Get an agent that belongs to the tenant, or raise 404"""
    result = await session.execute(
        select(Agent).where(
            Agent.id == uuid.UUID(agent_id),
            Agent.org_id == uuid.UUID(org_id),
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or does not belong to your organization",
        )
    return agent


async def _get_tenant_conversation(session, conversation_id: str, org_id: str) -> "Conversation":
    """Get a conversation that belongs to the tenant's agents, or raise 404"""
    agent_ids = await _get_org_agent_ids(session, org_id)

    result = await session.execute(
        select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
    )
    conv = result.scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conv.agent_id and conv.agent_id not in agent_ids:
        raise HTTPException(status_code=403, detail="Conversation does not belong to your organization")

    return conv
