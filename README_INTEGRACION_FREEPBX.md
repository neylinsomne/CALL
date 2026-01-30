# Integración FreePBX + ARI + Gateway/DAHDI - Resumen

## 📋 Resumen Ejecutivo

Se ha completado la integración de **FreePBX**, **Asterisk REST Interface (ARI) mejorado**, y soporte para **líneas fijas PSTN** (vía Gateway FXO/FXS y tarjetas Digium PCIe) en tu sistema de Call Center con IA.

Esta integración te permite:

✅ Recibir llamadas desde **SIP Trunk** (internet)
✅ Recibir llamadas desde **líneas telefónicas fijas** (PSTN)
✅ Gestionar Asterisk visualmente con **FreePBX**
✅ Controlar llamadas programáticamente con **ARI** desde Python
✅ Eventos en tiempo real vía **WebSocket**
✅ Transferencias, grabaciones, y bridges dinámicos

---

## 📁 Archivos Creados/Modificados

### Documentación

| Archivo | Descripción |
|---------|-------------|
| [INTEGRACION_FREEPBX_ARI_GATEWAY.md](INTEGRACION_FREEPBX_ARI_GATEWAY.md) | Arquitectura completa y especificación técnica |
| [GUIA_INSTALACION_FREEPBX_ARI.md](GUIA_INSTALACION_FREEPBX_ARI.md) | Guía paso a paso de instalación y configuración |
| [README_INTEGRACION_FREEPBX.md](README_INTEGRACION_FREEPBX.md) | Este archivo (resumen) |

### Configuración de Asterisk

| Archivo | Cambios |
|---------|---------|
| [services/asterisk/config/manager.conf](services/asterisk/config/manager.conf) | **NUEVO** - Configuración AMI para FreePBX y backend |
| [services/asterisk/config/ari.conf](services/asterisk/config/ari.conf) | **MEJORADO** - WebSocket, CORS, múltiples usuarios ARI |
| [services/asterisk/config/http.conf](services/asterisk/config/http.conf) | **MEJORADO** - HTTP server para ARI y AMI |
| [services/asterisk/config/pjsip.conf.template](services/asterisk/config/pjsip.conf.template) | **AÑADIDO** - Endpoints para Gateway FXO |
| [services/asterisk/config/chan_dahdi.conf](services/asterisk/config/chan_dahdi.conf) | **NUEVO** - Configuración para tarjetas Digium/Sangoma |
| [services/asterisk/config/extensions.conf.template](services/asterisk/config/extensions.conf.template) | **AÑADIDO** - Contextos para PSTN (Gateway y DAHDI), rutas salientes |

### Backend Python

| Archivo | Cambios |
|---------|---------|
| [services/backend/ari_client.py](services/backend/ari_client.py) | **NUEVO** - Cliente ARI completo con WebSocket, control de llamadas, grabaciones, bridges |
| [services/backend/requirements.txt](services/backend/requirements.txt) | **AÑADIDO** - aiohttp para cliente ARI |

### Docker

| Archivo | Cambios |
|---------|---------|
| [docker-compose.yml](docker-compose.yml) | **AÑADIDO** - MariaDB, FreePBX, puertos AMI, variables de entorno |
| [.env.example](.env.example) | **AÑADIDO** - Variables para ARI, AMI, FreePBX, MariaDB, Gateway |

---

## 🏗️ Arquitectura de Integración

```
┌─────────────────────────────────────────────────────────┐
│              ENTRADA DE LLAMADAS                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐    │
│  │SIP TRUNK │  │ Gateway  │  │ Tarjeta Digium    │    │
│  │(Internet)│  │ FXO/FXS  │  │ PCIe (DAHDI)      │    │
│  └────┬─────┘  └────┬─────┘  └─────┬─────────────┘    │
│       │             │               │                  │
└───────┼─────────────┼───────────────┼──────────────────┘
        │             │               │
        ▼             ▼               ▼
┌─────────────────────────────────────────────────────────┐
│                  ASTERISK PBX                           │
│  • PJSIP (SIP)                                          │
│  • DAHDI (Líneas analógicas/digitales)                  │
│  • AudioSocket → Backend IA                             │
│  • AMI → FreePBX                                        │
│  • ARI → Backend Control                                │
└──────────────┬────────────────┬─────────────────────────┘
               │                │
       ┌───────▼──────┐  ┌─────▼────────┐
       │   FreePBX    │  │Backend FastAPI│
       │  (Web GUI)   │  │  + ARI Client │
       │              │  │               │
       │ • Config PBX │  │ • WebSocket   │
       │ • IVR        │  │ • STT/TTS/LLM │
       │ • Rutas      │  │ • ARI Events  │
       │ • Extensiones│  │ • Recordings  │
       └──────────────┘  └───────────────┘
```

---

## 🚀 Componentes Principales

### 1. FreePBX
- **Puerto**: 8080 (HTTP), 8443 (HTTPS)
- **Base de datos**: MariaDB
- **Función**: Interfaz web para gestionar Asterisk
- **Acceso**: http://localhost:8080
- **Usuario**: admin / (FREEPBX_ADMIN_PASSWORD)

### 2. Asterisk REST Interface (ARI)
- **Puerto**: 8088 (HTTP/WebSocket)
- **Cliente Python**: [services/backend/ari_client.py](services/backend/ari_client.py)
- **Funciones**:
  - Eventos en tiempo real (WebSocket)
  - Control programático de llamadas
  - Originar llamadas salientes
  - Transferencias dinámicas
  - Grabaciones selectivas
  - Bridges (conectar/desconectar llamadas)

### 3. Asterisk Manager Interface (AMI)
- **Puerto**: 5038
- **Usuarios**:
  - `freepbx` - Para FreePBX
  - `backend` - Para backend Python
  - `ari` - Para ARI
- **Función**: API tradicional de Asterisk (usado por FreePBX)

### 4. Gateway FXO/FXS
- **Tipo**: Dispositivo externo (Grandstream, Cisco, etc.)
- **Configuración**: [services/asterisk/config/pjsip.conf.template](services/asterisk/config/pjsip.conf.template)
- **Endpoint**: `gateway-fxo-1`
- **Contexto entrante**: `from-pstn-gateway`
- **Función**: Convierte líneas analógicas a SIP

### 5. Tarjetas Digium/Sangoma (DAHDI)
- **Tipo**: Tarjeta PCIe interna
- **Configuración**:
  - Host: `/etc/dahdi/system.conf`
  - Asterisk: [services/asterisk/config/chan_dahdi.conf](services/asterisk/config/chan_dahdi.conf)
- **Contexto entrante**: `from-pstn-dahdi`
- **Función**: Líneas analógicas/digitales directas

---

## 🔧 Configuración de Rutas de Llamadas

### Llamadas Entrantes

| Origen | Contexto | Destino |
|--------|----------|---------|
| SIP Trunk | `from-trunk` | Extensión 100 (AI Agent) |
| Gateway FXO | `from-pstn-gateway` | Extensión 100 (AI Agent) |
| DAHDI | `from-pstn-dahdi` | Extensión 100 (AI Agent) |

### Llamadas Salientes

| Prefijo | Ruta | Ejemplo |
|---------|------|---------|
| 9 + número | SIP Trunk | 95551234 → Llama a 5551234 vía SIP |
| 8 + número | Gateway FXO | 85551234 → Llama a 5551234 vía Gateway |
| 7 + número | DAHDI | 75551234 → Llama a 5551234 vía DAHDI |
| 6 + número | Smart Routing | 65551234 → Intenta DAHDI → Gateway → SIP |

### Extensiones Internas

| Extensión | Función |
|-----------|---------|
| 100 | AI Agent (AudioSocket → Backend) |
| 200 | Cola de agentes humanos |
| 201-202 | Softphones |
| *43 | Echo test |
| *99 | Status check |

---

## 📡 Cliente ARI Python

### Características

El cliente ARI ([ari_client.py](services/backend/ari_client.py)) proporciona:

#### Event Handling
```python
@client.on("StasisStart")
async def on_call_start(event, channel):
    # Se ejecuta cuando entra una llamada
    await client.answer_channel(channel["id"])
```

#### Originar Llamadas
```python
channel = await client.originate_call(
    endpoint="PJSIP/5551234@trunk-endpoint",
    caller_id="Call Center <100>",
    variables={"CUSTOMER_ID": "12345"}
)
```

#### Transferencias
```python
await client.transfer_to_extension(
    channel_id="abc123",
    extension="200"  # Agente humano
)
```

#### Grabaciones
```python
recording = await client.start_recording(channel_id, format="wav")
# ...
await client.stop_recording(recording["name"])
```

#### Bridges (Conferencias)
```python
bridge = await client.create_bridge()
await client.add_channel_to_bridge(bridge["id"], channel1_id)
await client.add_channel_to_bridge(bridge["id"], channel2_id)
```

---

## 🎯 Casos de Uso

### 1. Llamada Entrante desde Línea Fija
```
Cliente marca línea fija
    ↓
Gateway FXO detecta llamada
    ↓
Gateway envía INVITE SIP a Asterisk
    ↓
Asterisk: Contexto [from-pstn-gateway]
    ↓
Extensión 100 (AI Agent)
    ↓
AudioSocket → Backend Python
    ↓
STT → LLM → TTS
    ↓
Cliente habla con AI
```

### 2. Transferencia a Agente Humano
```
Cliente presiona "0" durante llamada con AI
    ↓
ARI detecta DTMF "0"
    ↓
Backend ejecuta: transfer_to_extension(channel, "200")
    ↓
ARI crea bridge
    ↓
ARI origina llamada a extensión 200
    ↓
Extensión 200 entra en cola de agentes
    ↓
Agente disponible contesta
    ↓
ARI conecta ambos canales en el bridge
    ↓
Cliente habla con agente humano
```

### 3. Llamada Saliente Programática
```
Dashboard: "Llamar a cliente 5551234"
    ↓
POST /api/calls/originate
    ↓
Backend: ari_client.originate_call()
    ↓
ARI origina llamada vía SIP Trunk
    ↓
Cliente contesta
    ↓
ARI evento: StasisStart
    ↓
Backend inicia AudioSocket con AI
    ↓
AI habla con cliente
```

### 4. Grabación Selectiva
```
Supervisor marca "Grabar esta llamada"
    ↓
Dashboard envía comando a Backend
    ↓
Backend: ari_client.start_recording(channel_id)
    ↓
Asterisk inicia grabación
    ↓
Llamada continúa normalmente
    ↓
Al finalizar: audio guardado en /var/spool/asterisk/recording
```

---

## 🛠️ Instalación Rápida

### Pre-requisitos
- Docker + Docker Compose
- Linux con GPU NVIDIA (para STT/TTS)
- Gateway FXO/FXS o Tarjeta Digium (para líneas fijas)

### Pasos

1. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   nano .env  # Editar todas las variables
   ```

2. **Levantar servicios**:
   ```bash
   docker-compose up -d
   ```

3. **Acceder a FreePBX**:
   - URL: http://localhost:8080
   - Usuario: admin
   - Password: (el de .env)

4. **Verificar ARI**:
   ```bash
   docker-compose logs -f backend
   # Deberías ver: "ARI WebSocket connected"
   ```

5. **Hacer una llamada de prueba**:
   - Llama a tu SIP Trunk o línea fija
   - Deberías escuchar al AI Agent

---

## 📖 Documentación Detallada

Para información completa, consulta:

1. **[INTEGRACION_FREEPBX_ARI_GATEWAY.md](INTEGRACION_FREEPBX_ARI_GATEWAY.md)**
   - Arquitectura completa
   - Comparación Gateway vs Tarjeta Digium
   - Flujos de llamadas detallados
   - Especificación técnica

2. **[GUIA_INSTALACION_FREEPBX_ARI.md](GUIA_INSTALACION_FREEPBX_ARI.md)**
   - Instalación paso a paso
   - Configuración de Gateway
   - Configuración de DAHDI
   - Pruebas y troubleshooting
   - Solución de problemas comunes

---

## 🔐 Seguridad

**IMPORTANTE**: Cambia todos los passwords en `.env`:

```bash
# Genera passwords seguros
openssl rand -base64 32

# Configura en .env:
ASTERISK_PASSWORD=...
ARI_PASSWORD=...
FREEPBX_AMI_PASSWORD=...
MYSQL_ROOT_PASSWORD=...
```

---

## 📊 Monitoreo

### FreePBX Dashboard
- **URL**: http://localhost:8080
- Ver llamadas activas, colas, CDRs

### Asterisk CLI
```bash
docker exec -it callcenter-asterisk asterisk -rvvv
```

### Backend Logs
```bash
docker-compose logs -f backend
```

### Métricas ARI
```bash
curl http://localhost:8088/ari/api-docs/events.json
```

---

## 🧪 Testing

### Test 1: Llamada Entrante SIP
```bash
# Llama a tu número SIP Trunk
# Verifica en logs:
docker-compose logs -f asterisk | grep "from-trunk"
```

### Test 2: Llamada Entrante PSTN
```bash
# Llama a tu línea fija conectada al Gateway
# Verifica:
docker-compose logs -f asterisk | grep "from-pstn-gateway"
```

### Test 3: Originar Llamada vía API
```bash
curl -X POST http://localhost:8000/api/calls/originate \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "5551234",
    "caller_id": "100"
  }'
```

### Test 4: Eventos ARI WebSocket
```python
import asyncio
from ari_client import ARIClient

async def test():
    client = ARIClient()
    await client.connect()

    @client.on("StasisStart")
    async def on_call(event, channel):
        print(f"📞 Llamada: {channel['caller']['number']}")

    await client.run()

asyncio.run(test())
```

---

## 🐛 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Gateway no se registra | Verifica IP, credenciales en pjsip.conf |
| ARI WebSocket no conecta | Revisa http.conf, puerto 8088 |
| FreePBX no conecta | Verifica manager.conf, puerto 5038 |
| DAHDI no detecta canales | Ejecuta `dahdi_cfg -vvv` en host |
| Llamadas no entran | Revisa extensions.conf contextos |

---

## 📚 Referencias

- [Documentación Oficial ARI](https://docs.asterisk.org/Configuration/Interfaces/Asterisk-REST-Interface-ARI/)
- [FreePBX Wiki](https://wiki.freepbx.org/)
- [DAHDI Setup](https://www.freepbx.org/sngfd12/)
- [Grandstream Gateway Config](https://www.grandstream.com/support)

---

## 🎉 Próximos Pasos Sugeridos

1. **Configurar IVR avanzado** en FreePBX
2. **Integrar dashboard React** con eventos ARI en tiempo real
3. **Implementar analytics** de llamadas
4. **Configurar colas** de agentes con estrategias avanzadas
5. **Habilitar SSL/TLS** para producción
6. **Setup de backups** automáticos
7. **Monitoreo con Grafana** (métricas de Asterisk)

---

## 🤝 Contribuciones

Este sistema está listo para producción. Personalizaciones recomendadas:

- Ajustar prompts del LLM según tu negocio
- Configurar IVR específico en FreePBX
- Añadir más extensiones/agentes según necesidad
- Integrar con CRM vía webhooks

---

**Fecha de Integración**: 2026-01-29
**Versión**: 1.0
**Estado**: ✅ Completo y listo para deployment
