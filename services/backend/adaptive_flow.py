"""
Adaptive Call Flow
==================

Sistema que adapta el flujo de llamadas según la configuración:
- Si usa SIP Trunk → Flujo por internet
- Si usa Gateway/DAHDI → Flujo PSTN
- Servicios de IA según configuración (STT, TTS, LLM)

El flujo se ajusta automáticamente según el hardware detectado.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Literal
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

FlowType = Literal["sip_trunk", "gateway", "dahdi", "hybrid"]


class AdaptiveCallFlow:
    """Gestiona el flujo de llamadas según configuración"""

    def __init__(self):
        self.config: Optional[Dict[str, Any]] = None
        self.flow_type: FlowType = "sip_trunk"  # Default
        self.services_enabled = {
            "stt": True,
            "tts": True,
            "llm": True
        }

        # URLs de servicios
        self.service_urls = {
            "stt": os.getenv("STT_URL", "http://stt:8002"),
            "tts": os.getenv("TTS_URL", "http://tts:8001"),
            "llm": os.getenv("LLM_URL", "http://llm:8003"),
            "audio_preprocess": os.getenv("AUDIO_PREPROCESS_URL", "http://audio_preprocess:8004")
        }

    async def load_config(self, config_path: Path = None):
        """
        Carga configuración guardada

        Args:
            config_path: Ruta al archivo de configuración (opcional)
        """
        if config_path is None:
            config_path = Path("/app/config/callcenter_config.json")
            if not config_path.exists():
                config_path = Path("./config/callcenter_config.json")

        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = json.load(f)

                # Determinar tipo de flujo
                self._determine_flow_type()

                # Configurar servicios habilitados
                self._configure_services()

                logger.info(f"✅ Configuración cargada: {self.flow_type}")
            else:
                logger.warning("⚠️  No se encontró configuración, usando valores por defecto")
                self._use_defaults()

        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            self._use_defaults()

    def _determine_flow_type(self):
        """Determina el tipo de flujo según configuración"""
        if not self.config:
            self.flow_type = "sip_trunk"
            return

        telephony = self.config.get("telephony", {})

        if telephony.get("useSipTrunk"):
            self.flow_type = "sip_trunk"

        else:
            hardware_type = telephony.get("hardware", {}).get("type", "sip_only")

            if hardware_type == "gateway":
                self.flow_type = "gateway"
            elif hardware_type == "dahdi":
                self.flow_type = "dahdi"
            elif hardware_type == "both":
                self.flow_type = "hybrid"
            else:
                self.flow_type = "sip_trunk"

    def _configure_services(self):
        """Configura qué servicios están habilitados"""
        if not self.config:
            return

        ai_services = self.config.get("aiServices", {})

        self.services_enabled = {
            "stt": ai_services.get("stt", {}).get("enabled", True),
            "tts": ai_services.get("tts", {}).get("enabled", True),
            "llm": ai_services.get("llm", {}).get("enabled", True)
        }

    def _use_defaults(self):
        """Usa configuración por defecto"""
        self.flow_type = "sip_trunk"
        self.services_enabled = {
            "stt": True,
            "tts": True,
            "llm": True
        }

    # ============================================
    # FLUJO DE LLAMADA
    # ============================================

    async def process_incoming_call(
        self,
        audio_chunk: bytes,
        conversation_id: str,
        caller_id: str,
        source: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Procesa una llamada entrante según el flujo configurado

        Args:
            audio_chunk: Chunk de audio (PCM 16-bit, 16kHz)
            conversation_id: ID de conversación
            caller_id: Número del llamante
            source: Fuente de la llamada (sip_trunk, gateway, dahdi)

        Returns:
            {
                "text": str,  # Texto del usuario
                "response": str,  # Respuesta del AI
                "audio": bytes,  # Audio de respuesta
                "metadata": dict
            }
        """
        result = {
            "text": "",
            "response": "",
            "audio": b"",
            "metadata": {
                "flow_type": self.flow_type,
                "source": source,
                "services_used": []
            }
        }

        try:
            # Paso 1: Preprocesamiento de audio (si está habilitado)
            if os.getenv("ENABLE_DENOISE", "true").lower() == "true":
                audio_chunk = await self._preprocess_audio(audio_chunk)
                result["metadata"]["services_used"].append("audio_preprocess")

            # Paso 2: Speech-to-Text
            if self.services_enabled["stt"]:
                text = await self._transcribe(audio_chunk)
                result["text"] = text
                result["metadata"]["services_used"].append("stt")
            else:
                logger.warning("STT deshabilitado, no se puede transcribir")
                return result

            # Paso 3: LLM (generar respuesta)
            if self.services_enabled["llm"]:
                response = await self._generate_response(text, conversation_id)
                result["response"] = response
                result["metadata"]["services_used"].append("llm")
            else:
                # Respuesta por defecto si LLM está deshabilitado
                result["response"] = "Lo siento, el servicio de inteligencia artificial no está disponible en este momento."

            # Paso 4: Text-to-Speech
            if self.services_enabled["tts"]:
                audio = await self._synthesize(result["response"])
                result["audio"] = audio
                result["metadata"]["services_used"].append("tts")
            else:
                logger.warning("TTS deshabilitado, no se puede sintetizar audio")

            return result

        except Exception as e:
            logger.error(f"Error procesando llamada: {e}")
            result["metadata"]["error"] = str(e)
            return result

    async def _preprocess_audio(self, audio: bytes) -> bytes:
        """Preprocesa audio (eliminación de ruido, etc.)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.service_urls['audio_preprocess']}/denoise",
                    content=audio,
                    headers={"Content-Type": "audio/raw"}
                )

                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"Audio preprocessing falló: {response.status_code}")
                    return audio  # Retornar original

        except Exception as e:
            logger.error(f"Error en preprocessing: {e}")
            return audio  # Retornar original si falla

    async def _transcribe(self, audio: bytes) -> str:
        """Transcribe audio a texto usando STT"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.service_urls['stt']}/transcribe",
                    content=audio,
                    headers={"Content-Type": "audio/raw"}
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("text", "")
                else:
                    logger.error(f"STT error: {response.status_code}")
                    return ""

        except Exception as e:
            logger.error(f"Error en transcripción: {e}")
            return ""

    async def _generate_response(self, text: str, conversation_id: str) -> str:
        """Genera respuesta usando LLM"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.service_urls['llm']}/generate",
                    json={
                        "text": text,
                        "conversation_id": conversation_id
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    logger.error(f"LLM error: {response.status_code}")
                    return "Disculpa, no pude procesar tu solicitud."

        except Exception as e:
            logger.error(f"Error en LLM: {e}")
            return "Disculpa, hubo un error procesando tu solicitud."

    async def _synthesize(self, text: str) -> bytes:
        """Sintetiza texto a audio usando TTS"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.service_urls['tts']}/synthesize",
                    json={"text": text}
                )

                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"TTS error: {response.status_code}")
                    return b""

        except Exception as e:
            logger.error(f"Error en síntesis: {e}")
            return b""

    # ============================================
    # INFORMACIÓN DE CONFIGURACIÓN
    # ============================================

    def get_flow_info(self) -> Dict[str, Any]:
        """
        Retorna información del flujo actual

        Returns:
            {
                "flow_type": str,
                "services_enabled": dict,
                "source_preference": list,
                "hardware_info": dict
            }
        """
        info = {
            "flow_type": self.flow_type,
            "services_enabled": self.services_enabled,
            "service_urls": self.service_urls
        }

        if self.config:
            telephony = self.config.get("telephony", {})

            if telephony.get("useSipTrunk"):
                info["source_preference"] = ["sip_trunk"]
                info["sip_trunk_host"] = telephony.get("sipTrunk", {}).get("host", "")

            else:
                hardware = telephony.get("hardware", {})
                info["hardware_type"] = hardware.get("type", "unknown")
                info["pstn_channels"] = hardware.get("pstnChannels", 0)

                # Preferencia de rutas
                if hardware.get("type") == "both":
                    info["source_preference"] = ["dahdi", "gateway", "sip_trunk"]
                elif hardware.get("type") == "gateway":
                    info["source_preference"] = ["gateway", "sip_trunk"]
                elif hardware.get("type") == "dahdi":
                    info["source_preference"] = ["dahdi", "sip_trunk"]
                else:
                    info["source_preference"] = ["sip_trunk"]

        return info

    def get_asterisk_context(self, source: str = None) -> str:
        """
        Retorna el contexto de Asterisk apropiado según la fuente

        Args:
            source: Fuente de la llamada (gateway, dahdi, sip_trunk)

        Returns:
            Nombre del contexto de Asterisk
        """
        if source == "gateway":
            return "from-pstn-gateway"
        elif source == "dahdi":
            return "from-pstn-dahdi"
        else:  # sip_trunk o unknown
            return "from-trunk"

    def get_outbound_prefix(self, route: str = "preferred") -> str:
        """
        Retorna el prefijo para llamadas salientes

        Args:
            route: "preferred", "gateway", "dahdi", "sip_trunk"

        Returns:
            Prefijo a marcar (ej: "9" para SIP trunk)
        """
        if route == "preferred":
            # Usar la ruta preferida según configuración
            if self.flow_type == "sip_trunk":
                return "9"
            elif self.flow_type == "gateway":
                return "8"
            elif self.flow_type == "dahdi":
                return "7"
            else:  # hybrid
                return "6"  # Smart routing

        elif route == "sip_trunk":
            return "9"
        elif route == "gateway":
            return "8"
        elif route == "dahdi":
            return "7"
        else:
            return "9"  # Default


# ============================================
# INSTANCIA GLOBAL
# ============================================

# Singleton para usar en toda la aplicación
adaptive_flow = AdaptiveCallFlow()


# ============================================
# FUNCIONES DE AYUDA
# ============================================

async def initialize_adaptive_flow():
    """Inicializa el flujo adaptativo cargando configuración"""
    await adaptive_flow.load_config()
    logger.info(f"🔄 Flujo adaptativo inicializado: {adaptive_flow.flow_type}")
    return adaptive_flow


def get_current_flow() -> AdaptiveCallFlow:
    """Obtiene la instancia actual del flujo adaptativo"""
    return adaptive_flow
