"""
Voice Distillation Pipeline - F5-TTS → Kokoro via KVoiceWalk
=============================================================
F5-TTS generates high-quality target audio, then Kokoro voice tensors
are evolved via random walk to match that voice. No training required.

Stages:
    1. reference_generator - F5-TTS generates target audio per style
    2. voice_evolver       - Random walk evolves Kokoro tensors
    3. voice_validator     - Prosody validation of evolved voices
    4. deploy              - Switch TTS_BACKEND to kokoro
"""

__version__ = "0.1.0"
