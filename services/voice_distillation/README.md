# Voice Distillation Pipeline

## Overview

Pipeline para destilar la identidad vocal de F5-TTS (modelo pesado, alta calidad) hacia tensores ligeros de Kokoro TTS (82M params, 210x realtime), produciendo modelos de voz por estilo para agentes de call center.

**No hay fine-tuning ni training** — solo optimizacion de tensores via random walk (KVoiceWalk).

```
F5-TTS (Teacher)  -->  Audio Objetivo  -->  KVoiceWalk  -->  Kokoro Tensor (.pt)
    pesado, lento        por estilo         random walk        ligero, rapido
```

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE DESTILACION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Stage 1: REFERENCE       Stage 2: EVOLVE      Stage 3: VALID  │
│  ┌──────────────┐       ┌───────────────┐    ┌──────────────┐  │
│  │ F5-TTS genera│       │ KVoiceWalk    │    │ Prosody      │  │
│  │ 4 clips      │──────>│ random walk   │───>│ validation   │  │
│  │ (1/estilo)   │       │ 10K steps     │    │ + comparison │  │
│  │ 20-30s c/u   │       │ per estilo    │    │              │  │
│  └──────────────┘       └───────────────┘    └──────┬───────┘  │
│                                                      │          │
│                         Stage 4: DEPLOY              │          │
│                         ┌───────────────┐            │          │
│                         │ TTS_BACKEND   │<───────────┘          │
│                         │ =kokoro       │                       │
│                         │ 4 tensores .pt│                       │
│                         └───────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estilos de Voz

| Estilo | Descripcion | Speed F5 | Uso |
|--------|-------------|----------|-----|
| `neutral` | Tono informativo estandar | 1.0 | Datos, numeros, informacion factual |
| `amable` | Tono calido y acogedor | 0.95 | Saludos, despedidas, bienvenidas |
| `empatico` | Tono comprensivo | 0.90 | Disculpas, problemas, frustracion |
| `profesional` | Tono formal y seguro | 1.05 | Procesos, politicas, confirmaciones |

Cada estilo produce un tensor `.pt` de dimension `511 x 1 x 256`.

---

## Stages del Pipeline

### Stage 1: Reference Generation (F5-TTS)

Genera audio objetivo de alta calidad usando F5-TTS para cada estilo.

- **Input**: Audio fuente WAV + transcripcion (voz a clonar)
- **Proceso**: F5-TTS sintetiza 5 frases por estilo, las concatena
- **Output**: `reference_audio/{estilo}/target.wav` (20-30s, LUFS -23)
- **Archivo**: `reference_generator.py`

### Stage 2: Voice Evolution (KVoiceWalk)

Evoluciona tensores de Kokoro via random walk hasta que reproduzcan la voz objetivo.

- **Input**: Audio referencia + voces base Kokoro (ef_dora, em_alex, em_santa)
- **Proceso**:
  1. Cargar/interpolar voces Kokoro existentes (mejor starting point)
  2. Random walk: mutar tensor -> sintetizar con Kokoro -> evaluar -> mantener si mejora
  3. Mutacion: `base + randn_like(base) * std * diversity`
  4. Early termination si score < 98% del mejor actual
- **Output**: `evolved_voices/{estilo}.pt`
- **Config**: 10,000 pasos, diversidad 0.01-0.15
- **Archivo**: `voice_evolver.py`

### Stage 3: Validation

Valida que los tensores evolucionados producen voz coherente y diferenciada.

- **Input**: Tensores evolucionados + audio referencia
- **Proceso**:
  1. Generar audio con frases de test
  2. Speaker similarity via resemblyzer (umbral >= 0.70)
  3. Self-consistency (umbral >= 0.85)
  4. Analisis prosodia (F0, energia, speech rate)
  5. Diferenciacion entre estilos
- **Output**: `validation/validation_report.json`
- **Archivo**: `voice_validator.py`

### Stage 4: Deploy

Copia tensores validados a produccion y activa Kokoro como backend TTS.

- Copiar `.pt` a directorio de modelos
- Configurar `TTS_BACKEND=kokoro` en `.env`
- Reiniciar servicio TTS

---

## Funcion de Scoring

Score hibrido usando **media armonica ponderada** (escala 0-100):

| Metrica | Peso | Descripcion |
|---------|------|-------------|
| Target Similarity | 48% | Coseno resemblyzer: voz generada vs audio F5-TTS |
| Self-Similarity | 50% | Consistencia: misma voz con diferentes textos |
| Feature Similarity | 2% | MFCCs, spectral centroid, pitch, energia |

```
score = harmonic_mean(target_sim * 0.48, self_sim * 0.50, feature_sim * 0.02) * 100
```

---

## Corpus de Entrenamiento (Sharvard)

El corpus en `services/training/sharvard_corpus.py` provee oraciones foneticamente balanceadas:

| Categoria | Cantidad | Proposito |
|-----------|----------|-----------|
| Pangramas Foneticos | 7 | Maxima cobertura fonetica por oracion |
| Listas Sharvard (01-05) | 50 | Oraciones generales balanceadas |
| Call Center | 15 | Frases especificas del dominio |
| Diptongos | 10 | Diptongos e hiatos |
| Numeros | 10 | Expresiones numericas |
| Pares Minimos | 14 | Distincion r/rr, b/v, s/z, n/n |
| Secuencias Dificiles | 9 | Clusters consonanticos, trabalenguas |
| Variaciones Emocionales | 12 | neutral, pregunta, enfasis, disculpa |
| **Total** | **~127** | |

---

## Metodologia de Data Labeling

### Concepto

Cada oracion del corpus recibe una **etiqueta de estilo** que determina con que tono vocal debe grabarse. Este etiquetado alimenta el pipeline de destilacion.

### Proceso de Etiquetado

1. **Asignacion de Estilo**: En el dashboard Voice Lab, cada oracion recibe un estilo via dropdown.

2. **Guia de Asignacion**:

   | Tipo de Oracion | Estilo Recomendado |
   |-----------------|-------------------|
   | Saludos, bienvenidas, despedidas | `amable` |
   | Disculpas, reconocimiento de problemas | `empatico` |
   | Datos, numeros, informacion factual | `neutral` |
   | Procesos, politicas, confirmaciones | `profesional` |
   | Pangramas y oraciones foneticas | `neutral` (baseline) |
   | Preguntas enfaticas | `profesional` |
   | Variaciones emotivas (disculpa) | `empatico` |

3. **Grabacion**: Cada oracion se graba con las caracteristicas vocales del estilo:
   - `neutral`: Ritmo constante, tono medio, sin inflexiones marcadas
   - `amable`: Tono mas alto, ritmo ligeramente mas lento, inflexion ascendente
   - `empatico`: Tono suave, pausas mas largas, ritmo mas lento
   - `profesional`: Tono firme, ritmo ligeramente mas rapido, articulacion clara

4. **Validacion de Calidad**: Cada grabacion se valida via:
   - Analisis prosodia (pitch medio, varianza energia, speech rate)
   - Comparacion con perfil del estilo asignado
   - Score de calidad 0-1

### Formato de Datos

```json
{
  "sentence_id": "shcc-01",
  "text": "Buenos dias, gracias por llamar a nuestro servicio.",
  "list": "lista_call_center",
  "style_label": "amable",
  "recording": {
    "path": "recordings/shcc-01_amable.wav",
    "duration_seconds": 3.2,
    "quality_score": 0.91,
    "prosody": {
      "pitch_mean": 210.5,
      "energy_std": 0.12,
      "speech_rate": 4.2
    }
  }
}
```

---

## Uso

### CLI

```bash
# Pipeline completo
python run_pipeline.py --stage all --reference-audio /path/to/voice.wav

# Stages individuales
python run_pipeline.py --stage reference --tts-url http://tts:8001
python run_pipeline.py --stage evolve --steps 5000 --styles neutral amable
python run_pipeline.py --stage validate
python run_pipeline.py --stage deploy

# Test rapido (100 pasos)
python run_pipeline.py --stage evolve --steps 100 --styles neutral
```

### Docker

```bash
# Iniciar pipeline (profile: training)
docker compose --profile training run voice_distillation \
  python run_pipeline.py --stage all --reference-audio /app/audio/voice.wav

# Activar Kokoro en produccion
# 1. Editar .env:
#    TTS_BACKEND=kokoro
#    KOKORO_VOICE_PATH=/data/distillation/evolved_voices/neutral.pt
# 2. Reiniciar:
docker compose restart tts

# Cambiar estilo en runtime
curl -X POST http://localhost:8001/set_voice?style=empatico
```

---

## Estructura de Archivos

```
services/voice_distillation/
  config.py              - Configuracion: estilos, scoring, paths
  run_pipeline.py        - CLI orquestador
  reference_generator.py - Stage 1: generacion audio F5-TTS
  voice_evolver.py       - Stage 2: random walk KVoiceWalk
  voice_interpolator.py  - Optimizacion starting point via interpolacion
  fitness_scorer.py      - Scoring hibrido (resemblyzer + self-sim + features)
  voice_validator.py     - Stage 3: validacion y diferenciacion
  Dockerfile
  requirements.txt
  README.md              - Este archivo
```

---

## Umbrales de Calidad

| Metrica | Umbral | Proposito |
|---------|--------|-----------|
| Speaker Similarity | >= 0.70 | Identidad vocal coincide |
| Self-Similarity | >= 0.85 | Consistencia cross-texto |
| Diferenciacion Estilos | > 5% CoV | Estilos suenan distintos |
| Duracion Minima Audio | >= 1.0s | Suficiente para scoring |

---

## Voces Base Kokoro (Espanol)

| Voice ID | Genero | Descripcion |
|----------|--------|-------------|
| `ef_dora` | Femenino | Dora - voz femenina espanola |
| `em_alex` | Masculino | Alex - voz masculina espanola |
| `em_santa` | Masculino | Santa - voz masculina espanola |

Idioma: `lang_code="e"` con fallback espeak-ng `es`.
