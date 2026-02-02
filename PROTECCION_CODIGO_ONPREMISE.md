# Protección de Código On-Premise

## Problema

Cuando vendes **software on-premise** a clientes, se enfrentan estos riesgos:

```
❌ RIESGOS SIN PROTECCIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cliente instala en su servidor
    ↓
Tiene acceso al código fuente
    ↓
Puede:
  • Copiar el código
  • Modificar licencias
  • Clonar para otros clientes
  • Vender como propio
  • No pagar mantenimiento
  • Ocultar número real de llamadas
```

## Solución: Protección Multi-Capa

```
✅ SISTEMA DE PROTECCIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Licenciamiento ──> Verifica licencia válida
2. Ofuscación ─────> Dificulta ingeniería inversa
3. Telemetría ─────> Reporta uso a tu servidor
4. Hardware Binding > Amarra a hardware específico
5. Encriptación ───> Cifra código sensible
6. Code Signing ───> Firma digital verificable
```

---

## Arquitectura de Protección

### Capa 1: Sistema de Licencias

```
┌────────────────────────────────────────────┐
│        TU SERVIDOR DE LICENCIAS            │
│  https://license.tuempresa.com             │
│                                            │
│  • Genera licencias                        │
│  • Valida activaciones                     │
│  • Trackea uso                             │
│  • Revoca licencias                        │
└──────────────┬─────────────────────────────┘
               │ HTTPS (verificación)
               │
┌──────────────▼─────────────────────────────┐
│     INSTALACIÓN ON-PREMISE (Cliente)       │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │  License Validator                   │ │
│  │  • Verifica al iniciar               │ │
│  │  • Valida cada N horas               │ │
│  │  • Envía métricas de uso             │ │
│  └──────────────────────────────────────┘ │
│             ↓                              │
│  ┌──────────────────────────────────────┐ │
│  │  App Principal (si licencia OK)      │ │
│  │  • STT, TTS, LLM                     │ │
│  │  • Asterisk                          │ │
│  │  • Call Center                       │ │
│  └──────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

---

## Implementación

### 1. Sistema de Licencias

#### Crear Servidor de Licencias (Tu lado)

```python
# services/license_server/main.py
# Este corre en TU servidor, no del cliente

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import secrets
import hashlib
from datetime import datetime, timedelta
import jwt

app = FastAPI()

SECRET_KEY = "tu_secreto_super_seguro_cambialo"
ALGORITHM = "HS256"

class LicenseRequest(BaseModel):
    hardware_id: str
    company_name: str
    plan: str  # "basic" | "pro" | "enterprise"


class LicenseValidation(BaseModel):
    license_key: str
    hardware_id: str


# Base de datos de licencias (usar PostgreSQL/MySQL en producción)
licenses_db = {}


def generate_hardware_id() -> str:
    """
    El cliente debe generar su hardware ID único basado en:
    - MAC address
    - CPU ID
    - Motherboard serial
    """
    # Esto lo genera el cliente, aquí solo ejemplo
    return hashlib.sha256(b"unique_hardware_info").hexdigest()


@app.post("/api/license/generate")
async def generate_license(request: LicenseRequest):
    """
    Genera una licencia nueva

    Solo TÚ puedes llamar a esto (autenticación requerida)
    """
    # Verificar que el cliente pagó, tiene contrato, etc.

    # Generar license key única
    license_key = secrets.token_urlsafe(32)

    # Calcular fecha de expiración según plan
    expiry_days = {
        "basic": 30,
        "pro": 365,
        "enterprise": 365 * 10
    }

    expires_at = datetime.utcnow() + timedelta(days=expiry_days.get(request.plan, 30))

    # Generar JWT firmado
    payload = {
        "license_key": license_key,
        "hardware_id": request.hardware_id,
        "company_name": request.company_name,
        "plan": request.plan,
        "expires_at": expires_at.isoformat(),
        "max_concurrent_calls": 10 if request.plan == "basic" else (50 if request.plan == "pro" else 999),
        "features": {
            "stt": True,
            "tts": True,
            "llm": request.plan in ["pro", "enterprise"],
            "voice_cloning": request.plan == "enterprise",
            "freepbx": request.plan in ["pro", "enterprise"]
        }
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Guardar en base de datos
    licenses_db[license_key] = {
        "token": token,
        "hardware_id": request.hardware_id,
        "expires_at": expires_at,
        "activated_at": datetime.utcnow(),
        "last_heartbeat": None,
        "total_calls": 0
    }

    return {
        "license_key": license_key,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "max_concurrent_calls": payload["max_concurrent_calls"],
        "features": payload["features"]
    }


@app.post("/api/license/validate")
async def validate_license(validation: LicenseValidation):
    """
    Valida que una licencia sea válida

    El cliente llama a esto:
    - Al iniciar la aplicación
    - Cada N horas (heartbeat)
    """
    # Verificar que la licencia existe
    if validation.license_key not in licenses_db:
        raise HTTPException(400, "Invalid license key")

    license_data = licenses_db[validation.license_key]

    # Verificar hardware ID (antipiratería)
    if license_data["hardware_id"] != validation.hardware_id:
        raise HTTPException(403, "License key does not match hardware ID. Contact support.")

    # Verificar expiración
    if datetime.fromisoformat(license_data["expires_at"].isoformat()) < datetime.utcnow():
        raise HTTPException(403, "License expired. Please renew.")

    # Decodificar token
    try:
        payload = jwt.decode(license_data["token"], SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(403, "License expired")
    except jwt.InvalidTokenError:
        raise HTTPException(403, "Invalid license token")

    # Actualizar último heartbeat
    license_data["last_heartbeat"] = datetime.utcnow()

    return {
        "valid": True,
        "expires_at": payload["expires_at"],
        "plan": payload["plan"],
        "max_concurrent_calls": payload["max_concurrent_calls"],
        "features": payload["features"],
        "days_remaining": (datetime.fromisoformat(payload["expires_at"]) - datetime.utcnow()).days
    }


@app.post("/api/license/heartbeat")
async def heartbeat(
    license_key: str,
    hardware_id: str,
    current_calls: int = 0,
    total_calls_today: int = 0
):
    """
    El cliente envía métricas periódicas

    Esto te permite:
    - Trackear uso real
    - Detectar piratería (múltiples HW IDs con misma licencia)
    - Facturar por uso
    """
    if license_key not in licenses_db:
        raise HTTPException(400, "Invalid license")

    license_data = licenses_db[license_key]

    # Verificar HW ID
    if license_data["hardware_id"] != hardware_id:
        # ALERTA: Posible piratería
        # Enviar notificación a admin
        raise HTTPException(403, "Hardware mismatch detected")

    # Actualizar métricas
    license_data["last_heartbeat"] = datetime.utcnow()
    license_data["total_calls"] += total_calls_today

    return {
        "status": "ok",
        "message": "Heartbeat received"
    }
```

#### Cliente: Validador de Licencias

```python
# services/backend/license_validator.py
# Este corre en el servidor del CLIENTE

import os
import hashlib
import platform
import uuid
import httpx
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)

LICENSE_SERVER_URL = "https://license.tuempresa.com"  # TU servidor
LICENSE_FILE = Path("/etc/callcenter/license.json")


class LicenseValidator:
    """Valida licencia del call center"""

    def __init__(self):
        self.license_key = None
        self.hardware_id = None
        self.license_data = None
        self.is_valid = False
        self.last_validation = None

    def get_hardware_id(self) -> str:
        """
        Genera ID único del hardware del cliente

        Combina:
        - MAC address
        - CPU ID
        - Motherboard UUID
        """
        identifiers = []

        # MAC address
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                           for elements in range(0, 2*6, 2)][::-1])
            identifiers.append(mac)
        except:
            pass

        # CPU info
        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    identifiers.append(cpuinfo[:100])  # Primeras líneas
        except:
            pass

        # Combinar y hashear
        combined = "".join(identifiers)
        hardware_id = hashlib.sha256(combined.encode()).hexdigest()

        return hardware_id

    async def load_license(self):
        """Carga licencia del archivo local"""
        if not LICENSE_FILE.exists():
            logger.error("❌ No se encontró archivo de licencia")
            logger.error(f"   Esperado en: {LICENSE_FILE}")
            logger.error("   Contacta a soporte para obtener una licencia")
            return False

        try:
            with open(LICENSE_FILE, 'r') as f:
                data = json.load(f)

            self.license_key = data.get("license_key")
            self.hardware_id = self.get_hardware_id()

            if not self.license_key:
                logger.error("❌ Licencia inválida: falta license_key")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Error cargando licencia: {e}")
            return False

    async def validate_online(self) -> bool:
        """
        Valida licencia con servidor remoto

        Returns:
            True si licencia válida, False si no
        """
        if not self.license_key:
            logger.error("❌ No hay licencia cargada")
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{LICENSE_SERVER_URL}/api/license/validate",
                    json={
                        "license_key": self.license_key,
                        "hardware_id": self.hardware_id
                    }
                )

                if response.status_code == 200:
                    self.license_data = response.json()
                    self.is_valid = True
                    self.last_validation = datetime.utcnow()

                    logger.info("✅ Licencia válida")
                    logger.info(f"   Plan: {self.license_data.get('plan')}")
                    logger.info(f"   Expira en: {self.license_data.get('days_remaining')} días")
                    logger.info(f"   Llamadas simultáneas: {self.license_data.get('max_concurrent_calls')}")

                    return True

                elif response.status_code == 403:
                    error = response.json()
                    logger.error(f"❌ Licencia inválida: {error.get('detail')}")
                    logger.error("   Contacta a soporte")
                    self.is_valid = False
                    return False

                else:
                    logger.error(f"❌ Error validando licencia: {response.status_code}")
                    # En caso de error de red, permitir gracia period
                    return await self._check_grace_period()

        except Exception as e:
            logger.warning(f"⚠️  No se pudo conectar al servidor de licencias: {e}")
            # Permitir funcionamiento offline temporal
            return await self._check_grace_period()

    async def _check_grace_period(self) -> bool:
        """
        Permite funcionamiento offline por 24 horas

        Si no puede conectar al servidor de licencias,
        permite que funcione por 24h más
        """
        if self.last_validation:
            grace_period = timedelta(hours=24)
            if datetime.utcnow() - self.last_validation < grace_period:
                logger.warning("⚠️  Usando licencia en modo offline (gracia 24h)")
                return True

        logger.error("❌ Período de gracia expirado. Requiere conexión al servidor de licencias.")
        return False

    async def send_heartbeat(self, current_calls: int, total_calls_today: int):
        """
        Envía heartbeat al servidor con métricas

        Debe ejecutarse cada hora
        """
        if not self.is_valid:
            return

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{LICENSE_SERVER_URL}/api/license/heartbeat",
                    params={
                        "license_key": self.license_key,
                        "hardware_id": self.hardware_id,
                        "current_calls": current_calls,
                        "total_calls_today": total_calls_today
                    }
                )
        except Exception as e:
            logger.warning(f"Heartbeat falló: {e}")

    def get_max_concurrent_calls(self) -> int:
        """Retorna límite de llamadas simultáneas según licencia"""
        if not self.license_data:
            return 0
        return self.license_data.get("max_concurrent_calls", 0)

    def is_feature_enabled(self, feature: str) -> bool:
        """Verifica si una feature está habilitada en la licencia"""
        if not self.license_data:
            return False

        features = self.license_data.get("features", {})
        return features.get(feature, False)


# Instancia global
license_validator = LicenseValidator()


async def initialize_license() -> bool:
    """
    Inicializa y valida licencia

    Llamar al inicio de la aplicación
    """
    logger.info("🔐 Validando licencia...")

    # Cargar licencia del archivo
    loaded = await license_validator.load_license()
    if not loaded:
        logger.error("❌ No se pudo cargar licencia")
        logger.error("━" * 60)
        logger.error("APLICACIÓN NO PUEDE INICIAR SIN LICENCIA VÁLIDA")
        logger.error("━" * 60)
        return False

    # Validar online
    valid = await license_validator.validate_online()
    if not valid:
        logger.error("❌ Licencia inválida")
        logger.error("━" * 60)
        logger.error("APLICACIÓN NO PUEDE INICIAR SIN LICENCIA VÁLIDA")
        logger.error("━" * 60)
        return False

    logger.info("✅ Licencia validada correctamente")
    return True
```

#### Integración en main.py

```python
# services/backend/main.py

from license_validator import initialize_license, license_validator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup

    # ✅ VALIDAR LICENCIA PRIMERO
    license_valid = await initialize_license()
    if not license_valid:
        logger.error("❌ SISTEMA BLOQUEADO: LICENCIA INVÁLIDA")
        # No permitir que el sistema inicie
        raise Exception("Invalid license. System cannot start.")

    await db.connect()
    init_config_manager()
    await initialize_adaptive_flow()

    # Iniciar heartbeat de licencia (cada hora)
    asyncio.create_task(license_heartbeat_task())

    yield

    # Shutdown
    await db.disconnect()


async def license_heartbeat_task():
    """Envía heartbeat de licencia cada hora"""
    while True:
        await asyncio.sleep(3600)  # 1 hora

        try:
            # Obtener métricas actuales
            current_calls = len(manager.active_connections)  # WebSocket manager
            total_calls_today = await db.get_calls_count_today()

            await license_validator.send_heartbeat(current_calls, total_calls_today)
        except Exception as e:
            logger.error(f"Error en heartbeat de licencia: {e}")


# Middleware para verificar límite de llamadas
@app.middleware("http")
async def check_concurrent_calls_limit(request: Request, call_next):
    # Verificar límite de llamadas simultáneas
    if request.url.path.startswith("/api/calls"):
        max_calls = license_validator.get_max_concurrent_calls()
        current_calls = len(manager.active_connections)

        if current_calls >= max_calls:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Límite de llamadas simultáneas alcanzado ({max_calls}). Actualiza tu plan."
                }
            )

    response = await call_next(request)
    return response
```

---

### 2. Hardware Binding (Amarre a Hardware)

Ya implementado en `get_hardware_id()` arriba. El sistema:

✅ Genera ID único basado en hardware del cliente
✅ Licencia solo funciona en ESE servidor
✅ Si copian la licencia a otro servidor → Error de hardware mismatch

---

### 3. Ofuscación de Código Python

```bash
# Instalar PyArmor
pip install pyarmor

# Ofuscar todo el código Python
pyarmor gen --recursive services/backend/
pyarmor gen --recursive services/stt/
pyarmor gen --recursive services/tts/
pyarmor gen --recursive services/llm/

# Resultado:
# - Código ofuscado en dist/
# - No se puede leer el código fuente
# - Dificulta ingeniería inversa
```

---

### 4. Telemetría y Tracking

```python
# services/backend/telemetry.py

import httpx
from datetime import datetime

TELEMETRY_SERVER = "https://telemetry.tuempresa.com"


async def send_telemetry(
    license_key: str,
    event_type: str,
    data: dict
):
    """
    Envía eventos de telemetría a tu servidor

    Eventos útiles:
    - app_start
    - call_initiated
    - call_ended
    - feature_used
    - error_occurred
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{TELEMETRY_SERVER}/api/events",
                json={
                    "license_key": license_key,
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                }
            )
    except:
        pass  # No bloquear si falla telemetría
```

---

## Deployment para Cliente On-Premise

### Paso 1: Compilar y Ofuscar

```bash
#!/bin/bash
# build_for_client.sh

echo "🔨 Compilando versión para cliente..."

# 1. Ofuscar código Python
pyarmor gen --recursive services/backend/ -O dist/backend
pyarmor gen --recursive services/stt/ -O dist/stt
pyarmor gen --recursive services/tts/ -O dist/tts
pyarmor gen --recursive services/llm/ -O dist/llm

# 2. Construir imágenes Docker
docker-compose build

# 3. Exportar imágenes
docker save callcenter-backend:latest | gzip > callcenter-backend.tar.gz
docker save callcenter-stt:latest | gzip > callcenter-stt.tar.gz
docker save callcenter-tts:latest | gzip > callcenter-tts.tar.gz
docker save callcenter-llm:latest | gzip > callcenter-llm.tar.gz

echo "✅ Build completo. Enviar archivos .tar.gz al cliente"
```

### Paso 2: Generar Licencia para Cliente

```bash
# Generar hardware ID del cliente
# (Cliente ejecuta esto y te lo envía)
python -c "from license_validator import LicenseValidator; print(LicenseValidator().get_hardware_id())"

# Resultado: a1b2c3d4e5f6... (hash único)
```

```bash
# TÚ generas la licencia
curl -X POST https://license.tuempresa.com/api/license/generate \
  -H "Authorization: Bearer TU_TOKEN_ADMIN" \
  -d '{
    "hardware_id": "a1b2c3d4e5f6...",
    "company_name": "Cliente XYZ",
    "plan": "enterprise"
  }'

# Resultado:
# {
#   "license_key": "xyz123...",
#   "token": "eyJhbGc...",
#   "expires_at": "2027-01-29"
# }
```

### Paso 3: Cliente Instala

```bash
# Cliente carga las imágenes
docker load < callcenter-backend.tar.gz
docker load < callcenter-stt.tar.gz
# ...

# Cliente crea archivo de licencia
sudo mkdir -p /etc/callcenter
sudo nano /etc/callcenter/license.json

# Contenido:
{
  "license_key": "xyz123..."
}

# Cliente inicia
docker-compose up -d

# Sistema valida licencia y arranca si es válida
```

---

## Resumen de Protecciones

| Protección | Qué Previene | Nivel |
|------------|--------------|-------|
| **Hardware Binding** | Copiar licencia a otro servidor | 🔒🔒🔒 Alto |
| **Validación Online** | Licencias piratas | 🔒🔒🔒 Alto |
| **Ofuscación** | Ingeniería inversa | 🔒🔒 Medio |
| **Telemetría** | Uso no autorizado | 🔒🔒 Medio |
| **Heartbeat** | Detectar piratería | 🔒🔒🔒 Alto |
| **Límite de llamadas** | Abuso | 🔒🔒🔒 Alto |
| **Docker images** | Copiar fácilmente | 🔒 Bajo |

---

## Recomendación Final

```
✅ STACK RECOMENDADO PARA ON-PREMISE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Sistema de licencias online (obligatorio)
2. Hardware binding (obligatorio)
3. Heartbeat cada hora (obligatorio)
4. Ofuscación con PyArmor (recomendado)
5. Telemetría de eventos (recomendado)
6. Docker images signed (opcional)
```

**¿Quieres que implemente el sistema completo de licencias?**
