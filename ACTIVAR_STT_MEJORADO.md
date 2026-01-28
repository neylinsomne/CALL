# Activar STT Mejorado con Clarificación y Corrección de Errores

Guía rápida para activar y probar el sistema STT optimizado con confidence scoring, banco de errores vectorial, y clarificaciones inteligentes.

---

## 1. Instalar Dependencias

```bash
cd services/stt

# Instalar nuevas dependencias para features mejoradas
pip install sentence-transformers faiss-cpu loguru

# Los modelos de embeddings se descargan automáticamente (~400MB)
# Se hace en el primer uso
```

---

## 2. Verificar Archivos

Asegúrate de tener estos archivos:

```
services/stt/
├── stt_server.py (MODIFICADO - con endpoint /transcribe/enhanced)
├── clarification_system.py (NUEVO)
├── error_correction_bank.py (NUEVO)
└── requirements.txt (MODIFICADO)
```

---

## 3. Reiniciar Servicio STT

```bash
# Si usas Docker
docker-compose restart stt

# Si trabajas localmente
cd services/stt
python stt_server.py
```

El servicio cargará:
1. Whisper large-v3
2. Sentence-transformers para embeddings
3. FAISS index para búsqueda rápida
4. Banco de errores pre-cargado

Verifica en logs:
```
[INFO] Whisper model loaded successfully!
[INFO] Enhanced STT features loaded
[INFO] Error correction bank initialized with 15 patterns
[INFO] Clarification system ready
```

---

## 4. Probar Features

### Test 1: Transcripción Básica vs Enhanced

#### Endpoint antiguo (básico):
```bash
curl -X POST http://localhost:8002/transcribe \
  -F "audio=@test_audio.wav"
```

Respuesta:
```json
{
  "text": "Necesito revisar el salgo de mi cuesta",
  "language": "es",
  "confidence": 0.92,
  "segments": [...]
}
```

#### Endpoint nuevo (mejorado):
```bash
curl -X POST http://localhost:8002/transcribe/enhanced \
  -F "audio=@test_audio.wav" \
  -F "conversation_id=test-123" \
  -F "enable_correction=true" \
  -F "enable_clarification=true"
```

Respuesta mejorada:
```json
{
  "text": "Necesito revisar el salgo de mi cuesta",
  "corrected_text": "Necesito revisar el saldo de mi cuenta",
  "language": "es",
  "confidence": 0.92,
  "word_confidences": [
    {"word": "Necesito", "confidence": 0.98},
    {"word": "revisar", "confidence": 0.95},
    {"word": "salgo", "confidence": 0.45},
    {"word": "cuesta", "confidence": 0.52}
  ],
  "corrections_made": [
    {"original": "salgo", "corrected": "saldo"},
    {"original": "cuesta", "corrected": "cuenta"}
  ],
  "needs_clarification": false,
  "intent_detected": "request_info",
  "normalized_entities": {...}
}
```

Nota: Corrección automática de "salgo" → "saldo" y "cuesta" → "cuenta"

---

### Test 2: Detección de Clarificación Necesaria

Graba un audio con una palabra crítica poco clara, como:

"Quiero [murmullo] mi cuenta"

El sistema debería detectar:

```json
{
  "text": "Quiero... mi cuenta",
  "corrected_text": "Quiero... mi cuenta",
  "needs_clarification": true,
  "clarification_type": "critical_word_unclear",
  "clarification_prompt": "¿Dijiste 'cancelar'? Quiero confirmar antes de proceder.",
  "word_confidences": [
    {"word": "Quiero", "confidence": 0.95},
    {"word": "cancelar", "confidence": 0.35},
    {"word": "mi", "confidence": 0.98},
    {"word": "cuenta", "confidence": 0.92}
  ]
}
```

Tipos de clarificación:
- `critical_word_unclear` - Palabra importante con baja confianza
- `semantic_incoherence` - Texto sin sentido
- `low_overall_confidence` - Confianza general baja
- `number_unclear` - Número mal escuchado

---

### Test 3: Aprendizaje desde Correcciones

Si el usuario corrige una transcripción:

```bash
curl -X POST http://localhost:8002/learn_correction \
  -F "original_text=Mi imeil es test" \
  -F "corrected_text=Mi email es test"
```

El sistema:
1. Identifica que "imeil" → "email"
2. Añade al banco de errores
3. Guarda en `models/learned_error_patterns.json`
4. Futuras transcripciones con "imeil" se corregirán automáticamente

Respuesta:
```json
{
  "status": "success",
  "message": "Correction learned successfully",
  "original": "Mi imeil es test",
  "corrected": "Mi email es test"
}
```

---

### Test 4: Detección de Intención

El sistema detecta automáticamente la intención:

Audio: "Quiero cancelar mi servicio"

```json
{
  "intent_detected": "cancel",
  "normalized_entities": {
    "numbers": [],
    "emails": [],
    "phones": [],
    "amounts": []
  }
}
```

Intenciones detectadas:
- `greeting` - Hola, buenos días
- `question` - Preguntas (¿cómo...?, ¿cuándo...?)
- `complaint` - Quejas
- `request_info` - Solicitud de información
- `request_transfer` - Transferir a supervisor
- `cancel` - Cancelación
- `update` - Cambios
- `payment` - Pagos
- `farewell` - Despedidas

---

### Test 5: Normalización de Entidades

Audio: "Mi teléfono es 612 345 678 y debo 45.50 euros"

```json
{
  "corrected_text": "Mi teléfono es 612 345 678 y debo 45.50 euros",
  "normalized_entities": {
    "phones": ["612 345 678"],
    "amounts": ["45.50 euros"],
    "numbers": [],
    "emails": [],
    "dates": []
  }
}
```

---

## 5. Integración con Backend

Modificar [services/backend/main.py](services/backend/main.py) para usar el endpoint mejorado:

```python
# En el WebSocket handler

async def handle_audio_chunk(websocket, conversation_id, audio_data):
    # Usar STT mejorado en lugar del básico
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://stt:8002/transcribe/enhanced",
            files={"audio": ("audio.wav", audio_data, "audio/wav")},
            data={
                "conversation_id": conversation_id,
                "enable_correction": True,
                "enable_clarification": True
            }
        )

    result = response.json()

    # Si necesita clarificación, enviar mensaje especial
    if result['needs_clarification']:
        await websocket.send_json({
            "type": "clarification_request",
            "text": result['clarification_prompt'],
            "original": result['text'],
            "confidence": result['confidence']
        })

        # Usar el prompt de clarificación como input al LLM
        llm_input = result['clarification_prompt']
    else:
        # Usar texto corregido normalmente
        llm_input = result['corrected_text']

        # Enviar transcripción al cliente
        await websocket.send_json({
            "type": "transcription",
            "text": result['corrected_text'],
            "original": result['text'],
            "corrections": result['corrections_made'],
            "confidence": result['confidence'],
            "intent": result['intent_detected']
        })

    # Continuar con LLM
    llm_response = await call_llm(conversation_id, llm_input, result['intent_detected'])
```

---

## 6. Verificar en Logs

```bash
# Ver logs del servicio STT
docker logs -f call-stt

# Buscar estos mensajes:
[INFO] Enhanced transcription requested
[INFO] Word-level confidence computed: 0.87
[INFO] Error correction applied: 2 changes
[INFO] Clarification needed: critical_word_unclear
[INFO] Intent detected: request_info
```

---

## 7. Configuración Avanzada

### Ajustar Umbrales de Clarificación

Editar [services/stt/clarification_system.py:29](services/stt/clarification_system.py#L29):

```python
def __init__(self):
    self.confidence_threshold = 0.7  # Reducir para más clarificaciones
    self.max_clarifications_per_conversation = 3  # Aumentar si es necesario
    self.semantic_coherence_threshold = 0.5  # Ajustar sensibilidad
```

### Añadir Palabras Críticas Personalizadas

Editar [services/stt/clarification_system.py:30-37](services/stt/clarification_system.py#L30-L37):

```python
self.critical_words = {
    "números": ["cuenta", "número", "código", "pin", "clave"],
    "acciones": ["cancelar", "eliminar", "transferir", "pagar"],
    "negaciones": ["no", "nunca", "ningún"],
    "confirmaciones": ["sí", "confirmo", "acepto"],
    "custom": ["tu", "palabra", "crítica"]  # AÑADIR AQUÍ
}
```

### Añadir Errores Comunes al Banco

Editar [services/stt/error_correction_bank.py:32-47](services/stt/error_correction_bank.py#L32-L47):

```python
self.error_patterns = {
    "cuesta": "cuenta",
    "salgo": "saldo",
    "i-mail": "email",
    # AÑADIR TUS PATRONES AQUÍ
    "tu_error": "tu_correccion",
}
```

O usar el endpoint para aprender dinámicamente (recomendado).

---

## 8. Métricas y Monitoreo

### Endpoint de Salud

```bash
curl http://localhost:8002/health
```

Respuesta:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_size": "large-v3",
  "device": "cuda",
  "enhanced_features": true,
  "error_bank_patterns": 15
}
```

### Métricas de Conversación

Las métricas STT ahora incluyen:

```python
{
    "conversation_id": "conv-123",
    "stt_metrics": {
        "avg_confidence": 0.87,
        "corrections_made": 5,
        "clarifications_requested": 2,
        "low_confidence_words": 12,
        "intents_detected": ["question", "request_info"],
        "entities_extracted": {"phones": 1, "emails": 1}
    }
}
```

---

## 9. Troubleshooting

### Error: "Enhanced features not available"

Causa: Faltan dependencias

Solución:
```bash
pip install sentence-transformers faiss-cpu loguru
```

### Error: "CUDA out of memory"

Causa: sentence-transformers + Whisper large en GPU pequeña

Solución:
```python
# En error_correction_bank.py, forzar CPU para embeddings
self.model = SentenceTransformer(
    'paraphrase-multilingual-MiniLM-L12-v2',
    device='cpu'
)
```

### Performance: Latencia alta (>1500ms)

Causa: Error correction añade overhead

Solución 1 - Reducir beam_size:
```python
# En stt_server.py
beam_size=3  # En lugar de 5
```

Solución 2 - Desactivar correction para mensajes cortos:
```python
if len(audio_data) < 3000:  # < 3 segundos
    enable_correction = False
```

### Correcciones Incorrectas

Causa: Banco de errores demasiado agresivo

Solución - Aumentar threshold:
```python
# En error_correction_bank.py
def correct_transcription(self, text: str, distance_threshold=0.5):
    # Aumentar a 0.9 para ser más conservador
```

---

## 10. Testing Completo

Script de prueba Python:

```python
import requests
import os

# Test completo del sistema
def test_enhanced_stt():
    url = "http://localhost:8002/transcribe/enhanced"

    # Audio de prueba
    audio_file = "test_audio.wav"

    with open(audio_file, "rb") as f:
        response = requests.post(
            url,
            files={"audio": f},
            data={
                "conversation_id": "test-123",
                "enable_correction": "true",
                "enable_clarification": "true"
            }
        )

    result = response.json()

    print("=== RESULTADO STT MEJORADO ===")
    print(f"Texto original: {result['text']}")
    print(f"Texto corregido: {result['corrected_text']}")
    print(f"Confianza global: {result['confidence']:.2%}")
    print(f"Intención: {result['intent_detected']}")

    if result['corrections_made']:
        print("\nCorrecciones aplicadas:")
        for corr in result['corrections_made']:
            print(f"  '{corr['original']}' → '{corr['corrected']}'")

    if result['needs_clarification']:
        print(f"\nCLARIFICACIÓN NECESARIA:")
        print(f"  Tipo: {result['clarification_type']}")
        print(f"  Prompt: {result['clarification_prompt']}")

    print("\nPalabras con baja confianza:")
    for word in result['word_confidences']:
        if word['confidence'] < 0.7:
            print(f"  '{word['word']}': {word['confidence']:.2%}")

    print("\nEntidades extraídas:")
    for entity_type, values in result['normalized_entities'].items():
        if values:
            print(f"  {entity_type}: {values}")

if __name__ == "__main__":
    test_enhanced_stt()
```

---

## Resultado Esperado

Con todo funcionando correctamente:

```
[13:45:23] Audio recibido (4.2s)
[13:45:23] Whisper transcription: 850ms
[13:45:24] Word confidence computed: avg 0.87
[13:45:24] Error correction: 2 changes applied
[13:45:24] Clarification check: none needed
[13:45:24] Intent detection: request_info
[13:45:24] Entity extraction: 1 phone, 0 emails
[13:45:24] Total STT latency: 920ms (vs 800ms sin features)

Usuario: "Necesito revisar el salgo de mi cuesta"
STT Mejorado: "Necesito revisar el saldo de mi cuenta" ✓
Intención: request_info ✓
Confianza: 0.92 ✓
Clarificación: No necesaria ✓
```

---

## Próximos Pasos

1. Probar con audios reales de tu call center
2. Monitorear qué errores comunes aparecen
3. Usar `/learn_correction` para mejorar el banco
4. Ajustar umbrales según tus necesidades
5. Integrar completamente en el pipeline principal

---

Lee documentación completa en:
- [OPTIMIZACION_STT_ESTADO_DEL_ARTE.md](OPTIMIZACION_STT_ESTADO_DEL_ARTE.md) - Documentación completa
- [MANEJO_VOZ_Y_CONTEXTO.md](MANEJO_VOZ_Y_CONTEXTO.md) - Prosodia y contexto
- [ACTIVAR_VOZ_CONTEXTUAL.md](ACTIVAR_VOZ_CONTEXTUAL.md) - Features de voz

---

El STT ahora es inteligente, se autocorrige, y sabe cuándo pedir ayuda.
