"""
Configuration Manager
====================

Maneja la configuración del sistema de call center:
- Detección de hardware
- Guardado/carga de configuración
- Generación de archivos .env
- Validación de configuración

Endpoints:
- POST /api/config/detect-hardware - Detecta hardware automáticamente
- POST /api/config/save - Guarda configuración
- GET /api/config - Obtiene configuración actual
- POST /api/config/validate - Valida configuración
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
import aiofiles

from hardware_detector import HardwareDetector

logger = logging.getLogger(__name__)

router = APIRouter()

# Ruta de configuración
CONFIG_DIR = Path("/app/config")  # En Docker
if not CONFIG_DIR.exists():
    CONFIG_DIR = Path("./config")  # Local para desarrollo

CONFIG_FILE = CONFIG_DIR / "callcenter_config.json"
ENV_FILE = Path(".env")


# ============================================
# MODELS
# ============================================

class SipTrunkConfig(BaseModel):
    host: str
    user: str
    password: str
    outboundCallerId: str = ""


class GatewayConfig(BaseModel):
    ip: str = ""
    user: str = "gateway"
    password: str = ""


class HardwareConfig(BaseModel):
    type: Optional[str] = None
    gateway: GatewayConfig = GatewayConfig()
    pstnChannels: int = 0


class TelephonyConfig(BaseModel):
    useSipTrunk: Optional[bool] = None
    sipTrunk: SipTrunkConfig = SipTrunkConfig(host="", user="", password="")
    hardware: HardwareConfig = HardwareConfig()


class STTConfig(BaseModel):
    enabled: bool = True
    port: int = 8002
    model: str = "large-v3"
    device: str = "cuda"
    language: str = "es"


class TTSConfig(BaseModel):
    enabled: bool = True
    port: int = 8001
    model: str = "jpgallegoar/F5-Spanish"
    device: str = "cuda"


class LLMConfig(BaseModel):
    enabled: bool = True
    port: int = 8003
    model: str = "local-model"
    provider: str = "lm-studio"


class AIServicesConfig(BaseModel):
    stt: STTConfig = STTConfig()
    tts: TTSConfig = TTSConfig()
    llm: LLMConfig = LLMConfig()


class VoiceTrainingConfig(BaseModel):
    enabled: bool = False
    referenceAudio: Optional[str] = None
    targetSpeaker: str = ""


class CallCenterConfig(BaseModel):
    telephony: TelephonyConfig
    aiServices: AIServicesConfig = AIServicesConfig()
    voiceTraining: VoiceTrainingConfig = VoiceTrainingConfig()


# ============================================
# ENDPOINTS
# ============================================

@router.post("/api/config/detect-hardware")
async def detect_hardware():
    """
    Detecta automáticamente el hardware de telefonía disponible

    Returns:
        {
            "hardware_type": "gateway" | "dahdi" | "both" | "sip_only",
            "pstn_channels": int,
            "gateway_detected": bool,
            "gateway_ip": str | null,
            "dahdi_detected": bool,
            "dahdi_channels": list,
            "max_concurrent_calls": int,
            "route_preference": list
        }
    """
    try:
        detector = HardwareDetector()
        hardware_type = await detector.detect_hardware()

        pipeline_config = detector.get_pipeline_config()

        result = {
            "hardware_type": hardware_type,
            "pstn_channels": detector.get_available_channels(),
            "gateway_detected": detector.gateway_count > 0,
            "gateway_ip": os.getenv("GATEWAY_FXO_IP") if detector.gateway_count > 0 else None,
            "dahdi_detected": detector.dahdi_count > 0,
            "dahdi_channels": detector.dahdi_channels,
            "max_concurrent_calls": pipeline_config["max_concurrent_calls"],
            "route_preference": pipeline_config["route_preference"],
            "codecs": pipeline_config["codecs"],
            "contexts": pipeline_config["contexts"]
        }

        logger.info(f"✅ Hardware detectado: {hardware_type}")
        return result

    except Exception as e:
        logger.error(f"Error detectando hardware: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/save")
async def save_configuration(config: CallCenterConfig):
    """
    Guarda la configuración del call center

    Args:
        config: Configuración completa del sistema

    Returns:
        {
            "success": bool,
            "config_file": str,
            "env_updated": bool
        }
    """
    try:
        # Crear directorio si no existe
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Guardar configuración como JSON
        config_dict = config.dict()

        async with aiofiles.open(CONFIG_FILE, 'w') as f:
            await f.write(json.dumps(config_dict, indent=2))

        logger.info(f"✅ Configuración guardada en {CONFIG_FILE}")

        # Actualizar archivo .env
        env_updated = await update_env_file(config)

        # Aplicar configuración a Asterisk (si es necesario)
        if config.telephony.useSipTrunk:
            await configure_sip_trunk(config.telephony.sipTrunk)
        else:
            await configure_pstn_hardware(config.telephony.hardware)

        return {
            "success": True,
            "config_file": str(CONFIG_FILE),
            "env_updated": env_updated,
            "message": "Configuración guardada correctamente"
        }

    except Exception as e:
        logger.error(f"Error guardando configuración: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/config")
async def get_configuration():
    """
    Obtiene la configuración actual del sistema

    Returns:
        CallCenterConfig | dict con valores por defecto
    """
    try:
        if CONFIG_FILE.exists():
            async with aiofiles.open(CONFIG_FILE, 'r') as f:
                content = await f.read()
                config_dict = json.loads(content)
                return config_dict
        else:
            # Retornar configuración por defecto
            return {
                "telephony": {
                    "useSipTrunk": None,
                    "sipTrunk": {"host": "", "user": "", "password": ""},
                    "hardware": {"type": None, "pstnChannels": 0}
                },
                "aiServices": {
                    "stt": {"enabled": True, "port": 8002, "model": "large-v3"},
                    "tts": {"enabled": True, "port": 8001},
                    "llm": {"enabled": True, "port": 8003, "provider": "lm-studio"}
                },
                "voiceTraining": {"enabled": False}
            }

    except Exception as e:
        logger.error(f"Error leyendo configuración: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/validate")
async def validate_configuration(config: CallCenterConfig):
    """
    Valida la configuración antes de guardarla

    Returns:
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str]
        }
    """
    errors = []
    warnings = []

    # Validar telefonía
    if config.telephony.useSipTrunk is None:
        errors.append("Debe seleccionar un tipo de telefonía (SIP Trunk o Hardware)")

    if config.telephony.useSipTrunk:
        if not config.telephony.sipTrunk.host:
            errors.append("El host del SIP Trunk es requerido")
        if not config.telephony.sipTrunk.user:
            errors.append("El usuario del SIP Trunk es requerido")
        if not config.telephony.sipTrunk.password:
            errors.append("La contraseña del SIP Trunk es requerida")

    # Validar servicios de IA
    if not any([
        config.aiServices.stt.enabled,
        config.aiServices.tts.enabled,
        config.aiServices.llm.enabled
    ]):
        warnings.append("Todos los servicios de IA están deshabilitados")

    # Validar voice training
    if config.voiceTraining.enabled and not config.voiceTraining.targetSpeaker:
        warnings.append("El nombre del speaker es recomendado para voice training")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


@router.post("/api/config/upload-voice")
async def upload_voice_reference(file: UploadFile = File(...)):
    """
    Sube archivo de audio de referencia para clonación de voz

    Returns:
        {
            "filename": str,
            "path": str,
            "size": int
        }
    """
    try:
        # Crear directorio para voice training
        voice_dir = CONFIG_DIR / "voice_training"
        voice_dir.mkdir(parents=True, exist_ok=True)

        # Guardar archivo
        file_path = voice_dir / file.filename

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        logger.info(f"✅ Audio de referencia guardado: {file_path}")

        return {
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"Error subiendo archivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# HELPER FUNCTIONS
# ============================================

async def update_env_file(config: CallCenterConfig) -> bool:
    """
    Actualiza el archivo .env con la nueva configuración

    Args:
        config: Configuración del call center

    Returns:
        True si se actualizó correctamente
    """
    try:
        # Leer .env actual
        env_vars = {}

        if ENV_FILE.exists():
            async with aiofiles.open(ENV_FILE, 'r') as f:
                content = await f.read()
                for line in content.split('\n'):
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

        # Actualizar variables según configuración

        # Telefonía
        if config.telephony.useSipTrunk:
            env_vars['SIP_TRUNK_HOST'] = config.telephony.sipTrunk.host
            env_vars['SIP_TRUNK_USER'] = config.telephony.sipTrunk.user
            env_vars['SIP_TRUNK_PASSWORD'] = config.telephony.sipTrunk.password
            if config.telephony.sipTrunk.outboundCallerId:
                env_vars['OUTBOUND_CALLERID'] = config.telephony.sipTrunk.outboundCallerId
        else:
            # Hardware PSTN
            if config.telephony.hardware.gateway.ip:
                env_vars['GATEWAY_FXO_IP'] = config.telephony.hardware.gateway.ip
                env_vars['GATEWAY_FXO_USER'] = config.telephony.hardware.gateway.user
                if config.telephony.hardware.gateway.password:
                    env_vars['GATEWAY_FXO_PASSWORD'] = config.telephony.hardware.gateway.password

        # Servicios de IA
        env_vars['STT_MODEL'] = config.aiServices.stt.model
        env_vars['STT_DEVICE'] = config.aiServices.stt.device
        env_vars['STT_LANGUAGE'] = config.aiServices.stt.language

        env_vars['TTS_MODEL'] = config.aiServices.tts.model
        env_vars['TTS_DEVICE'] = config.aiServices.tts.device

        env_vars['LM_STUDIO_MODEL'] = config.aiServices.llm.model

        # Escribir .env actualizado
        lines = []
        for key, value in env_vars.items():
            lines.append(f"{key}={value}")

        async with aiofiles.open(ENV_FILE, 'w') as f:
            await f.write('\n'.join(lines))

        logger.info("✅ Archivo .env actualizado")
        return True

    except Exception as e:
        logger.error(f"Error actualizando .env: {e}")
        return False


async def configure_sip_trunk(sip_config: SipTrunkConfig):
    """
    Configura SIP Trunk en Asterisk (genera archivo de configuración)

    Args:
        sip_config: Configuración del SIP Trunk
    """
    try:
        # Leer template
        template_path = Path("/etc/asterisk/custom/pjsip.conf.template")
        if not template_path.exists():
            template_path = Path("./services/asterisk/config/pjsip.conf.template")

        async with aiofiles.open(template_path, 'r') as f:
            template = await f.read()

        # Reemplazar variables
        config_content = template.replace("${SIP_TRUNK_HOST}", sip_config.host)
        config_content = config_content.replace("${SIP_TRUNK_USER}", sip_config.user)
        config_content = config_content.replace("${SIP_TRUNK_PASSWORD}", sip_config.password)

        # Guardar configuración generada
        output_path = Path("/etc/asterisk/pjsip_custom.conf")
        if not output_path.parent.exists():
            output_path = Path("./services/asterisk/config/pjsip_custom.conf")

        async with aiofiles.open(output_path, 'w') as f:
            await f.write(config_content)

        logger.info("✅ Configuración SIP Trunk actualizada")

    except Exception as e:
        logger.error(f"Error configurando SIP Trunk: {e}")


async def configure_pstn_hardware(hardware_config: HardwareConfig):
    """
    Configura hardware PSTN (Gateway/DAHDI) en Asterisk

    Args:
        hardware_config: Configuración del hardware
    """
    try:
        logger.info(f"Configurando hardware PSTN: {hardware_config.type}")

        # Aquí se generarían los archivos de configuración según el hardware
        # Por ahora solo logueamos

        if hardware_config.type == "gateway":
            logger.info(f"Gateway IP: {hardware_config.gateway.ip}")

        elif hardware_config.type == "dahdi":
            logger.info("DAHDI configurado")

        elif hardware_config.type == "both":
            logger.info("Gateway + DAHDI configurados")

    except Exception as e:
        logger.error(f"Error configurando hardware PSTN: {e}")


# ============================================
# INICIALIZACIÓN
# ============================================

def init_config_manager():
    """Inicializa el gestor de configuración"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Config directory: {CONFIG_DIR}")
