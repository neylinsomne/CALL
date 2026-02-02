# Arquitectura, Telefonia y Escalabilidad del AI Call Center

Documento tecnico que cubre la arquitectura de concurrencia, la configuracion de telefonia (Gateway FXO / Carrier Grade), y la integracion con NVIDIA Triton Inference Server para escalar a multiples agentes simultaneos.

---

## 1. Arquitectura General

```
                          +------------------+
                          |   React Dashboard |  :3001
                          |   (Vite + JSX)   |
                          +--------+---------+
                                   |
                                   | HTTP/WS
                                   v
+------------+    HTTP    +--------+---------+    HTTP    +-------------+
|  Asterisk  +----------->+     Backend      +----------->+    LLM      |
|  PBX :5060 |  AudioSocket  FastAPI :8000   |            | LangChain   |
+------------+            |  (Orquestador)   |            | :8003       |
                          +--+-----+-----+---+            +------+------+
                             |     |     |                       |
                     HTTP    |     |     |   HTTP          LM Studio
                             v     v     v                 (host:1234)
                    +------+ +---+ +--------+
                    | STT  | |TTS| | Audio  |
                    |:8002 | |:8001 Preproc |
                    +------+ +---+ |:8004   |
                                   +--------+

                    [--- GPU Services ---]
```

### Servicios

| Servicio | Puerto | Funcion | GPU |
|----------|--------|---------|-----|
| **backend** | 8000 | Orquestador central, WebSockets, API REST | No |
| **stt** | 8002 | Speech-to-Text (Whisper faster-whisper) | Si |
| **tts** | 8001 | Text-to-Speech (F5-TTS Spanish) | Configurable |
| **llm** | 8003 | LLM proxy a LM Studio via LangChain | No |
| **audio_preprocess** | 8004 | DeepFilterNet + SpeechBrain | Si |
| **triton** | 8010-8012 | NVIDIA Triton Inference Server (opcional) | Si |
| **asterisk** | 5060 | PBX SIP/VOIP | No |
| **freepbx** | 8080 | UI de gestion de Asterisk | No |
| **postgres** | 5432 | Base de datos principal | No |
| **dashboard** | 3001 | Frontend React | No |

---

## 2. Modelo de Concurrencia

### Como se manejan multiples llamadas simultaneas

El backend usa **asyncio** con un solo proceso uvicorn. Cada llamada entrante es un WebSocket independiente (`/ws/{conversation_id}`), y cada uno corre como una **coroutine** aislada dentro del mismo event loop.

```
Llamada A  --+
Llamada B  --+--> 1 event loop (1 hilo) --> coroutines alternandose
Llamada C  --+
```

**NO es un hilo por agente** -- es un solo hilo con multiples coroutines cooperativas.

### Flujo por llamada

```
Audio entrante
    |
    v
[Denoise] --> POST http://audio_preprocess:8004/denoise_bytes
    |
    v
[STT]     --> POST http://stt:8002/transcribe (multipart: audio WAV)
    |
    v
[Sentiment] --> Analisis local (keywords, sin I/O)
    |
    v
[LLM]     --> POST http://llm:8003/chat (JSON: conversation_id + text)
    |
    v
[TTS]     --> POST http://tts:8001/synthesize (JSON: text)
    |
    v
Audio de respuesta --> websocket.send_json()
```

Mientras una llamada espera la respuesta del STT (`await http_client.post(...)`), el event loop atiende otras llamadas. Eso es la **concurrencia cooperativa**.

### Aislamiento de sesiones

Las respuestas **nunca se cruzan** porque cada handler de WebSocket mantiene su propia referencia directa al socket del cliente:

- `ConnectionManager.active_connections[conversation_id]` - mapa de WebSockets
- `conversation_memories[conversation_id]` - historial de chat en el LLM
- `conversation_playback_state[conversation_id]` - estado de reproduccion
- `conversation_voice_profiles[conversation_id]` - perfil de voz

El `conversation_id` (UUID) es la clave universal que aisla todo el estado.

### Limitacion: servicios GPU son seriales

STT, TTS y audio_preprocess cargan un modelo en GPU como singleton global. Las llamadas de inferencia son **sincronas y bloqueantes**:

```python
# stt_server.py - bloquea el event loop completo
segments, info = whisper_model.transcribe(audio_array, ...)  # BLOQUEA
```

Si hay 10 llamadas simultaneas y todas mandan audio al STT al mismo tiempo, se procesan **una por una** en serie.

---

## 3. Pagina de Telefonia (/telephony)

### Proposito

Configurar como el sistema recibe llamadas telefonicas. Dos metodos soportados:

1. **Gateway FXO**: Para clientes que ya tienen lineas telefonicas analogicas. Un gateway fisico convierte las lineas a SIP.
2. **Carrier Grade / SIP Trunk**: Desvio de llamadas desde el operador telefonico al servidor SIP.

### Arquitectura de la pagina

```
Telephony.jsx
+-- Banner de estado (Conectado/Desconectado/Error)
+-- Selector de metodo
|   +-- Tarjeta "Gateway FXO" (icono hardware)
|   +-- Tarjeta "Carrier Grade" (icono nube)
+-- Formulario dinamico segun seleccion
|   +-- Campos de configuracion
|   +-- Lista de DIDs (agregar/eliminar numeros)
|   +-- Boton "Probar Conexion"
+-- Boton "Guardar Configuracion"
```

### Endpoints del backend

| Endpoint | Metodo | Funcion |
|----------|--------|---------|
| `/api/config/telephony` | GET | Obtener configuracion actual |
| `/api/config/telephony/save` | POST | Guardar config (JSON + .env + Asterisk) |
| `/api/config/telephony/test` | POST | Probar conectividad SIP via TCP socket |

### Modelos de datos

```python
class DIDNumber(BaseModel):
    number: str = ""        # "+5215512345678"
    label: str = ""         # "Linea Principal"
    active: bool = True

class FXOGatewayConfig(BaseModel):
    ip: str = ""
    sip_port: int = 5060
    user: str = "gateway"
    password: str = ""
    fxo_ports: int = 4
    codec: str = "ulaw"     # ulaw, alaw, g729
    dids: List[DIDNumber] = []

class CarrierGradeConfig(BaseModel):
    host: str = ""
    user: str = ""
    password: str = ""
    outbound_caller_id: str = ""
    auth_type: str = "register"  # "register" | "ip_auth"
    dids: List[DIDNumber] = []

class TelephonyReceptionConfig(BaseModel):
    method: str = ""  # "fxo_gateway" | "carrier_grade"
    fxo_gateway: Optional[FXOGatewayConfig]
    carrier_grade: Optional[CarrierGradeConfig]
```

### Integracion con el wizard

El Configuration Wizard (Step 1 - Telefonia) incluye un link "Configuracion Avanzada de Telefonia" que lleva a `/telephony` para configuraciones detalladas.

---

## 4. Escalabilidad: NVIDIA Triton Inference Server

### Problema

Con 1 GPU (RTX 5060 Ti, 8GB VRAM) y 10 agentes simultaneos, el STT se convierte en cuello de botella porque procesa un audio a la vez.

```
Agente 1: --STT 60ms--
Agente 2:              --STT 60ms--
...
Agente 10:                                                    --STT 60ms--
Total: 600ms para procesar todos (serial)
```

### Solucion: Triton con Python Backend

Triton carga **2 instancias** de Whisper small en GPU (0.5GB cada una), permitiendo 2 transcripciones en paralelo real.

```
CON TRITON (10 agentes, 2 instancias):
  Instancia 1: [A1]--[A3]--[A5]--[A7]--[A9]--
  Instancia 2: [A2]--[A4]--[A6]--[A8]--[A10]-
  Total: ~300ms para procesar todos
```

### Presupuesto VRAM

| Componente | VRAM |
|-----------|------|
| LM Studio (LLM) | ~3.0 GB |
| Triton Whisper small x2 | ~1.0 GB |
| Overhead CUDA | ~0.5 GB |
| **Total** | **~4.5 GB de 8 GB** |

TTS se mueve a CPU para liberar VRAM (el i9-14900K con 24 cores lo maneja).

### Estructura de archivos de Triton

```
services/triton/
+-- Dockerfile                    # nvcr.io/nvidia/tritonserver:24.01-py3
+-- model_repository/
    +-- whisper_stt/
        +-- config.pbtxt          # 2 instancias GPU, input/output BYTES
        +-- 1/
            +-- model.py          # Python Backend: WhisperModel + transcribe
```

### Flujo de datos con Triton

```
10 Agentes (WebSocket)
    |
    v
Backend (main.py) --POST /transcribe--> STT Service (stt_server.py)
                                              |
                                    USE_TRITON=true?
                                      |          |
                                     Si          No
                                      |          |
                                      v          v
                              Triton Server    Modelo local
                             +--------------+  (como siempre)
                             | Instancia 1  |
                             | Whisper small |
                             +--------------+
                             | Instancia 2  |
                             | Whisper small |
                             +--------------+
                             2 audios en paralelo
```

### Modo de operacion

El STT service actua como **adaptador transparente**. El backend no necesita cambios.

- `USE_TRITON=false` (default): STT carga Whisper localmente como siempre
- `USE_TRITON=true`: STT delega a Triton via HTTP API V2
- **Fallback automatico**: Si Triton cae, STT carga el modelo local

### Como activar Triton

```bash
# 1. En .env, cambiar:
USE_TRITON=true

# 2. Levantar con el perfil triton:
docker compose --profile triton up -d

# 3. Verificar que Triton esta listo:
curl http://localhost:8010/v2/health/ready
# {"live":true}

# 4. Verificar que STT usa Triton:
curl http://localhost:8002/health
# {"triton_mode": true, "triton_url": "http://triton:8010", ...}
```

### Config de Triton (config.pbtxt)

```protobuf
name: "whisper_stt"
backend: "python"
max_batch_size: 0              # faster-whisper no soporta batch

instance_group [
  {
    count: 2                   # 2 instancias en paralelo
    kind: KIND_GPU
    gpus: [ 0 ]
  }
]

input [
  { name: "audio_bytes",      datatype: TYPE_STRING, dims: [1] },
  { name: "language",         datatype: TYPE_STRING, dims: [1], optional: true },
  { name: "word_timestamps",  datatype: TYPE_BOOL,   dims: [1], optional: true }
]

output [
  { name: "result_json",      datatype: TYPE_STRING, dims: [1] }
]
```

### Variables de entorno relacionadas

```env
# Activar Triton
USE_TRITON=true

# Modelo para Triton (small usa menos VRAM, permite mas instancias)
TRITON_STT_MODEL=small
TRITON_COMPUTE_TYPE=float16

# Puertos (no conflictan con servicios existentes)
TRITON_HTTP_PORT=8010
TRITON_GRPC_PORT=8011
TRITON_METRICS_PORT=8012

# TTS en CPU para liberar VRAM
TTS_DEVICE=cpu
```

---

## 5. Opciones de Escalado sin Triton

Para quienes no quieran usar Triton, hay alternativas:

### Opcion A: Modelos mas pequenos (solo cambiar .env)

```env
STT_MODEL=small    # 0.5GB en vez de 3GB, 60ms en vez de 200ms
```

Con Whisper small, 10 agentes en el peor caso: 10 x 60ms = 600ms.

### Opcion B: CPU para TTS, GPU para STT

```env
TTS_DEVICE=cpu     # Libera ~1.5GB de VRAM
STT_DEVICE=cuda    # Mantiene GPU para lo critico
STT_MODEL=medium   # 1.5GB, buen balance calidad/velocidad
```

### Opcion C: Replicas Docker + nginx

```yaml
stt:
  deploy:
    replicas: 3
  environment:
    - DEVICE=cpu
    - STT_MODEL=small
    - OMP_NUM_THREADS=4
```

Con 3 replicas CPU y nginx como load balancer, se procesan 3 transcripciones en paralelo real.

---

## 6. Archivos Modificados/Creados

### Telefonia

| Archivo | Tipo | Descripcion |
|---------|------|-------------|
| `services/dashboard/src/pages/Telephony.jsx` | Nuevo | Pagina de configuracion de telefonia |
| `services/dashboard/src/App.jsx` | Mod | Ruta `/telephony` |
| `services/dashboard/src/components/Sidebar.jsx` | Mod | Item "Telefonia" en navegacion |
| `services/dashboard/src/pages/ConfigurationWizard.jsx` | Mod | Link a config avanzada de telefonia |
| `services/backend/config_manager.py` | Mod | Modelos y endpoints de telefonia |

### Triton

| Archivo | Tipo | Descripcion |
|---------|------|-------------|
| `services/triton/Dockerfile` | Nuevo | Container Triton Server |
| `services/triton/model_repository/whisper_stt/config.pbtxt` | Nuevo | Config del modelo |
| `services/triton/model_repository/whisper_stt/1/model.py` | Nuevo | Python Backend Whisper |
| `services/stt/stt_server.py` | Mod | Modo Triton + fallback |
| `services/stt/requirements.txt` | Mod | Agregado httpx |
| `docker-compose.yml` | Mod | Servicio triton, TTS sin GPU |
| `.env` | Mod | Variables Triton, TTS_DEVICE=cpu |

### Fixes de estabilidad

| Archivo | Tipo | Descripcion |
|---------|------|-------------|
| `services/backend/database.py` | Mod | Fix `metadata` reservado en SQLAlchemy |
| `services/backend/main.py` | Mod | Fix import `Dict` faltante |

---

## 7. Hardware de Referencia

Especificaciones del equipo de desarrollo y pruebas:

| Componente | Especificacion |
|-----------|---------------|
| CPU | Intel Core i9-14900K (24 cores / 32 hilos) |
| RAM | 64 GB DDR5 |
| GPU | NVIDIA GeForce RTX 5060 Ti (8 GB VRAM) |
| OS | Windows 11 + Docker Desktop (WSL2) |

### Capacidad estimada por configuracion

| Configuracion | Agentes simultaneos | Latencia STT (peor caso) |
|--------------|--------------------|-----------------------|
| Whisper large-v3, 1 instancia | 3-5 | ~600ms-1s |
| Whisper small, 1 instancia | 5-8 | ~300-500ms |
| Triton + Whisper small x2 | 8-12 | ~150-300ms |
| Triton + Whisper small x3 | 12-15 | ~100-200ms |
| Replicas CPU x3 (Whisper small) | 10-15 | ~200-400ms |
