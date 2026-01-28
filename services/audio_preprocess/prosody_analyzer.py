"""
Prosody Analyzer - Análisis de Entonación y Contexto Conversacional
Detecta preguntas, pausas naturales, tiempos muertos, y contexto emocional
"""

import numpy as np
import librosa
import io
from typing import Dict, Optional, Tuple
from loguru import logger


class ProsodyAnalyzer:
    """
    Analiza características prosódicas del habla:
    - Pitch (F0) - para detectar preguntas (tono ascendente)
    - Energy - para detectar pausas vs silencios
    - Ritmo - para detectar nerviosismo o reflexión
    - Duración de pausas - para saber si esperar más o responder
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

        # Thresholds ajustables
        self.silence_threshold = -40  # dB
        self.question_pitch_rise_threshold = 1.15  # 15% de incremento en pitch
        self.thinking_pause_min = 0.8  # segundos
        self.thinking_pause_max = 2.5  # segundos
        self.end_of_turn_pause = 1.5  # segundos

    def analyze_audio(self, audio_bytes: bytes) -> Dict:
        """
        Análisis completo de audio para contexto conversacional

        Returns:
            {
                "is_question": bool,  # Si termina con entonación de pregunta
                "has_speech": bool,  # Si hay voz (no silencio)
                "pause_duration": float,  # Duración del silencio actual
                "is_thinking_pause": bool,  # Pausa para pensar (no terminar turno)
                "should_wait": bool,  # Si debemos esperar más audio
                "pitch_contour": list,  # Contorno de pitch
                "energy_level": float,  # Nivel de energía promedio
                "speech_rate": float,  # Palabras por minuto estimado
                "emotional_tone": str  # neutral, nervous, calm, excited
            }
        """
        try:
            # Cargar audio
            audio = self._bytes_to_numpy(audio_bytes)

            # Si el audio es muy corto, no analizar
            if len(audio) < self.sample_rate * 0.1:  # < 100ms
                return self._empty_analysis()

            # Análisis de pitch (F0)
            pitch_data = self._analyze_pitch(audio)

            # Análisis de energía
            energy_data = self._analyze_energy(audio)

            # Análisis de pausas
            pause_data = self._analyze_pauses(audio, energy_data["rms"])

            # Análisis de ritmo de habla
            speech_rate = self._estimate_speech_rate(audio, energy_data["rms"])

            # Análisis emocional básico
            emotional_tone = self._analyze_emotional_tone(
                pitch_data["pitch_std"],
                energy_data["energy_mean"],
                speech_rate
            )

            # Determinar si es pregunta
            is_question = self._detect_question(
                pitch_data["pitch_contour"],
                pitch_data["pitch_trend"]
            )

            # Determinar si debemos esperar más
            should_wait = self._should_wait_for_more(
                pause_data["pause_duration"],
                is_question,
                energy_data["has_speech"]
            )

            return {
                "is_question": is_question,
                "has_speech": energy_data["has_speech"],
                "pause_duration": pause_data["pause_duration"],
                "is_thinking_pause": pause_data["is_thinking_pause"],
                "should_wait": should_wait,
                "pitch_contour": pitch_data["pitch_contour"],
                "pitch_mean": pitch_data["pitch_mean"],
                "pitch_std": pitch_data["pitch_std"],
                "energy_level": energy_data["energy_mean"],
                "speech_rate": speech_rate,
                "emotional_tone": emotional_tone,
                "confidence": 0.85  # Confidence score del análisis
            }

        except Exception as e:
            logger.error(f"Error en análisis de prosodia: {e}")
            return self._empty_analysis()

    def _analyze_pitch(self, audio: np.ndarray) -> Dict:
        """
        Analiza el pitch (F0) para detectar entonación
        """
        try:
            # Extraer pitch usando librosa
            f0 = librosa.yin(
                audio,
                fmin=librosa.note_to_hz('C2'),  # 65 Hz (voz humana baja)
                fmax=librosa.note_to_hz('C7'),  # 2093 Hz (voz humana alta)
                sr=self.sample_rate
            )

            # Filtrar valores no válidos
            f0_valid = f0[f0 > 0]

            if len(f0_valid) == 0:
                return {
                    "pitch_contour": [],
                    "pitch_mean": 0,
                    "pitch_std": 0,
                    "pitch_trend": 0
                }

            # Calcular tendencia (¿sube o baja al final?)
            # Comparar último 30% vs primer 30%
            split_point = int(len(f0_valid) * 0.3)
            if split_point > 0:
                start_pitch = np.mean(f0_valid[:split_point])
                end_pitch = np.mean(f0_valid[-split_point:])
                pitch_trend = (end_pitch / start_pitch) if start_pitch > 0 else 1.0
            else:
                pitch_trend = 1.0

            return {
                "pitch_contour": f0_valid.tolist()[-50:],  # Últimos 50 puntos
                "pitch_mean": float(np.mean(f0_valid)),
                "pitch_std": float(np.std(f0_valid)),
                "pitch_trend": float(pitch_trend)
            }

        except Exception as e:
            logger.error(f"Error en análisis de pitch: {e}")
            return {
                "pitch_contour": [],
                "pitch_mean": 0,
                "pitch_std": 0,
                "pitch_trend": 1.0
            }

    def _analyze_energy(self, audio: np.ndarray) -> Dict:
        """
        Analiza la energía del audio para detectar voz vs silencio
        """
        # Calcular RMS (Root Mean Square) energy
        rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)[0]

        # Convertir a dB
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)

        # Detectar si hay voz
        has_speech = np.mean(rms_db) > self.silence_threshold

        return {
            "rms": rms,
            "energy_mean": float(np.mean(rms_db)),
            "energy_std": float(np.std(rms_db)),
            "has_speech": has_speech
        }

    def _analyze_pauses(self, audio: np.ndarray, rms: np.ndarray) -> Dict:
        """
        Analiza las pausas en el habla
        """
        # Convertir RMS a dB
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)

        # Detectar frames de silencio
        silence_frames = rms_db < self.silence_threshold

        # Calcular duración del silencio al final
        trailing_silence = 0
        for i in range(len(silence_frames) - 1, -1, -1):
            if silence_frames[i]:
                trailing_silence += 1
            else:
                break

        # Convertir frames a segundos
        hop_length = 512
        pause_duration = trailing_silence * hop_length / self.sample_rate

        # Determinar si es pausa para pensar
        is_thinking_pause = (
            self.thinking_pause_min <= pause_duration <= self.thinking_pause_max
        )

        return {
            "pause_duration": float(pause_duration),
            "is_thinking_pause": is_thinking_pause,
            "silence_ratio": float(np.mean(silence_frames))
        }

    def _estimate_speech_rate(self, audio: np.ndarray, rms: np.ndarray) -> float:
        """
        Estima la velocidad de habla (palabras por minuto)
        Basado en el número de transiciones silencio-voz
        """
        try:
            rms_db = librosa.amplitude_to_db(rms, ref=np.max)
            is_speech = rms_db > self.silence_threshold

            # Contar transiciones (aproximación de sílabas)
            transitions = np.sum(np.abs(np.diff(is_speech.astype(int))))

            # Estimar palabras por minuto
            # Promedio: 2.5 sílabas por palabra, 150 WPM normal
            duration_minutes = len(audio) / (self.sample_rate * 60)
            if duration_minutes > 0:
                syllables_per_min = transitions / duration_minutes
                words_per_min = syllables_per_min / 2.5
                return float(words_per_min)

            return 150.0  # Default

        except Exception:
            return 150.0

    def _analyze_emotional_tone(
        self,
        pitch_std: float,
        energy_mean: float,
        speech_rate: float
    ) -> str:
        """
        Clasifica el tono emocional básico
        """
        # Nervioso: pitch variable + rápido
        if pitch_std > 40 and speech_rate > 180:
            return "nervous"

        # Emocionado: energía alta + rápido
        if energy_mean > -15 and speech_rate > 170:
            return "excited"

        # Calmado: pitch estable + lento
        if pitch_std < 20 and speech_rate < 130:
            return "calm"

        # Preocupado: energía baja + pitch variable
        if energy_mean < -25 and pitch_std > 30:
            return "concerned"

        return "neutral"

    def _detect_question(self, pitch_contour: list, pitch_trend: float) -> bool:
        """
        Detecta si el audio termina con entonación de pregunta

        En español, las preguntas típicamente tienen:
        - Tono ascendente al final (pitch_trend > 1.15)
        - O patrón descendente-ascendente para preguntas con pronombre
        """
        if not pitch_contour or len(pitch_contour) < 5:
            return False

        # Método 1: Tendencia general ascendente
        if pitch_trend > self.question_pitch_rise_threshold:
            return True

        # Método 2: Patrón ascendente en los últimos frames
        last_frames = pitch_contour[-10:] if len(pitch_contour) >= 10 else pitch_contour
        if len(last_frames) >= 3:
            last_third_mean = np.mean(last_frames[-3:])
            middle_third_mean = np.mean(last_frames[:len(last_frames)//2])

            if last_third_mean > middle_third_mean * 1.1:
                return True

        return False

    def _should_wait_for_more(
        self,
        pause_duration: float,
        is_question: bool,
        has_speech: bool
    ) -> bool:
        """
        Determina si debemos esperar más audio antes de procesar

        Casos para esperar:
        1. Pausa corta (< 1.5s) después de hablar - puede continuar
        2. Es una pregunta pero pausa muy corta - puede agregar contexto
        3. Pausa para pensar (0.8-2.5s) - esperar un poco más
        """
        # Si no hay voz, no esperar
        if not has_speech:
            return False

        # Si es pausa muy corta, esperar
        if pause_duration < 0.5:
            return True

        # Si es pregunta con pausa corta/media, esperar un poco
        if is_question and pause_duration < 1.0:
            return True

        # Si es pausa para pensar, esperar
        if self.thinking_pause_min <= pause_duration <= self.thinking_pause_max:
            return True

        # Si pausa larga (> 1.5s), procesar
        if pause_duration >= self.end_of_turn_pause:
            return False

        # Default: esperar si pausa < 1.5s
        return pause_duration < self.end_of_turn_pause

    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """
        Convierte bytes de audio a numpy array
        """
        try:
            # Intentar cargar como WAV
            audio_io = io.BytesIO(audio_bytes)
            audio, sr = librosa.load(audio_io, sr=self.sample_rate, mono=True)
            return audio
        except Exception:
            # Si falla, asumir PCM raw
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
            audio = audio_np.astype(np.float32) / 32768.0
            return audio

    def _empty_analysis(self) -> Dict:
        """
        Retorna análisis vacío para casos de error
        """
        return {
            "is_question": False,
            "has_speech": False,
            "pause_duration": 0.0,
            "is_thinking_pause": False,
            "should_wait": False,
            "pitch_contour": [],
            "pitch_mean": 0.0,
            "pitch_std": 0.0,
            "energy_level": -60.0,
            "speech_rate": 0.0,
            "emotional_tone": "unknown",
            "confidence": 0.0
        }


# Singleton
_prosody_analyzer: Optional[ProsodyAnalyzer] = None


def get_prosody_analyzer() -> ProsodyAnalyzer:
    """
    Obtiene la instancia singleton del analizador
    """
    global _prosody_analyzer
    if _prosody_analyzer is None:
        _prosody_analyzer = ProsodyAnalyzer()
    return _prosody_analyzer
