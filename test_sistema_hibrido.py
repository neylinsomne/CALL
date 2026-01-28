"""
Test del Sistema Híbrido Online/Offline
Demuestra el flujo completo: Online → Storage → Offline
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Agregar paths
sys.path.append(str(Path(__file__).parent / "services" / "storage"))
sys.path.append(str(Path(__file__).parent / "services" / "stt"))
sys.path.append(str(Path(__file__).parent / "services" / "analytics"))

print("=" * 80)
print("TEST: Sistema Híbrido Online/Offline")
print("=" * 80)


# ===========================================
# 1. Simular Procesamiento Online
# ===========================================

print("\n" + "=" * 80)
print("FASE 1: Procesamiento ONLINE (Durante la llamada)")
print("=" * 80)

async def test_online_processing():
    """Simula procesamiento durante la llamada"""

    print("\n[ONLINE] Inicializando pipeline...")

    try:
        from correction_pipeline import get_correction_pipeline

        pipeline = get_correction_pipeline()

        # Datos de prueba
        transcription = "Necesito revisar el salgo de mi cuesta y cambiar mi contra seña"
        word_confidences = [
            {"word": "Necesito", "confidence": 0.95},
            {"word": "revisar", "confidence": 0.92},
            {"word": "el", "confidence": 0.99},
            {"word": "salgo", "confidence": 0.45},
            {"word": "de", "confidence": 0.98},
            {"word": "mi", "confidence": 0.97},
            {"word": "cuesta", "confidence": 0.52},
            {"word": "y", "confidence": 0.99},
            {"word": "cambiar", "confidence": 0.94},
            {"word": "mi", "confidence": 0.97},
            {"word": "contra", "confidence": 0.61},
            {"word": "seña", "confidence": 0.58}
        ]

        print(f"\n[ONLINE] Transcripción original:")
        print(f"  '{transcription}'")

        # Procesar online
        import time
        start = time.time()

        result = await pipeline.process_online(
            transcription=transcription,
            word_confidences=word_confidences,
            conversation_id="test_conv_123"
        )

        elapsed = (time.time() - start) * 1000

        print(f"\n[ONLINE] Resultado ({elapsed:.2f}ms):")
        print(f"  Corregido: '{result['corrected_text']}'")
        print(f"  Correcciones: {len(result['corrections_made'])}")

        for corr in result['corrections_made']:
            print(f"    - '{corr['original']}' → '{corr['corrected']}' ({corr['method']})")

        if result['needs_clarification']:
            print(f"\n  ⚠️  Clarificación necesaria:")
            print(f"    Tipo: {result['clarification_type']}")
            print(f"    Prompt: {result['clarification_prompt']}")

        print(f"\n  ✓ Procesamiento online completado en {elapsed:.2f}ms")

        return result

    except ImportError as e:
        print(f"\n  ✗ Error: Pipeline no disponible - {e}")
        print(f"    Instalar: pip install -r services/stt/requirements.txt")
        return None


# ===========================================
# 2. Guardar en Storage
# ===========================================

print("\n" + "=" * 80)
print("FASE 2: Almacenamiento (Local/S3)")
print("=" * 80)

async def test_storage():
    """Test de almacenamiento"""

    print("\n[STORAGE] Inicializando sistema de almacenamiento...")

    try:
        from audio_storage import get_audio_storage, StorageBackend
        from metadata_schema import (
            create_recording_metadata,
            update_with_transcription,
            CallDirection
        )

        # Inicializar storage (solo local para test)
        storage = get_audio_storage(
            backend=StorageBackend.LOCAL,
            local_path="./data/test_recordings"
        )

        # Simular audio
        fake_audio = b"fake audio data for testing" * 1000  # ~27KB

        # Crear metadata
        recording_id = f"test_rec_{int(datetime.now().timestamp())}"
        conversation_id = "test_conv_123"

        metadata = create_recording_metadata(
            recording_id=recording_id,
            conversation_id=conversation_id,
            audio_data=fake_audio,
            direction=CallDirection.INBOUND,
            duration_seconds=120.5,
            agent_id="agent_test",
            caller_phone="+34612345678"
        )

        print(f"\n[STORAGE] Metadata creada:")
        print(f"  Recording ID: {recording_id}")
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Size: {len(fake_audio)} bytes")

        # Guardar
        result = storage.save_recording(
            audio_data=fake_audio,
            conversation_id=conversation_id,
            metadata=metadata.model_dump(mode='json'),
            format="wav"
        )

        print(f"\n[STORAGE] Grabación guardada:")
        print(f"  Local path: {result['local_path']}")
        print(f"  Metadata path: {result['metadata_path']}")
        print(f"  Checksum: {result['checksum'][:16]}...")

        # Simular transcripción online
        transcription_result = {
            "text": "Necesito revisar el salgo de mi cuesta",
            "corrected_text": "Necesito revisar el saldo de mi cuenta",
            "language": "es",
            "confidence": 0.87,
            "segments": [],
            "word_confidences": [],
            "corrections_made": [
                {"original": "salgo", "corrected": "saldo"},
                {"original": "cuesta", "corrected": "cuenta"}
            ],
            "processing_mode": "online",
            "processing_time_ms": 15.2
        }

        # Actualizar metadata con transcripción
        metadata = update_with_transcription(metadata, transcription_result)

        # Guardar metadata actualizada
        metadata_path = Path(result['metadata_path'])
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.model_dump(mode='json'), f, indent=2, ensure_ascii=False)

        print(f"\n  ✓ Metadata actualizada con transcripción online")

        # Stats
        stats = storage.get_storage_stats()
        print(f"\n[STORAGE] Estadísticas:")
        print(f"  Total grabaciones: {stats['local']['total_recordings']}")
        print(f"  Tamaño total: {stats['local']['total_size_mb']:.2f} MB")

        return result['recording_id']

    except Exception as e:
        print(f"\n  ✗ Error en storage: {e}")
        import traceback
        traceback.print_exc()
        return None


# ===========================================
# 3. Procesamiento Offline
# ===========================================

print("\n" + "=" * 80)
print("FASE 3: Procesamiento OFFLINE (Post-procesamiento)")
print("=" * 80)

async def test_offline_processing(recording_id: str):
    """Simula procesamiento batch offline"""

    print(f"\n[OFFLINE] Procesando grabación: {recording_id}")

    try:
        from batch_processor import BatchProcessor

        processor = BatchProcessor()

        # Procesar
        result = await processor.process_recording(recording_id)

        if result:
            print(f"\n[OFFLINE] Procesamiento completado:")
            print(f"  Processed: {result.get('processed', False)}")
            print(f"  Processing mode: {result.get('processing_mode', 'N/A')}")

            # Transcripción
            if result.get('transcription'):
                trans = result['transcription']
                print(f"\n  Transcripción:")
                print(f"    Original: {trans.get('text', '')[:50]}...")
                print(f"    Corregido: {trans.get('corrected_text', '')[:50]}...")
                print(f"    Correcciones: {len(trans.get('corrections_made', []))}")

            # Sentiment
            if result.get('sentiment'):
                sent = result['sentiment']
                print(f"\n  Sentiment:")
                print(f"    Label: {sent.get('label', 'N/A')}")
                print(f"    Score: {sent.get('score', 0):.2f}")

            # Intent
            if result.get('intent'):
                intent = result['intent']
                print(f"\n  Intent:")
                print(f"    Primary: {intent.get('primary_intent', 'N/A')}")
                print(f"    Confidence: {intent.get('confidence', 0):.2f}")

            # Entities
            if result.get('entities'):
                entities = result['entities']
                print(f"\n  Entidades extraídas:")
                for entity_type, values in entities.items():
                    if values:
                        print(f"    {entity_type}: {values}")

            # Topics
            if result.get('topics'):
                topics = result['topics']
                print(f"\n  Tópicos:")
                print(f"    Topics: {topics.get('topics', [])}")
                print(f"    Keywords: {topics.get('keywords', [])}")
                print(f"    Coherence: {topics.get('coherence_score', 0):.2f}")

            print(f"\n  ✓ Procesamiento offline completado")

        else:
            print(f"\n  ✗ Error: No se pudo procesar la grabación")

        # Stats del processor
        stats = processor.get_stats()
        print(f"\n[OFFLINE] Estadísticas del batch processor:")
        print(f"  Total procesados: {stats['total_processed']}")
        print(f"  Exitosos: {stats['successful']}")
        print(f"  Fallidos: {stats['failed']}")

        return result

    except Exception as e:
        print(f"\n  ✗ Error en procesamiento offline: {e}")
        import traceback
        traceback.print_exc()
        return None


# ===========================================
# Main Test Flow
# ===========================================

async def main():
    """Ejecuta el test completo"""

    print("\n📝 Este test demuestra el flujo completo:")
    print("  1. Procesamiento ONLINE (rápido, durante llamada)")
    print("  2. Almacenamiento (local/S3 con metadata)")
    print("  3. Procesamiento OFFLINE (profundo, después)")

    # Fase 1: Online
    online_result = await test_online_processing()

    if not online_result:
        print("\n❌ Test abortado: Pipeline online no disponible")
        return

    # Fase 2: Storage
    recording_id = await test_storage()

    if not recording_id:
        print("\n❌ Test abortado: Storage no disponible")
        return

    # Fase 3: Offline
    offline_result = await test_offline_processing(recording_id)

    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DEL TEST")
    print("=" * 80)

    if online_result and recording_id and offline_result:
        print("\n✅ Test completado exitosamente!")
        print(f"\nComparación Online vs Offline:")
        print(f"  Online latency: {online_result.get('processing_time_ms', 0):.2f}ms")
        print(f"  Online corrections: {len(online_result.get('corrections_made', []))}")
        print(f"  Offline corrections: {len(offline_result.get('transcription', {}).get('corrections_made', []))}")
        print(f"\nGrabación guardada en: {recording_id}")
    else:
        print("\n⚠️  Test parcialmente completado")
        print("  Algunas dependencias pueden no estar instaladas")

    print("\n" + "=" * 80)
    print("Para más información:")
    print("  - SISTEMA_HIBRIDO_ONLINE_OFFLINE.md")
    print("  - METODOS_CLASIFICACION_ERRORES.md")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
