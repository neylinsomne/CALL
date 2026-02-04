"""
Pipeline Configuration
======================
Central configuration for the voice distillation pipeline.
"""

import os
from pathlib import Path


# =============================================
# Paths
# =============================================

BASE_DIR = Path(os.getenv("DISTILLATION_OUTPUT", "/data/distillation"))
REFERENCE_DIR = BASE_DIR / "reference_audio"
EVOLVED_DIR = BASE_DIR / "evolved_voices"
INTERPOLATED_DIR = BASE_DIR / "interpolated"
VALIDATION_DIR = BASE_DIR / "validation"
RUNS_DIR = BASE_DIR / "runs"

# External service URLs
TTS_URL = os.getenv("TTS_URL", "http://tts:8001")
AUDIO_PREPROCESS_URL = os.getenv("AUDIO_PREPROCESS_URL", "http://audio_preprocess:8004")


# =============================================
# Kokoro Configuration
# =============================================

KOKORO_LANG = "e"  # Spanish
KOKORO_MODEL = "hexgrad/Kokoro-82M"
KOKORO_SAMPLE_RATE = 24000

# Available Spanish voices (Kokoro v1.0)
KOKORO_BASE_VOICES = {
    "ef_dora": {"gender": "female", "description": "Dora - Spanish female"},
    "em_alex": {"gender": "male", "description": "Alex - Spanish male"},
    "em_santa": {"gender": "male", "description": "Santa - Spanish male"},
}


# =============================================
# Style Definitions
# =============================================

STYLES = {
    "neutral": {
        "description": "Tono informativo estandar",
        "f5_speed": 1.0,
        "reference_phrases": [
            "Le informo que su solicitud ha sido procesada correctamente.",
            "El horario de atencion es de lunes a viernes de ocho a seis.",
            "Su numero de referencia es el cuatro cinco siete tres dos uno.",
            "Los documentos se encuentran disponibles en su correo electronico.",
            "El proceso de verificacion tardara aproximadamente tres dias habiles.",
        ],
    },
    "amable": {
        "description": "Tono calido y acogedor",
        "f5_speed": 0.95,
        "reference_phrases": [
            "Buenos dias, con mucho gusto le ayudo con eso.",
            "Que bueno que nos contacta, estamos aqui para servirle.",
            "Excelente, me da mucho gusto poder ayudarle hoy.",
            "No se preocupe, con todo gusto le resolvemos esto rapidamente.",
            "Fue un placer atenderle, que tenga un maravilloso dia.",
        ],
    },
    "empatico": {
        "description": "Tono comprensivo ante problemas",
        "f5_speed": 0.9,
        "reference_phrases": [
            "Entiendo perfectamente su situacion, vamos a resolverlo juntos.",
            "Lamento mucho los inconvenientes que esto le ha causado.",
            "Comprendo su frustracion y quiero asegurarle que trabajaremos en esto.",
            "Es completamente comprensible su preocupacion, dejeme ayudarle.",
            "Siento mucho que haya tenido esta experiencia, lo vamos a solucionar.",
        ],
    },
    "profesional": {
        "description": "Tono formal y seguro",
        "f5_speed": 1.05,
        "reference_phrases": [
            "Segun nuestro protocolo, el procedimiento es el siguiente.",
            "Le confirmo que la transaccion ha sido procesada exitosamente.",
            "De acuerdo con nuestras politicas, procederemos de la siguiente manera.",
            "El departamento correspondiente ya ha sido notificado de su caso.",
            "Queda registrado su requerimiento con el numero de ticket asignado.",
        ],
    },
}


# =============================================
# Evolution Parameters (KVoiceWalk-inspired)
# =============================================

WALK_STEPS = 10_000
POPULATION_LIMIT = 10
DIVERSITY_RANGE = (0.01, 0.15)
EARLY_TERMINATION_RATIO = 0.98  # Skip if score < 98% of current best
CLIP_TENSORS = True  # Clip mutated tensors to observed min/max

# Scoring weights (harmonic mean)
SCORING_WEIGHTS = {
    "target_similarity": 0.48,
    "self_similarity": 0.50,
    "feature_similarity": 0.02,
}


# =============================================
# Audio Standards (from training/audio_processor)
# =============================================

SAMPLE_RATE = 24000
TARGET_LUFS = -23.0
MIN_DURATION = 3.0
MAX_DURATION = 30.0


# =============================================
# Quality Thresholds
# =============================================

RESEMBLYZER_THRESHOLD = 0.70  # Min cosine similarity for voice match
SELF_SIMILARITY_THRESHOLD = 0.85  # Min self-consistency
