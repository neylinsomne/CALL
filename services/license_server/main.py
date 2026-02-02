"""
License Server - Sistema de Gestión de Licencias
================================================

Servidor centralizado para validar licencias de clientes on-premise.
Rastrea uso, valida hardware binding, y previene piratería.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
import secrets
import hashlib
import os
from contextlib import asynccontextmanager

# Database setup
DATABASE_URL = os.getenv("LICENSE_DATABASE_URL", "sqlite:///./licenses.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class License(Base):
    """Modelo de licencia en la base de datos"""
    __tablename__ = "licenses"

    license_key = Column(String, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)
    hardware_id = Column(String, nullable=True)  # Se vincula en primera activación

    # Limits
    max_concurrent_calls = Column(Integer, default=5)
    max_agents = Column(Integer, default=10)

    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_trial = Column(Boolean, default=False)

    # Telemetry
    total_calls = Column(Integer, default=0)
    total_minutes = Column(Integer, default=0)
    metadata = Column(JSON, default={})  # Información adicional


class Heartbeat(Base):
    """Registro de heartbeats para detectar uso"""
    __tablename__ = "heartbeats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    license_key = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Telemetry data
    active_calls = Column(Integer, default=0)
    active_agents = Column(Integer, default=0)
    server_ip = Column(String, nullable=True)
    version = Column(String, nullable=True)

    # Resource usage
    cpu_usage = Column(Integer, nullable=True)
    memory_usage = Column(Integer, nullable=True)
    disk_usage = Column(Integer, nullable=True)


# Pydantic models
class LicenseCreate(BaseModel):
    """Request para crear nueva licencia"""
    client_name: str = Field(..., min_length=3, max_length=100)
    client_email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    max_concurrent_calls: int = Field(default=5, ge=1, le=1000)
    max_agents: int = Field(default=10, ge=1, le=500)
    validity_days: int = Field(default=365, ge=1, le=3650)
    is_trial: bool = False


class LicenseValidateRequest(BaseModel):
    """Request para validar licencia"""
    license_key: str = Field(..., min_length=32, max_length=64)
    hardware_id: str = Field(..., min_length=32, max_length=128)


class LicenseValidateResponse(BaseModel):
    """Response de validación"""
    valid: bool
    message: str
    license_info: Optional[dict] = None


class HeartbeatRequest(BaseModel):
    """Request de heartbeat desde cliente"""
    license_key: str
    active_calls: int = 0
    active_agents: int = 0
    server_ip: Optional[str] = None
    version: Optional[str] = None
    cpu_usage: Optional[int] = None
    memory_usage: Optional[int] = None
    disk_usage: Optional[int] = None


class CallReportRequest(BaseModel):
    """Reporte de llamadas completadas"""
    license_key: str
    calls_count: int
    total_minutes: int


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# License generation
def generate_license_key() -> str:
    """Genera una clave de licencia única"""
    # Formato: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
    parts = []
    for _ in range(8):
        part = secrets.token_hex(2).upper()
        parts.append(part)
    return '-'.join(parts)


def verify_hardware_binding(license: License, hardware_id: str) -> bool:
    """Verifica que el hardware_id coincida con la licencia"""
    if license.hardware_id is None:
        # Primera activación - vincular hardware
        return True
    return license.hardware_id == hardware_id


# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="License Server",
    description="Sistema de gestión de licencias para Call Center AI on-premise",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# License endpoints
@app.post("/api/license/generate", response_model=dict)
async def generate_license(
    license_data: LicenseCreate,
    db: Session = Depends(get_db)
):
    """
    Genera una nueva licencia para un cliente.

    Solo debe ser accesible por administradores internos.
    """
    try:
        # Generar clave única
        license_key = generate_license_key()

        # Calcular fecha de expiración
        expires_at = datetime.utcnow() + timedelta(days=license_data.validity_days)

        # Crear licencia
        new_license = License(
            license_key=license_key,
            client_name=license_data.client_name,
            client_email=license_data.client_email,
            max_concurrent_calls=license_data.max_concurrent_calls,
            max_agents=license_data.max_agents,
            expires_at=expires_at,
            is_trial=license_data.is_trial,
            is_active=True,
            metadata={
                "generated_by": "admin",
                "creation_timestamp": datetime.utcnow().isoformat()
            }
        )

        db.add(new_license)
        db.commit()
        db.refresh(new_license)

        return {
            "success": True,
            "license_key": license_key,
            "client_name": license_data.client_name,
            "expires_at": expires_at.isoformat(),
            "max_concurrent_calls": license_data.max_concurrent_calls,
            "max_agents": license_data.max_agents,
            "is_trial": license_data.is_trial
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating license: {str(e)}"
        )


@app.post("/api/license/validate", response_model=LicenseValidateResponse)
async def validate_license(
    request: LicenseValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Valida una licencia y vincula hardware en primera activación.

    Usado por clientes on-premise para verificar licencias.
    """
    # Buscar licencia
    license = db.query(License).filter(License.license_key == request.license_key).first()

    if not license:
        return LicenseValidateResponse(
            valid=False,
            message="Licencia no encontrada"
        )

    # Verificar si está activa
    if not license.is_active:
        return LicenseValidateResponse(
            valid=False,
            message="Licencia desactivada"
        )

    # Verificar expiración
    if datetime.utcnow() > license.expires_at:
        return LicenseValidateResponse(
            valid=False,
            message=f"Licencia expirada el {license.expires_at.isoformat()}"
        )

    # Verificar hardware binding
    if not verify_hardware_binding(license, request.hardware_id):
        return LicenseValidateResponse(
            valid=False,
            message="Hardware no autorizado. Esta licencia está vinculada a otro servidor."
        )

    # Primera activación - vincular hardware
    if license.hardware_id is None:
        license.hardware_id = request.hardware_id
        license.activated_at = datetime.utcnow()
        db.commit()

    # Actualizar último heartbeat
    license.last_heartbeat = datetime.utcnow()
    db.commit()

    # Calcular días restantes
    days_remaining = (license.expires_at - datetime.utcnow()).days

    return LicenseValidateResponse(
        valid=True,
        message="Licencia válida",
        license_info={
            "client_name": license.client_name,
            "max_concurrent_calls": license.max_concurrent_calls,
            "max_agents": license.max_agents,
            "expires_at": license.expires_at.isoformat(),
            "days_remaining": days_remaining,
            "is_trial": license.is_trial,
            "activated_at": license.activated_at.isoformat() if license.activated_at else None
        }
    )


@app.post("/api/license/heartbeat")
async def receive_heartbeat(
    heartbeat: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    """
    Recibe heartbeat de cliente on-premise.

    Permite rastrear uso y detectar instalaciones no autorizadas.
    """
    # Verificar que la licencia existe
    license = db.query(License).filter(License.license_key == heartbeat.license_key).first()

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )

    # Actualizar último heartbeat en licencia
    license.last_heartbeat = datetime.utcnow()

    # Registrar heartbeat
    new_heartbeat = Heartbeat(
        license_key=heartbeat.license_key,
        active_calls=heartbeat.active_calls,
        active_agents=heartbeat.active_agents,
        server_ip=heartbeat.server_ip,
        version=heartbeat.version,
        cpu_usage=heartbeat.cpu_usage,
        memory_usage=heartbeat.memory_usage,
        disk_usage=heartbeat.disk_usage
    )

    db.add(new_heartbeat)

    # Verificar límites
    warnings = []
    if heartbeat.active_calls > license.max_concurrent_calls:
        warnings.append(f"Llamadas concurrentes ({heartbeat.active_calls}) exceden el límite ({license.max_concurrent_calls})")

    if heartbeat.active_agents > license.max_agents:
        warnings.append(f"Agentes activos ({heartbeat.active_agents}) exceden el límite ({license.max_agents})")

    db.commit()

    return {
        "success": True,
        "timestamp": datetime.utcnow().isoformat(),
        "warnings": warnings if warnings else None,
        "license_status": "active" if license.is_active else "inactive",
        "days_remaining": (license.expires_at - datetime.utcnow()).days
    }


@app.post("/api/license/report-calls")
async def report_calls(
    report: CallReportRequest,
    db: Session = Depends(get_db)
):
    """
    Recibe reporte de llamadas completadas.

    Actualiza estadísticas de uso.
    """
    license = db.query(License).filter(License.license_key == report.license_key).first()

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )

    # Actualizar estadísticas
    license.total_calls += report.calls_count
    license.total_minutes += report.total_minutes

    db.commit()

    return {
        "success": True,
        "total_calls": license.total_calls,
        "total_minutes": license.total_minutes
    }


@app.get("/api/license/{license_key}/info")
async def get_license_info(
    license_key: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene información detallada de una licencia.

    Solo para administradores.
    """
    license = db.query(License).filter(License.license_key == license_key).first()

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )

    # Obtener últimos heartbeats
    recent_heartbeats = db.query(Heartbeat).filter(
        Heartbeat.license_key == license_key
    ).order_by(Heartbeat.timestamp.desc()).limit(10).all()

    return {
        "license_key": license.license_key,
        "client_name": license.client_name,
        "client_email": license.client_email,
        "hardware_id": license.hardware_id,
        "max_concurrent_calls": license.max_concurrent_calls,
        "max_agents": license.max_agents,
        "created_at": license.created_at.isoformat(),
        "activated_at": license.activated_at.isoformat() if license.activated_at else None,
        "expires_at": license.expires_at.isoformat(),
        "last_heartbeat": license.last_heartbeat.isoformat() if license.last_heartbeat else None,
        "is_active": license.is_active,
        "is_trial": license.is_trial,
        "total_calls": license.total_calls,
        "total_minutes": license.total_minutes,
        "days_remaining": (license.expires_at - datetime.utcnow()).days,
        "recent_heartbeats": [
            {
                "timestamp": hb.timestamp.isoformat(),
                "active_calls": hb.active_calls,
                "active_agents": hb.active_agents,
                "server_ip": hb.server_ip,
                "version": hb.version
            }
            for hb in recent_heartbeats
        ]
    }


@app.get("/api/licenses/list")
async def list_licenses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lista todas las licencias.

    Solo para administradores.
    """
    licenses = db.query(License).offset(skip).limit(limit).all()

    return {
        "total": db.query(License).count(),
        "licenses": [
            {
                "license_key": lic.license_key,
                "client_name": lic.client_name,
                "client_email": lic.client_email,
                "expires_at": lic.expires_at.isoformat(),
                "is_active": lic.is_active,
                "is_trial": lic.is_trial,
                "total_calls": lic.total_calls,
                "last_heartbeat": lic.last_heartbeat.isoformat() if lic.last_heartbeat else None,
                "days_remaining": (lic.expires_at - datetime.utcnow()).days
            }
            for lic in licenses
        ]
    }


@app.put("/api/license/{license_key}/deactivate")
async def deactivate_license(
    license_key: str,
    db: Session = Depends(get_db)
):
    """
    Desactiva una licencia.

    Útil para cancelaciones o violaciones de términos.
    """
    license = db.query(License).filter(License.license_key == license_key).first()

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )

    license.is_active = False
    db.commit()

    return {
        "success": True,
        "message": f"Licencia {license_key} desactivada",
        "client_name": license.client_name
    }


@app.put("/api/license/{license_key}/extend")
async def extend_license(
    license_key: str,
    days: int,
    db: Session = Depends(get_db)
):
    """
    Extiende la validez de una licencia.

    Útil para renovaciones.
    """
    license = db.query(License).filter(License.license_key == license_key).first()

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )

    license.expires_at = license.expires_at + timedelta(days=days)
    db.commit()

    return {
        "success": True,
        "message": f"Licencia extendida por {days} días",
        "new_expiration": license.expires_at.isoformat(),
        "days_remaining": (license.expires_at - datetime.utcnow()).days
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
