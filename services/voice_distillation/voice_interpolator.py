"""
Voice Interpolator
==================
Explores the tensor space between existing Kokoro voices to find
better starting points for the random walk evolution.

Inspired by KVoiceWalk's initial_selector.interpolate_search().
"""

import itertools
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from loguru import logger

from config import (
    KOKORO_LANG, KOKORO_MODEL, KOKORO_BASE_VOICES,
    POPULATION_LIMIT, INTERPOLATED_DIR, SAMPLE_RATE,
)


class VoiceInterpolator:
    """
    Loads existing Kokoro voice tensors, evaluates them against a target,
    and creates interpolated blends as superior starting populations.
    """

    def __init__(
        self,
        scorer,  # FitnessScorer instance
        speech_gen,  # SpeechGenerator instance (Kokoro pipeline wrapper)
        voice_dir: Optional[Path] = None,
    ):
        """
        Args:
            scorer: FitnessScorer for evaluating voice quality.
            speech_gen: SpeechGenerator for Kokoro inference.
            voice_dir: Directory containing .pt voice tensors.
                       If None, uses Kokoro's bundled Spanish voices.
        """
        self.scorer = scorer
        self.speech_gen = speech_gen
        self.voice_dir = voice_dir
        self.voices: Dict[str, torch.Tensor] = {}

    def load_voices(self) -> int:
        """
        Load all available voice tensors.
        Returns number of voices loaded.
        """
        self.voices = {}

        if self.voice_dir and self.voice_dir.exists():
            # Load from custom directory
            for pt_file in sorted(self.voice_dir.glob("*.pt")):
                try:
                    tensor = torch.load(pt_file, map_location="cpu", weights_only=True)
                    self.voices[pt_file.stem] = tensor
                except Exception as e:
                    logger.warning(f"Failed to load {pt_file}: {e}")

        # Load Kokoro's built-in Spanish voices
        try:
            from kokoro import KPipeline
            pipeline = KPipeline(lang_code=KOKORO_LANG, model_id=KOKORO_MODEL)
            for voice_id in KOKORO_BASE_VOICES:
                try:
                    voice_tensor = pipeline.load_voice(voice_id)
                    if voice_tensor is not None:
                        self.voices[voice_id] = voice_tensor
                except Exception as e:
                    logger.warning(f"Failed to load Kokoro voice '{voice_id}': {e}")
        except ImportError:
            logger.warning("Kokoro not available, using only custom voices")

        logger.info(f"Loaded {len(self.voices)} voices: {list(self.voices.keys())}")
        return len(self.voices)

    def evaluate_voices(self, test_text: str) -> List[Tuple[str, float, torch.Tensor]]:
        """
        Score each loaded voice against the target.

        Args:
            test_text: Text to synthesize for evaluation.

        Returns:
            Sorted list of (voice_id, score, tensor) tuples, best first.
        """
        results = []

        for voice_id, tensor in self.voices.items():
            try:
                audio = self.speech_gen.generate(test_text, tensor)
                if audio is None or len(audio) < SAMPLE_RATE * 0.3:
                    continue

                score_result = self.scorer.score(audio)
                overall = score_result["overall"]
                results.append((voice_id, overall, tensor))
                logger.info(
                    f"  Voice '{voice_id}': overall={overall:.2f} "
                    f"(target={score_result['target_similarity']:.3f}, "
                    f"features={score_result['feature_similarity']:.3f})"
                )
            except Exception as e:
                logger.warning(f"  Voice '{voice_id}' evaluation failed: {e}")

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def interpolate_search(
        self,
        test_text: str,
        output_dir: Path = INTERPOLATED_DIR,
        alpha_range: Tuple[float, float] = (-1.5, 1.5),
        alpha_steps: int = 7,
    ) -> List[Tuple[str, float, torch.Tensor]]:
        """
        Create interpolated voices from pairs of existing voices and
        evaluate them against the target.

        Interpolation formula:
            midpoint = (voice_a + voice_b) / 2
            diff = voice_a - voice_b
            interpolated = midpoint + (diff * alpha / 2)

        With alpha=0: exact midpoint
        With alpha=1: voice_a
        With alpha=-1: voice_b
        With |alpha|>1: extrapolation beyond the pair

        Returns:
            Top N interpolated voices sorted by score.
        """
        if len(self.voices) < 2:
            logger.warning("Need at least 2 voices for interpolation")
            return self.evaluate_voices(test_text)

        # First, rank existing voices
        ranked = self.evaluate_voices(test_text)
        # Use top voices for interpolation
        top_voices = ranked[:min(len(ranked), POPULATION_LIMIT)]

        logger.info(
            f"Interpolating between top {len(top_voices)} voices "
            f"(alpha range: {alpha_range}, steps: {alpha_steps})"
        )

        alphas = np.linspace(alpha_range[0], alpha_range[1], alpha_steps)
        all_results = list(top_voices)  # Start with original voices

        for (id_a, score_a, tensor_a), (id_b, score_b, tensor_b) in itertools.combinations(top_voices, 2):
            midpoint = (tensor_a + tensor_b) / 2.0
            diff = tensor_a - tensor_b

            for alpha in alphas:
                if abs(alpha) < 0.1:  # Skip near-midpoint (already covered)
                    continue

                interpolated = midpoint + (diff * alpha / 2.0)
                interp_name = f"{id_a}_x_{id_b}_a{alpha:.2f}"

                try:
                    audio = self.speech_gen.generate(test_text, interpolated)
                    if audio is None or len(audio) < SAMPLE_RATE * 0.3:
                        continue

                    score_result = self.scorer.score(audio)
                    overall = score_result["overall"]
                    all_results.append((interp_name, overall, interpolated))

                    if overall > max(score_a, score_b):
                        logger.info(
                            f"  Interpolation '{interp_name}': {overall:.2f} "
                            f"(better than parents {score_a:.2f}, {score_b:.2f})"
                        )
                except Exception as e:
                    logger.debug(f"  Interpolation '{interp_name}' failed: {e}")

        # Sort by score and return top N
        all_results.sort(key=lambda x: x[1], reverse=True)
        best = all_results[:POPULATION_LIMIT]

        # Save best interpolations to disk
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, score, tensor in best:
            save_path = output_dir / f"{name}.pt"
            torch.save(tensor, save_path)
            logger.info(f"Saved interpolated voice: {name} (score: {score:.2f})")

        return best

    def get_statistics(self) -> Dict:
        """
        Compute statistics across all loaded voice tensors.
        Used by the evolver for mutation scaling.
        """
        if not self.voices:
            return {"mean": None, "std": None, "min": None, "max": None}

        tensors = list(self.voices.values())
        stacked = torch.stack(tensors)

        return {
            "mean": stacked.mean(dim=0),
            "std": stacked.std(dim=0),
            "min": stacked.min(dim=0).values,
            "max": stacked.max(dim=0).values,
            "count": len(tensors),
        }
