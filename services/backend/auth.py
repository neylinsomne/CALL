"""
Multi-Tenant Authentication Module
====================================
Handles API token validation, org_id injection, and scope-based permissions.

Tokens are stored hashed in the database. The raw token format is:
    cc_{prefix}_{random_secret}

Where:
    - cc_ is a fixed prefix for identification
    - {prefix} is 8 chars stored in plain text for quick lookup
    - {random_secret} is 32 chars, only stored as SHA-256 hash

Token rotation:
    - Tokens expire after 90 days (configurable)
    - Background task marks expired tokens as inactive
    - Admins generate new tokens via POST /api/admin/tokens
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import Depends, HTTPException, Header, status, Request
from sqlalchemy import select, update
from loguru import logger

from database import get_local_session, OrganizationLocal, ApiTokenLocal


# Configuration
TOKEN_EXPIRY_DAYS = int(os.getenv("TOKEN_EXPIRY_DAYS", "90"))
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")


# =============================================
# Token Utilities
# =============================================

def generate_token() -> dict:
    """
    Generate a new API token.

    Returns dict with:
        - raw_token: the full token to give to the client (only shown once)
        - token_prefix: stored in DB for quick lookup
        - token_hash: SHA-256 hash stored in DB for validation
    """
    prefix = secrets.token_hex(4)  # 8 chars
    secret = secrets.token_hex(16)  # 32 chars
    raw_token = f"cc_{prefix}_{secret}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return {
        "raw_token": raw_token,
        "token_prefix": prefix,
        "token_hash": token_hash,
    }


def hash_token(raw_token: str) -> str:
    """Hash a raw token for comparison"""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def parse_token(raw_token: str) -> Optional[dict]:
    """Parse a raw token into prefix and hash. Returns None if format invalid."""
    if not raw_token or not raw_token.startswith("cc_"):
        return None
    parts = raw_token.split("_", 2)
    if len(parts) != 3:
        return None
    prefix = parts[1]
    if len(prefix) != 8:
        return None
    return {
        "token_prefix": prefix,
        "token_hash": hashlib.sha256(raw_token.encode()).hexdigest(),
    }


# =============================================
# Admin Authentication (internal use)
# =============================================

async def verify_admin(x_api_key: Optional[str] = Header(None)):
    """
    Verify admin access via X-API-Key header.
    Used for internal admin endpoints only.
    """
    if not x_api_key or x_api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key",
        )
    return True


# =============================================
# Tenant Authentication (client API)
# =============================================

class TenantContext:
    """Holds the authenticated tenant information for the current request."""

    def __init__(self, org_id: str, org_name: str, plan_type: str,
                 scopes: List[str], token_id: str):
        self.org_id = org_id
        self.org_name = org_name
        self.plan_type = plan_type
        self.scopes = scopes
        self.token_id = token_id

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


async def get_current_tenant(
    authorization: Optional[str] = Header(None),
) -> TenantContext:
    """
    FastAPI dependency that validates the Bearer token and returns
    the authenticated tenant context.

    Expected header: Authorization: Bearer cc_{prefix}_{secret}
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse Bearer token
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = parts[1]
    parsed = parse_token(raw_token)
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up token in database
    async with get_local_session() as session:
        result = await session.execute(
            select(ApiTokenLocal).where(
                ApiTokenLocal.token_prefix == parsed["token_prefix"],
                ApiTokenLocal.is_active == True,
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify hash
        if token_record.token_hash != parsed["token_hash"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check expiration
        if token_record.expires_at and token_record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired. Contact administrator to obtain a new token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last_used_at
        token_record.last_used_at = datetime.utcnow()

        # Get the organization
        org_result = await session.execute(
            select(OrganizationLocal).where(
                OrganizationLocal.id == token_record.org_id
            )
        )
        org = org_result.scalar_one_or_none()

        if not org or not org.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization is inactive",
            )

        scopes = [s.strip() for s in token_record.scope.split(",")]

        return TenantContext(
            org_id=str(org.id),
            org_name=org.name,
            plan_type=org.plan_type,
            scopes=scopes,
            token_id=str(token_record.id),
        )


# =============================================
# Scope-Based Permission Decorator
# =============================================

def require_scope(scope: str):
    """
    Returns a FastAPI dependency that checks if the authenticated
    tenant has the required scope.

    Usage:
        @router.get("/agents", dependencies=[Depends(require_scope("agent:read"))])
        async def list_agents(tenant: TenantContext = Depends(get_current_tenant)):
            ...
    """
    async def _check_scope(
        tenant: TenantContext = Depends(get_current_tenant),
    ) -> TenantContext:
        if not tenant.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {scope}",
            )
        return tenant

    return _check_scope


# =============================================
# Background Task: Expire Old Tokens
# =============================================

async def expire_old_tokens():
    """
    Mark tokens past their expires_at as inactive.
    Should be called periodically by a scheduler.
    """
    async with get_local_session() as session:
        now = datetime.utcnow()
        result = await session.execute(
            update(ApiTokenLocal)
            .where(
                ApiTokenLocal.is_active == True,
                ApiTokenLocal.expires_at != None,
                ApiTokenLocal.expires_at < now,
            )
            .values(is_active=False)
        )
        expired_count = result.rowcount
        if expired_count > 0:
            logger.info(f"Expired {expired_count} token(s)")
        return expired_count
