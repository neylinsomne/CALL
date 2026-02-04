"""
Admin API - Internal Management Endpoints
==========================================
CRUD operations for organizations, tokens, and agents.
All endpoints require ADMIN_API_KEY via X-API-Key header.

These endpoints are for OUR internal use only (not exposed to clients).
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from loguru import logger

from database import (
    get_local_session,
    OrganizationLocal,
    ApiTokenLocal,
    Agent,
)
from auth import verify_admin, generate_token, TOKEN_EXPIRY_DAYS

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# =============================================
# Pydantic Schemas
# =============================================

# -- Organizations --

class OrgCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    domain: Optional[str] = Field(None, max_length=200)
    plan_type: str = Field("basic", pattern=r"^(basic|professional|enterprise)$")
    max_agents: int = Field(5, ge=1, le=500)
    settings: Optional[dict] = None


class OrgUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    domain: Optional[str] = Field(None, max_length=200)
    plan_type: Optional[str] = Field(None, pattern=r"^(basic|professional|enterprise)$")
    max_agents: Optional[int] = Field(None, ge=1, le=500)
    is_active: Optional[bool] = None
    settings: Optional[dict] = None


class OrgResponse(BaseModel):
    id: str
    name: str
    domain: Optional[str]
    plan_type: str
    max_agents: int
    is_active: bool
    settings: Optional[dict]
    created_at: str
    updated_at: str


# -- Tokens --

class TokenCreateRequest(BaseModel):
    org_id: str
    name: Optional[str] = Field(None, max_length=100)
    scope: str = Field("agent:read,agent:write,calls:read,qa:read")
    expiry_days: Optional[int] = Field(None, ge=1, le=3650)


class TokenResponse(BaseModel):
    id: str
    org_id: str
    token_prefix: str
    name: Optional[str]
    scope: str
    expires_at: Optional[str]
    last_used_at: Optional[str]
    is_active: bool
    created_at: str


class TokenCreatedResponse(TokenResponse):
    raw_token: str  # Only returned on creation, never again


# -- Agents --

class AgentCreateRequest(BaseModel):
    org_id: str
    name: str = Field(..., min_length=1, max_length=200)
    sip_port: Optional[int] = None
    ws_port: Optional[int] = None
    config: Optional[dict] = None


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[str] = Field(None, pattern=r"^(idle|active|busy|offline|error)$")
    sip_port: Optional[int] = None
    ws_port: Optional[int] = None
    config: Optional[dict] = None


class AgentResponse(BaseModel):
    id: str
    org_id: str
    name: str
    status: str
    sip_port: Optional[int]
    ws_port: Optional[int]
    config: Optional[dict]
    created_at: str
    updated_at: str


# =============================================
# Organization Endpoints
# =============================================

@router.post("/orgs", response_model=OrgResponse, dependencies=[Depends(verify_admin)])
async def create_organization(data: OrgCreateRequest):
    """Create a new client organization"""
    async with get_local_session() as session:
        # Check domain uniqueness
        if data.domain:
            existing = await session.execute(
                select(OrganizationLocal).where(
                    OrganizationLocal.domain == data.domain
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Domain '{data.domain}' already in use",
                )

        org = OrganizationLocal(
            name=data.name,
            domain=data.domain,
            plan_type=data.plan_type,
            max_agents=data.max_agents,
            settings=data.settings or {},
        )
        session.add(org)
        await session.flush()

        logger.info(f"Organization created: {org.name} ({org.id})")
        return _org_to_response(org)


@router.get("/orgs", response_model=List[OrgResponse], dependencies=[Depends(verify_admin)])
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(False),
):
    """List all organizations"""
    async with get_local_session() as session:
        query = select(OrganizationLocal).order_by(OrganizationLocal.created_at.desc())
        if active_only:
            query = query.where(OrganizationLocal.is_active == True)
        query = query.offset(skip).limit(limit)

        result = await session.execute(query)
        orgs = result.scalars().all()
        return [_org_to_response(o) for o in orgs]


@router.get("/orgs/{org_id}", response_model=OrgResponse, dependencies=[Depends(verify_admin)])
async def get_organization(org_id: str):
    """Get organization details"""
    async with get_local_session() as session:
        org = await _get_org_or_404(session, org_id)
        return _org_to_response(org)


@router.put("/orgs/{org_id}", response_model=OrgResponse, dependencies=[Depends(verify_admin)])
async def update_organization(org_id: str, data: OrgUpdateRequest):
    """Update organization details"""
    async with get_local_session() as session:
        org = await _get_org_or_404(session, org_id)

        if data.name is not None:
            org.name = data.name
        if data.domain is not None:
            # Check domain uniqueness
            if data.domain:
                existing = await session.execute(
                    select(OrganizationLocal).where(
                        OrganizationLocal.domain == data.domain,
                        OrganizationLocal.id != org.id,
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Domain '{data.domain}' already in use",
                    )
            org.domain = data.domain
        if data.plan_type is not None:
            org.plan_type = data.plan_type
        if data.max_agents is not None:
            org.max_agents = data.max_agents
        if data.is_active is not None:
            org.is_active = data.is_active
        if data.settings is not None:
            org.settings = data.settings

        org.updated_at = datetime.now(timezone.utc)
        logger.info(f"Organization updated: {org.name} ({org.id})")
        return _org_to_response(org)


@router.delete("/orgs/{org_id}", dependencies=[Depends(verify_admin)])
async def delete_organization(org_id: str):
    """Deactivate an organization (soft delete)"""
    async with get_local_session() as session:
        org = await _get_org_or_404(session, org_id)
        org.is_active = False
        org.updated_at = datetime.now(timezone.utc)

        # Deactivate all tokens for this org
        tokens_result = await session.execute(
            select(ApiTokenLocal).where(
                ApiTokenLocal.org_id == org.id,
                ApiTokenLocal.is_active == True,
            )
        )
        for token in tokens_result.scalars().all():
            token.is_active = False

        logger.warning(f"Organization deactivated: {org.name} ({org.id})")
        return {"status": "deactivated", "org_id": str(org.id)}


# =============================================
# Token Endpoints
# =============================================

@router.post("/tokens", response_model=TokenCreatedResponse, dependencies=[Depends(verify_admin)])
async def create_token(data: TokenCreateRequest):
    """
    Generate a new API token for an organization.
    The raw token is returned ONLY in this response.
    """
    async with get_local_session() as session:
        # Verify org exists
        await _get_org_or_404(session, data.org_id)

        token_data = generate_token()
        expiry_days = data.expiry_days or TOKEN_EXPIRY_DAYS

        token_record = ApiTokenLocal(
            org_id=uuid.UUID(data.org_id),
            token_hash=token_data["token_hash"],
            token_prefix=token_data["token_prefix"],
            name=data.name,
            scope=data.scope,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expiry_days),
        )
        session.add(token_record)
        await session.flush()

        logger.info(
            f"Token created for org {data.org_id}: "
            f"prefix={token_data['token_prefix']}, expires in {expiry_days} days"
        )

        response = _token_to_response(token_record)
        response["raw_token"] = token_data["raw_token"]
        return response


@router.get("/tokens", response_model=List[TokenResponse], dependencies=[Depends(verify_admin)])
async def list_tokens(
    org_id: Optional[str] = Query(None),
    active_only: bool = Query(False),
):
    """List tokens, optionally filtered by organization"""
    async with get_local_session() as session:
        query = select(ApiTokenLocal).order_by(ApiTokenLocal.created_at.desc())
        if org_id:
            query = query.where(ApiTokenLocal.org_id == uuid.UUID(org_id))
        if active_only:
            query = query.where(ApiTokenLocal.is_active == True)

        result = await session.execute(query)
        tokens = result.scalars().all()
        return [_token_to_response(t) for t in tokens]


@router.post("/tokens/{token_id}/rotate", dependencies=[Depends(verify_admin)])
async def rotate_token(token_id: str):
    """
    Rotate a token: deactivate the old one and generate a new one
    with the same org_id, scope, and expiry period.
    """
    async with get_local_session() as session:
        result = await session.execute(
            select(ApiTokenLocal).where(ApiTokenLocal.id == uuid.UUID(token_id))
        )
        old_token = result.scalar_one_or_none()
        if not old_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found",
            )

        # Deactivate old token
        old_token.is_active = False

        # Generate new token with same properties
        token_data = generate_token()
        new_token = ApiTokenLocal(
            org_id=old_token.org_id,
            token_hash=token_data["token_hash"],
            token_prefix=token_data["token_prefix"],
            name=old_token.name,
            scope=old_token.scope,
            expires_at=datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS),
        )
        session.add(new_token)
        await session.flush()

        logger.info(
            f"Token rotated for org {old_token.org_id}: "
            f"old={old_token.token_prefix} -> new={token_data['token_prefix']}"
        )

        response = _token_to_response(new_token)
        response["raw_token"] = token_data["raw_token"]
        response["old_token_prefix"] = old_token.token_prefix
        return response


@router.delete("/tokens/{token_id}", dependencies=[Depends(verify_admin)])
async def revoke_token(token_id: str):
    """Revoke (deactivate) a token"""
    async with get_local_session() as session:
        result = await session.execute(
            select(ApiTokenLocal).where(ApiTokenLocal.id == uuid.UUID(token_id))
        )
        token = result.scalar_one_or_none()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found",
            )

        token.is_active = False
        logger.warning(f"Token revoked: {token.token_prefix} (org {token.org_id})")
        return {"status": "revoked", "token_id": str(token.id)}


# =============================================
# Agent Endpoints (admin view)
# =============================================

@router.post("/agents", response_model=AgentResponse, dependencies=[Depends(verify_admin)])
async def create_agent(data: AgentCreateRequest):
    """Register a new agent for an organization"""
    async with get_local_session() as session:
        org = await _get_org_or_404(session, data.org_id)

        # Check agent limit
        count_result = await session.execute(
            select(func.count(Agent.id)).where(
                Agent.org_id == org.id
            )
        )
        current_count = count_result.scalar()
        if current_count >= org.max_agents:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Agent limit reached ({current_count}/{org.max_agents}). "
                       f"Upgrade plan to add more agents.",
            )

        agent = Agent(
            org_id=org.id,
            name=data.name,
            sip_port=data.sip_port,
            ws_port=data.ws_port,
            config=data.config or {},
        )
        session.add(agent)
        await session.flush()

        logger.info(f"Agent created: {agent.name} ({agent.id}) for org {data.org_id}")
        return _agent_to_response(agent)


@router.get("/agents", response_model=List[AgentResponse], dependencies=[Depends(verify_admin)])
async def list_agents(
    org_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """List all agents, optionally filtered by org or status"""
    async with get_local_session() as session:
        query = select(Agent).order_by(Agent.created_at.desc())
        if org_id:
            query = query.where(Agent.org_id == uuid.UUID(org_id))
        if status_filter:
            query = query.where(Agent.status == status_filter)

        result = await session.execute(query)
        agents = result.scalars().all()
        return [_agent_to_response(a) for a in agents]


@router.get("/agents/{agent_id}", response_model=AgentResponse, dependencies=[Depends(verify_admin)])
async def get_agent(agent_id: str):
    """Get agent details"""
    async with get_local_session() as session:
        result = await session.execute(
            select(Agent).where(Agent.id == uuid.UUID(agent_id))
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return _agent_to_response(agent)


@router.put("/agents/{agent_id}", response_model=AgentResponse, dependencies=[Depends(verify_admin)])
async def update_agent(agent_id: str, data: AgentUpdateRequest):
    """Update agent configuration"""
    async with get_local_session() as session:
        result = await session.execute(
            select(Agent).where(Agent.id == uuid.UUID(agent_id))
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        if data.name is not None:
            agent.name = data.name
        if data.status is not None:
            agent.status = data.status
        if data.sip_port is not None:
            agent.sip_port = data.sip_port
        if data.ws_port is not None:
            agent.ws_port = data.ws_port
        if data.config is not None:
            agent.config = data.config

        agent.updated_at = datetime.now(timezone.utc)
        logger.info(f"Agent updated: {agent.name} ({agent.id})")
        return _agent_to_response(agent)


# =============================================
# Admin Dashboard Stats
# =============================================

@router.get("/stats", dependencies=[Depends(verify_admin)])
async def get_admin_stats():
    """Get overall system statistics"""
    async with get_local_session() as session:
        # Count organizations
        org_count = (await session.execute(
            select(func.count(OrganizationLocal.id))
        )).scalar()
        active_org_count = (await session.execute(
            select(func.count(OrganizationLocal.id)).where(
                OrganizationLocal.is_active == True
            )
        )).scalar()

        # Count tokens
        token_count = (await session.execute(
            select(func.count(ApiTokenLocal.id))
        )).scalar()
        active_token_count = (await session.execute(
            select(func.count(ApiTokenLocal.id)).where(
                ApiTokenLocal.is_active == True
            )
        )).scalar()

        # Count agents
        agent_count = (await session.execute(
            select(func.count(Agent.id))
        )).scalar()
        active_agent_count = (await session.execute(
            select(func.count(Agent.id)).where(
                Agent.status.in_(["idle", "active", "busy"])
            )
        )).scalar()

        return {
            "organizations": {"total": org_count, "active": active_org_count},
            "tokens": {"total": token_count, "active": active_token_count},
            "agents": {"total": agent_count, "online": active_agent_count},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# =============================================
# Internal Helpers
# =============================================

async def _get_org_or_404(session, org_id: str) -> OrganizationLocal:
    """Get an organization or raise 404"""
    result = await session.execute(
        select(OrganizationLocal).where(
            OrganizationLocal.id == uuid.UUID(org_id)
        )
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return org


def _org_to_response(org: OrganizationLocal) -> dict:
    return {
        "id": str(org.id),
        "name": org.name,
        "domain": org.domain,
        "plan_type": org.plan_type,
        "max_agents": org.max_agents,
        "is_active": org.is_active,
        "settings": org.settings,
        "created_at": org.created_at.isoformat() if org.created_at else "",
        "updated_at": org.updated_at.isoformat() if org.updated_at else "",
    }


def _token_to_response(token: ApiTokenLocal) -> dict:
    return {
        "id": str(token.id),
        "org_id": str(token.org_id),
        "token_prefix": token.token_prefix,
        "name": token.name,
        "scope": token.scope,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
        "is_active": token.is_active,
        "created_at": token.created_at.isoformat() if token.created_at else "",
    }


def _agent_to_response(agent: Agent) -> dict:
    return {
        "id": str(agent.id),
        "org_id": str(agent.org_id),
        "name": agent.name,
        "status": agent.status,
        "sip_port": agent.sip_port,
        "ws_port": agent.ws_port,
        "config": agent.config,
        "created_at": agent.created_at.isoformat() if agent.created_at else "",
        "updated_at": agent.updated_at.isoformat() if agent.updated_at else "",
    }
