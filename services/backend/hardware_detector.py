"""
Hardware Detector para Telefonía
=================================

Detecta automáticamente qué hardware de telefonía está disponible:
- Gateway FXO/FXS (Grandstream, Cisco, etc.)
- Tarjetas DAHDI (Sangoma, Digium)

Y configura el pipeline de llamadas en consecuencia.

Uso:
    from hardware_detector import HardwareDetector

    detector = HardwareDetector()
    hardware_type = await detector.detect_hardware()
    config = detector.get_pipeline_config()
"""

import os
import subprocess
import logging
from typing import Literal, Optional, List, Dict
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

HardwareType = Literal["gateway", "dahdi", "both", "sip_only"]


class HardwareDetector:
    """Detecta automáticamente hardware de telefonía PSTN"""

    def __init__(self):
        self.hardware_type: HardwareType = "sip_only"
        self.gateway_endpoints: List[Dict] = []
        self.dahdi_channels: List[tuple] = []
        self.gateway_count = 0
        self.dahdi_count = 0

    async def detect_hardware(self) -> HardwareType:
        """
        Detecta qué hardware está disponible

        Returns:
            "gateway": Solo Gateway FXO/FXS detectado
            "dahdi": Solo tarjetas DAHDI detectadas
            "both": Ambos tipos de hardware
            "sip_only": Solo SIP trunk (sin PSTN)
        """
        logger.info("🔍 Iniciando detección de hardware...")

        # Ejecutar detección en paralelo
        results = await asyncio.gather(
            self._detect_gateway(),
            self._detect_dahdi(),
            return_exceptions=True
        )

        has_gateway = results[0] if isinstance(results[0], bool) else False
        has_dahdi = results[1] if isinstance(results[1], bool) else False

        # Determinar tipo de hardware
        if has_gateway and has_dahdi:
            self.hardware_type = "both"
            logger.info("✅ Hardware detectado: Gateway + DAHDI")
        elif has_gateway:
            self.hardware_type = "gateway"
            logger.info("✅ Hardware detectado: Gateway FXO/FXS")
        elif has_dahdi:
            self.hardware_type = "dahdi"
            logger.info("✅ Hardware detectado: DAHDI")
        else:
            self.hardware_type = "sip_only"
            logger.info("ℹ️  Solo SIP Trunk detectado (sin hardware PSTN)")

        return self.hardware_type

    async def _detect_gateway(self) -> bool:
        """
        Detecta Gateway FXO/FXS

        Método 1: Consultar endpoints PJSIP via ARI
        Método 2: Ping al Gateway IP (fallback)
        Método 3: Verificar registro SIP

        Returns:
            True si se detectó gateway, False en caso contrario
        """
        try:
            logger.debug("Detectando Gateway FXO/FXS...")

            # Configuración
            asterisk_host = os.getenv("ASTERISK_HOST", "asterisk")
            ari_user = os.getenv("ARI_USER", "callcenter-ai")
            ari_password = os.getenv("ARI_PASSWORD", "ari123")

            # Método 1: Consultar ARI endpoints
            try:
                url = f"http://{asterisk_host}:8088/ari/endpoints"
                auth = aiohttp.BasicAuth(ari_user, ari_password)

                async with aiohttp.ClientSession(auth=auth) as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            endpoints = await resp.json()

                            # Buscar endpoints de gateway
                            gateway_eps = [
                                ep for ep in endpoints
                                if "gateway" in ep.get("resource", "").lower()
                                or "fxo" in ep.get("resource", "").lower()
                            ]

                            if gateway_eps:
                                self.gateway_endpoints = gateway_eps
                                self.gateway_count = len(gateway_eps)
                                logger.info(f"✅ Gateway detectado vía ARI: {self.gateway_count} endpoints")
                                return True

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.debug(f"ARI no disponible: {e}, probando método alternativo...")

            # Método 2: Ping al Gateway IP
            gateway_ip = os.getenv("GATEWAY_FXO_IP", "192.168.1.100")

            if gateway_ip and gateway_ip != "192.168.1.100":  # Solo si está configurado
                try:
                    # Ping (funciona en Linux/Mac, en Windows usa -n en vez de -c)
                    ping_cmd = ["ping", "-c", "1", "-W", "1", gateway_ip]
                    if os.name == "nt":  # Windows
                        ping_cmd = ["ping", "-n", "1", "-w", "1000", gateway_ip]

                    result = subprocess.run(
                        ping_cmd,
                        capture_output=True,
                        timeout=2
                    )

                    if result.returncode == 0:
                        self.gateway_count = 4  # Asumimos 4 puertos por defecto
                        logger.info(f"✅ Gateway detectado vía ping: {gateway_ip}")
                        return True

                except (subprocess.SubprocessError, FileNotFoundError) as e:
                    logger.debug(f"Ping falló: {e}")

            # Método 3: Verificar variable de entorno
            if os.getenv("GATEWAY_FXO_USER"):
                self.gateway_count = 4
                logger.info("✅ Gateway configurado en .env")
                return True

        except Exception as e:
            logger.warning(f"Error detectando gateway: {e}")

        logger.debug("❌ No se detectó Gateway")
        return False

    async def _detect_dahdi(self) -> bool:
        """
        Detecta tarjetas DAHDI

        Método 1: Verificar dispositivo /dev/dahdi
        Método 2: Ejecutar dahdi_scan (si disponible)
        Método 3: Consultar Asterisk CLI

        Returns:
            True si se detectó DAHDI, False en caso contrario
        """
        try:
            logger.debug("Detectando tarjetas DAHDI...")

            # Método 1: Verificar dispositivo /dev/dahdi
            if os.path.exists("/dev/dahdi"):
                logger.debug("✅ Dispositivo /dev/dahdi encontrado")

                # Método 2: Ejecutar dahdi_scan para detalles
                try:
                    result = subprocess.run(
                        ["dahdi_scan"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        output = result.stdout

                        # Parsear canales
                        # Ejemplo output:
                        # [1] FXS Kewlstart (Default) (SWEC: MG2)
                        # [2] FXO Kewlstart (Default) (SWEC: MG2)

                        import re
                        channels = re.findall(r'\[(\d+)\]\s+(\w+)', output)

                        if channels:
                            self.dahdi_channels = channels
                            self.dahdi_count = len(channels)
                            logger.info(f"✅ DAHDI detectado vía dahdi_scan: {self.dahdi_count} canales")
                            return True

                except FileNotFoundError:
                    logger.debug("dahdi_scan no disponible")

                # Método 2b: Leer /proc/dahdi
                try:
                    with open("/proc/dahdi/1", "r") as f:
                        # Si podemos leer, DAHDI está activo
                        self.dahdi_count = 4  # Asumimos 4 por defecto
                        logger.info("✅ DAHDI detectado vía /proc")
                        return True
                except FileNotFoundError:
                    pass

                # Si existe /dev/dahdi pero no podemos leer detalles
                self.dahdi_count = 4
                logger.info("✅ DAHDI detectado vía /dev/dahdi")
                return True

            # Método 3: Preguntar a Asterisk vía AMI o CLI (dentro de Docker)
            # Solo si estamos dentro del contenedor de Asterisk
            try:
                result = subprocess.run(
                    ["asterisk", "-rx", "dahdi show channels"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                if result.returncode == 0 and "Chan" in result.stdout:
                    # Parsear output
                    lines = result.stdout.split("\n")
                    channel_lines = [l for l in lines if l.strip() and not l.startswith("Chan")]

                    if channel_lines:
                        self.dahdi_count = len(channel_lines)
                        logger.info(f"✅ DAHDI detectado vía Asterisk CLI: {self.dahdi_count} canales")
                        return True

            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        except Exception as e:
            logger.warning(f"Error detectando DAHDI: {e}")

        logger.debug("❌ No se detectó DAHDI")
        return False

    def get_available_channels(self, hardware_type: Optional[HardwareType] = None) -> int:
        """
        Retorna el número de canales PSTN disponibles

        Args:
            hardware_type: Si None, usa self.hardware_type

        Returns:
            Número de canales disponibles
        """
        hw_type = hardware_type or self.hardware_type

        if hw_type == "gateway":
            return self.gateway_count

        elif hw_type == "dahdi":
            return self.dahdi_count

        elif hw_type == "both":
            return self.gateway_count + self.dahdi_count

        else:  # sip_only
            return 0

    def get_pipeline_config(self) -> dict:
        """
        Retorna configuración del pipeline según hardware detectado

        Returns:
            dict con configuración recomendada:
            - hardware_type: Tipo de hardware detectado
            - pstn_channels: Canales PSTN disponibles
            - max_concurrent_calls: Máximo de llamadas simultáneas (estimado)
            - route_preference: Orden de preferencia para llamadas salientes
            - codecs: Codecs recomendados
            - use_transcoding: Si se requiere transcoding
            - contexts: Contextos de Asterisk para cada tipo
        """
        config = {
            "hardware_type": self.hardware_type,
            "pstn_channels": self.get_available_channels(),
            "max_concurrent_calls": 0,
            "route_preference": [],
            "codecs": ["ulaw", "alaw"],
            "use_transcoding": False,
            "contexts": {}
        }

        # Configuración por tipo de hardware
        if self.hardware_type == "gateway":
            config.update({
                "max_concurrent_calls": self.gateway_count,
                "route_preference": ["gateway", "sip_trunk"],
                "codecs": ["ulaw", "alaw"],  # Gateways prefieren ulaw
                "use_transcoding": False,
                "contexts": {
                    "inbound": "from-pstn-gateway",
                    "outbound": "8"  # Prefijo 8 para Gateway
                }
            })

        elif self.hardware_type == "dahdi":
            config.update({
                "max_concurrent_calls": self.dahdi_count,
                "route_preference": ["dahdi", "sip_trunk"],
                "codecs": ["ulaw", "alaw", "g722"],
                "use_transcoding": False,
                "contexts": {
                    "inbound": "from-pstn-dahdi",
                    "outbound": "7"  # Prefijo 7 para DAHDI
                }
            })

        elif self.hardware_type == "both":
            config.update({
                "max_concurrent_calls": self.gateway_count + self.dahdi_count,
                "route_preference": ["dahdi", "gateway", "sip_trunk"],
                "codecs": ["ulaw", "alaw", "g722"],
                "use_transcoding": False,
                "contexts": {
                    "inbound": ["from-pstn-dahdi", "from-pstn-gateway"],
                    "outbound": {
                        "dahdi": "7",
                        "gateway": "8",
                        "smart": "6"  # Smart routing
                    }
                }
            })

        else:  # sip_only
            config.update({
                "max_concurrent_calls": 100,  # Limitado por CPU/GPU, no por líneas
                "route_preference": ["sip_trunk"],
                "codecs": ["opus", "ulaw", "alaw"],  # Opus para mejor calidad
                "use_transcoding": True,  # Puede variar según provider
                "contexts": {
                    "inbound": "from-trunk",
                    "outbound": "9"  # Prefijo 9 para SIP
                }
            })

        return config

    def get_hardware_summary(self) -> str:
        """
        Retorna un resumen legible del hardware detectado

        Returns:
            String con resumen del hardware
        """
        lines = ["=" * 60, "HARDWARE DE TELEFONÍA DETECTADO", "=" * 60]

        if self.hardware_type == "sip_only":
            lines.append("🌐 Tipo: Solo SIP Trunk (sin hardware PSTN)")
            lines.append("📞 Canales PSTN: 0")
            lines.append("💡 Todas las llamadas irán por SIP trunk")

        else:
            lines.append(f"📡 Tipo: {self.hardware_type.upper()}")

            if self.gateway_count > 0:
                lines.append(f"📞 Gateway FXO/FXS: {self.gateway_count} canales")

            if self.dahdi_count > 0:
                lines.append(f"🎛️  DAHDI (Tarjeta PCIe): {self.dahdi_count} canales")

            lines.append(f"📊 Total canales PSTN: {self.get_available_channels()}")

        config = self.get_pipeline_config()
        lines.append(f"⚡ Llamadas simultáneas estimadas: {config['max_concurrent_calls']}")
        lines.append(f"🎯 Preferencia de rutas: {' → '.join(config['route_preference'])}")
        lines.append(f"🎵 Codecs: {', '.join(config['codecs'])}")

        lines.append("=" * 60)

        return "\n".join(lines)

    async def validate_configuration(self) -> Dict[str, bool]:
        """
        Valida que la configuración de Asterisk coincida con el hardware detectado

        Returns:
            Dict con resultados de validación:
            - pjsip_configured: Endpoints de Gateway configurados en pjsip.conf
            - dahdi_configured: DAHDI configurado en chan_dahdi.conf
            - extensions_configured: Contextos configurados en extensions.conf
        """
        results = {
            "pjsip_configured": False,
            "dahdi_configured": False,
            "extensions_configured": False
        }

        # TODO: Implementar validación leyendo archivos de config
        # Por ahora solo retornamos el estado

        return results


# ============================================
# EJEMPLO DE USO
# ============================================

async def main():
    """Ejemplo de uso del detector"""

    detector = HardwareDetector()

    # Detectar hardware
    hardware_type = await detector.detect_hardware()

    # Mostrar resumen
    print(detector.get_hardware_summary())

    # Obtener configuración
    config = detector.get_pipeline_config()

    print("\n📋 CONFIGURACIÓN RECOMENDADA:")
    import json
    print(json.dumps(config, indent=2))

    # Validar
    validation = await detector.validate_configuration()
    print("\n✅ VALIDACIÓN:")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(main())
