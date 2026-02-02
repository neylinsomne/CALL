"""
License Validator - Cliente On-Premise
======================================

Valida licencias con el servidor central.
Implementa hardware binding, validación offline con grace period,
y telemetría de uso.
"""

import os
import uuid
import hashlib
import platform
import subprocess
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class LicenseValidator:
    """
    Validador de licencias para instalaciones on-premise.

    Features:
    - Hardware binding (MAC + CPU + Motherboard)
    - Validación online con servidor central
    - Grace period de 24 horas para operación offline
    - Heartbeat automático cada 5 minutos
    - Límites de llamadas concurrentes
    """

    def __init__(
        self,
        license_key: Optional[str] = None,
        license_server_url: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        self.license_key = license_key or os.getenv("LICENSE_KEY")
        self.license_server_url = license_server_url or os.getenv(
            "LICENSE_SERVER_URL",
            "https://license.callcenter-ai.com"
        )

        self.cache_dir = Path(cache_dir or os.getenv("LICENSE_CACHE_DIR", "/var/lib/callcenter/license"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.cache_dir / "license_cache.json"
        self.hardware_id = self.get_hardware_id()

        self.license_info: Optional[Dict] = None
        self.last_validation: Optional[datetime] = None
        self.validation_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        # State
        self._is_valid = False
        self._active_calls = 0
        self._active_agents = 0

    def get_hardware_id(self) -> str:
        """
        Genera un ID único basado en hardware del servidor.

        Combina:
        - MAC address de la interfaz principal
        - CPU ID
        - Motherboard serial (si disponible)

        Returns:
            SHA-256 hash del hardware identificado
        """
        identifiers = []

        try:
            # MAC Address
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                          for elements in range(0, 2*6, 2)][::-1])
            identifiers.append(f"MAC:{mac}")

            # CPU Info
            if platform.system() == "Linux":
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        cpuinfo = f.read()
                        for line in cpuinfo.split("\n"):
                            if "Serial" in line or "processor" in line:
                                identifiers.append(line.strip())
                                break
                except Exception:
                    pass

            # Motherboard serial (Linux)
            if platform.system() == "Linux":
                try:
                    result = subprocess.run(
                        ["cat", "/sys/class/dmi/id/board_serial"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        identifiers.append(f"BOARD:{result.stdout.strip()}")
                except Exception:
                    pass

            # Motherboard serial (Windows)
            elif platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["wmic", "baseboard", "get", "serialnumber"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        serial = result.stdout.split("\n")[1].strip()
                        identifiers.append(f"BOARD:{serial}")
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Error getting hardware info: {e}")

        # Fallback - al menos MAC
        if not identifiers:
            identifiers.append(f"MAC:{uuid.getnode()}")

        # Generar hash
        combined = "|".join(identifiers)
        hardware_id = hashlib.sha256(combined.encode()).hexdigest()

        logger.info(f"Hardware ID generated: {hardware_id[:16]}...")
        return hardware_id

    def load_cache(self) -> Optional[Dict]:
        """
        Carga información de licencia desde cache local.

        Returns:
            Información de licencia cacheada o None
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r") as f:
                    cache = json.load(f)
                    return cache
        except Exception as e:
            logger.error(f"Error loading license cache: {e}")
        return None

    def save_cache(self, license_info: Dict):
        """
        Guarda información de licencia en cache local.

        Args:
            license_info: Información de la licencia
        """
        try:
            cache = {
                "license_info": license_info,
                "last_validation": datetime.utcnow().isoformat(),
                "hardware_id": self.hardware_id
            }
            with open(self.cache_file, "w") as f:
                json.dump(cache, f, indent=2)
            logger.info("License cache saved")
        except Exception as e:
            logger.error(f"Error saving license cache: {e}")

    async def validate_online(self) -> bool:
        """
        Valida la licencia con el servidor central.

        Returns:
            True si la licencia es válida
        """
        if not self.license_key:
            logger.error("No license key provided")
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.license_server_url}/api/license/validate",
                    json={
                        "license_key": self.license_key,
                        "hardware_id": self.hardware_id
                    }
                )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("valid"):
                        self.license_info = data.get("license_info")
                        self.last_validation = datetime.utcnow()
                        self._is_valid = True

                        # Guardar en cache
                        self.save_cache(self.license_info)

                        logger.info(f"License validated successfully: {self.license_info.get('client_name')}")
                        return True
                    else:
                        logger.error(f"License validation failed: {data.get('message')}")
                        self._is_valid = False
                        return False
                else:
                    logger.error(f"License server returned {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Error validating license online: {e}")
            return False

    async def validate_offline(self) -> bool:
        """
        Valida usando cache local con grace period de 24 horas.

        Returns:
            True si la licencia cacheada es válida
        """
        cache = self.load_cache()

        if not cache:
            logger.warning("No license cache found")
            return False

        # Verificar hardware ID
        if cache.get("hardware_id") != self.hardware_id:
            logger.error("Hardware ID mismatch - possible license transfer")
            return False

        # Verificar grace period (24 horas)
        last_validation = datetime.fromisoformat(cache["last_validation"])
        grace_period = timedelta(hours=24)

        if datetime.utcnow() - last_validation > grace_period:
            logger.error("Grace period expired - online validation required")
            return False

        # Licencia válida en modo offline
        self.license_info = cache["license_info"]
        self.last_validation = last_validation
        self._is_valid = True

        logger.info("License validated from cache (offline mode)")
        return True

    async def validate(self) -> bool:
        """
        Valida la licencia (online primero, luego offline).

        Returns:
            True si la licencia es válida
        """
        # Intentar validación online
        online_valid = await self.validate_online()

        if online_valid:
            return True

        # Fallback a validación offline
        logger.warning("Online validation failed, trying offline validation")
        offline_valid = await self.validate_offline()

        return offline_valid

    async def send_heartbeat(self):
        """
        Envía heartbeat al servidor central con telemetría.
        """
        if not self.license_key or not self._is_valid:
            return

        try:
            # Obtener IP del servidor
            try:
                import socket
                server_ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                server_ip = "unknown"

            # Obtener versión del sistema
            from . import __version__
            version = __version__

            # Obtener uso de recursos
            cpu_usage, memory_usage, disk_usage = self._get_resource_usage()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.license_server_url}/api/license/heartbeat",
                    json={
                        "license_key": self.license_key,
                        "active_calls": self._active_calls,
                        "active_agents": self._active_agents,
                        "server_ip": server_ip,
                        "version": version,
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage,
                        "disk_usage": disk_usage
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("warnings"):
                        for warning in data["warnings"]:
                            logger.warning(f"License warning: {warning}")

                    logger.debug("Heartbeat sent successfully")
                else:
                    logger.error(f"Heartbeat failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")

    def _get_resource_usage(self) -> tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Obtiene uso de recursos del sistema.

        Returns:
            Tupla (cpu_usage, memory_usage, disk_usage) en porcentaje
        """
        try:
            import psutil
            cpu = int(psutil.cpu_percent(interval=1))
            memory = int(psutil.virtual_memory().percent)
            disk = int(psutil.disk_usage('/').percent)
            return cpu, memory, disk
        except Exception:
            return None, None, None

    async def heartbeat_loop(self):
        """
        Loop de heartbeat (cada 5 minutos).
        """
        while True:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(300)  # 5 minutos
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(300)

    async def validation_loop(self):
        """
        Loop de validación (cada 1 hora).
        """
        while True:
            try:
                await asyncio.sleep(3600)  # 1 hora
                await self.validate_online()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in validation loop: {e}")

    async def start(self):
        """
        Inicia el validador de licencias.

        - Valida la licencia inicialmente
        - Inicia loops de heartbeat y validación
        """
        # Validación inicial
        is_valid = await self.validate()

        if not is_valid:
            raise Exception("License validation failed")

        logger.info(f"License validated: {self.license_info.get('client_name')}")
        logger.info(f"Max concurrent calls: {self.license_info.get('max_concurrent_calls')}")
        logger.info(f"Max agents: {self.license_info.get('max_agents')}")
        logger.info(f"Expires: {self.license_info.get('expires_at')}")

        # Iniciar loops
        self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        self.validation_task = asyncio.create_task(self.validation_loop())

    async def stop(self):
        """
        Detiene el validador de licencias.
        """
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.validation_task:
            self.validation_task.cancel()
            try:
                await self.validation_task
            except asyncio.CancelledError:
                pass

    @property
    def is_valid(self) -> bool:
        """Retorna si la licencia es válida"""
        return self._is_valid

    @property
    def max_concurrent_calls(self) -> int:
        """Retorna el límite de llamadas concurrentes"""
        if self.license_info:
            return self.license_info.get("max_concurrent_calls", 5)
        return 0

    @property
    def max_agents(self) -> int:
        """Retorna el límite de agentes"""
        if self.license_info:
            return self.license_info.get("max_agents", 10)
        return 0

    def increment_active_calls(self):
        """Incrementa el contador de llamadas activas"""
        self._active_calls += 1

    def decrement_active_calls(self):
        """Decrementa el contador de llamadas activas"""
        self._active_calls = max(0, self._active_calls - 1)

    def can_accept_call(self) -> bool:
        """
        Verifica si se puede aceptar una nueva llamada.

        Returns:
            True si no se ha excedido el límite
        """
        if not self._is_valid:
            return False

        return self._active_calls < self.max_concurrent_calls

    def set_active_agents(self, count: int):
        """Establece el número de agentes activos"""
        self._active_agents = count

    async def report_calls(self, calls_count: int, total_minutes: int):
        """
        Reporta llamadas completadas al servidor.

        Args:
            calls_count: Número de llamadas completadas
            total_minutes: Total de minutos de llamadas
        """
        if not self.license_key or not self._is_valid:
            return

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.license_server_url}/api/license/report-calls",
                    json={
                        "license_key": self.license_key,
                        "calls_count": calls_count,
                        "total_minutes": total_minutes
                    }
                )

                if response.status_code == 200:
                    logger.info(f"Reported {calls_count} calls ({total_minutes} minutes)")
                else:
                    logger.error(f"Failed to report calls: {response.status_code}")

        except Exception as e:
            logger.error(f"Error reporting calls: {e}")


# Singleton instance
_license_validator: Optional[LicenseValidator] = None


def get_license_validator() -> LicenseValidator:
    """
    Obtiene la instancia singleton del validador de licencias.

    Returns:
        Instancia del validador
    """
    global _license_validator
    if _license_validator is None:
        _license_validator = LicenseValidator()
    return _license_validator
