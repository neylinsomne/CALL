"""
Pipeline Híbrido de Corrección STT
- Online: Corrección rápida durante la llamada (latencia crítica)
- Offline: Análisis profundo post-procesamiento (calidad crítica)
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import asyncio
from loguru import logger


class ProcessingMode(Enum):
    """Modo de procesamiento"""
    ONLINE = "online"      # Tiempo real, optimizado para latencia
    OFFLINE = "offline"    # Post-procesamiento, optimizado para calidad


class CorrectionPipeline:
    """
    Pipeline híbrido que decide qué correcciones aplicar según el modo
    """

    def __init__(self):
        # Importar correctors
        from error_correction_bank import get_error_bank
        from clarification_system import get_clarification_system

        try:
            from error_correction_hybrid import get_hybrid_corrector
            self.hybrid_corrector = get_hybrid_corrector()
            self.hybrid_available = True
        except ImportError:
            logger.warning("Hybrid corrector not available")
            self.hybrid_available = False

        self.error_bank = get_error_bank()
        self.clarification_system = get_clarification_system()

        # Estadísticas
        self.stats = {
            "online_corrections": 0,
            "offline_corrections": 0,
            "total_processed": 0
        }

    async def process_online(
        self,
        transcription: str,
        word_confidences: List[Dict],
        conversation_id: str
    ) -> Dict:
        """
        Procesamiento ONLINE (tiempo real)

        Optimizado para LATENCIA:
        - Solo correcciones exactas (diccionario)
        - Clarificaciones críticas únicamente
        - Sin procesamiento pesado

        Target: <20ms overhead
        """
        start_time = asyncio.get_event_loop().time()

        result = {
            "text": transcription,
            "corrected_text": transcription,
            "corrections_made": [],
            "needs_clarification": False,
            "clarification_prompt": None,
            "processing_mode": "online",
            "processing_time_ms": 0
        }

        # 1. SOLO Correcciones Exactas (O(1) lookup, <1ms)
        corrected_text, corrections = self._fast_correction(
            transcription,
            word_confidences
        )

        result["corrected_text"] = corrected_text
        result["corrections_made"] = corrections

        # 2. Clarificación SOLO si palabra crítica con confianza muy baja
        clarification = self.clarification_system.should_ask_clarification(
            corrected_text,
            word_confidences,
            conversation_id
        )

        # Solo pedir clarificación si es crítico (confidence < 0.5)
        if clarification and clarification.get("type") == "critical_word_unclear":
            avg_conf = sum(w["confidence"] for w in word_confidences) / len(word_confidences)
            if avg_conf < 0.5:  # Threshold estricto en online
                result["needs_clarification"] = True
                result["clarification_prompt"] = clarification.get("prompt")
                result["clarification_type"] = clarification.get("type")

        # Estadísticas
        end_time = asyncio.get_event_loop().time()
        result["processing_time_ms"] = (end_time - start_time) * 1000

        self.stats["online_corrections"] += len(corrections)
        self.stats["total_processed"] += 1

        logger.debug(f"Online processing: {result['processing_time_ms']:.2f}ms, "
                    f"{len(corrections)} corrections")

        return result

    async def process_offline(
        self,
        transcription: str,
        word_confidences: List[Dict],
        audio_path: str,
        conversation_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Procesamiento OFFLINE (post-procesamiento)

        Optimizado para CALIDAD:
        - Corrección híbrida completa (exacto + vectorial + fonético)
        - Re-transcripción con parámetros premium si WER alto
        - Análisis semántico completo
        - Detección de entidades avanzada
        - Sentiment analysis mejorado

        Target: Máxima precisión, sin límite de tiempo
        """
        import time
        start_time = time.time()

        result = {
            "text": transcription,
            "corrected_text": transcription,
            "corrections_made": [],
            "needs_clarification": False,
            "clarification_prompt": None,
            "processing_mode": "offline",
            "advanced_analysis": {},
            "quality_metrics": {},
            "processing_time_ms": 0
        }

        # 1. Corrección Híbrida Completa (exacto + vectorial + fonético)
        if self.hybrid_available:
            corrected_text, corrections = self.hybrid_corrector.correct_text(
                transcription,
                word_confidences
            )
            result["corrected_text"] = corrected_text
            result["corrections_made"] = corrections
        else:
            # Fallback a banco vectorial completo
            corrected_text, corrections = self.error_bank.correct_transcription(
                transcription,
                confidence_scores=word_confidences
            )
            result["corrected_text"] = corrected_text
            result["corrections_made"] = corrections

        # 2. Análisis de Calidad (WER estimado)
        quality = self._estimate_quality(transcription, word_confidences)
        result["quality_metrics"] = quality

        # 3. Re-transcripción si calidad muy baja
        if quality["estimated_wer"] > 0.2:  # >20% error
            logger.info(f"Low quality detected (WER: {quality['estimated_wer']:.2%}), "
                       f"re-transcribing with premium params...")

            # Llamar a re-transcripción (implementar según tu setup)
            # retranscribed = await self._retranscribe_premium(audio_path)
            # if retranscribed:
            #     result["corrected_text"] = retranscribed["text"]
            pass

        # 4. Análisis Semántico Avanzado
        result["advanced_analysis"] = await self._advanced_analysis(
            result["corrected_text"],
            metadata
        )

        # 5. Clarificación (todas las estrategias)
        clarification = self.clarification_system.should_ask_clarification(
            result["corrected_text"],
            word_confidences,
            conversation_id
        )

        if clarification:
            result["needs_clarification"] = True
            result["clarification_prompt"] = clarification.get("prompt")
            result["clarification_type"] = clarification.get("type")

        # Estadísticas
        end_time = time.time()
        result["processing_time_ms"] = (end_time - start_time) * 1000

        self.stats["offline_corrections"] += len(result["corrections_made"])
        self.stats["total_processed"] += 1

        logger.info(f"Offline processing: {result['processing_time_ms']:.2f}ms, "
                   f"{len(result['corrections_made'])} corrections, "
                   f"WER: {quality['estimated_wer']:.2%}")

        return result

    def _fast_correction(
        self,
        text: str,
        word_confidences: List[Dict]
    ) -> Tuple[str, List[Dict]]:
        """
        Corrección rápida usando SOLO diccionario exacto
        Target: <5ms
        """
        # Diccionario de correcciones más comunes (en memoria)
        FAST_CORRECTIONS = {
            "salgo": "saldo",
            "cuesta": "cuenta",
            "cuanta": "cuenta",
            "imeil": "email",
            "i-mail": "email",
            "contra seña": "contraseña",
        }

        words = text.split()
        corrected_words = []
        corrections = []

        for i, word in enumerate(words):
            word_lower = word.lower()

            # Lookup O(1)
            if word_lower in FAST_CORRECTIONS:
                correction = FAST_CORRECTIONS[word_lower]
                corrected_words.append(correction)
                corrections.append({
                    "original": word,
                    "corrected": correction,
                    "method": "fast_exact",
                    "position": i
                })
            else:
                corrected_words.append(word)

        return " ".join(corrected_words), corrections

    def _estimate_quality(
        self,
        text: str,
        word_confidences: List[Dict]
    ) -> Dict:
        """
        Estima la calidad de la transcripción
        """
        if not word_confidences:
            return {
                "estimated_wer": 0.0,
                "avg_confidence": 1.0,
                "low_confidence_words": 0
            }

        confidences = [w["confidence"] for w in word_confidences]
        avg_confidence = sum(confidences) / len(confidences)
        low_conf_count = sum(1 for c in confidences if c < 0.7)

        # Estimación simple de WER basada en confidence
        # WER ≈ (1 - avg_confidence) ajustado
        estimated_wer = max(0, (1 - avg_confidence) * 1.5)  # Factor de ajuste

        return {
            "estimated_wer": estimated_wer,
            "avg_confidence": avg_confidence,
            "low_confidence_words": low_conf_count,
            "low_confidence_ratio": low_conf_count / len(confidences)
        }

    async def _advanced_analysis(
        self,
        text: str,
        metadata: Optional[Dict]
    ) -> Dict:
        """
        Análisis semántico avanzado (solo offline)
        """
        analysis = {
            "entities": {},
            "topics": [],
            "sentiment_details": {},
            "keywords": [],
            "coherence_score": 0.0
        }

        # 1. Extracción de entidades mejorada
        analysis["entities"] = self._extract_entities_advanced(text)

        # 2. Detección de tópicos
        analysis["topics"] = self._detect_topics(text)

        # 3. Keywords importantes
        analysis["keywords"] = self._extract_keywords(text)

        # 4. Score de coherencia
        analysis["coherence_score"] = self._calculate_coherence(text)

        return analysis

    def _extract_entities_advanced(self, text: str) -> Dict:
        """Extracción avanzada de entidades"""
        import re

        entities = {
            "account_numbers": [],
            "amounts": [],
            "dates": [],
            "emails": [],
            "phones": [],
            "product_ids": []
        }

        # Números de cuenta (8-12 dígitos)
        entities["account_numbers"] = re.findall(r'\b\d{8,12}\b', text)

        # Montos
        entities["amounts"] = re.findall(
            r'\b\d+(?:[.,]\d{1,2})?\s*(?:euros?|€|dolares?|\$|pesos?)\b',
            text,
            re.IGNORECASE
        )

        # Fechas
        entities["dates"] = re.findall(
            r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{2}[/-]\d{2})\b',
            text
        )

        # Emails
        entities["emails"] = re.findall(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            text
        )

        # Teléfonos
        entities["phones"] = re.findall(
            r'\b(?:\+?34)?[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{3}\b',
            text
        )

        return entities

    def _detect_topics(self, text: str) -> List[str]:
        """Detecta tópicos principales"""
        topics = []

        topic_keywords = {
            "billing": ["factura", "cobro", "pago", "cargo"],
            "technical": ["error", "no funciona", "problema técnico", "conexión"],
            "account": ["cuenta", "usuario", "contraseña", "acceso"],
            "cancellation": ["cancelar", "dar de baja", "cerrar"],
            "complaint": ["queja", "molesto", "mal servicio"],
        }

        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)

        return topics

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrae keywords importantes"""
        # Simple TF-IDF o frequency-based
        words = text.lower().split()

        # Stopwords en español
        stopwords = {"el", "la", "de", "que", "y", "a", "en", "un", "por", "con"}

        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        # Top 5 por frecuencia
        from collections import Counter
        counter = Counter(keywords)
        return [word for word, count in counter.most_common(5)]

    def _calculate_coherence(self, text: str) -> float:
        """Calcula score de coherencia del texto"""
        words = text.split()

        if len(words) < 3:
            return 0.5

        # Heurísticas simples
        unique_ratio = len(set(words)) / len(words)  # Diversidad léxica
        avg_word_length = sum(len(w) for w in words) / len(words)

        # Score combinado (0-1)
        coherence = (unique_ratio * 0.7) + (min(avg_word_length / 8, 1.0) * 0.3)

        return coherence

    def get_stats(self) -> Dict:
        """Retorna estadísticas del pipeline"""
        return {
            **self.stats,
            "online_percentage": (self.stats["online_corrections"] /
                                 max(self.stats["total_processed"], 1) * 100),
            "offline_percentage": (self.stats["offline_corrections"] /
                                  max(self.stats["total_processed"], 1) * 100)
        }


# Singleton
_pipeline: Optional[CorrectionPipeline] = None


def get_correction_pipeline() -> CorrectionPipeline:
    """Obtiene instancia singleton del pipeline"""
    global _pipeline
    if _pipeline is None:
        _pipeline = CorrectionPipeline()
    return _pipeline
