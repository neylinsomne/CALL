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
import socket
import logging
from typing import Dict, Any, Optional, List
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
    use_triton: bool = False
    triton_model: str = "small"
    triton_instance_count: int = 2


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


class SecurityConfig(BaseModel):
    enableTLS: bool = True
    enableSRTP: bool = True
    certificateType: str = "self-signed"  # "self-signed" | "letsencrypt" | "custom"
    domain: str = ""
    forceSecure: bool = True


class CallCenterConfig(BaseModel):
    telephony: TelephonyConfig
    aiServices: AIServicesConfig = AIServicesConfig()
    security: SecurityConfig = SecurityConfig()
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

        # Generar certificados SSL si TLS está habilitado
        certs_generated = False
        if config.security.enableTLS:
            try:
                cert_result = await generate_certificates(
                    cert_type=config.security.certificateType,
                    domain=config.security.domain or "asterisk.local"
                )
                certs_generated = cert_result.get("success", False)
                logger.info(f"✅ Certificados generados: {cert_result.get('message')}")
            except Exception as e:
                logger.warning(f"⚠️  Error generando certificados (continuando): {e}")

        return {
            "success": True,
            "config_file": str(CONFIG_FILE),
            "env_updated": env_updated,
            "certificates_generated": certs_generated,
            "message": "Configuración guardada correctamente" + (
                " con certificados SSL generados" if certs_generated else ""
            )
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


@router.post("/api/config/generate-certificates")
async def generate_certificates(
    cert_type: str = "self-signed",
    domain: str = None
):
    """
    Genera certificados SSL para TLS/SRTP

    Args:
        cert_type: "self-signed" | "letsencrypt"
        domain: Dominio (requerido para Let's Encrypt)

    Returns:
        {
            "success": bool,
            "type": str,
            "cert_file": str,
            "key_file": str,
            "message": str
        }
    """
    import subprocess

    try:
        cert_dir = Path("/etc/asterisk/keys")
        cert_dir.mkdir(parents=True, exist_ok=True)

        if cert_type == "self-signed":
            logger.info("Generando certificados autofirmados...")

            # Generar clave privada
            subprocess.run([
                "openssl", "genrsa",
                "-out", str(cert_dir / "asterisk.key"),
                "4096"
            ], check=True, capture_output=True)

            # Generar certificado autofirmado (válido 10 años)
            subprocess.run([
                "openssl", "req", "-new", "-x509",
                "-days", "3650",
                "-key", str(cert_dir / "asterisk.key"),
                "-out", str(cert_dir / "asterisk.crt"),
                "-subj", f"/C=US/ST=State/L=City/O=Call Center AI/CN={domain or 'asterisk.local'}"
            ], check=True, capture_output=True)

            # Generar CA
            subprocess.run([
                "openssl", "genrsa",
                "-out", str(cert_dir / "ca.key"),
                "4096"
            ], check=True, capture_output=True)

            subprocess.run([
                "openssl", "req", "-new", "-x509",
                "-days", "3650",
                "-key", str(cert_dir / "ca.key"),
                "-out", str(cert_dir / "ca.crt"),
                "-subj", f"/C=US/ST=State/L=City/O=Call Center AI CA/CN=CA-{domain or 'asterisk.local'}"
            ], check=True, capture_output=True)

            # Permisos
            os.chmod(cert_dir / "asterisk.key", 0o600)
            os.chmod(cert_dir / "ca.key", 0o600)
            os.chmod(cert_dir / "asterisk.crt", 0o644)
            os.chmod(cert_dir / "ca.crt", 0o644)

            logger.info("✅ Certificados autofirmados generados")

            return {
                "success": True,
                "type": "self-signed",
                "cert_file": str(cert_dir / "asterisk.crt"),
                "key_file": str(cert_dir / "asterisk.key"),
                "ca_file": str(cert_dir / "ca.crt"),
                "message": "Certificados autofirmados generados correctamente (válidos 10 años)"
            }

        elif cert_type == "letsencrypt":
            if not domain:
                raise HTTPException(400, "Domain is required for Let's Encrypt")

            logger.warning("Let's Encrypt requiere configuración manual")

            return {
                "success": False,
                "type": "letsencrypt",
                "message": "Let's Encrypt requiere que el dominio apunte a este servidor y que el puerto 80 esté abierto. Configúralo manualmente con certbot."
            }

        else:
            raise HTTPException(400, f"Invalid certificate type: {cert_type}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Error generando certificados: {e.stderr}")
        raise HTTPException(500, f"Error al ejecutar openssl: {e.stderr.decode() if e.stderr else str(e)}")

    except Exception as e:
        logger.error(f"Error generando certificados: {e}")
        raise HTTPException(500, str(e))


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
        env_vars['USE_TRITON'] = str(config.aiServices.stt.use_triton).lower()
        if config.aiServices.stt.use_triton:
            env_vars['TRITON_STT_MODEL'] = config.aiServices.stt.triton_model

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
# TELEPHONY RECEPTION MODELS
# ============================================

class DIDNumber(BaseModel):
    number: str = ""
    label: str = ""
    active: bool = True


class FXOGatewayConfig(BaseModel):
    ip: str = ""
    sip_port: int = 5060
    user: str = "gateway"
    password: str = ""
    fxo_ports: int = 4
    codec: str = "ulaw"
    dids: List[DIDNumber] = []


class CarrierGradeConfig(BaseModel):
    host: str = ""
    user: str = ""
    password: str = ""
    outbound_caller_id: str = ""
    auth_type: str = "register"
    dids: List[DIDNumber] = []


class TelephonyReceptionConfig(BaseModel):
    method: str = ""  # "fxo_gateway" | "carrier_grade"
    fxo_gateway: Optional[FXOGatewayConfig] = FXOGatewayConfig()
    carrier_grade: Optional[CarrierGradeConfig] = CarrierGradeConfig()


TELEPHONY_CONFIG_FILE = CONFIG_DIR / "telephony_config.json"


# ============================================
# TELEPHONY RECEPTION ENDPOINTS
# ============================================

@router.post("/api/config/telephony/save")
async def save_telephony_config(config: TelephonyReceptionConfig):
    """
    Guarda la configuración de recepción de telefonía.
    Soporta Gateway FXO y Carrier Grade / SIP Trunk.
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        config_dict = config.dict()
        async with aiofiles.open(TELEPHONY_CONFIG_FILE, 'w') as f:
            await f.write(json.dumps(config_dict, indent=2))

        # Actualizar .env con las variables correspondientes
        await _update_telephony_env(config)

        # Generar configuración de Asterisk según el método
        await _apply_telephony_config(config)

        logger.info(f"Configuración de telefonía guardada: {config.method}")

        return {
            "success": True,
            "method": config.method,
            "config_file": str(TELEPHONY_CONFIG_FILE),
            "message": f"Configuración de {config.method} guardada correctamente"
        }

    except Exception as e:
        logger.error(f"Error guardando configuración de telefonía: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/config/telephony")
async def get_telephony_config():
    """
    Obtiene la configuración de recepción de telefonía actual.
    """
    try:
        if TELEPHONY_CONFIG_FILE.exists():
            async with aiofiles.open(TELEPHONY_CONFIG_FILE, 'r') as f:
                content = await f.read()
                return json.loads(content)
        else:
            return TelephonyReceptionConfig().dict()

    except Exception as e:
        logger.error(f"Error leyendo configuración de telefonía: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/telephony/test")
async def test_telephony_connection(config: TelephonyReceptionConfig):
    """
    Prueba la conectividad SIP hacia el gateway o trunk.
    Hace un intento de conexión TCP al puerto SIP del destino.
    """
    try:
        if config.method == "fxo_gateway":
            target_ip = config.fxo_gateway.ip
            target_port = config.fxo_gateway.sip_port
            label = f"Gateway FXO ({target_ip}:{target_port})"
        elif config.method == "carrier_grade":
            target_ip = config.carrier_grade.host
            target_port = 5060
            label = f"Carrier Grade ({target_ip}:{target_port})"
        else:
            raise HTTPException(400, "Método de telefonía no especificado")

        if not target_ip:
            raise HTTPException(400, "IP/Host del destino no configurado")

        # Test de conectividad TCP al puerto SIP
        reachable = False
        error_msg = ""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((target_ip, target_port))
            reachable = result == 0
            if not reachable:
                error_msg = f"No se pudo conectar al puerto {target_port}"
            sock.close()
        except socket.gaierror:
            error_msg = f"No se pudo resolver el host: {target_ip}"
        except socket.timeout:
            error_msg = "Timeout al conectar (5s)"
        except Exception as e:
            error_msg = str(e)

        return {
            "reachable": reachable,
            "target": label,
            "ip": target_ip,
            "port": target_port,
            "error": error_msg if not reachable else None,
            "message": f"Conexión exitosa a {label}" if reachable else f"Fallo: {error_msg}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error probando conectividad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _update_telephony_env(config: TelephonyReceptionConfig) -> bool:
    """Actualiza .env con variables de telefonía de recepción."""
    try:
        env_vars = {}
        if ENV_FILE.exists():
            async with aiofiles.open(ENV_FILE, 'r') as f:
                content = await f.read()
                for line in content.split('\n'):
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

        if config.method == "fxo_gateway" and config.fxo_gateway:
            env_vars['GATEWAY_FXO_IP'] = config.fxo_gateway.ip
            env_vars['GATEWAY_FXO_USER'] = config.fxo_gateway.user
            env_vars['GATEWAY_FXO_PASSWORD'] = config.fxo_gateway.password
            env_vars['GATEWAY_FXO_PORT'] = str(config.fxo_gateway.sip_port)
            env_vars['GATEWAY_FXO_CODEC'] = config.fxo_gateway.codec
            env_vars['GATEWAY_FXO_PORTS'] = str(config.fxo_gateway.fxo_ports)
            env_vars['TELEPHONY_METHOD'] = 'fxo_gateway'

        elif config.method == "carrier_grade" and config.carrier_grade:
            env_vars['SIP_TRUNK_HOST'] = config.carrier_grade.host
            env_vars['SIP_TRUNK_USER'] = config.carrier_grade.user
            env_vars['SIP_TRUNK_PASSWORD'] = config.carrier_grade.password
            if config.carrier_grade.outbound_caller_id:
                env_vars['OUTBOUND_CALLERID'] = config.carrier_grade.outbound_caller_id
            env_vars['SIP_AUTH_TYPE'] = config.carrier_grade.auth_type
            env_vars['TELEPHONY_METHOD'] = 'carrier_grade'

        lines = [f"{key}={value}" for key, value in env_vars.items()]
        async with aiofiles.open(ENV_FILE, 'w') as f:
            await f.write('\n'.join(lines))

        return True
    except Exception as e:
        logger.error(f"Error actualizando .env para telefonía: {e}")
        return False


async def _apply_telephony_config(config: TelephonyReceptionConfig):
    """Aplica la configuración de telefonía a los templates de Asterisk."""
    try:
        template_path = Path("/etc/asterisk/custom/pjsip.conf.template")
        if not template_path.exists():
            template_path = Path("./services/asterisk/config/pjsip.conf.template")

        if not template_path.exists():
            logger.warning("No se encontró template pjsip.conf.template")
            return

        async with aiofiles.open(template_path, 'r') as f:
            template = await f.read()

        if config.method == "fxo_gateway" and config.fxo_gateway:
            gw = config.fxo_gateway
            content = template.replace("${GATEWAY_FXO_IP:-192.168.1.100}", gw.ip)
            content = content.replace("${GATEWAY_FXO_IP}", gw.ip)
            content = content.replace("${GATEWAY_FXO_USER:-gateway}", gw.user)
            content = content.replace("${GATEWAY_FXO_USER}", gw.user)
            content = content.replace("${GATEWAY_FXO_PASSWORD:-gateway123}", gw.password)
            content = content.replace("${GATEWAY_FXO_PASSWORD}", gw.password)

        elif config.method == "carrier_grade" and config.carrier_grade:
            cg = config.carrier_grade
            content = template.replace("${SIP_TRUNK_HOST}", cg.host)
            content = content.replace("${SIP_TRUNK_USER}", cg.user)
            content = content.replace("${SIP_TRUNK_PASSWORD}", cg.password)

        else:
            return

        output_path = Path("/etc/asterisk/pjsip_custom.conf")
        if not output_path.parent.exists():
            output_path = Path("./services/asterisk/config/pjsip_custom.conf")

        async with aiofiles.open(output_path, 'w') as f:
            await f.write(content)

        logger.info(f"Configuración de Asterisk aplicada para {config.method}")

    except Exception as e:
        logger.error(f"Error aplicando configuración de telefonía: {e}")


# ============================================
# CLIENT PROVISIONING MODELS
# ============================================

class ClientCompany(BaseModel):
    name: str
    contactName: str = ""
    contactEmail: str = ""
    contactPhone: str = ""
    notes: str = ""


class AgentExtension(BaseModel):
    extension: str
    name: str
    password: str
    enabled: bool = True


class ClientAgents(BaseModel):
    count: int
    extensionPrefix: str = "10"
    generatePasswords: bool = True
    extensions: List[AgentExtension] = []


class ClientDDNS(BaseModel):
    enabled: bool = False
    provider: str = "duckdns"
    domain: str = ""
    token: str = ""


class ClientSipTrunk(BaseModel):
    host: str = ""
    user: str = ""
    password: str = ""
    outboundCallerId: str = ""


class ClientGateway(BaseModel):
    ip: str = ""
    user: str = "gateway"
    password: str = ""
    fxoPorts: int = 4


class ClientNetwork(BaseModel):
    connectionType: str = "sip_trunk"  # "sip_trunk" | "gateway_fxo"
    externalIp: str = ""
    autoDetectIp: bool = True
    localNetwork: str = "192.168.1.0/24"
    rtpPortStart: int = 10000
    rtpPortEnd: int = 20000
    sipProviderWhitelist: str = ""
    ddns: ClientDDNS = ClientDDNS()
    sipTrunk: ClientSipTrunk = ClientSipTrunk()
    gateway: ClientGateway = ClientGateway()


class ClientProvisionRequest(BaseModel):
    company: ClientCompany
    agents: ClientAgents
    network: ClientNetwork


CLIENTS_DIR = CONFIG_DIR / "clients"


# ============================================
# CLIENT PROVISIONING ENDPOINTS
# ============================================

@router.post("/api/clients/provision")
async def provision_client(request: ClientProvisionRequest):
    """
    Provisiona un nuevo cliente con extensiones y configuración de red.

    Genera:
    - Archivo de configuración del cliente (JSON)
    - Archivo .env específico para el cliente
    - Configuración PJSIP para las extensiones

    Returns:
        {
            "success": bool,
            "client_id": str,
            "config_file": str,
            "extensions_count": int,
            "message": str
        }
    """
    try:
        import hashlib
        from datetime import datetime

        # Crear directorio de clientes
        CLIENTS_DIR.mkdir(parents=True, exist_ok=True)

        # Generar ID único para el cliente
        client_id = hashlib.md5(
            f"{request.company.name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        client_dir = CLIENTS_DIR / client_id
        client_dir.mkdir(parents=True, exist_ok=True)

        # Guardar configuración del cliente como JSON
        config_dict = request.dict()
        config_dict["client_id"] = client_id
        config_dict["created_at"] = datetime.now().isoformat()

        config_file = client_dir / "config.json"
        async with aiofiles.open(config_file, 'w') as f:
            await f.write(json.dumps(config_dict, indent=2, ensure_ascii=False))

        # Generar archivo .env específico para el cliente
        env_content = _generate_client_env(request, client_id)
        env_file = client_dir / ".env"
        async with aiofiles.open(env_file, 'w') as f:
            await f.write(env_content)

        # Generar configuración PJSIP para las extensiones
        pjsip_content = _generate_client_pjsip(request)
        pjsip_file = client_dir / "pjsip_extensions.conf"
        async with aiofiles.open(pjsip_file, 'w') as f:
            await f.write(pjsip_content)

        logger.info(f"✅ Cliente provisionado: {request.company.name} (ID: {client_id})")

        return {
            "success": True,
            "client_id": client_id,
            "config_file": str(config_file),
            "env_file": str(env_file),
            "pjsip_file": str(pjsip_file),
            "extensions_count": len(request.agents.extensions),
            "message": f"Cliente '{request.company.name}' provisionado exitosamente con {len(request.agents.extensions)} extensiones"
        }

    except Exception as e:
        logger.error(f"Error provisionando cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/clients")
async def list_clients():
    """
    Lista todos los clientes provisionados.
    """
    try:
        clients = []

        if not CLIENTS_DIR.exists():
            return {"clients": []}

        for client_dir in CLIENTS_DIR.iterdir():
            if client_dir.is_dir():
                config_file = client_dir / "config.json"
                if config_file.exists():
                    async with aiofiles.open(config_file, 'r') as f:
                        content = await f.read()
                        config = json.loads(content)
                        clients.append({
                            "client_id": config.get("client_id"),
                            "company_name": config.get("company", {}).get("name"),
                            "extensions_count": len(config.get("agents", {}).get("extensions", [])),
                            "connection_type": config.get("network", {}).get("connectionType"),
                            "created_at": config.get("created_at")
                        })

        return {"clients": clients}

    except Exception as e:
        logger.error(f"Error listando clientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/clients/{client_id}")
async def get_client(client_id: str):
    """
    Obtiene la configuración completa de un cliente.
    """
    try:
        config_file = CLIENTS_DIR / client_id / "config.json"

        if not config_file.exists():
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        async with aiofiles.open(config_file, 'r') as f:
            content = await f.read()
            return json.loads(content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo cliente {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/clients/{client_id}/download")
async def download_client_config(client_id: str):
    """
    Descarga el archivo .env del cliente.
    """
    try:
        env_file = CLIENTS_DIR / client_id / ".env"

        if not env_file.exists():
            raise HTTPException(status_code=404, detail="Archivo de configuración no encontrado")

        async with aiofiles.open(env_file, 'r') as f:
            content = await f.read()

        return {
            "client_id": client_id,
            "filename": f"{client_id}.env",
            "content": content
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error descargando config de {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_client_env(request: ClientProvisionRequest, client_id: str) -> str:
    """Genera contenido del archivo .env para un cliente."""
    lines = [
        f"# Configuración para: {request.company.name}",
        f"# Client ID: {client_id}",
        f"# Generado: {__import__('datetime').datetime.now().isoformat()}",
        "",
        "# ================================",
        "# DATOS DEL CLIENTE",
        "# ================================",
        f'COMPANY_NAME="{request.company.name}"',
        f'CONTACT_NAME="{request.company.contactName}"',
        f'CONTACT_EMAIL="{request.company.contactEmail}"',
        "",
        "# ================================",
        "# CONFIGURACIÓN DE RED / NAT",
        "# ================================",
        f"EXTERNAL_IP={request.network.externalIp or '# Auto-detectar'}",
        f"LOCAL_NETWORK={request.network.localNetwork}",
        f"RTP_PORT_START={request.network.rtpPortStart}",
        f"RTP_PORT_END={request.network.rtpPortEnd}",
    ]

    if request.network.sipProviderWhitelist:
        lines.append(f"SIP_PROVIDER_WHITELIST={request.network.sipProviderWhitelist}")

    if request.network.ddns.enabled:
        lines.extend([
            "",
            "# DDNS",
            "DDNS_ENABLED=true",
            f"DDNS_PROVIDER={request.network.ddns.provider}",
            f"DDNS_DOMAIN={request.network.ddns.domain}",
            f"DDNS_TOKEN={request.network.ddns.token}",
        ])

    lines.append("")

    if request.network.connectionType == "sip_trunk":
        lines.extend([
            "# ================================",
            "# SIP TRUNK",
            "# ================================",
            f"SIP_TRUNK_HOST={request.network.sipTrunk.host}",
            f"SIP_TRUNK_USER={request.network.sipTrunk.user}",
            f"SIP_TRUNK_PASSWORD={request.network.sipTrunk.password}",
            f"OUTBOUND_CALLERID={request.network.sipTrunk.outboundCallerId}",
        ])
    else:
        lines.extend([
            "# ================================",
            "# GATEWAY FXO",
            "# ================================",
            f"GATEWAY_FXO_IP={request.network.gateway.ip}",
            f"GATEWAY_FXO_USER={request.network.gateway.user}",
            f"GATEWAY_FXO_PASSWORD={request.network.gateway.password}",
            f"GATEWAY_FXO_PORTS={request.network.gateway.fxoPorts}",
        ])

    lines.extend([
        "",
        "# ================================",
        "# EXTENSIONES / AGENTES",
        "# ================================",
    ])

    for i, ext in enumerate(request.agents.extensions):
        lines.extend([
            f"# Agente {i + 1}",
            f"AGENT_{i + 1}_EXT={ext.extension}",
            f'AGENT_{i + 1}_NAME="{ext.name}"',
            f"AGENT_{i + 1}_PASS={ext.password}",
            "",
        ])

    return "\n".join(lines)


def _generate_client_pjsip(request: ClientProvisionRequest) -> str:
    """Genera configuración PJSIP para las extensiones del cliente."""
    lines = [
        f"; PJSIP Extensions para: {request.company.name}",
        f"; Generado automáticamente",
        "",
    ]

    for ext in request.agents.extensions:
        lines.extend([
            f"; --- {ext.name} ---",
            f"[{ext.extension}]",
            "type=endpoint",
            "context=call-center",
            "disallow=all",
            "allow=ulaw",
            "allow=alaw",
            "allow=opus",
            f"auth={ext.extension}",
            f"aors={ext.extension}",
            "direct_media=no",
            "force_rport=yes",
            "rewrite_contact=yes",
            "rtp_symmetric=yes",
            f'callerid="{ext.name}" <{ext.extension}>',
            "",
            f"[{ext.extension}]",
            "type=auth",
            "auth_type=userpass",
            f"username={ext.extension}",
            f"password={ext.password}",
            "",
            f"[{ext.extension}]",
            "type=aor",
            "max_contacts=3",
            "remove_existing=yes",
            "",
        ])

    return "\n".join(lines)


# ============================================
# INICIALIZACIÓN
# ============================================

def init_config_manager():
    """Inicializa el gestor de configuración"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CLIENTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Config directory: {CONFIG_DIR}")
    logger.info(f"Clients directory: {CLIENTS_DIR}")
