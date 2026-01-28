"""
Sistema Híbrido de Corrección de Errores
Combina 3 métodos: Exacto → Vectorial → Fonético
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from loguru import logger

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    VECTORIZATION_AVAILABLE = True
except ImportError:
    VECTORIZATION_AVAILABLE = False

try:
    import phonetics
    PHONETIC_AVAILABLE = True
except ImportError:
    PHONETIC_AVAILABLE = False


class HybridErrorCorrector:
    """
    Sistema de corrección multi-nivel para máxima precisión
    """

    def __init__(self):
        # Nivel 1: Diccionario exacto (O(1) lookup)
        self.exact_corrections = {
            # Errores comunes conocidos
            "salgo": "saldo",
            "cuesta": "cuenta",
            "cuanta": "cuenta",
            "imeil": "email",
            "i-mail": "email",
            "contra seña": "contraseña",
        }

        # Nivel 2: Búsqueda vectorial (embeddings)
        self.vectorization_enabled = VECTORIZATION_AVAILABLE
        if self.vectorization_enabled:
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self._build_vector_index()

        # Nivel 3: Búsqueda fonética
        self.phonetic_enabled = PHONETIC_AVAILABLE

        # Estadísticas
        self.stats = {
            "exact_matches": 0,
            "vector_matches": 0,
            "phonetic_matches": 0,
            "no_correction": 0
        }

    def _build_vector_index(self):
        """Construye índice FAISS con patrones comunes"""
        # Expandir diccionario con variaciones
        self.vector_patterns = {
            "saldo": "saldo",
            "salgo": "saldo",
            "salgó": "saldo",
            "cuenta": "cuenta",
            "cuesta": "cuenta",
            "cuanta": "cuenta",
            "email": "email",
            "imeil": "email",
            "e-mail": "email",
            "correo": "email",
            "contraseña": "contraseña",
            "contra seña": "contraseña",
            "password": "contraseña",
            "usuario": "usuario",
            "user": "usuario",
            "cancelar": "cancelar",
            "cansalar": "cancelar",
            "eliminar": "eliminar",
            "borrar": "eliminar",
        }

        # Generar embeddings
        self.pattern_texts = list(self.vector_patterns.keys())
        embeddings = self.model.encode(self.pattern_texts)

        # Crear índice FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))

        logger.info(f"Vector index built with {len(self.pattern_texts)} patterns")

    def correct_word(
        self,
        word: str,
        confidence: float = 1.0,
        context: Optional[List[str]] = None
    ) -> Tuple[str, str, float]:
        """
        Corrige una palabra usando sistema multi-nivel

        Returns:
            (corrected_word, method_used, correction_confidence)
        """
        word_lower = word.lower().strip()

        # Solo corregir si baja confianza
        if confidence > 0.85:
            self.stats["no_correction"] += 1
            return word, "no_correction", confidence

        # NIVEL 1: Búsqueda exacta (más rápido, 95% de casos)
        if word_lower in self.exact_corrections:
            self.stats["exact_matches"] += 1
            return self.exact_corrections[word_lower], "exact_match", 1.0

        # NIVEL 2: Búsqueda vectorial (4% de casos, errores similares)
        if self.vectorization_enabled and confidence < 0.7:
            correction, dist = self._vector_search(word_lower)
            if correction and dist < 0.7:  # Threshold ajustable
                self.stats["vector_matches"] += 1
                correction_conf = 1.0 - (dist / 2.0)  # Normalizar a [0,1]
                return correction, "vector_similarity", correction_conf

        # NIVEL 3: Búsqueda fonética (1% de casos, homofonía)
        if self.phonetic_enabled and confidence < 0.6:
            correction = self._phonetic_search(word_lower)
            if correction:
                self.stats["phonetic_matches"] += 1
                return correction, "phonetic_match", 0.75

        # Sin corrección encontrada
        self.stats["no_correction"] += 1
        return word, "no_correction", confidence

    def _vector_search(self, word: str) -> Tuple[Optional[str], float]:
        """
        Búsqueda por similitud vectorial usando FAISS

        Returns:
            (correction, distance)
        """
        try:
            # Convertir palabra a embedding
            word_embedding = self.model.encode([word])

            # Buscar k vecinos más cercanos
            k = 3  # Top 3 candidatos
            distances, indices = self.index.search(
                word_embedding.astype('float32'),
                k
            )

            # Retornar el más cercano
            if len(distances[0]) > 0:
                best_idx = indices[0][0]
                best_dist = distances[0][0]
                pattern_key = self.pattern_texts[best_idx]
                correction = self.vector_patterns[pattern_key]

                logger.debug(f"Vector match: '{word}' → '{correction}' (dist: {best_dist:.3f})")
                return correction, float(best_dist)

        except Exception as e:
            logger.error(f"Error in vector search: {e}")

        return None, float('inf')

    def _phonetic_search(self, word: str) -> Optional[str]:
        """
        Búsqueda fonética (palabras que suenan similar)

        Útil para homofonía: cuenta/cuesta, hay/ahí
        """
        if not self.phonetic_enabled:
            return None

        try:
            word_phonetic = phonetics.metaphone(word)

            # Buscar en patrones exactos
            for pattern_word, correction in self.exact_corrections.items():
                if phonetics.metaphone(pattern_word) == word_phonetic:
                    logger.debug(f"Phonetic match: '{word}' → '{correction}'")
                    return correction

        except Exception as e:
            logger.debug(f"Phonetic search failed: {e}")

        return None

    def correct_text(
        self,
        text: str,
        word_confidences: Optional<List[Dict]] = None
    ) -> Tuple[str, List[Dict]]:
        """
        Corrige un texto completo palabra por palabra

        Args:
            text: Texto transcrito
            word_confidences: Lista de {"word": str, "confidence": float}

        Returns:
            (corrected_text, corrections_made)
        """
        words = text.split()
        corrected_words = []
        corrections_made = []

        for i, word in enumerate(words):
            # Obtener confianza de esta palabra
            confidence = 1.0
            if word_confidences:
                word_conf = next(
                    (w for w in word_confidences if w["word"].strip().lower() == word.lower()),
                    None
                )
                if word_conf:
                    confidence = word_conf["confidence"]

            # Corregir palabra
            corrected, method, corr_confidence = self.correct_word(
                word,
                confidence=confidence,
                context=words[max(0, i-2):i]  # 2 palabras de contexto
            )

            corrected_words.append(corrected)

            # Registrar corrección si hubo cambio
            if corrected.lower() != word.lower():
                corrections_made.append({
                    "original": word,
                    "corrected": corrected,
                    "method": method,
                    "original_confidence": confidence,
                    "correction_confidence": corr_confidence,
                    "position": i
                })

        return " ".join(corrected_words), corrections_made

    def get_stats(self) -> Dict:
        """Retorna estadísticas de uso"""
        total = sum(self.stats.values())
        return {
            "total_corrections": total,
            "exact_matches": self.stats["exact_matches"],
            "vector_matches": self.stats["vector_matches"],
            "phonetic_matches": self.stats["phonetic_matches"],
            "no_correction": self.stats["no_correction"],
            "exact_percentage": (self.stats["exact_matches"] / total * 100) if total > 0 else 0,
            "vector_percentage": (self.stats["vector_matches"] / total * 100) if total > 0 else 0,
        }


# ==================================================
# Comparación de Métodos de Distancia
# ==================================================

class DistanceComparison:
    """
    Compara diferentes métricas de distancia para corrección de errores
    """

    @staticmethod
    def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Distancia L2 (Euclidiana)
        Mide distancia geométrica directa entre vectores
        """
        return np.linalg.norm(vec1 - vec2)

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Similitud de Coseno
        Mide ángulo entre vectores (ignora magnitud)
        Retorna: 1.0 = idénticos, 0.0 = ortogonales, -1.0 = opuestos
        """
        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        return dot_product / norm_product if norm_product > 0 else 0.0

    @staticmethod
    def manhattan_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Distancia L1 (Manhattan)
        Suma de diferencias absolutas
        """
        return np.sum(np.abs(vec1 - vec2))

    @staticmethod
    def levenshtein_distance(str1: str, str2: str) -> int:
        """
        Distancia de edición (caracteres)
        Mínimo número de operaciones para transformar str1 en str2
        """
        if len(str1) < len(str2):
            return DistanceComparison.levenshtein_distance(str2, str1)

        if len(str2) == 0:
            return len(str1)

        previous_row = range(len(str2) + 1)
        for i, c1 in enumerate(str1):
            current_row = [i + 1]
            for j, c2 in enumerate(str2):
                # Costo de insertar, eliminar, sustituir
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def compare_methods(word1: str, word2: str, model: SentenceTransformer):
        """
        Compara todos los métodos de distancia para dos palabras
        """
        # Embeddings para métodos vectoriales
        emb1 = model.encode([word1])[0]
        emb2 = model.encode([word2])[0]

        results = {
            "words": (word1, word2),
            "euclidean": DistanceComparison.euclidean_distance(emb1, emb2),
            "cosine_similarity": DistanceComparison.cosine_similarity(emb1, emb2),
            "manhattan": DistanceComparison.manhattan_distance(emb1, emb2),
            "levenshtein": DistanceComparison.levenshtein_distance(word1, word2),
            "levenshtein_normalized": DistanceComparison.levenshtein_distance(word1, word2) / max(len(word1), len(word2))
        }

        return results


# Singleton
_hybrid_corrector: Optional[HybridErrorCorrector] = None


def get_hybrid_corrector() -> HybridErrorCorrector:
    """Obtiene instancia singleton del corrector híbrido"""
    global _hybrid_corrector
    if _hybrid_corrector is None:
        _hybrid_corrector = HybridErrorCorrector()
    return _hybrid_corrector


# ==================================================
# Ejemplo de Uso
# ==================================================

if __name__ == "__main__":
    # Test del sistema híbrido
    corrector = HybridErrorCorrector()

    # Test casos
    test_cases = [
        ("Necesito revisar el salgo de mi cuesta", [
            {"word": "salgo", "confidence": 0.45},
            {"word": "cuesta", "confidence": 0.52}
        ]),
        ("Olvidé mi contra seña del i-mail", [
            {"word": "contra", "confidence": 0.6},
            {"word": "seña", "confidence": 0.55},
            {"word": "i-mail", "confidence": 0.4}
        ])
    ]

    for text, confidences in test_cases:
        print(f"\nOriginal: {text}")
        corrected, corrections = corrector.correct_text(text, confidences)
        print(f"Corregido: {corrected}")
        print(f"Correcciones: {corrections}")

    # Estadísticas
    print(f"\nEstadísticas: {corrector.get_stats()}")

    # Comparación de métricas
    if VECTORIZATION_AVAILABLE:
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        pairs = [
            ("salgo", "saldo"),
            ("cuesta", "cuenta"),
            ("email", "imeil"),
            ("hola", "adiós")  # Control negativo
        ]

        print("\n=== Comparación de Métricas de Distancia ===")
        for word1, word2 in pairs:
            results = DistanceComparison.compare_methods(word1, word2, model)
            print(f"\n'{word1}' vs '{word2}':")
            print(f"  Euclidiana: {results['euclidean']:.3f}")
            print(f"  Coseno: {results['cosine_similarity']:.3f}")
            print(f"  Manhattan: {results['manhattan']:.3f}")
            print(f"  Levenshtein: {results['levenshtein']} ediciones")
            print(f"  Levenshtein norm: {results['levenshtein_normalized']:.3f}")
