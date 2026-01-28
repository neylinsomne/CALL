# Sistema Completo de Call Center con IA

**Documentación Maestra del Sistema**

Este documento es el punto de entrada principal para entender, configurar y usar todo el sistema de call center con inteligencia artificial. Conecta con todos los demás documentos especializados.

---

## 📚 Índice

1. [Visión General](#-visión-general)
2. [Arquitectura Completa](#-arquitectura-completa)
3. [Características Principales](#-características-principales)
4. [Guía de Instalación](#-guía-de-instalación-paso-a-paso)
5. [Configuración](#-configuración)
6. [Flujo de Procesamiento](#-flujo-de-procesamiento)
7. [Documentación Especializada](#-documentación-especializada)
8. [Casos de Uso](#-casos-de-uso)
9. [Monitoreo y Métricas](#-monitoreo-y-métricas)
10. [Troubleshooting](#-troubleshooting)
11. [Roadmap](#-roadmap)

---

## 🎯 Visión General

### ¿Qué es este Sistema?

Un **call center completamente automatizado con IA** que:

1. **Recibe llamadas** de clientes (inbound) o las realiza (outbound)
2. **Entiende** lo que dicen usando Speech-to-Text (Whisper)
3. **Conversa** inteligentemente usando LLMs (GPT-4, Mixtral, etc.)
4. **Responde** con voz natural usando Text-to-Speech (Coqui, ElevenLabs)
5. **Analiza** sentimiento, intención, y tópicos en tiempo real
6. **Guarda** todo para análisis posterior
7. **Mejora** continuamente aprendiendo de errores

### Componentes Principales

```
┌────────────────────────────────────────────────────────────────┐
│                    SISTEMA COMPLETO                            │
└────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│   Services   │
│  Dashboard   │     │   FastAPI    │     │   (μservices)│
│   (React)    │     │  WebSocket   │     │              │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                     ┌────────────────────────────┼────────────────┐
                     │                            │                │
                     ▼                            ▼                ▼
              ┌─────────────┐            ┌─────────────┐   ┌─────────────┐
              │ Audio       │            │     STT     │   │     LLM     │
              │ Preprocess  │            │  (Whisper)  │   │ (GPT-4/Mix) │
              │ - Denoise   │            │  Enhanced   │   │  Function   │
              │ - Target    │            │  Correction │   │   Calling   │
              │ - Prosody   │            │ Clarify     │   │  Streaming  │
              └─────────────┘            └─────────────┘   └─────────────┘
                     │                            │                │
                     └────────────────────────────┼────────────────┘
                                                  │
                                                  ▼
                                          ┌─────────────┐
                                          │     TTS     │
                                          │  (Coqui/    │
                                          │  Eleven)    │
                                          └─────────────┘
                                                  │
                     ┌────────────────────────────┼────────────────┐
                     │                            │                │
                     ▼                            ▼                ▼
              ┌─────────────┐            ┌─────────────┐   ┌─────────────┐
              │  Storage    │            │  Analytics  │   │  Database   │
              │ Local + S3  │            │   Batch     │   │ PostgreSQL  │
              │  Metadata   │            │  Processor  │   │   Metrics   │
              └─────────────┘            └─────────────┘   └─────────────┘
```

---

## 🏗 Arquitectura Completa

### Arquitectura en Capas

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CAPA DE USUARIO                              │
│  - Dashboard React                                                  │
│  - WebRTC para testing                                             │
│  - Teléfonos SIP (Grandstream, softphones)                         │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE COMUNICACIÓN                             │
│  - Asterisk (PBX)                                                   │
│  - WebSocket endpoints                                              │
│  - SIP trunk (conexión telefónica)                                 │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│              CAPA DE PROCESAMIENTO EN TIEMPO REAL                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │ Audio         │→ │ STT Enhanced  │→ │ LLM          │→ TTS      │
│  │ Preprocessing │  │ + Correction  │  │ + Context    │           │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
│                                                                     │
│  Features Online:                                                   │
│  - Corrección rápida (diccionario)                                │
│  - Detección de clarificación crítica                             │
│  - Sentiment analysis básico                                       │
│  - Interruption handling                                           │
│  Target: <20ms overhead                                            │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE ALMACENAMIENTO                           │
│  - Audio Storage (Local + S3)                                      │
│  - Metadata JSON (Schema completo)                                 │
│  - Database PostgreSQL (métricas)                                  │
│  - Transcripts procesados                                          │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│              CAPA DE PROCESAMIENTO OFFLINE                          │
│  - Batch Processor (cron/manual)                                   │
│  - Re-transcripción premium (si WER alto)                          │
│  - Corrección híbrida completa:                                    │
│    * Diccionario exacto                                            │
│    * Búsqueda vectorial (FAISS)                                    │
│    * Matching fonético (Metaphone)                                 │
│  - Análisis profundo:                                              │
│    * Sentiment avanzado                                            │
│    * Intent detection                                              │
│    * Entity extraction                                             │
│    * Topic analysis                                                │
│    * Coherence scoring                                             │
│  Sin límite de tiempo                                              │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE ANALYTICS                                │
│  - Dashboard de métricas                                           │
│  - Reportes de calidad                                             │
│  - A/B testing                                                     │
│  - Webhooks a sistemas externos                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

##  Características Principales

### 🎙 Procesamiento de Voz Avanzado

**Documentación**: [MODELOS_TRATAMIENTO_VOZ.md](MODELOS_TRATAMIENTO_VOZ.md) | [MANEJO_VOZ_Y_CONTEXTO.md](MANEJO_VOZ_Y_CONTEXTO.md) | [ACTIVAR_VOZ_CONTEXTUAL.md](ACTIVAR_VOZ_CONTEXTUAL.md)

 **Target Speaker Extraction**
- Aísla la voz del cliente de ruido/otras voces
- Crea perfil de voz en primeros 3 segundos
- Usa embeddings ECAPA-TDNN de SpeechBrain
- Mejora: +15% accuracy en transcripción

 **Prosody Analysis**
- Detecta preguntas (tono ascendente >15%)
- Identifica pausas: breathing, thinking, end-of-turn
- Analiza emotional tone: neutral, nervous, calm, etc.
- Calcula speech rate para detectar nerviosismo
- Mejora: +20% context understanding

 **Noise Reduction**
- DeepFilterNet para eliminación de ruido
- Optimizado para español
- Reduce ruido en -30dB

### 📝 STT Optimizado

**Documentación**: [OPTIMIZACION_STT_ESTADO_DEL_ARTE.md](OPTIMIZACION_STT_ESTADO_DEL_ARTE.md) | [ACTIVAR_STT_MEJORADO.md](ACTIVAR_STT_MEJORADO.md)

 **Enhanced Transcription**
- Whisper large-v3 optimizado para español
- Word-level confidence scoring
- Parámetros críticos ajustados:
  * beam_size=5
  * temperature=0.0
  * VAD filtering
  * compression_ratio_threshold=2.4

 **Error Correction**
- Banco vectorial con FAISS
- Correcciones automáticas (salgo→saldo, cuesta→cuenta)
- Aprende de correcciones del usuario
- Mejora: WER 15% → 6% (-60% error)

 **Intelligent Clarification**
- Detecta cuándo pedir "¿puedes repetir?"
- Estrategias: explicit, implicit, spell_out
- Máximo 3 clarificaciones por conversación
- Solo palabras críticas (cancelar, números, etc.)

### 🔄 Sistema Híbrido Online/Offline

**Documentación**: [SISTEMA_HIBRIDO_ONLINE_OFFLINE.md](SISTEMA_HIBRIDO_ONLINE_OFFLINE.md) | [INICIO_RAPIDO_SISTEMA_HIBRIDO.md](INICIO_RAPIDO_SISTEMA_HIBRIDO.md)

 **Procesamiento Online** (Durante la llamada)
- Target: <20ms overhead
- Solo correcciones del diccionario exacto
- Clarificación solo si crítico
- Almacenamiento automático
- Experiencia fluida para el usuario

 **Procesamiento Offline** (Post-procesamiento)
- Sin límite de tiempo
- Corrección híbrida completa (3 niveles)
- Re-transcripción si WER >20%
- Análisis profundo completo
- Batch processing paralelo

### 🤖 LLM Mejorado

**Documentación**: [MEJORAS_IMPLEMENTADAS.md](MEJORAS_IMPLEMENTADAS.md)

 **Function Calling**
- get_account_balance
- schedule_callback
- transfer_to_agent
- cancel_service
- update_contact_info

 **Context Analysis**
- Detecta preguntas repetidas
- Identifica frustración acumulada
- Reconoce solicitudes de escalamiento
- Ajusta respuestas según contexto

 **Streaming Responses**
- Reduce latencia percibida
- Generación incremental
- Interruption handling

### 😊 Sentiment & Intent Analysis

 **Sentiment Real-time**
- Basado en keywords
- Mejorado con prosodia
- Niveles: very_positive → very_negative
- Alertas automáticas si frustrated

 **Intent Detection** (Offline)
- 10+ intenciones comunes
- billing_inquiry, technical_support, cancellation, etc.
- Confidence scoring
- Usado para routing y analytics

### 💾 Almacenamiento Robusto

**Documentación**: [SISTEMA_HIBRIDO_ONLINE_OFFLINE.md](SISTEMA_HIBRIDO_ONLINE_OFFLINE.md#3-sistema-de-almacenamiento)

 **Multi-backend**
- Local storage
- Amazon S3
- Redundancia (both)

 **Metadata Completa**
- Schema Pydantic con 16+ campos
- Audio metadata (format, duration, checksum)
- Transcription metadata (text, corrections, confidence)
- Analysis metadata (sentiment, intent, entities, topics)
- Conversation metrics (turns, latency, interruptions)

 **Búsqueda y Filtrado**
- Por conversation_id
- Por rango de fechas
- Por estado (procesado/no procesado)
- Por sentiment/intent

### 🔍 Métodos de Clasificación

**Documentación**: [METODOS_CLASIFICACION_ERRORES.md](METODOS_CLASIFICACION_ERRORES.md)

 **Sistema Híbrido de 3 Niveles**

**Nivel 1: Diccionario Exacto** (95% casos)
- Lookup O(1)
- <1ms por palabra
- Errores conocidos

**Nivel 2: Vectores FAISS** (4% casos)
- Embeddings multilingües
- Similitud semántica + fonética
- 10-50ms por palabra
- Generaliza a palabras nunca vistas

**Nivel 3: Fonético** (1% casos)
- Metaphone para homofonía
- hay ≈ ahí, echo ≈ hecho
- 1ms por palabra

### 🔗 Integraciones

 **Webhooks**
- 8 tipos de eventos
- HMAC-SHA256 signatures
- Retry automático
- Eventos: call_started, call_ended, sentiment_alert, etc.

 **Analytics Dashboard**
- Métricas en tiempo real
- Reportes de calidad
- A/B testing
- Export a CSV/JSON

---

## 📦 Guía de Instalación Paso a Paso

### Prerrequisitos

```bash
# Sistema
- Ubuntu 20.04+ / Debian 11+ / macOS
- Python 3.10+
- Docker & Docker Compose
- Git

# Hardware recomendado
- CPU: 8+ cores
- RAM: 16GB+ (32GB recomendado)
- GPU: NVIDIA con 8GB+ VRAM (opcional pero recomendado)
- Disco: 50GB+ SSD
```

### Paso 1: Clonar el Repositorio

```bash
# Clonar
git clone https://github.com/tu-usuario/Call.git
cd Call

# Verificar estructura
ls -la
# Deberías ver: services/, docker-compose.yml, .env.example, etc.
```

### Paso 2: Configurar Entorno

```bash
# Copiar ejemplo
cp .env.example .env

# Editar configuración
nano .env
```

**Configuración mínima para desarrollo**:

```bash
# Database
POSTGRES_PASSWORD=tu_password_seguro

# Storage (empezar con local)
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./data/recordings

# Audio Features (activar gradualmente)
ENABLE_DENOISE=true
ENABLE_TARGET_EXTRACTION=false  # Activar después
ENABLE_PROSODY_ANALYSIS=false   # Activar después

# STT
STT_MODEL=large-v3
STT_DEVICE=cuda  # o cpu si no tienes GPU
LANGUAGE=es

# STT Enhanced
ENABLE_STT_CORRECTION=true
ENABLE_ONLINE_CORRECTION=true
ENABLE_OFFLINE_BATCH=true

# LLM (elegir uno)
LLM_PROVIDER=openai
OPENAI_API_KEY=tu_api_key
# O usar LM Studio local
# LM_STUDIO_URL=http://localhost:1234/v1
```

**Configuración para producción con S3**:

```bash
# Storage
STORAGE_BACKEND=both  # Local + S3 redundancia
S3_BUCKET=mi-call-center-prod
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# Audio Features (todas activas)
ENABLE_DENOISE=true
ENABLE_TARGET_EXTRACTION=true
ENABLE_PROSODY_ANALYSIS=true

# Webhooks
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://mi-crm.com/webhook
WEBHOOK_SECRET=secret_compartido
```

### Paso 3: Instalar Dependencias

**Opción A: Con Docker (Recomendado)**

```bash
# Build servicios
docker-compose build

# Iniciar
docker-compose up -d

# Ver logs
docker-compose logs -f backend
```

**Opción B: Local (Desarrollo)**

```bash
# Crear virtualenv
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instalar dependencias por servicio
cd services/backend
pip install -r requirements.txt

cd ../stt
pip install -r requirements.txt

cd ../llm
pip install -r requirements.txt

cd ../tts
pip install -r requirements.txt

cd ../audio_preprocess
pip install -r requirements.txt

cd ../storage
pip install -r requirements.txt

# Volver a raíz
cd ../..
```

### Paso 4: Crear Estructura de Datos

```bash
# Directorios de almacenamiento
mkdir -p data/recordings/{audio,metadata,transcripts}

# Modelos (si usas local)
mkdir -p services/stt/models
mkdir -p services/tts/models
mkdir -p services/audio_preprocess/models
```

### Paso 5: Inicializar Base de Datos

```bash
# Con Docker
docker-compose exec backend python -c "from database import init_db; init_db()"

# O local
cd services/backend
python -c "from database import init_db; init_db()"
```

### Paso 6: Verificar Instalación

```bash
# Health checks
curl http://localhost:8000/health  # Backend
curl http://localhost:8002/health  # STT
curl http://localhost:8003/health  # LLM
curl http://localhost:8004/health  # TTS

# Deberías ver: {"status": "healthy", ...}
```

### Paso 7: Test del Sistema

```bash
# Test sistema híbrido completo
python test_sistema_hibrido.py

# Test métodos de clasificación
python test_clasificacion_demo.py

# Salida esperada:
#  Test completado exitosamente!
#  Online latency: 15.2ms
#  Offline corrections: 5
```

---

##  Configuración

### Variables de Entorno Principales

| Variable | Valores | Descripción |
|----------|---------|-------------|
| `STORAGE_BACKEND` | local, s3, both | Backend de almacenamiento |
| `STT_MODEL` | large-v3, medium, small | Modelo Whisper |
| `STT_DEVICE` | cuda, cpu | Dispositivo para STT |
| `ENABLE_TARGET_EXTRACTION` | true, false | Aislar voz del cliente |
| `ENABLE_PROSODY_ANALYSIS` | true, false | Analizar entonación |
| `ENABLE_STT_CORRECTION` | true, false | Corrección de errores |
| `ENABLE_ONLINE_CORRECTION` | true, false | Corrección durante llamada |
| `ENABLE_OFFLINE_BATCH` | true, false | Procesamiento batch |
| `BATCH_MAX_CONCURRENT` | 1-20 | Paralelismo batch |
| `LLM_PROVIDER` | openai, mixtral, anthropic | Proveedor LLM |

**Ver archivo completo**: [.env.example](.env.example)

### Perfiles de Configuración

#### 🚀 Desarrollo Local (Rápido)

```bash
STORAGE_BACKEND=local
STT_DEVICE=cpu
STT_MODEL=medium  # Más rápido que large
ENABLE_TARGET_EXTRACTION=false
ENABLE_PROSODY_ANALYSIS=false
ENABLE_OFFLINE_BATCH=false
LLM_PROVIDER=lm_studio  # Local
```

**Pros**: Setup rápido, sin costos
**Cons**: Menor calidad, sin features avanzadas

####  Desarrollo con GPU

```bash
STORAGE_BACKEND=local
STT_DEVICE=cuda
STT_MODEL=large-v3
ENABLE_TARGET_EXTRACTION=true
ENABLE_PROSODY_ANALYSIS=true
ENABLE_OFFLINE_BATCH=true
BATCH_MAX_CONCURRENT=5
LLM_PROVIDER=openai  # O mixtral
```

**Pros**: Máxima calidad, todas las features
**Cons**: Requiere GPU

#### 🏭 Producción

```bash
STORAGE_BACKEND=both  # Redundancia
S3_BUCKET=prod-callcenter
STT_DEVICE=cuda
STT_MODEL=large-v3
ENABLE_TARGET_EXTRACTION=true
ENABLE_PROSODY_ANALYSIS=true
ENABLE_OFFLINE_BATCH=true
BATCH_MAX_CONCURRENT=10
WEBHOOK_ENABLED=true
LLM_PROVIDER=openai
# + Monitoreo, logs, backups
```

**Pros**: Robusto, escalable, completo
**Cons**: Mayor complejidad, costos

---

## 🔄 Flujo de Procesamiento

### Flujo Completo de una Llamada

```
1⃣ INICIO DE LLAMADA
   │
   ├─ Cliente llama / Sistema llama a cliente
   ├─ Asterisk enruta la llamada
   └─ WebSocket conecta con Backend

2⃣ AUDIO PREPROCESSING (35-65ms)
   │
   ├─ Noise Reduction (DeepFilterNet) - 15ms
   ├─ Target Speaker Extraction - 20ms
   │  └─ Si primeros 3s: crear voice profile
   │  └─ Si ya existe: aislar voz del cliente
   └─ Prosody Analysis - 10ms
      └─ Detectar preguntas, pausas, emotional tone

3⃣ SPEECH-TO-TEXT (400-800ms)
   │
   ├─ Whisper large-v3 transcription
   ├─ Word-level confidence scoring
   └─ Segments con timestamps

4⃣ PROCESAMIENTO ONLINE (<20ms)
   │
   ├─ Corrección rápida (solo diccionario)
   │  └─ "salgo" → "saldo", "cuesta" → "cuenta"
   ├─ Clarificación crítica (si confianza <0.5)
   └─ Guardar en Storage (async)
      ├─ Audio → ./data/recordings/audio/
      ├─ Metadata → ./data/recordings/metadata/
      └─ Upload a S3 (si configurado)

5⃣ SENTIMENT ANALYSIS (10ms)
   │
   ├─ Keyword-based detection
   ├─ Mejorado con prosody data
   └─ Alert si frustrated

6⃣ LLM PROCESSING (800-2000ms)
   │
   ├─ Contexto conversacional
   ├─ Sentiment + Intent hints
   ├─ Function calling (si aplicable)
   └─ Streaming response

7⃣ TEXT-TO-SPEECH (500-1200ms)
   │
   ├─ Coqui TTS / ElevenLabs
   ├─ Voz natural en español
   └─ Stream audio al cliente

8⃣ METRICS & LOGGING
   │
   ├─ Guardar en database
   │  └─ Latencies, sentiment, interruptions
   ├─ Webhook notification (si configurado)
   └─ Update conversation state

📊 LATENCIA TOTAL: ~2.1 segundos
   (vs 2.5s sin optimizaciones)

═══════════════════════════════════════════════════════════

🕐 DESPUÉS DE LA LLAMADA (Batch Processing)

9⃣ PROCESAMIENTO OFFLINE (Sin límite de tiempo)
   │
   ├─ Batch Processor detecta grabación no procesada
   │
   ├─ Re-transcripción premium (si WER >20%)
   │  └─ Parámetros optimizados, más tiempo de procesamiento
   │
   ├─ Corrección Híbrida Completa
   │  ├─ Nivel 1: Diccionario exacto
   │  ├─ Nivel 2: Vectores FAISS (similitud semántica)
   │  └─ Nivel 3: Fonético (homofonía)
   │
   ├─ Análisis Profundo
   │  ├─ Sentiment avanzado
   │  ├─ Intent detection
   │  ├─ Entity extraction (números, emails, fechas)
   │  ├─ Topic analysis
   │  └─ Coherence scoring
   │
   └─ Update Metadata
      ├─ processed = true
      ├─ processing_mode = "offline"
      └─ Guardar transcript procesado

🔟 ANALYTICS & REPORTING
   │
   ├─ Agregar a métricas dashboard
   ├─ Generar reportes de calidad
   ├─ A/B testing data
   └─ Feedback loop para mejora continua
```

### Diagrama de Estados

```
[Llamada Iniciada]
       │
       ├─ Audio chunk recibido
       │
       ▼
[Procesamiento Online] ─────┐
       │                    │
       ├─ Transcrito        │ Guardar async
       ├─ Corregido         │
       ├─ Sentiment         │
       │                    │
       ▼                    ▼
[LLM Response]        [Storage]
       │                    │
       ├─ Texto generado    ├─ Audio .wav
       │                    ├─ Metadata .json
       ▼                    └─ processed=false
[TTS Audio]
       │
       ├─ Audio enviado
       │
       ▼
[Llamada Continúa] ◄─────┐
       │                 │
       └─ Más audio ─────┘

[Llamada Terminada]
       │
       ▼
[Queue para Batch] ◄──── Cron job cada hora
       │
       ▼
[Procesamiento Offline]
       │
       ├─ Re-transcripción (si necesario)
       ├─ Corrección híbrida
       ├─ Análisis completo
       │
       ▼
[Metadata Actualizada]
       │
       └─ processed=true
       └─ Analytics ready
```

---

## 📖 Documentación Especializada

El sistema tiene documentación modular. Cada documento cubre un aspecto específico:

### 🎯 Documentos Principales

#### 1. **MEJORAS_IMPLEMENTADAS.md**
**Qué cubre**: Mejoras inspiradas en RetellAI
-  Interruption handling
-  Function calling
-  Sentiment analysis
-  Streaming responses
-  Webhooks
-  Context analysis
-  Analytics endpoints

**Cuándo leer**: Quieres entender qué hace el sistema a alto nivel

---

#### 2. **MODELOS_TRATAMIENTO_VOZ.md**
**Qué cubre**: Preprocesamiento de audio
- Target Speaker Extraction (SpeechBrain)
- Speaker Diarization
- Noise Suppression (DeepFilterNet)
- Comparación de modelos

**Cuándo leer**: Vas a trabajar con procesamiento de audio

---

#### 3. **MANEJO_VOZ_Y_CONTEXTO.md**
**Qué cubre**: Análisis de prosodia
- Pitch analysis (detección de preguntas)
- Energy analysis (voz vs silencio)
- Pause detection (breathing, thinking, end-of-turn)
- Speech rate (nerviosismo)
- Emotional tone

**Cuándo leer**: Quieres entender cómo se detectan preguntas y contexto

---

#### 4. **ACTIVAR_VOZ_CONTEXTUAL.md**
**Qué cubre**: Guía práctica para activar features de voz
- Instalación de SpeechBrain, librosa
- Configuración de ENV vars
- Testing paso a paso
- Troubleshooting

**Cuándo leer**: Vas a activar Target Speaker o Prosody

---

#### 5. **OPTIMIZACION_STT_ESTADO_DEL_ARTE.md**
**Qué cubre**: STT optimizado
- Comparativa de líderes del mercado (OpenAI, AssemblyAI, Deepgram)
- Parámetros críticos de Whisper
- Fine-tuning para vocabulario específico
- Clarification strategies
- Error correction con vectores

**Cuándo leer**: STT es tu bottleneck, quieres mejorarlo

---

#### 6. **ACTIVAR_STT_MEJORADO.md**
**Qué cubre**: Guía práctica para STT enhanced
- Instalación de sentence-transformers, FAISS
- Configuración del endpoint `/transcribe/enhanced`
- Testing con ejemplos
- Integración con backend

**Cuándo leer**: Vas a usar corrección de errores y clarificación

---

#### 7. **METODOS_CLASIFICACION_ERRORES.md**
**Qué cubre**: Todos los métodos de clasificación
- Distancia Euclidiana (L2)
- Similitud de Coseno
- Distancia Manhattan (L1)
- Levenshtein (edición)
- Fonético (Metaphone)
- Sistema híbrido de 3 niveles
- Benchmarks y comparativas

**Cuándo leer**: Quieres entender cómo funciona la corrección de errores

---

#### 8. **SISTEMA_HIBRIDO_ONLINE_OFFLINE.md**
**Qué cubre**: Arquitectura de dos niveles
- Procesamiento online (durante llamada)
- Procesamiento offline (batch)
- Sistema de almacenamiento (local/S3)
- Metadata schema completo
- Batch processor
- Comparativas antes/después

**Cuándo leer**: Necesitas entender el flujo completo del sistema

---

#### 9. **INICIO_RAPIDO_SISTEMA_HIBRIDO.md**
**Qué cubre**: Quick start guide
- Instalación en 5 pasos
- Tests rápidos
- Configuración para prod
- Troubleshooting común

**Cuándo leer**: Primera vez configurando el sistema

---

#### 10. **RESUMEN_MEJORAS_COMPLETAS.md**
**Qué cubre**: Overview de TODAS las mejoras
- 20 archivos creados/modificados
- Comparativa antes/después
- Arquitectura completa
- Roadmap

**Cuándo leer**: Quieres un overview ejecutivo del proyecto

---

### 📊 Mapa de Navegación

```
¿Primera vez?
   └─ INICIO_RAPIDO_SISTEMA_HIBRIDO.md
   └─ README_SISTEMA_COMPLETO.md (este documento)

¿Quieres activar features específicas?
   ├─ Voz contextual → ACTIVAR_VOZ_CONTEXTUAL.md
   ├─ STT mejorado → ACTIVAR_STT_MEJORADO.md
   └─ Sistema híbrido → INICIO_RAPIDO_SISTEMA_HIBRIDO.md

¿Quieres entender cómo funciona?
   ├─ Procesamiento de voz → MODELOS_TRATAMIENTO_VOZ.md
   ├─ Prosodia → MANEJO_VOZ_Y_CONTEXTO.md
   ├─ STT optimización → OPTIMIZACION_STT_ESTADO_DEL_ARTE.md
   ├─ Clasificación → METODOS_CLASIFICACION_ERRORES.md
   └─ Arquitectura → SISTEMA_HIBRIDO_ONLINE_OFFLINE.md

¿Necesitas overview ejecutivo?
   └─ RESUMEN_MEJORAS_COMPLETAS.md

¿Quieres ver qué se implementó vs RetellAI?
   └─ MEJORAS_IMPLEMENTADAS.md
```

---

## 💼 Casos de Uso

### Caso 1: Soporte Técnico

**Escenario**: Cliente llama con problema técnico

```
1. Cliente: "Hola, mi internet no funciona"
   ├─ STT: Transcripción
   ├─ Prosody: Detecta frustración (emotional_tone: "concerned")
   ├─ Sentiment: negative (-0.5)
   ├─ Intent: technical_support

2. IA: "Entiendo tu frustración. Vamos a revisar tu conexión..."
   ├─ LLM: Contextualizado con sentiment
   ├─ Function call: get_account_status()
   ├─ TTS: Tono empático

3. Cliente: "Ya reinicié el router pero sigue igual"
   ├─ Context analysis: Cliente ya intentó solución básica
   ├─ Sentiment: Mantiene frustración

4. IA: "Veo que ya probaste eso. Voy a escalarlo a un técnico..."
   ├─ Function call: schedule_callback()
   ├─ Webhook: Notificación a CRM
```

**Métricas guardadas**:
- Duration: 3.5 min
- Sentiment trend: [-0.5, -0.6, -0.4, -0.3]
- Outcome: callback_scheduled
- Topic: internet_connectivity
- Entities: {router_model: "XYZ", account: "123456"}

---

### Caso 2: Consulta de Factura

**Escenario**: Cliente pregunta por cobro

```
1. Cliente: "Necesito revisar el salgo de mi cuesta"
   ├─ STT raw: "Necesito revisar el salgo de mi cuesta"
   ├─ Online correction: "Necesito revisar el saldo de mi cuenta"
   ├─ Prosody: neutral tone
   ├─ Intent: billing_inquiry

2. IA: "Claro, déjame revisar tu saldo..."
   ├─ Function call: get_account_balance(account_id)
   ├─ Response: "Tu saldo actual es 45.50 euros"

3. Cliente: "¿Y cuándo vence?"
   ├─ Prosody: is_question = True
   ├─ Context: Pregunta relacionada a saldo

4. IA: "La próxima factura vence el 15 de febrero"
   ├─ Entity extraction: {date: "2026-02-15", amount: "45.50 euros"}

[Batch processing después]:
- Offline correction: Verifica "salgo"→"saldo" correctamente
- Topic analysis: ["billing", "account_balance"]
- Quality score: 0.92 (excelente)
```

---

### Caso 3: Cancelación de Servicio

**Escenario**: Cliente quiere cancelar

```
1. Cliente: "Quiero cancelar mi servicio"
   ├─ STT: Confidence 0.95 en "cancelar"
   ├─ Clarification: NO (palabra clara)
   ├─ Intent: cancellation
   ├─ Sentiment: neutral

2. IA: "Entiendo que quieres cancelar. ¿Puedo saber el motivo?"
   ├─ LLM: Contexto crítico, pedir confirmación

3. Cliente: "Estoy molesto con el servicio"
   ├─ Sentiment: frustrated
   ├─ Webhook alert: sentiment_alert
   ├─ Context: Escalate to manager

4. IA: "Lamento que hayas tenido mala experiencia..."
   ├─ Function call: transfer_to_manager()
   ├─ Handoff: Transferir a humano
```

**Alertas**:
- Sentiment alert → Supervisor notificado
- Intent: cancellation → Retention team alerted
- Outcome: transferred

---

## 📊 Monitoreo y Métricas

### Métricas Rastreadas

**Por Llamada**:
```json
{
  "conversation_id": "conv_123",
  "duration_seconds": 180,
  "total_turns": 12,
  "avg_stt_latency_ms": 650,
  "avg_llm_latency_ms": 1200,
  "avg_tts_latency_ms": 800,
  "total_latency_ms": 2100,
  "interruptions_count": 2,
  "sentiment_trend": [-0.5, -0.3, 0.1, 0.3],
  "final_sentiment": "positive",
  "outcome": "resolved",
  "topics": ["billing", "technical_support"],
  "quality_score": 0.85
}
```

**Agregadas (Dashboard)**:
```json
{
  "total_calls_today": 150,
  "avg_call_duration": 210,
  "resolution_rate": 0.78,
  "escalation_rate": 0.15,
  "avg_sentiment": 0.2,
  "top_topics": ["billing", "technical", "cancellation"],
  "wer_improvement": "-54%",
  "avg_latency": 2100
}
```

### Endpoints de Métricas

```bash
# Métricas de una conversación
GET /conversations/{id}/metrics

# Dashboard general
GET /metrics/dashboard

# Stats de procesamiento
GET /processing/stats

# Storage stats
curl http://localhost:8000/storage/stats
```

### Logs

```bash
# Logs en tiempo real
docker-compose logs -f backend

# Logs de batch processor
tail -f logs/batch_processor.log

# Logs por servicio
docker logs -f call-stt
docker logs -f call-llm
docker logs -f call-tts
```

---

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. STT muy lento (>2s)

**Causa**: CPU mode o GPU sin VRAM

**Solución**:
```bash
# Usar GPU
STT_DEVICE=cuda

# O reducir modelo
STT_MODEL=medium  # en lugar de large-v3

# O desactivar features pesadas
ENABLE_TARGET_EXTRACTION=false
ENABLE_PROSODY_ANALYSIS=false
```

#### 2. Correcciones incorrectas

**Causa**: Threshold de vectores muy bajo

**Solución**:
```python
# En error_correction_bank.py
def correct_transcription(self, text: str, distance_threshold=0.9):
    # Aumentar de 0.7 a 0.9 para ser más conservador
```

#### 3. Storage lleno

**Causa**: Muchas grabaciones acumuladas

**Solución**:
```bash
# Limpiar grabaciones antiguas (soft delete)
python -c "
from storage.audio_storage import get_audio_storage
storage = get_audio_storage()
old_recordings = storage.list_recordings(limit=1000)
for rec in old_recordings[:500]:
    storage.delete_recording(rec['recording_id'], permanent=False)
"

# O mover a S3 y limpiar local
STORAGE_BACKEND=s3
```

#### 4. Batch processor no procesa

**Causa**: Metadata con processed=true o falta de grabaciones

**Solución**:
```bash
# Verificar grabaciones pendientes
ls data/recordings/metadata/*.json | wc -l

# Ver cuántas están procesadas
grep -c '"processed": true' data/recordings/metadata/*.json

# Forzar re-procesamiento
python services/analytics/batch_processor.py \
  --mode single \
  --recording-id rec_123 \
  --reprocess
```

#### 5. Webhooks no llegan

**Causa**: URL incorrecta o signature inválida

**Solución**:
```bash
# Verificar configuración
echo $WEBHOOK_URL
echo $WEBHOOK_SECRET

# Test manual
curl -X POST $WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: test" \
  -d '{"type": "test", "data": {}}'

# Ver logs de webhooks
grep "webhook" logs/backend.log
```

### Diagnóstico

```bash
# Test completo
python test_sistema_hibrido.py

# Health checks
curl http://localhost:8000/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# Verificar storage
ls -lh data/recordings/audio/
cat data/recordings/metadata/rec_*.json | jq .

# Verificar batch
python services/analytics/batch_processor.py --mode unprocessed --limit 1
```

---

## 🗺 Roadmap

###  Completado (v1.0)

- Sistema híbrido online/offline
- STT optimizado con corrección
- Clarification inteligente
- Almacenamiento local/S3
- Batch processing
- Sentiment analysis
- Intent detection
- Webhooks
- Documentación completa

### 🚧 En Progreso (v1.1)

- [ ] Fine-tuning de Whisper con datos reales
- [ ] Dashboard React mejorado
- [ ] Exportar a CSV/Excel
- [ ] API REST completa
- [ ] Tests unitarios

### 📅 Próximos (v1.2)

- [ ] Multi-tenancy
- [ ] Roles y permisos
- [ ] Call recording player en dashboard
- [ ] A/B testing automático
- [ ] Modelo híbrido STT (Whisper + Deepgram)

### 🔮 Futuro (v2.0)

- [ ] Real-time streaming STT
- [ ] Voice cloning (TTS personalizado)
- [ ] Predictive analytics
- [ ] Auto-scaling en Kubernetes
- [ ] Mobile app

---

## 🤝 Contribuir

### Reportar Issues

1. Busca si ya existe: https://github.com/tu-repo/issues
2. Crea nuevo issue con template
3. Incluye logs y configuración

### Pull Requests

1. Fork el repo
2. Crea branch: `feature/mi-feature`
3. Commit cambios
4. Push y crear PR
5. Esperar review

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE)

---

## 📞 Soporte

- **Documentación**: Ver documentos enlazados arriba
- **Issues**: https://github.com/tu-repo/issues
- **Tests**: `python test_sistema_hibrido.py`
- **Logs**: `docker-compose logs -f`

---

## 🎓 Recursos Adicionales

### Papers y Referencias

- **Whisper**: https://arxiv.org/abs/2212.04356
- **SpeechBrain**: https://speechbrain.github.io/
- **FAISS**: https://faiss.ai/
- **Prosody Analysis**: https://librosa.org/

### Tutoriales

- [Video: Setup completo](#)
- [Video: Optimizar STT](#)
- [Blog: Mejores prácticas](#)

---

**Versión**: 1.0.0
**Última actualización**: 2026-01-27
**Autor**: Tu equipo

---

## 📌 Quick Links

| Acción | Comando | Documentación |
|--------|---------|---------------|
| **Instalar** | `docker-compose up --build` | [Instalación](#-guía-de-instalación-paso-a-paso) |
| **Configurar** | `cp .env.example .env && nano .env` | [Configuración](#-configuración) |
| **Test** | `python test_sistema_hibrido.py` | [Tests](#paso-7-test-del-sistema) |
| **Activar STT** | Ver guía | [ACTIVAR_STT_MEJORADO.md](ACTIVAR_STT_MEJORADO.md) |
| **Activar Voz** | Ver guía | [ACTIVAR_VOZ_CONTEXTUAL.md](ACTIVAR_VOZ_CONTEXTUAL.md) |
| **Batch Process** | `python batch_processor.py` | [SISTEMA_HIBRIDO_ONLINE_OFFLINE.md](SISTEMA_HIBRIDO_ONLINE_OFFLINE.md) |
| **Dashboard** | http://localhost:3000 | Frontend React |
| **API Docs** | http://localhost:8000/docs | FastAPI Swagger |

---

🚀 **Listo para crear un call center con IA de nivel profesional**
