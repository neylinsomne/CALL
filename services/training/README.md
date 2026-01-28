# F5-TTS Fine-tuning Guide for Call Center Voice

Este directorio contiene scripts académicamente rigurosos para personalizar la voz del modelo F5-TTS.

## 📋 Estándares Acústicos (ITU-R BS.1770)

| Parámetro | Estándar | Justificación |
|-----------|----------|---------------|
| Sample Rate | 24kHz | Óptimo para BigVGAN vocoder |
| Bit Depth | 16-bit PCM | Mínimo para rango dinámico |
| Canales | Mono | DiT procesa monocanal |
| Loudness | **-23 LUFS** | EBU R128 broadcast standard |
| True Peak | -1 dBTP | Evita distorsión |
| Duración | 5-15 segundos | Atención cuadrática limita longitud |

## 🎙 Corpus de Entrenamiento

### Opción 1: Corpus Sharvard (Recomendado)
```bash
python sharvard_corpus.py corpus_grabacion.txt call_center
```

Genera 200+ oraciones fonéticamente balanceadas incluyendo:
- Pangramas fonéticos (cobertura completa)
- Listas Sharvard (balance estadístico)
- Pares mínimos (r/rr, s/z, n/ñ)
- Frases call center específicas
- Variaciones emocionales

### Opción 2: Corpus Mínimo (50 oraciones)
```bash
python sharvard_corpus.py corpus_minimo.txt minimal
```

### Opción 3: Grabaciones existentes
Usa tus propios audios (ver sección de procesamiento).

---

## 🎤 Protocolo de Grabación

### Equipo recomendado:
- Micrófono condensador con pop filter
- Ambiente tratado acústicamente (< -50dB ruido de fondo)
- Software: Audacity, Adobe Audition, o similar

### Configuración de grabación:
```
- Frecuencia: 48kHz (se convertirá a 24kHz)
- Bits: 24-bit (mayor rango dinámico)
- Formato: WAV sin compresión
```

### Tips de grabación:
1. **Consistencia**: Mantén distancia constante al micrófono
2. **Naturalidad**: Lee como si hablaras, no como si leyeras
3. **Pausas**: 1-2 segundos entre oraciones
4. **Hidratación**: Bebe agua para evitar ruidos de boca

---

## 🔧 Pipeline de Procesamiento

### 1. Generar corpus para grabar
```bash
docker-compose run --rm training python sharvard_corpus.py /app/data/corpus.txt call_center
```

### 2. Colocar audios grabados
```bash
# Copia tus archivos WAV a:
services/training/data/raw_audio/
```

### 3. Procesar audio (LUFS normalization)
```bash
docker-compose run --rm training python audio_processor.py \
    -i /app/data/raw_audio \
    -o /app/data/normalized \
    --use-ffmpeg
```

### 4. Preparar dataset
```bash
docker-compose run --rm training python prepare_data.py \
    -i /app/data/normalized \
    -o /app/data/processed \
    -w large-v3
```

### 5. Verificar cobertura fonética
```bash
docker-compose run --rm training python -c "
from text_normalizer import check_phonetic_coverage
from sharvard_corpus import get_all_training_sentences
coverage = check_phonetic_coverage(get_all_training_sentences())
print(f'Cobertura: {coverage[\"coverage_percent\"]:.1f}%')
"
```

---

## 🚀 Entrenamiento

### Configuración recomendada (GPU 24GB)
```yaml
# config.yaml
training:
  precision: bf16          # CRÍTICO para estabilidad
  batch_size: 4
  gradient_accumulation: 8
  learning_rate: 1.0e-5    # Bajo para fine-tuning
  epochs: 500              # 500-1000 necesarios
```

### Ejecutar entrenamiento
```bash
docker-compose run --rm training python finetune.py \
    -d /app/data/processed \
    -o /app/checkpoints \
    -c /app/config.yaml
```

### Monitorear con TensorBoard
```bash
tensorboard --logdir=services/training/checkpoints/logs
```

---

##  Errores Comunes

### "Audio repite en lugar de generar"
**Causa**: Audio de referencia >30 segundos
**Solución**: Usar clips de 10-15 segundos máximo

### "Voz inestable/distorsionada"
**Causa**: LUFS inconsistente o clipping
**Solución**: Reprocesar con `audio_processor.py`

### "OOM (Out of Memory)"
**Causa**: Batch size muy grande
**Solución**: Reducir `batch_size` a 2, aumentar `gradient_accumulation` a 16

### "Números/abreviaturas incorrectos"
**Causa**: Texto sin normalizar
**Solución**: Usar `text_normalizer.py` antes de entrenar

---

## 📁 Estructura Final

```
services/training/
├── config.yaml                 # Configuración de entrenamiento
├── sharvard_corpus.py          # Corpus fonéticamente balanceado
├── text_normalizer.py          # Normalización de texto español
├── audio_processor.py          # LUFS normalization
├── prepare_data.py             # Preparación de dataset
├── finetune.py                 # Script de entrenamiento
└── data/
    ├── raw_audio/              # Grabaciones originales
    ├── normalized/             # Audio normalizado LUFS
    └── processed/              # Dataset final
        ├── *.wav
        ├── metadata.json
        └── filelist.txt
```

---

## 📊 Métricas de Éxito

| Métrica | Objetivo | Cómo medir |
|---------|----------|------------|
| MCD (Mel Cepstral Distortion) | < 5.0 dB | Logs de TensorBoard |
| Similaridad de speaker | > 0.85 | Encoder de speaker |
| Cobertura fonética | 100% | `check_phonetic_coverage()` |
| Duración total | 1-5 horas | Procesamiento audio |
