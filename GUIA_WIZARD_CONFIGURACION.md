# Guía del Wizard de Configuración

## Descripción

El **Wizard de Configuración** es una interfaz web intuitiva que detecta automáticamente tu hardware de telefonía y configura el sistema según tus necesidades.

---

## Características

✅ **Detección automática de hardware** (Gateway FXO/FXS vs Tarjetas DAHDI)
✅ **Configuración de SIP Trunk** manual
✅ **Configuración de servicios de IA** (STT, TTS, LLM)
✅ **Clonación de voz personalizada** (opcional)
✅ **Flujo adaptativo** según hardware detectado

---

## Acceso al Wizard

### Opción 1: Primera vez (automático)
Al iniciar el sistema por primera vez sin configuración, serás redirigido automáticamente al wizard.

### Opción 2: Manual
Accede directamente a: **http://localhost:3001/setup**

---

## Flujo del Wizard (4 Pasos)

### **Paso 1: Configuración de Telefonía**

#### Pregunta Principal: ¿Usas SIP TRUNK?

**Opción A: SÍ → Configuración Manual**

Si seleccionas "Sí, SIP TRUNK", verás un formulario para ingresar:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Host del Proveedor SIP** | Dominio del proveedor | `sip.proveedor.com` |
| **Usuario** | Tu usuario SIP | `usuario_sip` |
| **Contraseña** | Contraseña de autenticación | `••••••••` |
| **Caller ID Saliente** (opcional) | Número para llamadas salientes | `+1234567890` |

**Opción B: NO → Detección Automática de Hardware**

Si seleccionas "No, líneas fijas", el sistema detectará automáticamente:

1. **Gateway FXO/FXS**
   - Escanea la red buscando endpoints PJSIP
   - Hace ping a la IP configurada en GATEWAY_FXO_IP
   - Si lo encuentra, muestra:
     - IP del gateway
     - Número de canales detectados
     - Solicita contraseña del gateway

2. **Tarjetas DAHDI (Digium/Sangoma)**
   - Verifica dispositivo `/dev/dahdi`
   - Ejecuta `dahdi_scan` para detalles
   - Si las encuentra, muestra:
     - Tipo de tarjeta
     - Número de canales detectados
     - Tipo de señalización (FXO/FXS)

3. **Ambos (Híbrido)**
   - Si detecta Gateway + DAHDI simultáneamente
   - Configura rutas preferenciales: DAHDI → Gateway → SIP

**Resultado de Detección:**

```
✅ Hardware Detectado
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tipo: both
Canales PSTN: 12
Gateway IP: 192.168.1.100
DAHDI Canales: 8
━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Paso 2: Servicios de IA**

Configuración de los 3 servicios principales:

#### **STT (Speech-to-Text)**
| Configuración | Opciones |
|---------------|----------|
| Habilitado | ☑️ Sí / ☐ No |
| Puerto | `8002` (fijo) |
| Dispositivo | CUDA (GPU) / CPU |
| Modelo | `large-v3` (mejor) / `medium` / `small` (más rápido) |
| Idioma | `es` (español) |

#### **TTS (Text-to-Speech)**
| Configuración | Opciones |
|---------------|----------|
| Habilitado | ☑️ Sí / ☐ No |
| Puerto | `8001` (fijo) |
| Dispositivo | CUDA (GPU) / CPU |
| Modelo | `jpgallegoar/F5-Spanish` (fijo) |

#### **LLM (Large Language Model)**
| Configuración | Opciones |
|---------------|----------|
| Habilitado | ☑️ Sí / ☐ No |
| Puerto | `8003` (fijo) |
| Proveedor | LM Studio (local) / OpenAI API / Anthropic (Claude) |

**Nota:** Si deshabilitas un servicio, las llamadas no podrán usar esa funcionalidad.

---

### **Paso 3: Entrenamiento de Voz** (Opcional)

Clonación de voz personalizada para que el AI suene como tú quieras.

| Campo | Descripción |
|-------|-------------|
| **Habilitar clonación** | ☐ Activar entrenamiento de voz |
| **Audio de Referencia** | Sube un archivo de 10-30 segundos |
| **Nombre del Speaker** | Ej: "Agente Virtual Empresa" |

**Formatos soportados:** WAV, MP3, FLAC
**Duración recomendada:** 10-30 segundos
**Calidad:** Voz clara, sin ruido de fondo

⏱️ **Tiempo de entrenamiento:** 10-30 minutos (en segundo plano)

---

### **Paso 4: Resumen y Confirmación**

Revisa toda la configuración antes de guardar:

**Ejemplo de resumen:**

```
📋 RESUMEN DE CONFIGURACIÓN

📞 Telefonía
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hardware: both
Canales PSTN: 12
Gateway IP: 192.168.1.100
DAHDI Canales: 8

🤖 Servicios de IA
━━━━━━━━━━━━━━━━━━━━━━━━━━━
STT (Whisper): ✓ Habilitado
TTS (F5-TTS): ✓ Habilitado
LLM: ✓ lm-studio

🎤 Clonación de Voz
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Audio de referencia: voz_empresa.wav
Speaker: Agente Virtual Empresa
```

**Botón:** 🟢 **Guardar y Finalizar**

---

## ¿Qué sucede al guardar?

1. **Se guarda la configuración** en `/app/config/callcenter_config.json`

2. **Se actualiza `.env`** con las nuevas variables:
   ```bash
   # Si usas SIP Trunk
   SIP_TRUNK_HOST=sip.proveedor.com
   SIP_TRUNK_USER=usuario_sip
   SIP_TRUNK_PASSWORD=password_seguro

   # Si usas Gateway
   GATEWAY_FXO_IP=192.168.1.100
   GATEWAY_FXO_USER=gateway
   GATEWAY_FXO_PASSWORD=password_gateway

   # Servicios de IA
   STT_MODEL=large-v3
   STT_DEVICE=cuda
   TTS_DEVICE=cuda
   ```

3. **Se configura el flujo adaptativo**:
   - Si detectó Gateway → Rutas `8XXXXXXX` para llamadas salientes por Gateway
   - Si detectó DAHDI → Rutas `7XXXXXXX` para llamadas salientes por DAHDI
   - Si detectó ambos → Rutas `6XXXXXXX` para smart routing (intenta todos)
   - SIP Trunk → Rutas `9XXXXXXX` (siempre disponible)

4. **Se generan archivos de configuración de Asterisk**:
   - `pjsip_custom.conf` con endpoints configurados
   - Se actualizan contextos en `extensions.conf`

5. **Redirección al Dashboard**

---

## Flujos de Llamadas Configurados

Según tu configuración, el sistema usará estos flujos:

### **Caso 1: Solo SIP Trunk**

```
Llamada Entrante (Internet)
    ↓
SIP Trunk → Asterisk [from-trunk]
    ↓
AudioSocket → Backend IA
    ↓
STT → LLM → TTS
    ↓
Respuesta al cliente
```

### **Caso 2: Solo Gateway FXO**

```
Llamada Entrante (Línea Fija)
    ↓
Gateway FXO → Asterisk [from-pstn-gateway]
    ↓
AudioSocket → Backend IA
    ↓
STT → LLM → TTS
    ↓
Respuesta al cliente
```

### **Caso 3: Solo DAHDI**

```
Llamada Entrante (Línea Fija)
    ↓
Tarjeta Digium → Asterisk [from-pstn-dahdi]
    ↓
AudioSocket → Backend IA
    ↓
STT → LLM → TTS
    ↓
Respuesta al cliente
```

### **Caso 4: Híbrido (Gateway + DAHDI)**

```
Llamada Entrante (Línea Fija 1-8)
    ↓
Tarjeta DAHDI → Asterisk [from-pstn-dahdi]
    ↓
AudioSocket → Backend IA
    ↓
STT → LLM → TTS
    ↓
Respuesta al cliente

───────────────────────────────────

Llamada Entrante (Línea Fija 9-12)
    ↓
Gateway FXO → Asterisk [from-pstn-gateway]
    ↓
(Mismo flujo de IA)
```

**Llamadas salientes (smart routing):**
```
Marca 65551234
    ↓
Intenta:
1. DAHDI (canal disponible?) → Marca por línea fija
2. Gateway (canal disponible?) → Marca por gateway
3. SIP Trunk (siempre) → Marca por internet
```

---

## Endpoints de API

El wizard expone estos endpoints:

### `POST /api/config/detect-hardware`
Detecta hardware automáticamente.

**Response:**
```json
{
  "hardware_type": "both",
  "pstn_channels": 12,
  "gateway_detected": true,
  "gateway_ip": "192.168.1.100",
  "dahdi_detected": true,
  "dahdi_channels": [
    ["1", "FXO"],
    ["2", "FXO"]
  ],
  "max_concurrent_calls": 12,
  "route_preference": ["dahdi", "gateway", "sip_trunk"]
}
```

### `POST /api/config/save`
Guarda configuración.

**Request:**
```json
{
  "telephony": {
    "useSipTrunk": false,
    "hardware": {
      "type": "both",
      "pstnChannels": 12
    }
  },
  "aiServices": {
    "stt": { "enabled": true, "model": "large-v3" },
    "tts": { "enabled": true },
    "llm": { "enabled": true, "provider": "lm-studio" }
  }
}
```

**Response:**
```json
{
  "success": true,
  "config_file": "/app/config/callcenter_config.json",
  "env_updated": true
}
```

### `GET /api/config`
Obtiene configuración actual.

### `POST /api/config/validate`
Valida configuración antes de guardar.

### `POST /api/config/upload-voice`
Sube audio de referencia para clonación.

---

## Servicios en Puertos

Todos los servicios están disponibles en puertos específicos:

| Servicio | Puerto | URL |
|----------|--------|-----|
| **Backend API** | 8000 | http://localhost:8000 |
| **TTS (F5-TTS)** | 8001 | http://localhost:8001 |
| **STT (Whisper)** | 8002 | http://localhost:8002 |
| **LLM (LangChain)** | 8003 | http://localhost:8003 |
| **Audio Preprocess** | 8004 | http://localhost:8004 |
| **Asterisk ARI** | 8088 | http://localhost:8088 |
| **Asterisk AMI** | 5038 | (TCP) |
| **FreePBX Web UI** | 8080 | http://localhost:8080 |
| **Dashboard React** | 3001 | http://localhost:3001 |

---

## Reconfigurar el Sistema

Si necesitas cambiar la configuración después:

1. Accede al wizard: http://localhost:3001/setup
2. Modifica los valores necesarios
3. Guarda de nuevo

⚠️ **Nota:** Al guardar, se reiniciará el flujo de llamadas según la nueva configuración.

---

## Troubleshooting

### El wizard no detecta mi Gateway

**Soluciones:**
1. Verifica que el Gateway esté encendido y conectado a la red
2. Verifica que la IP en `.env` (`GATEWAY_FXO_IP`) sea correcta
3. Haz ping manual: `ping 192.168.1.100`
4. Verifica que el Gateway esté configurado para registrarse en Asterisk

### El wizard no detecta DAHDI

**Soluciones:**
1. Verifica que la tarjeta esté instalada: `lspci | grep -i digium`
2. Verifica drivers DAHDI: `lsmod | grep dahdi`
3. Ejecuta: `sudo dahdi_cfg -vvv`
4. Si estás en Docker, asegúrate de mapear `/dev/dahdi`

### Los servicios de IA no inician

**Soluciones:**
1. Verifica logs: `docker-compose logs -f stt tts llm`
2. Verifica que tienes GPU NVIDIA: `nvidia-smi`
3. Verifica que los modelos se descargaron correctamente
4. Si no tienes GPU, cambia `DEVICE` a `cpu` (más lento)

### El voice training falla

**Soluciones:**
1. Verifica que el audio sea de buena calidad (sin ruido)
2. Verifica duración (10-30 segundos recomendado)
3. Revisa logs: `docker-compose logs -f tts`

---

## Ejemplos de Configuración

### Ejemplo 1: Oficina Pequeña con SIP Trunk

```
Paso 1: ✅ Sí, SIP TRUNK
  Host: sip.voip.ms
  User: 123456
  Password: ••••••••

Paso 2: ✅ Todos los servicios habilitados
  STT: large-v3, CUDA
  TTS: F5-Spanish, CUDA
  LLM: lm-studio

Paso 3: ☐ Sin clonación de voz

→ Resultado: Llamadas por internet, máximo 100 llamadas simultáneas (límite: GPU)
```

### Ejemplo 2: Call Center con Gateway + DAHDI

```
Paso 1: ☐ No, líneas fijas
  Hardware detectado: both
  DAHDI: 8 canales
  Gateway: 4 canales
  Total: 12 líneas PSTN

Paso 2: ✅ Todos los servicios habilitados

Paso 3: ✅ Clonación de voz
  Audio: voz_empresa.wav
  Speaker: Agente Virtual Empresa

→ Resultado: 12 líneas fijas, smart routing, voz personalizada
```

### Ejemplo 3: Solo DAHDI con voz personalizada

```
Paso 1: ☐ No, líneas fijas
  Hardware detectado: dahdi
  DAHDI: 24 canales (Sangoma A400)

Paso 2: ✅ Todos habilitados

Paso 3: ✅ Clonación de voz

→ Resultado: 24 líneas fijas directas, alta calidad, voz personalizada
```

---

## Próximos Pasos

Después de completar el wizard:

1. **Prueba una llamada** al número de tu trunk o línea fija
2. **Accede al Dashboard**: http://localhost:3001
3. **Verifica FreePBX**: http://localhost:8080 (si lo instalaste)
4. **Monitorea logs**: `docker-compose logs -f`

---

## Archivos Generados

El wizard crea/modifica estos archivos:

```
/app/config/
  └── callcenter_config.json    # Configuración guardada

.env                             # Variables de entorno actualizadas

/etc/asterisk/
  ├── pjsip_custom.conf         # Endpoints generados
  └── extensions_custom.conf     # Contextos generados (si aplica)

/app/config/voice_training/
  └── reference_audio.wav       # Audio de referencia (si aplica)
```

---

## Soporte

Si tienes problemas:

1. Revisa logs: `docker-compose logs -f backend`
2. Verifica conectividad de hardware
3. Consulta [GUIA_INSTALACION_FREEPBX_ARI.md](GUIA_INSTALACION_FREEPBX_ARI.md)
4. Consulta [ARQUITECTURA_AVANZADA_ARI.md](ARQUITECTURA_AVANZADA_ARI.md)

---

**Fecha:** 2026-01-29
**Versión:** 1.0
**Estado:** ✅ Wizard completo y funcional
