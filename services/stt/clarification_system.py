"""
Sistema de Clarificación Inteligente
Decide cuándo pedir al usuario que repita basándose en confidence scores
"""

from typing import Dict, List, Optional
import numpy as np
from loguru import logger


class ClarificationSystem:
    """
    Sistema inteligente que decide cuándo pedir clarificación
    basado en confidence scores y contexto semántico
    """

    def __init__(self):
        # Thresholds ajustables
        self.confidence_threshold = 0.7
        self.critical_confidence_threshold = 0.5
        self.semantic_coherence_threshold = 0.6

        # Palabras que si se escuchan mal, arruinan la conversación
        self.critical_words = {
            "números": ["cuenta", "número", "código", "pin", "clave", "tarjeta", "cvv"],
            "acciones": ["cancelar", "eliminar", "transferir", "pagar", "borrar", "comprar"],
            "negaciones": ["no", "nunca", "ningún", "jamás"],
            "confirmaciones": ["sí", "confirmo", "acepto", "autorizo"],
            "cantidades": ["mil", "millón", "cientos", "pesos", "dólares", "euros"]
        }

        # Contador de clarificaciones por conversación (no abusar)
        self.clarification_counts = {}
        self.max_clarifications_per_conversation = 3

    def should_ask_clarification(
        self,
        transcription: str,
        word_confidences: List[Dict],
        conversation_id: str,
        conversation_context: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Determina si debemos pedir clarificación

        Args:
            transcription: Texto transcrito
            word_confidences: Lista de {"word": str, "confidence": float, "start": float, "end": float}
            conversation_id: ID de la conversación
            conversation_context: Mensajes previos

        Returns:
            None si todo está claro
            Dict con estrategia de clarificación si hay dudas
        """

        # Verificar límite de clarificaciones
        if self._has_exceeded_clarification_limit(conversation_id):
            logger.warning(f"[{conversation_id}] Max clarifications reached, skipping")
            return None

        # 1. Verificar si hay palabras con confianza baja
        low_confidence_words = [
            w for w in word_confidences
            if w["confidence"] < self.confidence_threshold
        ]

        if not low_confidence_words:
            return None  # Todo claro

        # 2. Calcular confianza promedio
        avg_confidence = np.mean([w["confidence"] for w in word_confidences])

        # 3. Verificar si son palabras críticas
        critical_issues = self._check_critical_words(low_confidence_words)

        if critical_issues:
            self._increment_clarification_count(conversation_id)
            return {
                "type": "critical_word_unclear",
                "strategy": "explicit_confirmation",
                "words": critical_issues,
                "confidence": avg_confidence,
                "prompt": self._generate_confirmation_prompt(critical_issues[0], transcription)
            }

        # 4. Verificar coherencia semántica
        if self._is_semantically_broken(transcription, word_confidences):
            self._increment_clarification_count(conversation_id)
            return {
                "type": "semantic_incoherence",
                "strategy": "full_repeat",
                "confidence": avg_confidence,
                "prompt": "Disculpa, hubo interferencia. ¿Puedes repetir lo que dijiste?"
            }

        # 5. Si confianza global muy baja
        if avg_confidence < 0.5:
            self._increment_clarification_count(conversation_id)
            return {
                "type": "low_overall_confidence",
                "strategy": "implicit_clarification",
                "confidence": avg_confidence,
                "prompt": self._generate_implicit_prompt(transcription)
            }

        # 6. Verificar si hay números con baja confianza
        numbers_issue = self._check_numbers(transcription, low_confidence_words)
        if numbers_issue:
            self._increment_clarification_count(conversation_id)
            return {
                "type": "number_unclear",
                "strategy": "spell_out",
                "confidence": avg_confidence,
                "prompt": numbers_issue["prompt"]
            }

        return None  # Confianza suficiente

    def _check_critical_words(self, low_conf_words: List[Dict]) -> List[str]:
        """Identifica si hay palabras críticas con baja confianza"""
        critical = []
        for word_data in low_conf_words:
            word = word_data["word"].lower().strip()

            # Verificar contra todas las categorías críticas
            for category, words_list in self.critical_words.items():
                if any(crit in word or word in crit for crit in words_list):
                    if word not in critical:
                        critical.append(word)

        return critical

    def _is_semantically_broken(self, text: str, word_confidences: List[Dict]) -> bool:
        """Detecta si el texto no tiene sentido semántico"""
        words = text.split()

        # Texto muy corto
        if len(words) < 3:
            return False  # Muy corto para juzgar

        # Muchas repeticiones (alucinación del modelo)
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.5:
            logger.warning(f"High repetition detected: {text}")
            return True

        # Muchas palabras de una sola letra (gibberish)
        single_char_words = [w for w in words if len(w) == 1 and w not in ["y", "o", "a"]]
        if len(single_char_words) / len(words) > 0.3:
            logger.warning(f"Too many single-char words: {text}")
            return True

        # Confianza muy variable (señal de audio inconsistente)
        confidences = [w["confidence"] for w in word_confidences]
        if len(confidences) > 2:
            confidence_std = np.std(confidences)
            if confidence_std > 0.35:  # Alta variabilidad
                logger.warning(f"High confidence variance: std={confidence_std:.2f}")
                return True

        return False

    def _check_numbers(self, text: str, low_conf_words: List[Dict]) -> Optional[Dict]:
        """Verifica si hay números con baja confianza"""
        import re

        # Buscar números en el texto
        number_pattern = r'\b\d+\b'
        numbers = re.findall(number_pattern, text)

        if not numbers:
            return None

        # Verificar si algún número tiene baja confianza
        for word_data in low_conf_words:
            word = word_data["word"].strip()
            if any(char.isdigit() for char in word):
                return {
                    "number": word,
                    "prompt": f"¿Puedes repetir el número? Escuché '{word}' pero quiero confirmarlo."
                }

        # Verificar si hay palabras numéricas en español con baja confianza
        spanish_numbers = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez"]
        for word_data in low_conf_words:
            word = word_data["word"].lower().strip()
            if word in spanish_numbers:
                return {
                    "number": word,
                    "prompt": "¿Puedes deletrear el código o número dígito por dígito?"
                }

        return None

    def _generate_confirmation_prompt(self, critical_word: str, full_text: str) -> str:
        """Genera prompt para confirmar palabra crítica"""
        word_lower = critical_word.lower()

        # Templates específicos según tipo de palabra crítica
        if word_lower in ["cancelar", "eliminar", "borrar"]:
            return f"Entendí que quieres '{critical_word}'. ¿Es correcto? Es una acción importante y quiero confirmar."

        elif word_lower in ["no", "nunca", "ningún"]:
            return f"¿Dijiste '{critical_word}'? Quiero asegurarme antes de continuar."

        elif word_lower in ["sí", "confirmo", "acepto"]:
            return f"¿Confirmas que deseas proceder? Entendí '{critical_word}'."

        elif word_lower in ["pagar", "transferir", "comprar"]:
            return f"Entendí que quieres '{critical_word}'. ¿Puedes confirmarlo?"

        elif any(char.isdigit() for char in critical_word):
            return f"¿Puedes repetir el número '{critical_word}'? Quiero asegurarme."

        else:
            return f"¿Dijiste '{critical_word}'? Quiero confirmarlo."

    def _generate_implicit_prompt(self, transcription: str) -> str:
        """Genera prompt implícito que repite lo entendido (menos agresivo)"""
        # Acortar si es muy largo
        if len(transcription) > 100:
            transcription = transcription[:100] + "..."

        return f"Entiendo que {transcription}. ¿Es correcto?"

    def _has_exceeded_clarification_limit(self, conversation_id: str) -> bool:
        """Verifica si ya pedimos demasiadas clarificaciones"""
        count = self.clarification_counts.get(conversation_id, 0)
        return count >= self.max_clarifications_per_conversation

    def _increment_clarification_count(self, conversation_id: str):
        """Incrementa contador de clarificaciones"""
        if conversation_id not in self.clarification_counts:
            self.clarification_counts[conversation_id] = 0
        self.clarification_counts[conversation_id] += 1

    def reset_conversation(self, conversation_id: str):
        """Resetea contador de clarificaciones para una conversación"""
        if conversation_id in self.clarification_counts:
            del self.clarification_counts[conversation_id]


# Singleton
_clarification_system: Optional[ClarificationSystem] = None


def get_clarification_system() -> ClarificationSystem:
    """Obtiene instancia singleton del sistema de clarificación"""
    global _clarification_system
    if _clarification_system is None:
        _clarification_system = ClarificationSystem()
    return _clarification_system
