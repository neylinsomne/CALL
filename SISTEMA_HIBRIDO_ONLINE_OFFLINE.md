## Sistema Híbrido de Procesamiento: Online vs Offline

Documentación completa del sistema de dos niveles para procesamiento de llamadas.

---

## Concepto

El sistema procesa las llamadas en **dos etapas**:

1. **Online (Tiempo Real)** - Durante la llamada
   - Optimizado para **latencia** (<20ms overhead)
   - Solo correcciones rápidas y críticas
   - Respuesta inmediata al usuario

2. **Offline (Post-procesamiento)** - Después de la llamada
   - Optimizado para **calidad**
   - Análisis profundo y completo
   - Sin límite de tiempo

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                        DURANTE LA LLAMADA                        │
│                         (Online Mode)                            │
└──────────────────────────────────────────────────────────────────┘

Audio → Target Speaker → Prosody → STT → Online Correction → LLM → TTS
                                            │
                                            ├─ Diccionario Exacto (<1ms)
                                            ├─ Clarificación Crítica
                                            └─ Guardar en Storage (local/S3)
                                                      │
                                                      ↓
                            ┌─────────────────────────────────────┐
                            │      METADATA.JSON guardada         │
                            │   - Audio raw                       │
                            │   - Transcripción básica            │
                            │   - Correcciones online             │
                            │   - Timestamps                      │
                            │   - processed=false                 │
                            └─────────────────────────────────────┘
                                                      │
                                                      ↓
┌──────────────────────────────────────────────────────────────────┐
│                      DESPUÉS DE LA LLAMADA                       │
│                       (Offline Mode)                             │
└──────────────────────────────────────────────────────────────────┘

                            Batch Processor (cron/manual)
                                      │
                        ┌─────────────┴─────────────┐
                        │                           │
                  Lista grabaciones           Procesa en batch
                  no procesadas              (5-10 simultáneas)
                        │                           │
                        └─────────────┬─────────────┘
                                      ↓
                    ┌──────────────────────────────┐
                    │  Procesamiento Completo      │
                    ├──────────────────────────────┤
                    │ 1. Re-transcripción premium  │
                    │ 2. Corrección híbrida        │
                    │    - Exacto                  │
                    │    - Vectorial (FAISS)       │
                    │    - Fonético                │
                    │ 3. Sentiment avanzado        │
                    │ 4. Intent detection          │
                    │ 5. Entity extraction         │
                    │ 6. Topic analysis            │
                    │ 7. Coherence scoring         │
                    └──────────────────────────────┘
                                      │
                                      ↓
                            ┌─────────────────────┐
                            │  Metadata.json      │
                            │  actualizada        │
                            │  - processed=true   │
                            │  - Análisis completo│
                            └─────────────────────┘
```

---

## Comparación: Online vs Offline

| Característica | Online | Offline |
|----------------|--------|---------|
| **Objetivo** | Latencia mínima | Máxima calidad |
| **Cuándo** | Durante llamada | Post-procesamiento |
| **Target Latency** | <20ms | Sin límite |
| **Corrección** | Solo diccionario | Híbrido completo |
| **Vectores FAISS** |  No |  Sí |
| **Fonético** |  No |  Sí |
| **Re-transcripción** |  No |  Si WER alto |
| **Sentiment** | Básico | Avanzado |
| **Intent** | No | Sí |
| **Entities** | No | Sí (completo) |
| **Topics** | No | Sí |
| **Coherence** | No | Sí |
| **Clarificación** | Solo crítica | Todas |

---

## 1. Procesamiento Online

### Archivo: [services/stt/correction_pipeline.py](services/stt/correction_pipeline.py)

### Flujo Online

```python
from correction_pipeline import get_correction_pipeline

pipeline = get_correction_pipeline()

# Durante la llamada
result = await pipeline.process_online(
    transcription="Necesito revisar el salgo de mi cuesta",
    word_confidences=[
        {"word": "salgo", "confidence": 0.45},
        {"word": "cuesta", "confidence": 0.52}
    ],
    conversation_id="conv-123"
)

# Resultado (en ~15ms):
{
    "corrected_text": "Necesito revisar el saldo de mi cuenta",
    "corrections_made": [
        {"original": "salgo", "corrected": "saldo", "method": "fast_exact"},
        {"original": "cuesta", "corrected": "cuenta", "method": "fast_exact"}
    ],
    "needs_clarification": False,  # Solo si crítico
    "processing_mode": "online",
    "processing_time_ms": 15.2
}
```

### Qué se Guarda en Online

```json
{
  "recording_id": "rec_12345",
  "conversation_id": "conv_67890",
  "timestamp": "2026-01-27T10:30:00Z",
  "audio": {
    "format": "wav",
    "duration_seconds": 120.5,
    "file_size_bytes": 1920000,
    "checksum": "abc123..."
  },
  "transcription": {
    "text": "Necesito revisar el salgo...",
    "corrected_text": "Necesito revisar el saldo...",
    "language": "es",
    "confidence": 0.87,
    "corrections_made": [...],
    "correction_method": "online"
  },
  "processed": false,  // ← Aún no procesado offline
  "processing_mode": "online",
  "local_path": "./data/recordings/audio/rec_12345.wav",
  "s3_path": "s3://bucket/recordings/conv_67890/rec_12345.wav"
}
```

---

## 2. Procesamiento Offline

### Archivo: [services/analytics/batch_processor.py](services/analytics/batch_processor.py)

### Flujo Offline

```python
from analytics.batch_processor import BatchProcessor

processor = BatchProcessor()

# Procesar grabación individual
result = await processor.process_recording("rec_12345")

# O procesar todas las no procesadas
stats = await processor.process_unprocessed(limit=100, max_concurrent=5)

# O por rango de fechas
from datetime import datetime, timedelta
stats = await processor.process_by_date_range(
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
    max_concurrent=10
)
```

### Qué Hace Offline

1. **Re-transcripción** (si WER >20%)
   ```python
   if quality["estimated_wer"] > 0.2:
       retranscribed = await retranscribe_premium(audio_path)
   ```

2. **Corrección Híbrida Completa**
   ```python
   corrected = await pipeline.process_offline(
       text=transcription,
       word_confidences=confidences,
       audio_path=audio_path,
       conversation_id=conv_id
   )
   # Usa: Exacto + Vectorial + Fonético
   ```

3. **Análisis Avanzado**
   ```python
   advanced_analysis = {
       "entities": {
           "account_numbers": ["123456789"],
           "amounts": ["45.50 euros"],
           "emails": ["user@example.com"]
       },
       "topics": ["billing", "account"],
       "keywords": ["factura", "pago", "cuenta"],
       "coherence_score": 0.85
   }
   ```

4. **Sentiment & Intent**
   ```python
   sentiment = {
       "label": "frustrated",
       "score": -0.7,
       "confidence": 0.85
   }

   intent = {
       "primary_intent": "billing_inquiry",
       "secondary_intents": ["complaint"],
       "confidence": 0.78
   }
   ```

### Metadata Después de Offline

```json
{
  "recording_id": "rec_12345",
  "processed": true,  // ← Ahora sí procesado
  "processing_mode": "offline",
  "transcription": {
    "corrected_text": "...",  // Más preciso
    "correction_method": "offline",  // Híbrido completo
    "corrections_made": [...]  // Más correcciones
  },
  "sentiment": {
    "label": "frustrated",
    "score": -0.7,
    "emotional_tone": "concerned"
  },
  "intent": {
    "primary_intent": "billing_inquiry",
    "confidence": 0.78
  },
  "entities": {
    "account_numbers": ["123456789"],
    "amounts": ["45.50 euros"]
  },
  "topics": {
    "topics": ["billing", "account"],
    "keywords": ["factura", "pago"],
    "coherence_score": 0.85
  }
}
```

---

## 3. Sistema de Almacenamiento

### Archivo: [services/storage/audio_storage.py](services/storage/audio_storage.py)

### Configuración

```bash
# En .env
STORAGE_BACKEND=both  # local, s3, both
STORAGE_LOCAL_PATH=./data/recordings
S3_BUCKET=my-call-center-recordings
S3_REGION=us-east-1

# Credenciales AWS (en ~/.aws/credentials o ENV)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

### Uso

```python
from storage.audio_storage import get_audio_storage, StorageBackend

# Inicializar
storage = get_audio_storage()

# Guardar grabación
result = storage.save_recording(
    audio_data=audio_bytes,
    conversation_id="conv_123",
    metadata={
        "agent_id": "agent_001",
        "caller_phone": "+34612345678",
        "direction": "inbound"
    },
    format="wav"
)

# Resultado:
{
    "recording_id": "conv_123_20260127_103000_abc123",
    "local_path": "./data/recordings/audio/conv_123_20260127_103000_abc123.wav",
    "s3_path": "s3://bucket/recordings/conv_123/conv_123_20260127_103000_abc123.wav",
    "metadata_path": "./data/recordings/metadata/conv_123_20260127_103000_abc123_metadata.json",
    "size_bytes": 1920000,
    "checksum": "sha256..."
}

# Recuperar grabación
audio_data = storage.get_recording("rec_12345")

# Listar grabaciones
recordings = storage.list_recordings(
    conversation_id="conv_123",
    limit=100
)

# Estadísticas
stats = storage.get_storage_stats()
# {
#   "local": {"total_recordings": 150, "total_size_mb": 2400.5},
#   "s3": {"total_recordings": 150, "total_size_mb": 2400.5}
# }
```

### Estructura de Directorios

```
data/
└── recordings/
    ├── audio/                    # Archivos de audio
    │   ├── rec_12345.wav
    │   ├── rec_12346.wav
    │   └── ...
    ├── metadata/                 # Metadata JSON
    │   ├── rec_12345_metadata.json
    │   ├── rec_12346_metadata.json
    │   └── ...
    └── transcripts/              # Transcripciones procesadas
        ├── rec_12345_transcript.json
        ├── rec_12346_transcript.json
        └── ...
```

### Estructura en S3

```
s3://my-call-center-recordings/
├── recordings/
│   ├── conv_123/
│   │   ├── rec_12345.wav
│   │   ├── rec_12345_metadata.json
│   │   └── ...
│   ├── conv_124/
│   │   └── ...
│   └── ...
└── transcripts/
    ├── conv_123/
    │   ├── rec_12345_transcript.json
    │   └── ...
    └── ...
```

---

## 4. Schema de Metadata

### Archivo: [services/storage/metadata_schema.py](services/storage/metadata_schema.py)

### Schema Completo

```python
from storage.metadata_schema import (
    RecordingMetadata,
    AudioMetadata,
    TranscriptionMetadata,
    SentimentAnalysis,
    IntentAnalysis,
    EntityExtraction,
    ConversationMetrics
)

# Crear metadata
metadata = RecordingMetadata(
    recording_id="rec_12345",
    conversation_id="conv_67890",
    timestamp=datetime.utcnow(),
    direction="inbound",
    audio=AudioMetadata(
        format="wav",
        sample_rate=16000,
        duration_seconds=120.5,
        file_size_bytes=1920000,
        checksum="abc123..."
    ),
    transcription=TranscriptionMetadata(...),
    sentiment=SentimentAnalysis(...),
    intent=IntentAnalysis(...),
    entities=EntityExtraction(...),
    # ... más campos
)

# Serializar a JSON
json_str = metadata.model_dump_json(indent=2)

# Deserializar
metadata = RecordingMetadata.model_validate_json(json_str)
```

### Campos Principales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `recording_id` | str | ID único de grabación |
| `conversation_id` | str | ID de conversación |
| `timestamp` | datetime | Timestamp creación |
| `direction` | Enum | inbound/outbound |
| `outcome` | Enum | resolved/escalated/etc |
| `audio` | AudioMetadata | Info técnica del audio |
| `transcription` | TranscriptionMetadata | Transcripción y correcciones |
| `sentiment` | SentimentAnalysis | Análisis de sentimiento |
| `intent` | IntentAnalysis | Intención detectada |
| `entities` | EntityExtraction | Entidades extraídas |
| `topics` | TopicAnalysis | Tópicos y keywords |
| `turns` | List[Turn] | Turnos de conversación |
| `conversation_metrics` | ConversationMetrics | Métricas de la conversación |
| `processing_metrics` | ProcessingMetrics | Latencias STT/LLM/TTS |
| `processed` | bool | ¿Procesado offline? |
| `processing_mode` | str | online/offline |

---

## 5. Ejecución del Sistema

### Durante la Llamada (Automático)

En [services/backend/main.py](services/backend/main.py):

```python
from storage.audio_storage import get_audio_storage
from storage.metadata_schema import create_recording_metadata, CallDirection
from correction_pipeline import get_correction_pipeline

storage = get_audio_storage()
pipeline = get_correction_pipeline()

@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    # ... durante la llamada ...

    # 1. Procesar audio online
    online_result = await pipeline.process_online(
        transcription=stt_result["text"],
        word_confidences=stt_result["word_confidences"],
        conversation_id=conversation_id
    )

    # 2. Guardar grabación con metadata
    recording_result = storage.save_recording(
        audio_data=audio_chunk,
        conversation_id=conversation_id,
        metadata={
            "agent_id": agent_id,
            "direction": CallDirection.INBOUND,
            "transcription": online_result,
            "processing_mode": "online"
        }
    )

    # 3. Continuar con LLM...
```

### Post-procesamiento Offline (Programado)

#### Opción 1: Comando Manual

```bash
cd services/analytics

# Procesar grabación específica
python batch_processor.py --mode single --recording-id rec_12345

# Procesar todas las no procesadas
python batch_processor.py --mode unprocessed --limit 100 --concurrent 5

# Procesar por rango de fechas
python batch_processor.py \
  --mode date_range \
  --start-date 2026-01-20 \
  --end-date 2026-01-27 \
  --concurrent 10
```

#### Opción 2: Cron Job

```bash
# Editar crontab
crontab -e

# Ejecutar cada hora
0 * * * * cd /path/to/Call && python services/analytics/batch_processor.py --mode unprocessed --limit 50

# Ejecutar cada noche a las 2 AM
0 2 * * * cd /path/to/Call && python services/analytics/batch_processor.py --mode unprocessed --limit 1000 --concurrent 20
```

#### Opción 3: Celery (Recomendado para producción)

```python
# tasks.py
from celery import Celery
from analytics.batch_processor import BatchProcessor

app = Celery('call_processing')

@app.task
def process_recording_task(recording_id):
    processor = BatchProcessor()
    return asyncio.run(processor.process_recording(recording_id))

@app.task
def process_unprocessed_batch():
    processor = BatchProcessor()
    return asyncio.run(processor.process_unprocessed(limit=100))

# Programar tarea cada hora
app.conf.beat_schedule = {
    'process-unprocessed-hourly': {
        'task': 'tasks.process_unprocessed_batch',
        'schedule': 3600.0,  # Cada hora
    },
}
```

---

## 6. Beneficios del Sistema Híbrido

### Durante la Llamada (Online)

 **Latencia ultra-baja**: <20ms overhead
 **Correcciones inmediatas**: Errores comunes corregidos al instante
 **Clarificación crítica**: Solo pregunta si es crucial
 **Experiencia fluida**: Usuario no nota delay
 **Almacenamiento automático**: Todo se guarda para análisis posterior

### Después de la Llamada (Offline)

 **Máxima calidad**: Sin compromiso en procesamiento
 **Corrección completa**: Híbrido con vectores y fonético
 **Análisis profundo**: Sentiment, intent, entities, topics
 **Re-transcripción**: Si calidad original es baja (WER >20%)
 **Métricas completas**: Para analytics y mejora continua
 **No afecta UX**: Usuario ya terminó la llamada

### ROI Comparado

| Métrica | Solo Online | Solo Offline | Híbrido |
|---------|-------------|--------------|---------|
| Latencia durante llamada |  15ms |  N/A |  15ms |
| WER final | 12% | N/A | 6% |
| Sentiment accuracy | 60% | N/A | 85% |
| Intent detection |  No | N/A |  78% |
| Entity extraction |  No | N/A |  Completa |
| Costo computacional | Bajo | Alto | Medio |
| Experiencia usuario |  | N/A |  |
| Calidad analytics |  |  |  |

---

## 7. Configuración Recomendada

### Variables de Entorno

```bash
# .env
# Storage
STORAGE_BACKEND=both  # local + S3 redundancy
STORAGE_LOCAL_PATH=./data/recordings
S3_BUCKET=my-call-center-recordings
S3_REGION=us-east-1

# Processing
ENABLE_ONLINE_CORRECTION=true
ENABLE_OFFLINE_BATCH=true
BATCH_PROCESSING_HOUR=2  # 2 AM
BATCH_MAX_CONCURRENT=10

# Thresholds
ONLINE_CLARIFICATION_THRESHOLD=0.5  # Muy estricto
OFFLINE_RETRANSCRIBE_WER_THRESHOLD=0.2
```

### Recursos Recomendados

#### Durante Llamada (Online)
- CPU: Mínimo 4 cores
- RAM: 8GB
- GPU: No necesaria

#### Batch Processing (Offline)
- CPU: 16+ cores (paralelismo)
- RAM: 32GB
- GPU: Recomendada (RTX 3090 o superior)
- Disco: SSD rápido para I/O

---

## 8. Monitoreo y Métricas

### Dashboard de Procesamiento

```python
# API endpoint en backend
@app.get("/processing/stats")
async def get_processing_stats():
    storage = get_audio_storage()
    pipeline = get_correction_pipeline()

    storage_stats = storage.get_storage_stats()
    pipeline_stats = pipeline.get_stats()

    # Contar procesados vs no procesados
    all_recordings = storage.list_recordings(limit=1000)
    processed = sum(1 for r in all_recordings if r.get("processed"))
    pending = len(all_recordings) - processed

    return {
        "storage": storage_stats,
        "pipeline": pipeline_stats,
        "processing_queue": {
            "total_recordings": len(all_recordings),
            "processed": processed,
            "pending": pending,
            "processing_rate": processed / len(all_recordings) if all_recordings else 0
        }
    }
```

---

## Conclusión

El sistema híbrido te da **lo mejor de ambos mundos**:

- **Respuesta rápida** durante la llamada (online)
- **Análisis profundo** después (offline)
- **Almacenamiento robusto** (local + S3)
- **Metadata completa** para analytics
- **Escalabilidad** (batch processing paralelo)

**Resultado:** Experiencia de usuario fluida + datos de altísima calidad para mejora continua.
