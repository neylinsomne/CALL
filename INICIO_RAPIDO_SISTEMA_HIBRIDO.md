# Inicio Rápido: Sistema Híbrido Online/Offline

Guía para configurar y probar el sistema híbrido de procesamiento de llamadas.

---

## Qué es el Sistema Híbrido

Un sistema de **dos niveles** para procesar llamadas:

1. **Online (Tiempo Real)**: Corrección rápida durante la llamada (<20ms)
2. **Offline (Batch)**: Análisis profundo después de la llamada (calidad máxima)

**Beneficio**: Latencia ultra-baja + Máxima calidad de análisis

---

## Instalación Rápida

### 1. Instalar Dependencias

```bash
# STT con corrección avanzada
cd services/stt
pip install -r requirements.txt

# Storage (S3 opcional)
cd ../storage
pip install -r requirements.txt

# Volver a raíz
cd ../..
```

### 2. Configurar Variables de Entorno

```bash
# Copiar ejemplo
cp .env.example .env

# Editar .env
nano .env
```

Configuración mínima:

```bash
# Storage (local para empezar)
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./data/recordings

# Features online
ENABLE_ONLINE_CORRECTION=true
ENABLE_STT_CORRECTION=true

# Features offline
ENABLE_OFFLINE_BATCH=true
BATCH_MAX_CONCURRENT=5

# STT básico
STT_MODEL=large-v3
LANGUAGE=es
```

Para producción con S3:

```bash
# Storage con S3
STORAGE_BACKEND=both  # local + S3
S3_BUCKET=my-call-center-recordings
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### 3. Crear Directorios

```bash
mkdir -p data/recordings/{audio,metadata,transcripts}
mkdir -p services/stt/models
```

---

## Test Rápido

### Test del Sistema Completo

```bash
python test_sistema_hibrido.py
```

Esto ejecuta:
1.  Procesamiento online (simulado)
2.  Almacenamiento con metadata
3.  Procesamiento offline (batch)

### Test de Métodos de Clasificación

```bash
python test_clasificacion_demo.py
```

Compara todos los métodos de corrección:
- Levenshtein
- Fonético
- Vectores (FAISS)
- Híbrido

---

## Uso en Producción

### Durante la Llamada (Automático)

El procesamiento online se ejecuta automáticamente en el WebSocket endpoint:

```python
# En services/backend/main.py
from storage.audio_storage import get_audio_storage
from correction_pipeline import get_correction_pipeline

storage = get_audio_storage()
pipeline = get_correction_pipeline()

@app.websocket("/ws/{conversation_id}")
async def handle_call(websocket: WebSocket, conversation_id: str):
    # ... durante la llamada ...

    # 1. Procesar STT online
    online_result = await pipeline.process_online(
        transcription=stt_text,
        word_confidences=stt_confidences,
        conversation_id=conversation_id
    )

    # 2. Guardar automáticamente
    storage.save_recording(
        audio_data=audio_chunk,
        conversation_id=conversation_id,
        metadata={
            "transcription": online_result,
            "agent_id": agent_id
        }
    )

    # 3. Continuar con LLM usando texto corregido
    llm_response = await call_llm(online_result["corrected_text"])
```

### Post-procesamiento Batch

#### Opción 1: Comando Manual

```bash
cd services/analytics

# Procesar grabación específica
python batch_processor.py --mode single --recording-id rec_12345

# Procesar todas las no procesadas (últimas 100)
python batch_processor.py --mode unprocessed --limit 100 --concurrent 5

# Procesar últimos 7 días
python batch_processor.py \
  --mode date_range \
  --start-date 2026-01-20 \
  --end-date 2026-01-27 \
  --concurrent 10
```

#### Opción 2: Cron Job Automático

```bash
# Editar crontab
crontab -e

# Ejecutar cada hora
0 * * * * cd /path/to/Call && python services/analytics/batch_processor.py --mode unprocessed --limit 50

# Ejecutar cada noche a las 2 AM
0 2 * * * cd /path/to/Call && python services/analytics/batch_processor.py --mode unprocessed --limit 1000 --concurrent 20
```

#### Opción 3: Servicio Systemd (Recomendado)

```bash
# Crear servicio
sudo nano /etc/systemd/system/call-batch-processor.service
```

```ini
[Unit]
Description=Call Center Batch Processor
After=network.target

[Service]
Type=simple
User=callcenter
WorkingDirectory=/path/to/Call
ExecStart=/path/to/python services/analytics/batch_processor.py --mode unprocessed --limit 100 --concurrent 10
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

```bash
# Activar y iniciar
sudo systemctl enable call-batch-processor
sudo systemctl start call-batch-processor

# Ver logs
sudo journalctl -u call-batch-processor -f
```

---

## Verificar Funcionamiento

### 1. Verificar Grabaciones Guardadas

```bash
# Listar grabaciones locales
ls -lh data/recordings/audio/

# Ver metadata de una grabación
cat data/recordings/metadata/rec_*_metadata.json | jq .
```

### 2. Verificar Procesamiento Online

```bash
# Buscar grabaciones no procesadas
grep -l '"processed": false' data/recordings/metadata/*.json
```

### 3. Verificar Procesamiento Offline

```bash
# Buscar grabaciones procesadas
grep -l '"processed": true' data/recordings/metadata/*.json
grep -l '"processing_mode": "offline"' data/recordings/metadata/*.json
```

### 4. API de Estadísticas

```bash
# Stats de storage
curl http://localhost:8000/processing/stats

# Respuesta:
{
  "storage": {
    "local": {
      "total_recordings": 150,
      "total_size_mb": 2400.5
    }
  },
  "processing_queue": {
    "total_recordings": 150,
    "processed": 95,
    "pending": 55,
    "processing_rate": 0.63
  }
}
```

---

## Estructura de Archivos

```
Call/
├── data/
│   └── recordings/
│       ├── audio/              # Audio WAV
│       │   ├── rec_12345.wav
│       │   └── ...
│       ├── metadata/           # Metadata JSON
│       │   ├── rec_12345_metadata.json
│       │   └── ...
│       └── transcripts/        # Transcripciones procesadas
│           ├── rec_12345_transcript.json
│           └── ...
│
├── services/
│   ├── stt/
│   │   ├── stt_server.py              # Endpoint /transcribe/enhanced
│   │   ├── correction_pipeline.py     # Pipeline online/offline
│   │   ├── error_correction_bank.py   # Banco vectorial
│   │   ├── error_correction_hybrid.py # Corrector híbrido
│   │   └── clarification_system.py    # Sistema de clarificación
│   │
│   ├── storage/
│   │   ├── audio_storage.py           # Storage local/S3
│   │   └── metadata_schema.py         # Schema Pydantic
│   │
│   └── analytics/
│       └── batch_processor.py         # Procesamiento batch
│
└── DOCUMENTACION/
    ├── SISTEMA_HIBRIDO_ONLINE_OFFLINE.md
    ├── METODOS_CLASIFICACION_ERRORES.md
    ├── ACTIVAR_STT_MEJORADO.md
    └── RESUMEN_MEJORAS_COMPLETAS.md
```

---

## Troubleshooting

### Error: "Pipeline not available"

```bash
# Instalar dependencias faltantes
cd services/stt
pip install sentence-transformers faiss-cpu loguru
```

### Error: "Storage not initialized"

```bash
# Crear directorios
mkdir -p data/recordings/{audio,metadata,transcripts}

# Verificar permisos
chmod -R 755 data/
```

### Error: "S3 bucket not found"

```bash
# Verificar credenciales AWS
aws s3 ls s3://my-call-center-recordings/

# Crear bucket si no existe
aws s3 mb s3://my-call-center-recordings --region us-east-1
```

### Error: "No recordings to process"

```bash
# Verificar que hay grabaciones
ls -la data/recordings/audio/

# Verificar metadata
cat data/recordings/metadata/*.json | jq '.processed'
```

### Alta latencia en Online

Si el procesamiento online es >50ms:

```bash
# En .env, desactivar features pesadas
ENABLE_PROSODY_ANALYSIS=false
ENABLE_TARGET_EXTRACTION=false

# Usar solo diccionario exacto (no vectores)
ENABLE_ONLINE_CORRECTION=true
# pero NO habilitar vectores en online mode
```

### Batch processor lento

```bash
# Aumentar paralelismo
python batch_processor.py --mode unprocessed --concurrent 20

# O reducir si hay problemas de memoria
python batch_processor.py --mode unprocessed --concurrent 2
```

---

## Próximos Pasos

1. **Integrar con Backend**
   - Modificar [services/backend/main.py](services/backend/main.py)
   - Usar `correction_pipeline` y `audio_storage`

2. **Configurar S3**
   - Crear bucket en AWS
   - Configurar credenciales
   - Cambiar `STORAGE_BACKEND=both`

3. **Automatizar Batch**
   - Configurar cron job o systemd
   - Monitorear con logs

4. **Dashboard de Métricas**
   - Implementar endpoint `/processing/stats`
   - Visualizar en React dashboard

5. **Fine-tuning**
   - Recopilar datos reales
   - Fine-tune Whisper con tu vocabulario
   - Mejorar banco de errores

---

## Recursos Adicionales

- **Documentación Completa**: [SISTEMA_HIBRIDO_ONLINE_OFFLINE.md](SISTEMA_HIBRIDO_ONLINE_OFFLINE.md)
- **Métodos de Clasificación**: [METODOS_CLASIFICACION_ERRORES.md](METODOS_CLASIFICACION_ERRORES.md)
- **STT Optimizado**: [ACTIVAR_STT_MEJORADO.md](ACTIVAR_STT_MEJORADO.md)
- **Resumen General**: [RESUMEN_MEJORAS_COMPLETAS.md](RESUMEN_MEJORAS_COMPLETAS.md)

---

## Soporte

- **Issues**: https://github.com/tu-repo/issues
- **Logs**: `docker logs -f call-backend`
- **Test**: `python test_sistema_hibrido.py`

---

Listo para procesar llamadas con latencia ultra-baja + máxima calidad de análisis.
