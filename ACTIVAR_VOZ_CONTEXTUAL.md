# Activar Sistema de Voz Contextual

Guía rápida para activar y probar Target Speaker Extraction y Prosody Analysis.

---

## 1. Instalar Dependencias

```bash
cd services/audio_preprocess

# Instalar nuevas dependencias
pip install speechbrain librosa

# Descargar modelos (primera vez, ~1.5GB)
# Se hace automáticamente al iniciar
```

---

## 2. Configurar Variables de Entorno

Edita `.env` en la raíz del proyecto:

```bash
# Audio Processing Features
ENABLE_DENOISE=true  # Ya existe
ENABLE_TARGET_EXTRACTION=true  # NUEVO - Aislar voz del cliente
ENABLE_PROSODY_ANALYSIS=true  # NUEVO - Detectar preguntas y pausas
```

---

## 3. Reiniciar Servicios

```bash
docker-compose down
docker-compose up --build
```

O si trabajas localmente:

```bash
cd services/backend
python main.py
```

---

## 4. Probar Funcionalidad

### Test 1: Voice Profile Creation

1. Conectar WebSocket al endpoint: `ws://localhost:8000/ws/test-conversation`

2. Enviar audio (primeros 3 segundos crean el perfil)

3. Deberías recibir:
```json
{
  "type": "voice_profile_created",
  "message": "Perfil de voz creado exitosamente"
}
```

### Test 2: Prosody Analysis

Mientras hablas, recibirás mensajes en tiempo real:

```json
{
  "type": "prosody",
  "data": {
    "is_question": false,
    "pause_duration": 0.8,
    "should_wait": true,
    "emotional_tone": "neutral",
    "has_speech": true
  }
}
```

### Test 3: Question Detection

Haz una pregunta con entonación ascendente:

**Tú:** "¿Cómo funciona esto?"

Deberías ver:
```json
{
  "type": "transcription",
  "text": "¿Cómo funciona esto?",
  "prosody": {
    "is_question": true,
    "emotional_tone": "neutral",
    "speech_rate": 145
  }
}
```

### Test 4: Thinking Pause

Habla con pausas:

**Tú:** "Necesito ayuda con... [pausa 1.5s] ...mi cuenta"

El sistema debería:
- Detectar `is_thinking_pause = true`
- Esperar audio adicional
- Transcribir la frase completa

---

## 5. Verificar en Logs

```bash
# Ver logs del backend
docker logs -f call-backend

# Buscar estos mensajes:
[INFO] Target Speaker Extraction habilitado
[INFO] Prosody Analysis habilitado
[conversation_id] Voice profile created
[conversation_id] Target extraction: 65ms
```

---

## 6. Métricas en Base de Datos

Las nuevas métricas se guardan automáticamente:

```bash
curl http://localhost:8000/conversations/CONVERSATION_ID/metrics
```

Respuesta:
```json
{
  "conversation_id": "...",
  "total_turns": 5,
  "avg_stt_latency_ms": 420,
  "avg_llm_latency_ms": 1150,
  "avg_tts_latency_ms": 780,
  "target_extraction_ms": 65,
  "prosody_is_question": true,
  "prosody_emotional_tone": "neutral"
}
```

---

## 7. Desactivar Features (Opcional)

Si experimentas problemas o quieres comparar:

```bash
# En .env
ENABLE_TARGET_EXTRACTION=false
ENABLE_PROSODY_ANALYSIS=false
```

El sistema funcionará normalmente sin estas features.

---

## 8. Ajustar Sensibilidad

Si el sistema:
- **Corta demasiado pronto:** Aumenta `end_of_turn_pause`
- **Tarda mucho:** Reduce `end_of_turn_pause`
- **No detecta preguntas:** Reduce `question_pitch_rise_threshold`

Edita [prosody_analyzer.py](services/audio_preprocess/prosody_analyzer.py):

```python
def __init__(self, sample_rate: int = 16000):
    self.end_of_turn_pause = 2.0  # Aumentar/reducir
    self.question_pitch_rise_threshold = 1.10  # Reducir para más detección
    self.thinking_pause_max = 3.0  # Aumentar para más paciencia
```

---

## 9. Debugging

### Ver Análisis en Cliente

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/my-conversation');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'voice_profile_created':
      console.log('Perfil de voz listo');
      break;

    case 'prosody':
      console.log('Prosodia:', data.data);
      // Mostrar indicadores en UI
      if (data.data.should_wait) {
        showIndicator('Esperando más audio...');
      }
      if (data.data.is_question) {
        showIcon('❓');
      }
      break;

    case 'transcription':
      console.log('Transcripción:', data.text);
      if (data.prosody) {
        console.log('Es pregunta:', data.prosody.is_question);
      }
      break;
  }
};
```

---

## 10. Troubleshooting

### Error: "Target Speaker Extraction no disponible"

**Causa:** Falta speechbrain o modelos

**Solución:**
```bash
pip install speechbrain torch torchaudio
```

### Error: "Prosody Analysis no disponible"

**Causa:** Falta librosa

**Solución:**
```bash
pip install librosa
```

### Performance: Latencia alta

**Si target extraction añade >150ms:**

1. Reducir calidad del modelo:
```python
# En target_speaker.py
self.has_separator = False  # Desactivar separator
```

2. O desactivar completamente:
```bash
ENABLE_TARGET_EXTRACTION=false
```

---

## Resultado Esperado

Con todo activado:

```
[13:45:23] User connects
[13:45:23] Voice profile created (3.2s audio)
[13:45:26] Prosody: pause=1.2s, is_thinking=True, wait=True
[13:45:28] Prosody: pause=0.3s, is_question=True, wait=False
[13:45:28] Target extraction: 68ms
[13:45:28] STT: "¿Cómo puedo cambiar mi contraseña?" (WER: 0%)
[13:45:28] Sentiment: neutral (0.1)
[13:45:28] LLM guidance: "Usuario hizo pregunta"
[13:45:29] AI: "Para cambiar tu contraseña..."
[13:45:30] TTS: Generated
[13:45:30] Total latency: 2.1s (vs 2.5s sin features)
```

---

Lee documentación completa en:
- [MODELOS_TRATAMIENTO_VOZ.md](MODELOS_TRATAMIENTO_VOZ.md) - Modelos disponibles
- [MANEJO_VOZ_Y_CONTEXTO.md](MANEJO_VOZ_Y_CONTEXTO.md) - Cómo funciona todo

---

Listo para mejorar la calidad de tus conversaciones!
