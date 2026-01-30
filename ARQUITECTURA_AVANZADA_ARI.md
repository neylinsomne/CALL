# Arquitectura Avanzada: ARI, Canales, Transfers y Escalabilidad

## 1. Manejo de Transfers en ARI

### Transfer Handling según la documentación

Según [ARI Transfer Handling](https://docs.asterisk.org/Configuration/Interfaces/Asterisk-REST-Interface-ARI/Introduction-to-ARI-Transfer-Handling/), hay varios tipos de transfers:

#### Tipos de Transfers

**1. Blind Transfer (Transferencia Ciega)**
```python
# El agente transfiere sin hablar antes con el destino
async def blind_transfer(channel_id: str, extension: str):
    """Transferencia directa sin anuncio"""
    url = f"{base_url}/channels/{channel_id}/redirect"
    data = {"endpoint": f"PJSIP/{extension}"}
    await session.post(url, json=data)
```

**2. Attended Transfer (Transferencia Atendida)**
```python
# El agente habla primero con el destino antes de transferir
async def attended_transfer(channel_id: str, target_extension: str):
    """
    1. Crear bridge
    2. Poner llamada original en hold
    3. Llamar al nuevo destino
    4. Hablar con nuevo destino
    5. Unir ambas llamadas o cancelar
    """
    # 1. Crear bridge
    bridge = await ari_client.create_bridge(bridge_type="mixing")

    # 2. Poner canal original en el bridge (hold)
    await ari_client.add_channel_to_bridge(bridge["id"], channel_id)

    # 3. Originar llamada al nuevo destino
    new_channel = await ari_client.originate_call(
        endpoint=f"PJSIP/{target_extension}",
        context="call-center"
    )

    # 4. Esperar a que conteste (evento ChannelAnswered)
    # ... el agente habla con el nuevo destino ...

    # 5. Unir ambos canales
    await ari_client.add_channel_to_bridge(bridge["id"], new_channel["id"])

    # 6. Salir el agente
    await ari_client.remove_channel_from_bridge(bridge["id"], agent_channel_id)
```

**3. External Transfer (REFER)**
```python
# Transfer usando protocolo SIP REFER
# El endpoint SIP maneja el transfer
# ARI solo observa los eventos
```

---

## 2. Capacidad Máxima de Canales por Hardware

### Factores Limitantes

#### A. CPU y RAM
| Hardware | Canales Simultáneos | Notas |
|----------|---------------------|-------|
| 2 cores, 4GB RAM | ~50 canales | Sin transcoding |
| 4 cores, 8GB RAM | ~100 canales | Con transcoding ligero |
| 8 cores, 16GB RAM | ~200 canales | Transcoding moderado |
| 16 cores, 32GB RAM | ~500 canales | Call center grande |

**Fórmula aproximada**:
- Sin transcoding: ~25 canales por core
- Con transcoding (g729 ↔ ulaw): ~10 canales por core
- Con IA (STT/TTS/LLM): ~2-5 canales por core (depende de GPU)

#### B. GPU (Para STT/TTS/LLM)

**Tu caso con NVIDIA GPU:**

| Modelo GPU | STT (Whisper) | TTS (F5-TTS) | LLM | Total Simultáneo |
|------------|---------------|--------------|-----|------------------|
| RTX 3060 (12GB) | ~10 canales | ~15 canales | ~5 canales | **~5 canales** (bottleneck: LLM) |
| RTX 3090 (24GB) | ~20 canales | ~30 canales | ~10 canales | **~10 canales** |
| RTX 4090 (24GB) | ~30 canales | ~40 canales | ~15 canales | **~15 canales** |
| A100 (40GB) | ~50 canales | ~60 canales | ~30 canales | **~30 canales** |

**Bottleneck**: El LLM es el más pesado. Con Qwen3-14B o Llama-3.1-8B, el límite está en ~5-15 llamadas simultáneas por GPU.

**Optimizaciones posibles:**
```python
# 1. Batch processing de audio
# Procesar múltiples chunks en un solo forward pass

# 2. Model quantization
# int8/int4 para duplicar throughput

# 3. vLLM para LLM
# Optimizado para inferencia paralela
```

#### C. Tarjetas DAHDI

| Tarjeta | Tipo | Canales Máximos |
|---------|------|-----------------|
| Sangoma A200D | Analog FXO/FXS | 2-24 canales |
| Sangoma A400 | Analog FXO/FXS | 4-24 canales |
| Sangoma A104 | Digital E1/T1/PRI | 120 canales (4 E1) |
| Sangoma A108 | Digital E1/T1/PRI | 240 canales (8 E1) |

**Límite por servidor:**
- Máximo ~8 tarjetas por servidor (slots PCIe)
- Con A108 × 8 = **1,920 canales teóricos**
- En práctica: ~500-1000 canales por servidor (CPU/RAM limit)

#### D. Gateway FXO/FXS

| Gateway | Puertos | Canales Simultáneos |
|---------|---------|---------------------|
| Grandstream GXW4104 | 4 FXO | 4 |
| Grandstream GXW4108 | 8 FXO | 8 |
| Dinstar MTG1000 | 8-32 FXO | 8-32 |
| Cisco VG224 | 24 FXS | 24 |

**Múltiples Gateways:**
- Puedes tener N gateways conectados vía SIP
- Límite: CPU de Asterisk y ancho de banda de red

---

## 3. Detección Automática de Hardware (Gateway vs PCIe)

### Estrategia de Detección

```python
# services/backend/hardware_detector.py

import os
import subprocess
import logging
from typing import Literal, Optional
import aiohttp

logger = logging.getLogger(__name__)

HardwareType = Literal["gateway", "dahdi", "both", "none"]


class HardwareDetector:
    """Detecta automáticamente hardware de telefonía"""

    def __init__(self):
        self.hardware_type: HardwareType = "none"
        self.gateway_endpoints = []
        self.dahdi_channels = []

    async def detect_hardware(self) -> HardwareType:
        """
        Detecta qué hardware está disponible:
        - Gateway FXO/FXS (vía PJSIP endpoints)
        - Tarjetas DAHDI (vía /dev/dahdi)

        Returns:
            "gateway", "dahdi", "both", o "none"
        """
        has_gateway = await self._detect_gateway()
        has_dahdi = await self._detect_dahdi()

        if has_gateway and has_dahdi:
            self.hardware_type = "both"
        elif has_gateway:
            self.hardware_type = "gateway"
        elif has_dahdi:
            self.hardware_type = "dahdi"
        else:
            self.hardware_type = "none"

        logger.info(f"Hardware detectado: {self.hardware_type}")
        return self.hardware_type

    async def _detect_gateway(self) -> bool:
        """
        Detecta Gateway FXO/FXS verificando endpoints PJSIP

        Método 1: Consultar ARI
        Método 2: Ping al Gateway IP
        """
        try:
            # Método 1: Consultar Asterisk vía ARI
            asterisk_host = os.getenv("ASTERISK_HOST", "asterisk")
            ari_user = os.getenv("ARI_PASSWORD", "ari123")

            url = f"http://{asterisk_host}:8088/ari/endpoints"
            auth = aiohttp.BasicAuth("callcenter-ai", ari_user)

            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        endpoints = await resp.json()

                        # Buscar endpoints que empiecen con "gateway"
                        gateway_eps = [
                            ep for ep in endpoints
                            if ep["resource"].startswith("gateway-fxo")
                        ]

                        if gateway_eps:
                            self.gateway_endpoints = gateway_eps
                            logger.info(f"✅ Gateway detectado: {len(gateway_eps)} endpoints")
                            return True

            # Método 2: Ping al Gateway IP (fallback)
            gateway_ip = os.getenv("GATEWAY_FXO_IP", "192.168.1.100")
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", gateway_ip],
                capture_output=True,
                timeout=2
            )

            if result.returncode == 0:
                logger.info(f"✅ Gateway detectado vía ping: {gateway_ip}")
                return True

        except Exception as e:
            logger.warning(f"Error detectando gateway: {e}")

        logger.info("❌ No se detectó Gateway")
        return False

    async def _detect_dahdi(self) -> bool:
        """
        Detecta tarjetas DAHDI verificando /dev/dahdi

        Método 1: Verificar dispositivo /dev/dahdi
        Método 2: Ejecutar dahdi_scan
        """
        try:
            # Método 1: Verificar dispositivo
            if os.path.exists("/dev/dahdi"):
                logger.info("✅ Dispositivo /dev/dahdi encontrado")

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
                        self.dahdi_channels = channels

                        logger.info(f"✅ DAHDI detectado: {len(channels)} canales")
                        return True

                except FileNotFoundError:
                    # dahdi_scan no está instalado, pero /dev/dahdi existe
                    logger.info("✅ DAHDI detectado (sin dahdi_scan)")
                    return True

        except Exception as e:
            logger.warning(f"Error detectando DAHDI: {e}")

        logger.info("❌ No se detectó DAHDI")
        return False

    async def get_available_channels(self, hardware_type: Optional[HardwareType] = None) -> int:
        """
        Retorna el número de canales disponibles según el hardware

        Args:
            hardware_type: Si None, usa self.hardware_type

        Returns:
            Número de canales disponibles
        """
        hw_type = hardware_type or self.hardware_type

        if hw_type == "gateway":
            # Consultar gateway
            return len(self.gateway_endpoints) if self.gateway_endpoints else 4

        elif hw_type == "dahdi":
            # Consultar DAHDI
            return len(self.dahdi_channels) if self.dahdi_channels else 4

        elif hw_type == "both":
            gateway_count = len(self.gateway_endpoints) if self.gateway_endpoints else 4
            dahdi_count = len(self.dahdi_channels) if self.dahdi_channels else 4
            return gateway_count + dahdi_count

        else:
            return 0

    def get_pipeline_config(self) -> dict:
        """
        Retorna configuración del pipeline según hardware detectado

        Returns:
            dict con configuración recomendada
        """
        config = {
            "hardware_type": self.hardware_type,
            "max_concurrent_calls": 0,
            "route_preference": [],
            "codecs": ["ulaw", "alaw"],
            "use_transcoding": False
        }

        if self.hardware_type == "gateway":
            config["max_concurrent_calls"] = self.get_available_channels()
            config["route_preference"] = ["gateway", "sip_trunk"]
            # Los gateways suelen preferir ulaw
            config["codecs"] = ["ulaw", "alaw"]

        elif self.hardware_type == "dahdi":
            config["max_concurrent_calls"] = self.get_available_channels()
            config["route_preference"] = ["dahdi", "sip_trunk"]
            # DAHDI puede usar cualquier codec
            config["codecs"] = ["ulaw", "alaw", "g722"]

        elif self.hardware_type == "both":
            config["max_concurrent_calls"] = self.get_available_channels()
            config["route_preference"] = ["dahdi", "gateway", "sip_trunk"]
            config["codecs"] = ["ulaw", "alaw", "g722"]

        else:
            # Solo SIP trunk
            config["max_concurrent_calls"] = 100  # Arbitrario
            config["route_preference"] = ["sip_trunk"]
            config["codecs"] = ["opus", "ulaw", "alaw"]

        return config


# Uso en main.py
detector = HardwareDetector()

@app.on_event("startup")
async def startup_event():
    # Detectar hardware
    hardware_type = await detector.detect_hardware()
    pipeline_config = detector.get_pipeline_config()

    logger.info(f"Pipeline configurado para: {hardware_type}")
    logger.info(f"Máximo de llamadas simultáneas: {pipeline_config['max_concurrent_calls']}")
    logger.info(f"Preferencia de rutas: {pipeline_config['route_preference']}")
```

---

## 4. Local Channels en Asterisk

### ¿Qué son los Local Channels?

Según [ARI and Channels](https://docs.asterisk.org/Configuration/Interfaces/Asterisk-REST-Interface-ARI/Introduction-to-ARI-and-Channels/#internal-channels-local-channels):

**Local channels** son canales virtuales internos de Asterisk que permiten:
- Ejecutar el dialplan dentro de una aplicación ARI
- Crear "loops" de procesamiento
- Intercomunicación entre aplicaciones

### Casos de Uso en tu Arquitectura

#### 1. IVR Avanzado con IA

```python
# Usar local channel para ejecutar IVR tradicional + IA
async def handle_call_with_ivr(channel_id: str):
    """
    Combina IVR tradicional (Asterisk dialplan) con IA
    """
    # Crear local channel que ejecuta IVR
    local_channel = await ari_client.originate_call(
        endpoint=f"Local/100@ivr-menu",
        app="callcenter-ai"
    )

    # Crear bridge
    bridge = await ari_client.create_bridge()

    # Conectar llamada original con local channel
    await ari_client.add_channel_to_bridge(bridge["id"], channel_id)
    await ari_client.add_channel_to_bridge(bridge["id"], local_channel["id"])

    # El IVR se ejecuta en dialplan, luego puede volver a ARI
```

#### 2. Callbacks y Scheduled Calls

```python
# Local channel para llamadas programadas
async def schedule_callback(phone_number: str, schedule_time: datetime):
    """
    Programa una llamada para más tarde
    """
    # ... esperar hasta schedule_time ...

    # Crear local channel que origina la llamada
    local_channel = await ari_client.originate_call(
        endpoint=f"Local/{phone_number}@outbound-callback",
        app="callcenter-ai"
    )
```

#### 3. Conference Bridges

```python
# Local channels para conferencias de múltiples participantes
async def create_conference(participants: list[str]):
    """
    Crea conferencia de N participantes
    """
    bridge = await ari_client.create_bridge(bridge_type="mixing")

    for participant in participants:
        local_channel = await ari_client.originate_call(
            endpoint=f"Local/{participant}@call-center",
            app="callcenter-ai"
        )
        await ari_client.add_channel_to_bridge(bridge["id"], local_channel["id"])
```

### ¿Deberías usar Local Channels?

**SÍ, en estos casos:**
- ✅ Necesitas ejecutar lógica del dialplan desde ARI
- ✅ Quieres combinar IVR tradicional con IA
- ✅ Necesitas features de Asterisk (parking, queues, AGI)

**NO, en estos casos:**
- ❌ Solo necesitas control básico de llamadas
- ❌ Toda la lógica está en Python
- ❌ Quieres máximo rendimiento (los local channels tienen overhead)

**Recomendación para tu caso:**
Usa local channels **solo cuando necesites features específicos de Asterisk**. Para el flow normal de IA (STT → LLM → TTS), usa canales directos con AudioSocket.

---

## 5. ARI vs FreePBX: ¿Qué es mejor?

### Diferencias Fundamentales

| Aspecto | ARI | FreePBX |
|---------|-----|---------|
| **Tipo** | API programática (WebSocket + REST) | Interfaz gráfica web + AMI |
| **Control** | Código Python, máximo control | GUI, configuración visual |
| **Flexibilidad** | Total, puedes hacer cualquier cosa | Limitado a features de FreePBX |
| **Curva de aprendizaje** | Alta (requiere programación) | Baja (point & click) |
| **Rendimiento** | Excelente (solo lo que necesitas) | Bueno (overhead de AMI) |
| **Debugging** | Logs en tu código | Logs de Asterisk + FreePBX |
| **Escalabilidad** | Muy alta (cluster, load balancing) | Media (single server) |
| **Features avanzados** | Tú los implementas | Incluidos (IVR, queues, voicemail) |

### ¿Son Mutuamente Excluyentes?

**NO**, se complementan:

```
┌─────────────────────────────────────────┐
│         TU ARQUITECTURA HÍBRIDA         │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │   FreePBX    │  │  Backend Python │ │
│  │   (GUI)      │  │   + ARI Client  │ │
│  │              │  │                 │ │
│  │ • Config PBX │  │ • Control IA    │ │
│  │ • IVR manual │  │ • Eventos real  │ │
│  │ • Extensiones│  │ • Transferencias│ │
│  │ • Reportes   │  │ • Grabaciones   │ │
│  └──────┬───────┘  └────────┬────────┘ │
│         │                   │          │
│         └───────────┬───────┘          │
│                     ▼                  │
│            ┌─────────────────┐         │
│            │  ASTERISK PBX   │         │
│            │  • AMI (FreePBX)│         │
│            │  • ARI (Python) │         │
│            └─────────────────┘         │
└─────────────────────────────────────────┘
```

### Estrategia Recomendada: HÍBRIDA

**Usa FreePBX para:**
- ✅ Configuración inicial de Asterisk
- ✅ Gestión de extensiones y usuarios
- ✅ IVR tradicional (si necesitas)
- ✅ Reportes y CDR (Call Detail Records)
- ✅ Configuración de trunks y rutas
- ✅ Voicemail (si aplica)
- ✅ Monitoreo en tiempo real (GUI)

**Usa ARI para:**
- ✅ **Todo el flujo de IA** (STT → LLM → TTS)
- ✅ Control programático de llamadas
- ✅ Transferencias inteligentes (basadas en NLP)
- ✅ Grabación selectiva (según sentimiento)
- ✅ Integración con tu CRM/Backend
- ✅ Lógica de negocio compleja
- ✅ Estadísticas custom en tu dashboard

### División de Responsabilidades

```python
# extensions.conf.template

[call-center]
; === Llamadas que van al AI ===
exten => 100,1,NoOp(AI Agent)
 same => n,Answer()
 same => n,Set(CONVERSATION_ID=${UNIQUEID})
 same => n,AudioSocket(${CONVERSATION_ID},${AI_BACKEND_HOST}:${AI_BACKEND_PORT})
 same => n,Hangup()

; === Llamadas que van a cola humana (FreePBX) ===
exten => 200,1,NoOp(Human Queue - Managed by FreePBX)
 same => n,Answer()
 same => n,Queue(support-queue,t,,,120)  ; FreePBX gestiona esta queue
 same => n,Hangup()

; === IVR tradicional (FreePBX) ===
exten => 300,1,NoOp(IVR Menu - FreePBX)
 same => n,Answer()
 same => n,IVR(menu-principal)  ; Configurado en FreePBX GUI
 same => n,Hangup()
```

```python
# backend/main.py

@app.post("/api/calls/transfer-to-queue")
async def transfer_to_queue(channel_id: str, queue_name: str = "support-queue"):
    """
    Transfiere llamada a cola gestionada por FreePBX
    """
    # Usar ARI para transferir a extensión 200
    await ari_client.transfer_to_extension(channel_id, "200")

    # FreePBX toma el control desde aquí
    return {"status": "transferred_to_freepbx"}
```

---

## 6. Redis: ¿Es Necesario?

### ¿Para qué sirve Redis en un Call Center?

#### Casos de Uso

**1. State Management de Agentes**
```python
# Sin Redis (en memoria de Python)
active_agents = {}  # Se pierde si reinicia el backend

# Con Redis
import redis
r = redis.Redis(host='redis', port=6379)

# Persistente, compartido entre instancias
r.hset("agent:100", mapping={
    "status": "available",
    "current_call": None,
    "calls_today": 0
})
```

**2. Cache de Conversaciones**
```python
# Cachear contexto de conversación para respuestas rápidas
r.setex(f"conversation:{conversation_id}", 3600, json.dumps(messages))
```

**3. Rate Limiting**
```python
# Limitar llamadas por número
call_count = r.incr(f"calls:from:{caller_id}")
r.expire(f"calls:from:{caller_id}", 60)  # 1 minuto

if call_count > 5:
    # Bloquear spam
    return
```

**4. PubSub para Eventos**
```python
# Backend 1 publica evento
r.publish("call_events", json.dumps({
    "event": "transfer_requested",
    "channel_id": "abc123"
}))

# Backend 2, 3, N subscriben
pubsub = r.pubsub()
pubsub.subscribe("call_events")
for message in pubsub.listen():
    # Todos los backends reciben el evento
    handle_event(message)
```

**5. Distributed Locking**
```python
# Asegurar que solo un proceso maneja una llamada
lock = r.lock(f"lock:channel:{channel_id}", timeout=30)
if lock.acquire(blocking=False):
    try:
        # Procesar llamada
        await handle_call(channel_id)
    finally:
        lock.release()
```

### ¿Necesitas Redis en tu caso?

#### **SÍ, si tienes:**
- ✅ Múltiples instancias del backend (horizontal scaling)
- ✅ Más de 50 llamadas simultáneas
- ✅ Necesitas estado compartido entre procesos
- ✅ Quieres dashboards en tiempo real (PubSub)
- ✅ Necesitas cache de alta velocidad

#### **NO, si:**
- ❌ Solo tienes 1 instancia del backend
- ❌ Menos de 20 llamadas simultáneas
- ❌ El estado en PostgreSQL es suficiente
- ❌ No necesitas real-time updates en múltiples servicios

### Recomendación para tu Arquitectura

**FASE 1 (Actual)**: NO uses Redis
- Tu backend actual es single-instance
- PostgreSQL es suficiente para estado
- ARI WebSocket proporciona eventos en tiempo real
- Menos complejidad

**FASE 2 (Escalado > 50 llamadas)**: SÍ usa Redis
- Horizontal scaling del backend
- State management distribuido
- PubSub para dashboard real-time
- Cache de embeddings del LLM

### Implementación si decides usar Redis

```yaml
# docker-compose.yml

services:
  redis:
    image: redis:7-alpine
    container_name: callcenter-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - callcenter-network

volumes:
  redis_data:
```

```python
# services/backend/redis_manager.py

import redis.asyncio as redis
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


class RedisManager:
    """Gestor de Redis para estado de agentes y cache"""

    def __init__(self, host: str = "redis", port: int = 6379):
        self.redis: Optional[redis.Redis] = None
        self.host = host
        self.port = port

    async def connect(self):
        """Conecta a Redis"""
        self.redis = await redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True
        )
        logger.info("✅ Redis conectado")

    async def disconnect(self):
        """Desconecta de Redis"""
        if self.redis:
            await self.redis.close()

    # =========================================
    # AGENT STATE MANAGEMENT
    # =========================================

    async def set_agent_status(self, agent_id: str, status: str):
        """Actualiza estado de agente"""
        await self.redis.hset(f"agent:{agent_id}", "status", status)

    async def get_agent_status(self, agent_id: str) -> str:
        """Obtiene estado de agente"""
        return await self.redis.hget(f"agent:{agent_id}", "status")

    async def get_available_agents(self) -> list[str]:
        """Retorna lista de agentes disponibles"""
        agents = []
        cursor = 0

        while True:
            cursor, keys = await self.redis.scan(cursor, match="agent:*")
            for key in keys:
                status = await self.redis.hget(key, "status")
                if status == "available":
                    agent_id = key.split(":")[1]
                    agents.append(agent_id)

            if cursor == 0:
                break

        return agents

    # =========================================
    # CONVERSATION CACHE
    # =========================================

    async def cache_conversation(self, conversation_id: str, messages: list, ttl: int = 3600):
        """Cachea conversación por 1 hora"""
        await self.redis.setex(
            f"conv:{conversation_id}",
            ttl,
            json.dumps(messages)
        )

    async def get_cached_conversation(self, conversation_id: str) -> Optional[list]:
        """Obtiene conversación cacheada"""
        data = await self.redis.get(f"conv:{conversation_id}")
        return json.loads(data) if data else None

    # =========================================
    # RATE LIMITING
    # =========================================

    async def check_rate_limit(self, key: str, limit: int, window: int = 60) -> bool:
        """
        Rate limiting

        Args:
            key: Identificador (ej: caller_id)
            limit: Máximo de llamadas permitidas
            window: Ventana de tiempo en segundos

        Returns:
            True si está dentro del límite, False si excede
        """
        count = await self.redis.incr(f"rate:{key}")

        if count == 1:
            # Primera llamada en esta ventana
            await self.redis.expire(f"rate:{key}", window)

        return count <= limit

    # =========================================
    # PUBSUB
    # =========================================

    async def publish_event(self, channel: str, event: dict):
        """Publica evento a canal"""
        await self.redis.publish(channel, json.dumps(event))

    async def subscribe(self, channel: str):
        """Subscribirse a canal (retorna async iterator)"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)

        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
```

---

## 7. Recomendaciones Finales

### Arquitectura Óptima para tu Caso

```
┌────────────────────────────────────────────────────────────┐
│                    FRONTEND                                │
│  • FreePBX GUI (config, monitoreo)                         │
│  • Dashboard React (analytics, real-time)                  │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│                   BACKEND LAYER                            │
│  ┌──────────────────┐  ┌───────────────────────────────┐  │
│  │   FastAPI        │  │   ARI Client                  │  │
│  │   (REST API)     │  │   (WebSocket + Control)       │  │
│  └──────────────────┘  └───────────────────────────────┘  │
│                                                            │
│  [Redis] (opcional) - Solo si > 50 llamadas simultáneas   │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│                   ASTERISK PBX                             │
│  • AMI (para FreePBX)                                      │
│  • ARI (para Backend)                                      │
│  • PJSIP (SIP Trunk + Gateway)                             │
│  • DAHDI (Tarjetas Digium) - si aplica                     │
│  • AudioSocket → STT/TTS/LLM                               │
└────────────────────────┬───────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
  ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
  │ SIP TRUNK │   │  Gateway  │   │   DAHDI   │
  │ (Internet)│   │  FXO/FXS  │   │   PCIe    │
  └───────────┘   └───────────┘   └───────────┘
```

### Decision Tree

```
┌─ ¿Cuántas llamadas simultáneas necesitas? ─┐
│                                              │
├─ < 20 llamadas:                              │
│  • No uses Redis                             │
│  • Backend single-instance                   │
│  • FreePBX + ARI                             │
│  • Gateway FXO (si < 8 líneas fijas)         │
│                                              │
├─ 20-100 llamadas:                            │
│  • Considera Redis (opcional)                │
│  • Backend puede escalar a 2-3 instancias    │
│  • FreePBX + ARI definitivamente             │
│  • Gateway o Tarjeta Digium básica          │
│  • GPU más potente (RTX 3090+)              │
│                                              │
└─ > 100 llamadas:                             │
   • Redis obligatorio                         │
   • Backend multi-instance + load balancer    │
   • FreePBX + ARI + Asterisk Cluster          │
   • Múltiples tarjetas Digium (A104+)         │
   • Múltiples GPUs (A100)                     │
   • CDN para audio estático                   │
   └───────────────────────────────────────────┘
```

### Prioridades de Implementación

**AHORA (Fase 1):**
1. ✅ Implementar ARI client (ya hecho)
2. ✅ Configurar FreePBX (ya hecho)
3. ✅ Detección automática de hardware (script arriba)
4. Integrar ARI con tu main.py actual
5. Testear con llamadas reales

**PRÓXIMO MES (Fase 2):**
1. Optimizar modelo LLM (quantization, vLLM)
2. Implementar attended transfers
3. Métricas y analytics en dashboard
4. Backup automático de configuraciones

**FUTURO (Fase 3 - Escalado):**
1. Redis para > 50 llamadas
2. Cluster de Asterisk
3. Load balancer para backend
4. CDN para prompts de audio cacheados

---

## Conclusión

Para tu caso específico:

| Decisión | Recomendación |
|----------|---------------|
| **ARI vs FreePBX** | **AMBOS** (híbrido) |
| **Redis** | **NO** (por ahora) |
| **Local Channels** | **Solo cuando necesites dialplan** |
| **Hardware Detection** | **SÍ**, implementa el script |
| **Max Canales** | ~5-15 simultáneos con tu GPU actual |
| **Scaling Strategy** | Vertical first, horizontal después |

El límite real es tu **GPU** (STT/TTS/LLM), no Asterisk ni las líneas telefónicas.
