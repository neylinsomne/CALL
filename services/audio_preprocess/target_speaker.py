"""
Target Speaker Extraction
Aísla la voz de un hablante específico del audio mezclado
"""

import torch
import torchaudio
import io
import numpy as np
from typing import Optional
from loguru import logger


class TargetSpeakerExtractor:
    """
    Extrae la voz de un hablante objetivo basándose en un perfil de voz de referencia.
    Útil para aislar la voz del cliente en llamadas con ruido o múltiples hablantes.
    """

    def __init__(self, use_gpu: bool = True):
        """
        Inicializa el extractor de hablante objetivo

        Args:
            use_gpu: Si usar GPU (más rápido) o CPU
        """
        self.device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
        logger.info(f"Target Speaker Extractor usando: {self.device}")

        try:
            # Modelo de embeddings de hablante (ECAPA-TDNN)
            from speechbrain.pretrained import EncoderClassifier

            self.speaker_encoder = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="models/speaker_encoder",
                run_opts={"device": str(self.device)}
            )

            logger.info("Speaker encoder cargado exitosamente")

            # Modelo de separación de fuentes (opcional, mejora resultados)
            try:
                from speechbrain.pretrained import SepformerSeparation
                self.separator = SepformerSeparation.from_hparams(
                    source="speechbrain/sepformer-wham16k-enhancement",
                    savedir="models/sepformer",
                    run_opts={"device": str(self.device)}
                )
                logger.info("Separator model cargado exitosamente")
                self.has_separator = True
            except Exception as e:
                logger.warning(f"Separator no disponible: {e}. Usando solo encoder.")
                self.has_separator = False

        except Exception as e:
            logger.error(f"Error cargando modelos: {e}")
            raise

    def create_voice_profile(self, audio_bytes: bytes, sample_rate: int = 16000) -> torch.Tensor:
        """
        Crea un perfil de voz (embedding) a partir de audio de referencia.
        Usa los primeros segundos de audio del cliente para crear su "firma de voz".

        Args:
            audio_bytes: Audio en formato bytes (WAV)
            sample_rate: Frecuencia de muestreo del audio

        Returns:
            torch.Tensor: Embedding del hablante (vector de características)
        """
        try:
            # Convertir bytes a tensor
            waveform = self._bytes_to_tensor(audio_bytes, sample_rate)

            # Normalizar amplitud
            waveform = waveform / waveform.abs().max()

            # Extraer embedding
            with torch.no_grad():
                embedding = self.speaker_encoder.encode_batch(waveform.to(self.device))

            logger.debug(f"Voice profile created: shape={embedding.shape}")
            return embedding

        except Exception as e:
            logger.error(f"Error creating voice profile: {e}")
            raise

    def extract_target_speaker(
        self,
        audio_bytes: bytes,
        target_embedding: torch.Tensor,
        sample_rate: int = 16000,
        similarity_threshold: float = 0.5
    ) -> bytes:
        """
        Extrae la voz del hablante objetivo del audio mezclado.

        Args:
            audio_bytes: Audio mezclado (cliente + ruido + otras voces)
            target_embedding: Perfil de voz del hablante objetivo
            sample_rate: Frecuencia de muestreo
            similarity_threshold: Umbral de similitud para considerar que es el hablante (0-1)

        Returns:
            bytes: Audio con solo la voz del hablante objetivo
        """
        try:
            # Convertir bytes a tensor
            waveform = self._bytes_to_tensor(audio_bytes, sample_rate)

            # Si tenemos modelo de separación, separar fuentes primero
            if self.has_separator:
                waveform = self._separate_sources(waveform, target_embedding, similarity_threshold)
            else:
                # Sin separador, aplicar simple noise gating basado en embedding
                waveform = self._simple_extraction(waveform, target_embedding, sample_rate)

            # Convertir tensor de vuelta a bytes
            return self._tensor_to_bytes(waveform, sample_rate)

        except Exception as e:
            logger.error(f"Error extracting target speaker: {e}")
            # En caso de error, devolver audio original
            return audio_bytes

    def _separate_sources(
        self,
        waveform: torch.Tensor,
        target_embedding: torch.Tensor,
        threshold: float
    ) -> torch.Tensor:
        """
        Separa las fuentes de audio y selecciona la que mejor coincide con el embedding objetivo
        """
        with torch.no_grad():
            # Separar en múltiples fuentes
            separated = self.separator.separate_batch(waveform.to(self.device))

            # Si solo hay una fuente, devolverla
            if separated.shape[0] == 1:
                return separated[0].cpu()

            # Comparar cada fuente con el embedding objetivo
            best_match = None
            best_similarity = -1

            for i in range(separated.shape[0]):
                source = separated[i:i+1]

                # Extraer embedding de esta fuente
                source_embedding = self.speaker_encoder.encode_batch(source)

                # Calcular similitud coseno
                similarity = torch.cosine_similarity(
                    target_embedding,
                    source_embedding,
                    dim=-1
                ).item()

                logger.debug(f"Source {i} similarity: {similarity:.3f}")

                if similarity > best_similarity and similarity > threshold:
                    best_similarity = similarity
                    best_match = source

            # Si encontramos match, usarlo; sino, usar audio original
            if best_match is not None:
                logger.debug(f"Best match found with similarity: {best_similarity:.3f}")
                return best_match.squeeze(0).cpu()
            else:
                logger.warning(f"No match found above threshold {threshold}")
                return waveform

    def _simple_extraction(
        self,
        waveform: torch.Tensor,
        target_embedding: torch.Tensor,
        sample_rate: int
    ) -> torch.Tensor:
        """
        Extracción simple usando ventanas de tiempo y comparación de embeddings
        """
        window_size = int(sample_rate * 0.5)  # Ventanas de 0.5 segundos
        hop_size = int(sample_rate * 0.25)  # Overlap de 50%

        output_waveform = torch.zeros_like(waveform)
        num_samples = waveform.shape[1]

        with torch.no_grad():
            for start in range(0, num_samples - window_size, hop_size):
                end = start + window_size
                window = waveform[:, start:end]

                # Extraer embedding de la ventana
                try:
                    window_embedding = self.speaker_encoder.encode_batch(window.to(self.device))

                    # Calcular similitud
                    similarity = torch.cosine_similarity(
                        target_embedding,
                        window_embedding,
                        dim=-1
                    ).item()

                    # Si la similitud es alta, mantener la ventana
                    if similarity > 0.5:
                        output_waveform[:, start:end] = window

                except Exception as e:
                    # Si la ventana es muy corta o tiene problemas, mantenerla
                    output_waveform[:, start:end] = window

        return output_waveform

    def _bytes_to_tensor(self, audio_bytes: bytes, sample_rate: int) -> torch.Tensor:
        """
        Convierte bytes de audio a tensor PyTorch
        """
        # Intentar cargar como WAV desde bytes
        try:
            audio_io = io.BytesIO(audio_bytes)
            waveform, sr = torchaudio.load(audio_io)

            # Resamplear si es necesario
            if sr != sample_rate:
                resampler = torchaudio.transforms.Resample(sr, sample_rate)
                waveform = resampler(waveform)

            # Convertir a mono si es estéreo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)

            return waveform

        except Exception:
            # Si falla, asumir que son samples PCM raw
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
            waveform = torch.from_numpy(audio_np).float() / 32768.0
            waveform = waveform.unsqueeze(0)  # Add channel dimension
            return waveform

    def _tensor_to_bytes(self, waveform: torch.Tensor, sample_rate: int) -> bytes:
        """
        Convierte tensor PyTorch a bytes de audio (WAV)
        """
        # Normalizar y convertir a int16
        waveform = waveform.cpu()
        waveform = waveform / waveform.abs().max() * 0.95  # Evitar clipping
        waveform_int = (waveform * 32767).to(torch.int16)

        # Guardar a bytes como WAV
        audio_io = io.BytesIO()
        torchaudio.save(audio_io, waveform_int, sample_rate, format="wav")
        audio_io.seek(0)

        return audio_io.read()


# Singleton para reusar el modelo
_extractor_instance: Optional[TargetSpeakerExtractor] = None


def get_extractor() -> TargetSpeakerExtractor:
    """
    Obtiene la instancia singleton del extractor
    """
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = TargetSpeakerExtractor()
    return _extractor_instance
