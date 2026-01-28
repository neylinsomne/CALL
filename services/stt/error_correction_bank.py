"""
Banco de Vectores para Corrección de Errores Comunes en STT
Usa embeddings para detectar y corregir errores fonéticos automáticamente
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import json
import os
from pathlib import Path
from loguru import logger

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    VECTORIZATION_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers o faiss no disponible. Error correction limitado.")
    VECTORIZATION_AVAILABLE = False


class ErrorCorrectionBank:
    """
    Banco de vectores con errores comunes y sus correcciones
    Aprende de correcciones pasadas para mejorar continuamente
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.vectorization_enabled = VECTORIZATION_AVAILABLE

        # Banco de errores comunes → corrección (español call center)
        self.error_patterns = {
            # Confusiones fonéticas comunes
            "cuesta": "cuenta",
            "cuanta": "cuenta",
            "salgo": "saldo",
            "saldo": "saldo",  # Normalización
            "i-mail": "email",
            "imeil": "email",
            "e-mail": "email",
            "correo electrónico": "email",
            "contra seña": "contraseña",
            "contraseña": "contraseña",  # Normalización
            "pass word": "password",
            "usuario": "usuario",  # Normalización
            "user": "usuario",
            "PIN": "pin",
            "pin": "pin",
            "cancelar la": "cancelar",
            "borrar la": "borrar",
            "borrar mi": "borrar",
            "eliminar mi": "eliminar",

            # Números confusos
            "seiscientos": "600",
            "setecientos": "700",
            "ochocientos": "800",
            "novecientos": "900",

            # Acciones comunes
            "devolver": "reembolso",
            "regresar dinero": "reembolso",
            "factura": "factura",
            "recibo": "factura",

            # Términos técnicos
            "wi-fi": "wifi",
            "why-fi": "wifi",
            "router": "router",
            "rooter": "router",
            "módem": "modem",

            # Confusiones temporales
            "hay": "ahí",
            "ahí": "ahí",
            "aya": "haya",
            "echo": "hecho",
        }

        # Path para guardar patrones aprendidos
        self.learned_patterns_path = Path("models/learned_error_patterns.json")
        self._load_learned_patterns()

        if self.vectorization_enabled:
            try:
                self.model = SentenceTransformer(model_name)
                self.index = None
                self.error_texts = []
                self._build_index()
                logger.info(f"Error correction bank initialized with {len(self.error_patterns)} patterns")
            except Exception as e:
                logger.error(f"Error loading sentence transformer: {e}")
                self.vectorization_enabled = False

    def _load_learned_patterns(self):
        """Carga patrones aprendidos de correcciones anteriores"""
        if self.learned_patterns_path.exists():
            try:
                with open(self.learned_patterns_path, 'r', encoding='utf-8') as f:
                    learned = json.load(f)
                    self.error_patterns.update(learned)
                    logger.info(f"Loaded {len(learned)} learned error patterns")
            except Exception as e:
                logger.error(f"Error loading learned patterns: {e}")

    def _save_learned_patterns(self):
        """Guarda patrones aprendidos para persistencia"""
        try:
            self.learned_patterns_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.learned_patterns_path, 'w', encoding='utf-8') as f:
                json.dump(self.error_patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving learned patterns: {e}")

    def _build_index(self):
        """Construye índice FAISS de vectores de errores"""
        if not self.vectorization_enabled:
            return

        try:
            # Generar embeddings de errores
            self.error_texts = list(self.error_patterns.keys())
            error_embeddings = self.model.encode(self.error_texts, show_progress_bar=False)

            # Crear índice FAISS
            dimension = error_embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(error_embeddings.astype('float32'))

            logger.debug(f"FAISS index built with {len(self.error_texts)} entries")
        except Exception as e:
            logger.error(f"Error building FAISS index: {e}")
            self.vectorization_enabled = False

    def correct_transcription(
        self,
        text: str,
        distance_threshold: float = 0.7,
        confidence_scores: Optional[List[Dict]] = None
    ) -> Tuple[str, List[Dict]]:
        """
        Corrige errores comunes en la transcripción

        Args:
            text: Texto a corregir
            distance_threshold: Umbral de similitud (0-1, menor = más estricto)
            confidence_scores: Scores de confianza por palabra

        Returns:
            (texto_corregido, lista_de_correcciones)
        """
        words = text.split()
        corrected_words = []
        corrections_made = []

        for i, word in enumerate(words):
            word_lower = word.lower()

            # Priorizar palabras con baja confianza
            priority = False
            if confidence_scores and i < len(confidence_scores):
                if confidence_scores[i].get("confidence", 1.0) < 0.7:
                    priority = True

            # 1. Búsqueda exacta en el diccionario
            if word_lower in self.error_patterns:
                correction = self.error_patterns[word_lower]
                corrected_words.append(correction)
                corrections_made.append({
                    "original": word,
                    "correction": correction,
                    "method": "exact_match",
                    "position": i
                })
                logger.debug(f"Exact correction: '{word}' → '{correction}'")
                continue

            # 2. Búsqueda por vectores (si está disponible y es prioritario)
            if self.vectorization_enabled and (priority or len(word) > 3):
                correction = self._vector_search_correction(word_lower, distance_threshold)
                if correction:
                    corrected_words.append(correction)
                    corrections_made.append({
                        "original": word,
                        "correction": correction,
                        "method": "vector_match",
                        "position": i
                    })
                    logger.debug(f"Vector correction: '{word}' → '{correction}'")
                    continue

            # 3. No hay corrección, mantener palabra original
            corrected_words.append(word)

        corrected_text = " ".join(corrected_words)
        return corrected_text, corrections_made

    def _vector_search_correction(self, word: str, threshold: float) -> Optional[str]:
        """Busca corrección usando similitud de vectores"""
        if not self.vectorization_enabled or self.index is None:
            return None

        try:
            # Generar embedding de la palabra
            word_embedding = self.model.encode([word], show_progress_bar=False)

            # Buscar en el índice
            distances, indices = self.index.search(word_embedding.astype('float32'), k=1)

            # Si hay match cercano
            distance = distances[0][0]
            if distance < threshold:
                error_key = self.error_texts[indices[0][0]]
                correction = self.error_patterns[error_key]
                return correction

        except Exception as e:
            logger.error(f"Error in vector search: {e}")

        return None

    def add_error_pattern(self, error: str, correction: str, save: bool = True):
        """
        Añade nuevo patrón de error al banco (aprendizaje)

        Args:
            error: Palabra incorrecta
            correction: Corrección
            save: Si guardar en disco para persistencia
        """
        error_lower = error.lower()
        correction_lower = correction.lower()

        # Evitar agregar el mismo patrón
        if error_lower == correction_lower:
            return

        self.error_patterns[error_lower] = correction_lower
        logger.info(f"Learned new error pattern: '{error}' → '{correction}'")

        # Reconstruir índice
        if self.vectorization_enabled:
            self._build_index()

        # Guardar en disco
        if save:
            self._save_learned_patterns()

    def learn_from_clarification(
        self,
        original_transcription: str,
        corrected_transcription: str
    ):
        """
        Aprende de una corrección del usuario

        Args:
            original_transcription: Lo que el STT transcribió
            corrected_transcription: Lo que el usuario dijo realmente
        """
        orig_words = original_transcription.lower().split()
        corr_words = corrected_transcription.lower().split()

        # Encontrar palabras que cambiaron
        if len(orig_words) != len(corr_words):
            # Longitud diferente, difícil de alinear
            logger.warning("Transcriptions have different lengths, skipping learning")
            return

        for orig, corr in zip(orig_words, corr_words):
            if orig != corr:
                # Añadir al banco de errores
                self.add_error_pattern(orig, corr, save=True)

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas del banco de errores"""
        return {
            "total_patterns": len(self.error_patterns),
            "vectorization_enabled": self.vectorization_enabled,
            "learned_patterns_file": str(self.learned_patterns_path),
            "index_size": len(self.error_texts) if self.error_texts else 0
        }


# Singleton
_error_bank: Optional[ErrorCorrectionBank] = None


def get_error_bank() -> ErrorCorrectionBank:
    """Obtiene instancia singleton del banco de errores"""
    global _error_bank
    if _error_bank is None:
        _error_bank = ErrorCorrectionBank()
    return _error_bank
