# AI Call Center - VOIP Voice Assistant

Sistema de call center con IA que integra síntesis de voz en español, LLM conversacional via LM Studio, y VOIP con Asterisk.

## 🚀 Quick Start

```bash
# 1. Copiar configuración
cp .env.example .env

# 2. Editar .env con tus API keys
notepad .env

# 3. Iniciar LM Studio y cargar modelo (Qwen3-14B o Llama-3.1-8B)

# 4. Build y start
docker-compose up --build
```

## 📁 Estructura

```
├── services/
│   ├── backend/      # FastAPI + WebSocket manager
│   ├── tts/          # Spanish F5-TTS
│   ├── stt/          # Whisper STT
│   ├── llm/          # LangChain + LM Studio
│   ├── asterisk/     # Asterisk PBX
│   └── training/     # Fine-tuning pipeline
└── shared/models/    # Modelo storage compartido
```

## 🎤 Fine-tuning de Voz

Ver [services/training/README.md](services/training/README.md) para instrucciones de personalización de voz.

## 📞 Conexión VOIP

1. Configurar softphone (Zoiper, Linphone, etc.)
2. Registrar con credenciales en `.env`
3. Llamar a extensión `100`

## 🔧 Requisitos

- Docker & Docker Compose
- GPU NVIDIA con CUDA (para TTS)
- LM Studio corriendo localmente
- ~16GB RAM mínimo
