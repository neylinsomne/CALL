# Shared Models Directory
This directory stores downloaded models shared between services.

Models are automatically downloaded on first run:
- F5-TTS Spanish model
- Whisper large-v3

To pre-download models, run:
```bash
docker-compose run --rm tts python -c "from f5_tts.api import F5TTS; F5TTS()"
docker-compose run --rm stt python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3')"
```
