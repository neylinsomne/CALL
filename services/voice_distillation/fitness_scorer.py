"""
Fitness Scorer
==============
Hybrid scoring function that evaluates how closely a generated voice
matches a target voice. Combines three metrics via harmonic mean:
  - Target similarity (resemblyzer embeddings)
  - Self-similarity (model stability)
  - Feature similarity (acoustic quality)

Inspired by KVoiceWalk's FitnessScorer.
"""

import io
from typing import Dict, Optional, Tuple

import numpy as np
import librosa
import soundfile as sf
from loguru import logger

from config import SCORING_WEIGHTS, SAMPLE_RATE


class FitnessScorer:
    """
    Evaluates voice quality by comparing generated audio against target audio.
    Uses resemblyzer for speaker embeddings and librosa for acoustic features.
    """

    def __init__(self, target_audio_path: str):
        """
        Args:
            target_audio_path: Path to the F5-TTS generated target audio.
        """
        self.target_audio_path = target_audio_path
        self.weights = SCORING_WEIGHTS

        # Load resemblyzer encoder
        from resemblyzer import VoiceEncoder, preprocess_wav
        self.encoder = VoiceEncoder()
        self.preprocess_wav = preprocess_wav

        # Load and embed target audio
        target_wav = preprocess_wav(target_audio_path)
        self.target_embedding = self.encoder.embed_utterance(target_wav)

        # Extract target acoustic features
        target_audio, _ = librosa.load(target_audio_path, sr=SAMPLE_RATE)
        self.target_features = self._extract_features(target_audio)

        logger.info(
            f"FitnessScorer initialized with target: {target_audio_path} "
            f"(embedding shape: {self.target_embedding.shape})"
        )

    def score(
        self,
        audio_a: np.ndarray,
        audio_b: Optional[np.ndarray] = None,
        sample_rate: int = SAMPLE_RATE,
    ) -> Dict:
        """
        Compute hybrid fitness score for generated audio.

        Args:
            audio_a: Primary generated audio sample (float32, mono).
            audio_b: Secondary sample for self-similarity (same voice, different text).
                     If None, self-similarity is set to a default value.
            sample_rate: Audio sample rate.

        Returns:
            Dict with individual scores and overall composite score.
        """
        # Target similarity via resemblyzer
        target_sim = self._target_similarity(audio_a, sample_rate)

        # Self-similarity (consistency check)
        if audio_b is not None:
            self_sim = self._self_similarity(audio_a, audio_b, sample_rate)
        else:
            self_sim = 0.85  # Default assumption

        # Feature similarity (acoustic quality)
        feature_sim = self._feature_similarity(audio_a, sample_rate)

        # Harmonic mean with weights
        overall = self._harmonic_mean(
            values=[target_sim, self_sim, feature_sim],
            weights=[
                self.weights["target_similarity"],
                self.weights["self_similarity"],
                self.weights["feature_similarity"],
            ],
        )

        return {
            "overall": overall,
            "target_similarity": target_sim,
            "self_similarity": self_sim,
            "feature_similarity": feature_sim,
        }

    def _target_similarity(self, audio: np.ndarray, sample_rate: int) -> float:
        """
        Compute cosine similarity between audio embedding and target embedding.
        """
        try:
            # Write to buffer for resemblyzer preprocessing
            buf = io.BytesIO()
            sf.write(buf, audio, sample_rate, format="WAV")
            buf.seek(0)

            wav = self.preprocess_wav(buf)
            if len(wav) < sample_rate * 0.5:  # Too short
                return 0.0

            embedding = self.encoder.embed_utterance(wav)
            similarity = float(np.inner(self.target_embedding, embedding))
            return max(0.0, similarity)
        except Exception as e:
            logger.warning(f"Target similarity error: {e}")
            return 0.0

    def _self_similarity(
        self,
        audio_a: np.ndarray,
        audio_b: np.ndarray,
        sample_rate: int,
    ) -> float:
        """
        Measure consistency: same voice should produce similar embeddings
        regardless of text content.
        """
        try:
            buf_a = io.BytesIO()
            sf.write(buf_a, audio_a, sample_rate, format="WAV")
            buf_a.seek(0)

            buf_b = io.BytesIO()
            sf.write(buf_b, audio_b, sample_rate, format="WAV")
            buf_b.seek(0)

            wav_a = self.preprocess_wav(buf_a)
            wav_b = self.preprocess_wav(buf_b)

            if len(wav_a) < sample_rate * 0.3 or len(wav_b) < sample_rate * 0.3:
                return 0.0

            emb_a = self.encoder.embed_utterance(wav_a)
            emb_b = self.encoder.embed_utterance(wav_b)

            similarity = float(np.inner(emb_a, emb_b))
            return max(0.0, similarity)
        except Exception as e:
            logger.warning(f"Self-similarity error: {e}")
            return 0.0

    def _feature_similarity(self, audio: np.ndarray, sample_rate: int) -> float:
        """
        Compare acoustic features between generated and target audio.
        Uses MFCCs, spectral centroid, pitch, and energy.
        """
        try:
            if sample_rate != SAMPLE_RATE:
                audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=SAMPLE_RATE)

            gen_features = self._extract_features(audio)
            if gen_features is None:
                return 0.0

            # Compute normalized feature distance
            total_penalty = 0.0
            count = 0

            for key in self.target_features:
                if key not in gen_features:
                    continue
                target_val = self.target_features[key]
                gen_val = gen_features[key]

                if abs(target_val) < 1e-10:
                    continue

                # Percentage deviation
                deviation = abs(gen_val - target_val) / (abs(target_val) + 1e-10)
                total_penalty += deviation
                count += 1

            if count == 0:
                return 0.5

            avg_penalty = total_penalty / count
            # Convert penalty to similarity score (0-1)
            similarity = max(0.0, 1.0 - avg_penalty)
            return similarity

        except Exception as e:
            logger.warning(f"Feature similarity error: {e}")
            return 0.5

    def _extract_features(self, audio: np.ndarray) -> Optional[Dict[str, float]]:
        """
        Extract acoustic features from audio for comparison.
        """
        try:
            features = {}

            # MFCCs (mean of first 13 coefficients)
            mfccs = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=13)
            for i in range(13):
                features[f"mfcc_{i}"] = float(np.mean(mfccs[i]))

            # Spectral centroid
            centroid = librosa.feature.spectral_centroid(y=audio, sr=SAMPLE_RATE)
            features["spectral_centroid"] = float(np.mean(centroid))

            # Spectral bandwidth
            bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=SAMPLE_RATE)
            features["spectral_bandwidth"] = float(np.mean(bandwidth))

            # Spectral rolloff
            rolloff = librosa.feature.spectral_rolloff(y=audio, sr=SAMPLE_RATE)
            features["spectral_rolloff"] = float(np.mean(rolloff))

            # RMS energy
            rms = librosa.feature.rms(y=audio)
            features["rms_energy"] = float(np.mean(rms))

            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio)
            features["zero_crossing_rate"] = float(np.mean(zcr))

            # Pitch (F0)
            f0 = librosa.yin(
                audio,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
                sr=SAMPLE_RATE,
            )
            f0_valid = f0[f0 > 0]
            if len(f0_valid) > 0:
                features["pitch_mean"] = float(np.mean(f0_valid))
                features["pitch_std"] = float(np.std(f0_valid))
            else:
                features["pitch_mean"] = 0.0
                features["pitch_std"] = 0.0

            # Spectral contrast
            contrast = librosa.feature.spectral_contrast(y=audio, sr=SAMPLE_RATE)
            for i in range(min(7, contrast.shape[0])):
                features[f"spectral_contrast_{i}"] = float(np.mean(contrast[i]))

            return features

        except Exception as e:
            logger.warning(f"Feature extraction error: {e}")
            return None

    @staticmethod
    def _harmonic_mean(values: list, weights: list) -> float:
        """
        Weighted harmonic mean, scaled to 0-100.
        Allows strategic backsliding on individual metrics while
        maintaining overall improvement direction.
        """
        total_weight = sum(weights)
        weighted_reciprocal_sum = 0.0

        for v, w in zip(values, weights):
            if v <= 0:
                return 0.0
            weighted_reciprocal_sum += w / v

        if weighted_reciprocal_sum <= 0:
            return 0.0

        return (total_weight / weighted_reciprocal_sum) * 100
