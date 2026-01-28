"""
Sistema de Almacenamiento de Audio
Soporta almacenamiento local y S3 con metadata
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, BinaryIO
from enum import Enum
import hashlib
from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    logger.warning("boto3 no disponible. Solo almacenamiento local.")
    S3_AVAILABLE = False


class StorageBackend(Enum):
    """Tipo de almacenamiento"""
    LOCAL = "local"
    S3 = "s3"
    BOTH = "both"  # Redundancia: local + S3


class AudioStorage:
    """
    Gestiona almacenamiento de archivos de audio con metadata
    """

    def __init__(
        self,
        backend: StorageBackend = StorageBackend.LOCAL,
        local_path: str = "./data/recordings",
        s3_bucket: Optional[str] = None,
        s3_region: str = "us-east-1"
    ):
        self.backend = backend
        self.local_path = Path(local_path)
        self.s3_bucket = s3_bucket
        self.s3_region = s3_region

        # Crear directorio local si no existe
        self.local_path.mkdir(parents=True, exist_ok=True)

        # Subdirectorios
        self.audio_dir = self.local_path / "audio"
        self.metadata_dir = self.local_path / "metadata"
        self.transcripts_dir = self.local_path / "transcripts"

        for dir_path in [self.audio_dir, self.metadata_dir, self.transcripts_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Cliente S3
        if backend in [StorageBackend.S3, StorageBackend.BOTH] and S3_AVAILABLE:
            self.s3_client = boto3.client('s3', region_name=s3_region)
            logger.info(f"S3 storage initialized: bucket={s3_bucket}")
        else:
            self.s3_client = None

    def save_recording(
        self,
        audio_data: bytes,
        conversation_id: str,
        metadata: Dict,
        format: str = "wav"
    ) -> Dict:
        """
        Guarda grabación de audio con metadata

        Args:
            audio_data: Bytes del audio
            conversation_id: ID de la conversación
            metadata: Metadata de la grabación
            format: Formato de audio (wav, mp3, etc.)

        Returns:
            {
                "recording_id": str,
                "local_path": str,
                "s3_path": str,
                "metadata_path": str,
                "size_bytes": int,
                "checksum": str
            }
        """
        # Generar ID único para la grabación
        recording_id = f"{conversation_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Paths
        audio_filename = f"{recording_id}.{format}"
        metadata_filename = f"{recording_id}_metadata.json"

        local_audio_path = self.audio_dir / audio_filename
        local_metadata_path = self.metadata_dir / metadata_filename

        # Calcular checksum
        checksum = hashlib.sha256(audio_data).hexdigest()

        # Enriquecer metadata
        full_metadata = {
            "recording_id": recording_id,
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "format": format,
            "size_bytes": len(audio_data),
            "checksum": checksum,
            **metadata
        }

        result = {
            "recording_id": recording_id,
            "local_path": None,
            "s3_path": None,
            "metadata_path": None,
            "size_bytes": len(audio_data),
            "checksum": checksum
        }

        # Guardar localmente
        if self.backend in [StorageBackend.LOCAL, StorageBackend.BOTH]:
            try:
                # Audio
                with open(local_audio_path, 'wb') as f:
                    f.write(audio_data)

                # Metadata
                with open(local_metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(full_metadata, f, indent=2, ensure_ascii=False)

                result["local_path"] = str(local_audio_path)
                result["metadata_path"] = str(local_metadata_path)

                logger.info(f"Recording saved locally: {recording_id}")

            except Exception as e:
                logger.error(f"Error saving locally: {e}")

        # Guardar en S3
        if self.backend in [StorageBackend.S3, StorageBackend.BOTH] and self.s3_client:
            try:
                # Upload audio
                s3_audio_key = f"recordings/{conversation_id}/{audio_filename}"
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_audio_key,
                    Body=audio_data,
                    ContentType=f"audio/{format}",
                    Metadata={
                        "conversation_id": conversation_id,
                        "recording_id": recording_id,
                        "checksum": checksum
                    }
                )

                # Upload metadata
                s3_metadata_key = f"recordings/{conversation_id}/{metadata_filename}"
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_metadata_key,
                    Body=json.dumps(full_metadata, indent=2, ensure_ascii=False).encode('utf-8'),
                    ContentType="application/json"
                )

                result["s3_path"] = f"s3://{self.s3_bucket}/{s3_audio_key}"

                logger.info(f"Recording uploaded to S3: {recording_id}")

            except ClientError as e:
                logger.error(f"Error uploading to S3: {e}")

        return result

    def get_recording(
        self,
        recording_id: str,
        prefer_local: bool = True
    ) -> Optional[bytes]:
        """
        Recupera audio por recording_id

        Args:
            recording_id: ID de la grabación
            prefer_local: Intentar local primero antes de S3

        Returns:
            Audio bytes o None si no existe
        """
        # Intentar local primero
        if prefer_local and self.backend in [StorageBackend.LOCAL, StorageBackend.BOTH]:
            # Buscar archivo en local
            for audio_file in self.audio_dir.glob(f"{recording_id}.*"):
                try:
                    with open(audio_file, 'rb') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Error reading local file: {e}")

        # Intentar S3
        if self.backend in [StorageBackend.S3, StorageBackend.BOTH] and self.s3_client:
            try:
                # Necesitamos encontrar el objeto en S3
                # Buscar por prefix
                response = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix=f"recordings/",
                    MaxKeys=1000
                )

                for obj in response.get('Contents', []):
                    if recording_id in obj['Key'] and not obj['Key'].endswith('_metadata.json'):
                        # Descargar
                        response = self.s3_client.get_object(
                            Bucket=self.s3_bucket,
                            Key=obj['Key']
                        )
                        return response['Body'].read()

            except ClientError as e:
                logger.error(f"Error retrieving from S3: {e}")

        return None

    def get_metadata(self, recording_id: str) -> Optional[Dict]:
        """Recupera metadata de una grabación"""
        # Intentar local
        metadata_file = self.metadata_dir / f"{recording_id}_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading metadata: {e}")

        # Intentar S3
        if self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix=f"recordings/"
                )

                for obj in response.get('Contents', []):
                    if recording_id in obj['Key'] and obj['Key'].endswith('_metadata.json'):
                        response = self.s3_client.get_object(
                            Bucket=self.s3_bucket,
                            Key=obj['Key']
                        )
                        return json.loads(response['Body'].read().decode('utf-8'))

            except ClientError as e:
                logger.error(f"Error retrieving metadata from S3: {e}")

        return None

    def save_transcript(
        self,
        conversation_id: str,
        recording_id: str,
        transcript_data: Dict
    ) -> str:
        """
        Guarda transcripción procesada

        Args:
            conversation_id: ID de conversación
            recording_id: ID de grabación
            transcript_data: Datos de transcripción

        Returns:
            Path del archivo guardado
        """
        transcript_filename = f"{recording_id}_transcript.json"
        local_path = self.transcripts_dir / transcript_filename

        # Guardar localmente
        try:
            with open(local_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Transcript saved: {recording_id}")

        except Exception as e:
            logger.error(f"Error saving transcript: {e}")

        # Guardar en S3
        if self.s3_client:
            try:
                s3_key = f"transcripts/{conversation_id}/{transcript_filename}"
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=json.dumps(transcript_data, indent=2, ensure_ascii=False).encode('utf-8'),
                    ContentType="application/json"
                )

                logger.info(f"Transcript uploaded to S3: {recording_id}")

            except ClientError as e:
                logger.error(f"Error uploading transcript to S3: {e}")

        return str(local_path)

    def list_recordings(
        self,
        conversation_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Lista grabaciones con filtros opcionales

        Returns:
            Lista de metadata de grabaciones
        """
        recordings = []

        # Buscar en local
        for metadata_file in self.metadata_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # Aplicar filtros
                if conversation_id and metadata.get("conversation_id") != conversation_id:
                    continue

                if start_date or end_date:
                    timestamp = datetime.fromisoformat(metadata.get("timestamp", ""))
                    if start_date and timestamp < start_date:
                        continue
                    if end_date and timestamp > end_date:
                        continue

                recordings.append(metadata)

                if len(recordings) >= limit:
                    break

            except Exception as e:
                logger.error(f"Error reading metadata file: {e}")

        # Ordenar por timestamp (más reciente primero)
        recordings.sort(
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )

        return recordings[:limit]

    def delete_recording(self, recording_id: str, permanent: bool = False) -> bool:
        """
        Elimina grabación (soft delete por defecto)

        Args:
            recording_id: ID de la grabación
            permanent: Si True, elimina físicamente. Si False, marca como deleted.

        Returns:
            True si se eliminó correctamente
        """
        if permanent:
            # Eliminar físicamente
            deleted = False

            # Local
            for audio_file in self.audio_dir.glob(f"{recording_id}.*"):
                try:
                    audio_file.unlink()
                    deleted = True
                except Exception as e:
                    logger.error(f"Error deleting local file: {e}")

            metadata_file = self.metadata_dir / f"{recording_id}_metadata.json"
            if metadata_file.exists():
                try:
                    metadata_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting metadata: {e}")

            # S3
            if self.s3_client:
                try:
                    # Listar y eliminar objetos
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.s3_bucket,
                        Prefix=f"recordings/"
                    )

                    for obj in response.get('Contents', []):
                        if recording_id in obj['Key']:
                            self.s3_client.delete_object(
                                Bucket=self.s3_bucket,
                                Key=obj['Key']
                            )
                            deleted = True

                except ClientError as e:
                    logger.error(f"Error deleting from S3: {e}")

            return deleted

        else:
            # Soft delete: marcar metadata
            metadata = self.get_metadata(recording_id)
            if metadata:
                metadata["deleted"] = True
                metadata["deleted_at"] = datetime.utcnow().isoformat()

                # Guardar metadata actualizada
                metadata_file = self.metadata_dir / f"{recording_id}_metadata.json"
                try:
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    return True
                except Exception as e:
                    logger.error(f"Error updating metadata: {e}")

            return False

    def get_storage_stats(self) -> Dict:
        """Retorna estadísticas de almacenamiento"""
        stats = {
            "backend": self.backend.value,
            "local": {
                "total_recordings": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0
            },
            "s3": {
                "total_recordings": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0
            }
        }

        # Stats locales
        for audio_file in self.audio_dir.glob("*"):
            if audio_file.is_file():
                stats["local"]["total_recordings"] += 1
                stats["local"]["total_size_bytes"] += audio_file.stat().st_size

        stats["local"]["total_size_mb"] = stats["local"]["total_size_bytes"] / (1024 * 1024)

        # Stats S3
        if self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix="recordings/"
                )

                for obj in response.get('Contents', []):
                    if not obj['Key'].endswith('_metadata.json'):
                        stats["s3"]["total_recordings"] += 1
                        stats["s3"]["total_size_bytes"] += obj['Size']

                stats["s3"]["total_size_mb"] = stats["s3"]["total_size_bytes"] / (1024 * 1024)

            except ClientError as e:
                logger.error(f"Error getting S3 stats: {e}")

        return stats


# Singleton
_storage: Optional[AudioStorage] = None


def get_audio_storage(
    backend: Optional[StorageBackend] = None,
    **kwargs
) -> AudioStorage:
    """Obtiene instancia singleton de AudioStorage"""
    global _storage

    if _storage is None:
        # Leer configuración de ENV
        backend_str = os.getenv("STORAGE_BACKEND", "local")
        backend = StorageBackend(backend_str) if backend is None else backend

        s3_bucket = os.getenv("S3_BUCKET")
        s3_region = os.getenv("S3_REGION", "us-east-1")
        local_path = os.getenv("STORAGE_LOCAL_PATH", "./data/recordings")

        _storage = AudioStorage(
            backend=backend,
            local_path=local_path,
            s3_bucket=s3_bucket,
            s3_region=s3_region,
            **kwargs
        )

    return _storage
