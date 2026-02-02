"""
Triton Python Backend for Whisper STT (faster-whisper).

Each instance_group instance loads its own WhisperModel,
enabling true parallel inference on the same GPU.
"""

import json
import os
import tempfile

import numpy as np
import triton_python_backend_utils as pb_utils
from faster_whisper import WhisperModel


class TritonPythonModel:
    """Triton Python Backend model for Whisper speech-to-text."""

    def initialize(self, args):
        """Called once per instance when Triton loads the model."""
        self.model_config = json.loads(args["model_config"])

        model_size = os.getenv("STT_MODEL", "small")
        device = os.getenv("DEVICE", "cuda")
        compute_type = os.getenv("COMPUTE_TYPE", "float16")
        download_root = os.getenv("MODEL_CACHE", "/models/whisper")

        instance_id = args.get("model_instance_device_id", "0")
        pb_utils.Logger.log_info(
            f"[whisper_stt] Initializing instance on GPU {instance_id}, "
            f"model={model_size}, compute={compute_type}"
        )

        self.whisper_model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=download_root,
        )
        self.default_language = os.getenv("LANGUAGE", "es")

        pb_utils.Logger.log_info(
            f"[whisper_stt] Instance ready (GPU {instance_id})"
        )

    def execute(self, requests):
        """Process inference requests. One audio per request."""
        responses = []

        for request in requests:
            try:
                result = self._process_request(request)
            except Exception as e:
                pb_utils.Logger.log_error(f"[whisper_stt] Error: {e}")
                result = json.dumps({
                    "text": "",
                    "segments": [],
                    "language": "",
                    "confidence": 0.0,
                    "error": str(e),
                })

            output_tensor = pb_utils.Tensor(
                "result_json",
                np.array([result], dtype=np.object_),
            )
            responses.append(pb_utils.InferenceResponse([output_tensor]))

        return responses

    def _process_request(self, request):
        """Transcribe a single audio request."""
        # Extract audio bytes
        audio_bytes_tensor = pb_utils.get_input_tensor_by_name(
            request, "audio_bytes"
        )
        audio_bytes = audio_bytes_tensor.as_numpy()[0]
        if isinstance(audio_bytes, np.bytes_):
            audio_bytes = bytes(audio_bytes)
        elif isinstance(audio_bytes, str):
            audio_bytes = audio_bytes.encode("latin-1")

        # Extract optional language parameter
        language = self.default_language
        lang_tensor = pb_utils.get_input_tensor_by_name(request, "language")
        if lang_tensor is not None:
            lang_val = lang_tensor.as_numpy()[0]
            if isinstance(lang_val, (bytes, np.bytes_)):
                lang_val = lang_val.decode("utf-8")
            if lang_val:
                language = lang_val

        # Extract optional word_timestamps parameter
        word_timestamps = False
        wt_tensor = pb_utils.get_input_tensor_by_name(
            request, "word_timestamps"
        )
        if wt_tensor is not None:
            word_timestamps = bool(wt_tensor.as_numpy()[0])

        # Write audio to temp file (faster-whisper needs a file path)
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            segments_iter, info = self.whisper_model.transcribe(
                tmp_path,
                language=language if language != "auto" else None,
                task="transcribe",
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 200,
                },
                word_timestamps=word_timestamps,
            )

            segments_list = []
            full_text_parts = []

            for segment in segments_iter:
                seg_data = {
                    "start": round(segment.start, 3),
                    "end": round(segment.end, 3),
                    "text": segment.text.strip(),
                    "confidence": round(segment.avg_logprob, 4),
                }

                if word_timestamps and segment.words:
                    seg_data["words"] = [
                        {
                            "word": w.word.strip(),
                            "start": round(w.start, 3),
                            "end": round(w.end, 3),
                            "probability": round(w.probability, 4),
                        }
                        for w in segment.words
                    ]

                segments_list.append(seg_data)
                full_text_parts.append(segment.text.strip())

            return json.dumps({
                "text": " ".join(full_text_parts),
                "segments": segments_list,
                "language": info.language,
                "confidence": round(info.language_probability, 4),
            })
        finally:
            os.unlink(tmp_path)

    def finalize(self):
        """Called when the model instance is unloaded."""
        pb_utils.Logger.log_info("[whisper_stt] Finalizing instance")
        if hasattr(self, "whisper_model"):
            del self.whisper_model
