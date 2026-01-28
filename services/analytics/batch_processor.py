"""
Batch Processor para Análisis Offline de Grabaciones
Procesa grabaciones guardadas con análisis profundo
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sys
from loguru import logger

# Agregar paths
sys.path.append(str(Path(__file__).parent.parent / "storage"))
sys.path.append(str(Path(__file__).parent.parent / "stt"))

from storage.audio_storage import get_audio_storage, StorageBackend
from storage.metadata_schema import (
    RecordingMetadata,
    update_with_transcription,
    SentimentAnalysis,
    SentimentLabel,
    IntentAnalysis,
    EntityExtraction,
    TopicAnalysis,
    ConversationMetrics
)


class BatchProcessor:
    """
    Procesador batch para análisis offline de grabaciones
    """

    def __init__(self):
        self.storage = get_audio_storage()

        # Cargar corrector offline
        try:
            from correction_pipeline import get_correction_pipeline
            self.pipeline = get_correction_pipeline()
        except ImportError:
            logger.error("Correction pipeline not available")
            self.pipeline = None

        # Stats
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "avg_processing_time_ms": 0.0
        }

    async def process_recording(
        self,
        recording_id: str,
        reprocess: bool = False
    ) -> Optional[Dict]:
        """
        Procesa una grabación individual con análisis completo

        Args:
            recording_id: ID de la grabación
            reprocess: Si True, procesar aunque ya esté procesada

        Returns:
            Metadata actualizada o None si error
        """
        logger.info(f"Processing recording: {recording_id}")

        # 1. Obtener metadata
        metadata_dict = self.storage.get_metadata(recording_id)
        if not metadata_dict:
            logger.error(f"Metadata not found: {recording_id}")
            return None

        metadata = RecordingMetadata(**metadata_dict)

        # Verificar si ya está procesado
        if metadata.processed and not reprocess:
            logger.info(f"Already processed, skipping: {recording_id}")
            return metadata_dict

        # 2. Obtener audio
        audio_data = self.storage.get_recording(recording_id)
        if not audio_data:
            logger.error(f"Audio not found: {recording_id}")
            return None

        # 3. Re-transcribir con parámetros premium (si no existe transcripción)
        if not metadata.transcription or reprocess:
            transcription_result = await self._transcribe_premium(
                audio_data,
                recording_id
            )

            if transcription_result:
                metadata = update_with_transcription(metadata, transcription_result)

        # 4. Análisis offline completo
        if metadata.transcription:
            # Corrección offline
            if self.pipeline:
                corrected = await self.pipeline.process_offline(
                    text=metadata.transcription.corrected_text or metadata.transcription.text,
                    word_confidences=metadata.transcription.word_confidences,
                    audio_path=str(metadata.local_path or metadata.s3_path),
                    conversation_id=metadata.conversation_id
                )

                # Actualizar con correcciones offline
                metadata.transcription.corrected_text = corrected["corrected_text"]
                metadata.transcription.corrections_made.extend(corrected["corrections_made"])
                metadata.transcription.correction_method = "offline"

                # Análisis avanzado
                advanced = corrected.get("advanced_analysis", {})

                # Entidades
                if "entities" in advanced:
                    metadata.entities = EntityExtraction(**advanced["entities"])

                # Tópicos
                if "topics" in advanced:
                    metadata.topics = TopicAnalysis(
                        topics=advanced.get("topics", []),
                        keywords=advanced.get("keywords", []),
                        coherence_score=advanced.get("coherence_score", 0.0)
                    )

            # 5. Sentiment analysis mejorado
            sentiment_result = await self._analyze_sentiment_advanced(
                metadata.transcription.corrected_text or metadata.transcription.text
            )

            if sentiment_result:
                metadata.sentiment = SentimentAnalysis(**sentiment_result)

            # 6. Intent analysis
            intent_result = await self._analyze_intent(
                metadata.transcription.corrected_text or metadata.transcription.text
            )

            if intent_result:
                metadata.intent = IntentAnalysis(**intent_result)

        # 7. Marcar como procesado
        metadata.processed = True
        metadata.processing_mode = "offline"

        # 8. Guardar metadata actualizada
        updated_dict = metadata.model_dump(mode='json')

        # Guardar transcripción separada
        transcript_data = {
            "recording_id": recording_id,
            "conversation_id": metadata.conversation_id,
            "timestamp": metadata.timestamp.isoformat(),
            "transcription": updated_dict.get("transcription"),
            "sentiment": updated_dict.get("sentiment"),
            "intent": updated_dict.get("intent"),
            "entities": updated_dict.get("entities"),
            "topics": updated_dict.get("topics")
        }

        self.storage.save_transcript(
            conversation_id=metadata.conversation_id,
            recording_id=recording_id,
            transcript_data=transcript_data
        )

        # Actualizar stats
        self.stats["successful"] += 1
        self.stats["total_processed"] += 1

        logger.info(f"Successfully processed: {recording_id}")

        return updated_dict

    async def process_batch(
        self,
        recordings: List[str],
        max_concurrent: int = 5
    ) -> Dict:
        """
        Procesa múltiples grabaciones en paralelo

        Args:
            recordings: Lista de recording_ids
            max_concurrent: Máximo de grabaciones simultáneas

        Returns:
            Estadísticas del batch
        """
        logger.info(f"Processing batch: {len(recordings)} recordings")

        # Procesar en lotes
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(recording_id: str):
            async with semaphore:
                try:
                    return await self.process_recording(recording_id)
                except Exception as e:
                    logger.error(f"Error processing {recording_id}: {e}")
                    self.stats["failed"] += 1
                    return None

        # Ejecutar en paralelo
        results = await asyncio.gather(
            *[process_with_semaphore(rec_id) for rec_id in recordings],
            return_exceptions=True
        )

        # Calcular stats
        successful = sum(1 for r in results if r is not None)

        return {
            "total": len(recordings),
            "successful": successful,
            "failed": len(recordings) - successful,
            "results": [r for r in results if r is not None]
        }

    async def process_unprocessed(
        self,
        limit: int = 100,
        max_concurrent: int = 5
    ) -> Dict:
        """
        Procesa todas las grabaciones no procesadas

        Args:
            limit: Máximo de grabaciones a procesar
            max_concurrent: Paralelismo

        Returns:
            Estadísticas del proceso
        """
        # Listar grabaciones
        all_recordings = self.storage.list_recordings(limit=limit * 2)

        # Filtrar no procesadas
        unprocessed = [
            rec["recording_id"]
            for rec in all_recordings
            if not rec.get("processed", False)
        ][:limit]

        logger.info(f"Found {len(unprocessed)} unprocessed recordings")

        if not unprocessed:
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "message": "No unprocessed recordings found"
            }

        return await self.process_batch(unprocessed, max_concurrent)

    async def process_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        max_concurrent: int = 5
    ) -> Dict:
        """
        Procesa grabaciones en un rango de fechas

        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
            max_concurrent: Paralelismo

        Returns:
            Estadísticas del proceso
        """
        recordings = self.storage.list_recordings(
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        recording_ids = [rec["recording_id"] for rec in recordings]

        logger.info(f"Found {len(recording_ids)} recordings in date range")

        return await self.process_batch(recording_ids, max_concurrent)

    async def _transcribe_premium(
        self,
        audio_data: bytes,
        recording_id: str
    ) -> Optional[Dict]:
        """
        Re-transcribe con parámetros premium

        TODO: Implementar llamada a STT service con parámetros optimizados
        """
        # Placeholder - integrar con tu STT service
        logger.warning("Premium transcription not implemented, using placeholder")

        return {
            "text": "Placeholder transcription",
            "corrected_text": "Placeholder transcription",
            "language": "es",
            "confidence": 0.95,
            "segments": [],
            "word_confidences": [],
            "processing_mode": "offline",
            "processing_time_ms": 0.0
        }

    async def _analyze_sentiment_advanced(self, text: str) -> Optional[Dict]:
        """
        Análisis de sentimiento avanzado

        TODO: Integrar con modelo de sentiment más sofisticado
        """
        # Análisis simple por keywords
        text_lower = text.lower()

        # Keywords por categoría
        very_positive = ["excelente", "perfecto", "genial", "maravilloso"]
        positive = ["bien", "bueno", "gracias", "ok"]
        negative = ["mal", "problema", "error", "no funciona"]
        very_negative = ["pésimo", "horrible", "terrible"]
        frustrated = ["molesto", "frustrado", "enojado", "harto"]

        score = 0.0
        label = SentimentLabel.NEUTRAL

        if any(kw in text_lower for kw in very_positive):
            score = 0.9
            label = SentimentLabel.VERY_POSITIVE
        elif any(kw in text_lower for kw in positive):
            score = 0.5
            label = SentimentLabel.POSITIVE
        elif any(kw in text_lower for kw in frustrated):
            score = -0.7
            label = SentimentLabel.FRUSTRATED
        elif any(kw in text_lower for kw in very_negative):
            score = -0.9
            label = SentimentLabel.VERY_NEGATIVE
        elif any(kw in text_lower for kw in negative):
            score = -0.5
            label = SentimentLabel.NEGATIVE

        return {
            "label": label,
            "score": score,
            "confidence": 0.7,
            "keywords_detected": []
        }

    async def _analyze_intent(self, text: str) -> Optional[Dict]:
        """
        Análisis de intención

        TODO: Integrar con modelo de clasificación de intents
        """
        text_lower = text.lower()

        intent_patterns = {
            "billing_inquiry": ["factura", "cobro", "pago", "cargo"],
            "technical_support": ["error", "no funciona", "problema técnico"],
            "account_management": ["cuenta", "contraseña", "usuario"],
            "cancellation": ["cancelar", "dar de baja", "cerrar"],
            "complaint": ["queja", "molesto", "mal servicio"],
            "general_inquiry": ["información", "saber", "consulta"]
        }

        detected = []
        for intent, keywords in intent_patterns.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(intent)

        primary = detected[0] if detected else "general_inquiry"
        secondary = detected[1:] if len(detected) > 1 else []

        return {
            "primary_intent": primary,
            "secondary_intents": secondary,
            "confidence": 0.75 if detected else 0.3
        }

    def get_stats(self) -> Dict:
        """Retorna estadísticas del procesador"""
        return self.stats


# ==========================================
# CLI para ejecutar batch jobs
# ==========================================

async def main():
    """CLI para batch processing"""
    import argparse

    parser = argparse.ArgumentParser(description="Batch processor for call recordings")
    parser.add_argument(
        "--mode",
        choices=["unprocessed", "date_range", "single"],
        default="unprocessed",
        help="Processing mode"
    )
    parser.add_argument("--recording-id", help="Recording ID for single mode")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=100, help="Max recordings to process")
    parser.add_argument("--concurrent", type=int, default=5, help="Max concurrent processes")

    args = parser.parse_args()

    processor = BatchProcessor()

    if args.mode == "single":
        if not args.recording_id:
            logger.error("--recording-id required for single mode")
            return

        result = await processor.process_recording(args.recording_id)
        print(f"\nResult: {result}")

    elif args.mode == "unprocessed":
        result = await processor.process_unprocessed(
            limit=args.limit,
            max_concurrent=args.concurrent
        )
        print(f"\nProcessed: {result['successful']}/{result['total']}")

    elif args.mode == "date_range":
        if not args.start_date or not args.end_date:
            logger.error("--start-date and --end-date required for date_range mode")
            return

        start = datetime.fromisoformat(args.start_date)
        end = datetime.fromisoformat(args.end_date)

        result = await processor.process_by_date_range(
            start_date=start,
            end_date=end,
            max_concurrent=args.concurrent
        )
        print(f"\nProcessed: {result['successful']}/{result['total']}")

    # Stats finales
    stats = processor.get_stats()
    print(f"\nFinal stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
