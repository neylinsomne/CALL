"""
License Admin - Endpoints para gestión de licencias
===================================================

Router para que administradores internos gestionen licencias.
Solo debe ser accesible con autenticación de admin.
"""

import os
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import BaseModel, Field
import httpx
from loguru import logger

router = APIRouter(prefix="/api/admin/licenses", tags=["License Admin"])

# License server URL
LICENSE_SERVER_URL = os.getenv("LICENSE_SERVER_URL", "http://license_server:8000")

# Admin API key (simple authentication)
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")


# Authentication dependency
async def verify_admin(x_api_key: Optional[str] = Header(None)):
    """Verifica que el usuario tiene permisos de administrador"""
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True


# Pydantic models
class LicenseCreateRequest(BaseModel):
    """Request para crear nueva licencia"""
    client_name: str = Field(..., min_length=3, max_length=100)
    client_email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    max_concurrent_calls: int = Field(default=5, ge=1, le=1000)
    max_agents: int = Field(default=10, ge=1, le=500)
    validity_days: int = Field(default=365, ge=1, le=3650)
    is_trial: bool = False


class LicenseExtendRequest(BaseModel):
    """Request para extender licencia"""
    days: int = Field(..., ge=1, le=3650)


# Admin endpoints
@router.post("/generate", dependencies=[Depends(verify_admin)])
async def generate_license(license_data: LicenseCreateRequest):
    """
    Genera una nueva licencia.

    Requiere autenticación de administrador.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LICENSE_SERVER_URL}/api/license/generate",
                json=license_data.dict()
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"License generated for {license_data.client_name}: {data['license_key']}")
                return data
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"License server error: {response.text}"
                )

    except httpx.RequestError as e:
        logger.error(f"Error connecting to license server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="License server unavailable"
        )


@router.get("/list", dependencies=[Depends(verify_admin)])
async def list_licenses(skip: int = 0, limit: int = 100):
    """
    Lista todas las licencias.

    Requiere autenticación de administrador.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{LICENSE_SERVER_URL}/api/licenses/list",
                params={"skip": skip, "limit": limit}
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"License server error: {response.text}"
                )

    except httpx.RequestError as e:
        logger.error(f"Error connecting to license server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="License server unavailable"
        )


@router.get("/{license_key}", dependencies=[Depends(verify_admin)])
async def get_license_info(license_key: str):
    """
    Obtiene información detallada de una licencia.

    Requiere autenticación de administrador.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{LICENSE_SERVER_URL}/api/license/{license_key}/info"
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="License not found"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"License server error: {response.text}"
                )

    except httpx.RequestError as e:
        logger.error(f"Error connecting to license server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="License server unavailable"
        )


@router.put("/{license_key}/deactivate", dependencies=[Depends(verify_admin)])
async def deactivate_license(license_key: str):
    """
    Desactiva una licencia.

    Útil para cancelaciones o violaciones de términos.
    Requiere autenticación de administrador.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{LICENSE_SERVER_URL}/api/license/{license_key}/deactivate"
            )

            if response.status_code == 200:
                data = response.json()
                logger.warning(f"License deactivated: {license_key} ({data.get('client_name')})")
                return data
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="License not found"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"License server error: {response.text}"
                )

    except httpx.RequestError as e:
        logger.error(f"Error connecting to license server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="License server unavailable"
        )


@router.put("/{license_key}/extend", dependencies=[Depends(verify_admin)])
async def extend_license(license_key: str, extend_data: LicenseExtendRequest):
    """
    Extiende la validez de una licencia.

    Útil para renovaciones.
    Requiere autenticación de administrador.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{LICENSE_SERVER_URL}/api/license/{license_key}/extend",
                params={"days": extend_data.days}
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"License extended: {license_key} (+{extend_data.days} days)")
                return data
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="License not found"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"License server error: {response.text}"
                )

    except httpx.RequestError as e:
        logger.error(f"Error connecting to license server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="License server unavailable"
        )


@router.get("/stats/summary", dependencies=[Depends(verify_admin)])
async def get_license_stats():
    """
    Obtiene estadísticas resumidas de todas las licencias.

    Requiere autenticación de administrador.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get all licenses
            response = await client.get(
                f"{LICENSE_SERVER_URL}/api/licenses/list",
                params={"skip": 0, "limit": 1000}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="License server error"
                )

            data = response.json()
            licenses = data.get("licenses", [])

            # Calculate stats
            total = len(licenses)
            active = sum(1 for lic in licenses if lic["is_active"])
            expired = sum(1 for lic in licenses if lic["days_remaining"] <= 0)
            expiring_soon = sum(1 for lic in licenses if 0 < lic["days_remaining"] <= 30)
            trial = sum(1 for lic in licenses if lic["is_trial"])

            total_calls = sum(lic.get("total_calls", 0) for lic in licenses)

            # Find licenses without recent heartbeat (7 days)
            inactive = sum(
                1 for lic in licenses
                if lic.get("last_heartbeat") is None or
                (datetime.utcnow() - datetime.fromisoformat(lic["last_heartbeat"])).days > 7
            )

            return {
                "total_licenses": total,
                "active_licenses": active,
                "expired_licenses": expired,
                "expiring_soon": expiring_soon,
                "trial_licenses": trial,
                "inactive_licenses": inactive,
                "total_calls_processed": total_calls,
                "timestamp": datetime.utcnow().isoformat()
            }

    except httpx.RequestError as e:
        logger.error(f"Error connecting to license server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="License server unavailable"
        )
