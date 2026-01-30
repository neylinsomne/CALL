# Guía de Instalación: FreePBX + ARI + Gateway/DAHDI

Esta guía te llevará paso a paso para configurar la integración completa de FreePBX, ARI mejorado, y líneas fijas (PSTN) en tu sistema de Call Center con IA.

---

## Pre-requisitos

### Software Requerido
- Docker 20.10+ con Docker Compose
- Linux host (Ubuntu 22.04 LTS recomendado)
- NVIDIA GPU con drivers y NVIDIA Container Toolkit (ya instalado)
- Git

### Hardware Recomendado (según tu caso)
- **Gateway FXO/FXS**: Grandstream GXW4104/4108, Cisco SPA112, o similar
- **Tarjeta PCIe** (opcional): Sangoma A200/A400 (analógica) o A104 (digital E1/T1)

### Red
- Puertos abiertos:
  - 5060/UDP, TCP - SIP
  - 8088 - ARI/WebSocket
  - 5038 - AMI
  - 10000-10100/UDP - RTP
  - 8080 - FreePBX Web UI
  - 3306 - MariaDB (solo interno)

---

## Paso 1: Configurar Variables de Entorno

Copia el archivo de ejemplo y edítalo:

```bash
cd /c/dev/Call
cp .env.example .env
nano .env
```

Añade/modifica las siguientes variables:

```bash
# ======================================
# ASTERISK Y TELEPHONY
# ======================================
ASTERISK_USER=agent
ASTERISK_PASSWORD=tu_password_seguro
ASTERISK_SIP_PORT=5060
ASTERISK_WS_PORT=8088

# ======================================
# ARI (Asterisk REST Interface)
# ======================================
ARI_PASSWORD=ari_password_seguro
ARI_DASHBOARD_PASSWORD=dashboard_readonly

# ======================================
# AMI (Asterisk Manager Interface)
# ======================================
FREEPBX_AMI_PASSWORD=freepbx_ami_password
BACKEND_AMI_PASSWORD=backend_ami_password

# ======================================
# FREEPBX
# ======================================
FREEPBX_ADMIN_USER=admin
FREEPBX_ADMIN_PASSWORD=freepbx_admin_password

# ======================================
# MARIADB (Para FreePBX)
# ======================================
MYSQL_ROOT_PASSWORD=mysql_root_password
MYSQL_USER=asteriskuser
MYSQL_PASSWORD=mysql_asterisk_password

# ======================================
# GATEWAY FXO/FXS
# ======================================
GATEWAY_FXO_IP=192.168.1.100
GATEWAY_FXO_USER=gateway
GATEWAY_FXO_PASSWORD=gateway_password

# ======================================
# SIP TRUNK (Ya configurado)
# ======================================
SIP_TRUNK_HOST=tu-proveedor.sip.com
SIP_TRUNK_USER=tu_usuario
SIP_TRUNK_PASSWORD=tu_password
```

**IMPORTANTE**: Reemplaza todos los passwords con valores seguros.

---

## Paso 2: Configurar Gateway FXO/FXS (Si aplica)

Si vas a usar un Gateway para conectar líneas telefónicas fijas:

### A. Configuración Física

1. Conecta las líneas telefónicas a los puertos FXO del gateway
2. Conecta el gateway a tu red LAN
3. Enciende el gateway

### B. Configuración del Gateway

Accede a la interfaz web del gateway (generalmente http://192.168.1.100):

#### Grandstream GXW4104/4108:

1. **Network Settings**:
   - IP estática: 192.168.1.100 (o la que configuraste en .env)
   - Gateway: 192.168.1.1
   - DNS: 8.8.8.8

2. **SIP Settings** (para cada puerto FXO):
   - SIP Server: IP del servidor Asterisk (ej: 192.168.1.50)
   - SIP User ID: gateway
   - Authenticate ID: gateway
   - Authenticate Password: (el de GATEWAY_FXO_PASSWORD en .env)
   - SIP Transport: UDP
   - SIP Port: 5060

3. **FXO Port Settings**:
   - Habilitar todos los puertos que tengan líneas conectadas
   - Polarity Reversal: Yes (para detección de hangup)
   - Disconnect Tone: (configurar según tu país)

4. **Codec Preferences**:
   - PCMU (ulaw) - Prioridad 1
   - PCMA (alaw) - Prioridad 2

5. **Apply** y espera a que el gateway se registre

#### Cisco SPA112:

Similar, consulta el manual específico.

### C. Verificar Registro

Desde la consola de Asterisk:

```bash
docker exec -it callcenter-asterisk asterisk -rx "pjsip show endpoints"
```

Deberías ver `gateway-fxo-1` con estado **Available**.

---

## Paso 3: Instalar Drivers DAHDI (Solo si usas tarjeta PCIe)

**NOTA**: Este paso es solo si tienes una tarjeta Digium/Sangoma instalada.

### A. En el Host Linux

```bash
# Instalar dependencias
sudo apt-get update
sudo apt-get install -y build-essential linux-headers-$(uname -r) \
    wget git patch libusb-dev libnewt-dev

# Descargar DAHDI
cd /usr/src
sudo wget https://downloads.asterisk.org/pub/telephony/dahdi-linux-complete/dahdi-linux-complete-current.tar.gz
sudo tar -xzf dahdi-linux-complete-current.tar.gz
cd dahdi-linux-complete-*

# Compilar e instalar
sudo make all
sudo make install
sudo make config

# Cargar módulos
sudo modprobe dahdi
sudo modprobe dahdi_echocan_mg2
```

### B. Configurar /etc/dahdi/system.conf

```bash
sudo nano /etc/dahdi/system.conf
```

**Ejemplo para 4 puertos FXO + 2 puertos FXS:**

```ini
# DAHDI System Configuration

# General
loadzone = us
defaultzone = us

# 4 puertos FXO (líneas externas)
# Signalling: fxsks (FXS signalling for FXO ports)
fxsks=1-4

# 2 puertos FXS (teléfonos internos)
# Signalling: fxoks (FXO signalling for FXS ports)
fxoks=5-6

# Echo cancellation
echocanceller=mg2,1-6
```

### C. Aplicar Configuración

```bash
sudo dahdi_cfg -vvv
sudo dahdi_tool  # Verificar que aparecen todos los canales
```

### D. Modificar docker-compose.yml

Descomenta las líneas de DAHDI en el servicio `asterisk`:

```yaml
asterisk:
  # ... (resto de config)
  privileged: true
  devices:
    - /dev/dahdi:/dev/dahdi
```

---

## Paso 4: Levantar los Servicios

### A. Construir e Iniciar

```bash
cd /c/dev/Call

# Detener servicios actuales si están corriendo
docker-compose down

# Construir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d
```

### B. Verificar Estado

```bash
# Ver logs
docker-compose logs -f

# Verificar que todos los servicios estén corriendo
docker-compose ps
```

Deberías ver:
- postgres (healthy)
- mariadb (healthy)
- backend (running)
- asterisk (running)
- freepbx (running)
- stt, tts, llm (running)
- dashboard (running)

---

## Paso 5: Configurar FreePBX

### A. Acceder a FreePBX Web UI

1. Abre tu navegador: http://localhost:8080 (o la IP del servidor)

2. **Primera vez**: Wizard de configuración:
   - Usuario: admin
   - Password: (el de FREEPBX_ADMIN_PASSWORD en .env)
   - Sigue el wizard de configuración inicial

### B. Configurar Conectividad con Asterisk

FreePBX debería detectar automáticamente Asterisk vía AMI.

Verifica en:
- **Admin** → **Asterisk Manager** → Debe mostrar conexión exitosa

### C. Importar Configuración Existente

FreePBX debería ver las extensiones y trunks existentes en `/etc/asterisk/custom/`.

Si no los ve:

1. **Connectivity** → **Trunks** → **Add Trunk** → **Add PJSIP Trunk**
   - Trunk Name: `SIP_TRUNK_PROVIDER`
   - Outbound CallerID: Tu número
   - **PJSIP Settings**:
     - SIP Server: ${SIP_TRUNK_HOST}
     - Username: ${SIP_TRUNK_USER}
     - Secret: ${SIP_TRUNK_PASSWORD}
   - **Apply Config**

2. **Connectivity** → **Trunks** → **Add PJSIP Trunk** para Gateway FXO
   - Trunk Name: `GATEWAY_FXO`
   - **PJSIP Settings**:
     - SIP Server: ${GATEWAY_FXO_IP}
     - Username: ${GATEWAY_FXO_USER}
     - Secret: ${GATEWAY_FXO_PASSWORD}

3. **Applications** → **Extensions**:
   - Extension 100: AI Agent
   - Extension 200: Human Queue
   - Extension 201-202: Softphones

### D. Configurar DAHDI (si aplica)

1. **Connectivity** → **DAHDI** → **Scan for DAHDI channels**

2. Debería detectar los canales configurados (1-6 en el ejemplo)

3. **Assign** cada canal:
   - Canales 1-4 (FXO) → Context: `from-pstn-dahdi`
   - Canales 5-6 (FXS) → Extensions: 301, 302

4. **Apply Config**

---

## Paso 6: Integrar ARI con el Backend

### A. Modificar main.py del Backend

Edita [services/backend/main.py](services/backend/main.py):

```python
from ari_client import ARIClient

# ... (imports existentes)

# Crear instancia global del cliente ARI
ari_client = ARIClient()

@app.on_event("startup")
async def startup_event():
    # ... (código existente)

    # Conectar ARI
    await ari_client.connect()

    # Registrar event handlers
    register_ari_handlers(ari_client)

    # Iniciar listener en background
    asyncio.create_task(ari_client.listen_events())

def register_ari_handlers(client: ARIClient):
    """Registra handlers de eventos ARI"""

    @client.on("StasisStart")
    async def on_stasis_start(event, channel):
        logger.info(f"📞 Llamada entrante: {channel['caller']['number']}")

        # Contestar
        await client.answer_channel(channel["id"])

        # Aquí se integra con el flujo actual de AudioSocket
        # El AudioSocket ya está configurado en extensions.conf
        # Solo registramos el evento en la BD

        # Crear registro en PostgreSQL
        conversation_id = channel["id"]
        caller_id = channel["caller"]["number"]

        # ... (código para crear registro en BD)

    @client.on("ChannelHangupRequest")
    async def on_hangup(event, channel):
        logger.info(f"📴 Hangup: {channel['id']}")
        # Actualizar BD, detener grabación si aplica, etc.

    @client.on("ChannelDtmfReceived")
    async def on_dtmf(event, channel):
        digit = event["digit"]
        logger.info(f"🔢 DTMF recibido: {digit}")

        # Ejemplo: 0 = transferir a humano
        if digit == "0":
            await client.transfer_to_extension(channel["id"], "200")

# Endpoint para originar llamadas desde dashboard
@app.post("/api/calls/originate")
async def originate_call(request: CallOriginateRequest):
    """Origina una llamada saliente vía ARI"""

    channel = await ari_client.originate_call(
        endpoint=f"PJSIP/{request.phone_number}@trunk-endpoint",
        caller_id=f"Call Center <{request.caller_id}>",
        variables={
            "CUSTOMER_ID": request.customer_id
        }
    )

    return {"success": True, "channel_id": channel["id"]}
```

### B. Reiniciar Backend

```bash
docker-compose restart backend
```

### C. Verificar Logs

```bash
docker-compose logs -f backend
```

Deberías ver:
```
INFO: ARI Client initialized for asterisk:8088
INFO: ARI session created
INFO: Connecting to ARI WebSocket: ws://asterisk:8088/ari/events
INFO: ARI WebSocket connected
```

---

## Paso 7: Pruebas

### Test 1: Llamada Entrante por SIP Trunk

1. Llama al número de tu SIP Trunk
2. Deberías escuchar el AI Agent
3. Verifica en FreePBX: **Reports** → **Asterisk Logfiles**
4. Verifica en Dashboard: Debe aparecer la llamada activa

### Test 2: Llamada Entrante por Gateway FXO

1. Llama a una de las líneas fijas conectadas al gateway
2. El gateway enruta la llamada a Asterisk
3. Contexto `from-pstn-gateway` → AI Agent (extensión 100)
4. Verifica en logs de Asterisk:
   ```bash
   docker exec -it callcenter-asterisk asterisk -rvvv
   ```

### Test 3: Llamada Entrante por DAHDI

1. Llama a una línea conectada a la tarjeta Digium
2. DAHDI captura la llamada
3. Contexto `from-pstn-dahdi` → AI Agent
4. Verifica en Asterisk CLI:
   ```
   dahdi show channels
   ```

### Test 4: Transferencia a Agente Humano

1. Durante una llamada con el AI, presiona `0`
2. El handler de DTMF detecta y transfiere a extensión 200
3. La llamada entra en la cola de agentes humanos

### Test 5: Llamada Saliente vía ARI

1. Desde el dashboard o vía API:
   ```bash
   curl -X POST http://localhost:8000/api/calls/originate \
     -H "Content-Type: application/json" \
     -d '{
       "phone_number": "5551234567",
       "caller_id": "100",
       "customer_id": "12345"
     }'
   ```

2. Se origina una llamada saliente
3. Cuando el cliente contesta, entra al flujo de AudioSocket con el AI

### Test 6: Grabación Selectiva

1. Durante una llamada, desde el backend:
   ```python
   recording = await ari_client.start_recording(
       channel_id="tu_channel_id",
       format="wav",
       beep=True
   )
   ```

2. La llamada se graba
3. Detener grabación:
   ```python
   await ari_client.stop_recording(recording["name"])
   ```

---

## Paso 8: Monitoreo y Troubleshooting

### Asterisk CLI

```bash
docker exec -it callcenter-asterisk asterisk -rvvv
```

Comandos útiles:
```
pjsip show endpoints      # Ver endpoints SIP registrados
pjsip show registrations  # Ver registros de trunks
dahdi show channels       # Ver canales DAHDI (si aplica)
core show channels        # Ver llamadas activas
ari show apps            # Ver aplicaciones ARI
manager show connected    # Ver conexiones AMI (FreePBX)
```

### Logs de ARI

```bash
docker-compose logs -f asterisk | grep ARI
```

### Logs del Backend

```bash
docker-compose logs -f backend
```

### FreePBX Logs

En FreePBX Web UI:
- **Reports** → **Asterisk Logfiles**
- **Reports** → **System Logs**

### Base de Datos

```bash
# PostgreSQL (call logs)
docker exec -it callcenter-db psql -U callcenter -d callcenter
SELECT * FROM conversations ORDER BY started_at DESC LIMIT 10;

# MariaDB (FreePBX config)
docker exec -it callcenter-mariadb mysql -u root -p
USE asterisk;
SHOW TABLES;
```

---

## Solución de Problemas Comunes

### Gateway no se registra

1. Verifica IP del gateway:
   ```bash
   ping 192.168.1.100
   ```

2. Verifica configuración de PJSIP:
   ```bash
   docker exec -it callcenter-asterisk asterisk -rx "pjsip show endpoint gateway-fxo-1"
   ```

3. Revisa logs del gateway

4. Verifica firewall

### DAHDI no detecta canales

1. Verifica módulos en el host:
   ```bash
   lsmod | grep dahdi
   ```

2. Reconfigura DAHDI:
   ```bash
   sudo dahdi_cfg -vvv
   ```

3. Verifica permisos de /dev/dahdi en el contenedor

### ARI WebSocket no conecta

1. Verifica que http.conf tiene websocket habilitado

2. Verifica puerto 8088:
   ```bash
   curl http://localhost:8088/ari/api-docs
   ```

3. Verifica credenciales en ari.conf

### FreePBX no conecta con Asterisk

1. Verifica AMI:
   ```bash
   telnet localhost 5038
   ```

2. Revisa manager.conf

3. Verifica que FreePBX tiene las credenciales correctas

---

## Mantenimiento

### Backups

```bash
# Backup de PostgreSQL
docker exec callcenter-db pg_dump -U callcenter callcenter > backup_$(date +%Y%m%d).sql

# Backup de MariaDB (FreePBX)
docker exec callcenter-mariadb mysqldump -u root -p asterisk > freepbx_backup_$(date +%Y%m%d).sql

# Backup de configuración
tar -czf config_backup_$(date +%Y%m%d).tar.gz services/asterisk/config/
```

### Actualizaciones

```bash
# Actualizar imágenes
docker-compose pull

# Reconstruir
docker-compose build --no-cache

# Reiniciar
docker-compose up -d
```

---

## Próximos Pasos

1. **Integrar con Dashboard React**: Añadir visualización de llamadas activas en tiempo real usando WebSocket del backend

2. **Implementar IVR avanzado**: Usar FreePBX GUI para crear menús IVR complejos

3. **Configurar colas de agentes**: Setup completo de queues con estrategias de ring, penalties, etc.

4. **Añadir reportes**: Usar FreePBX Call Detail Records para analytics avanzados

5. **Habilitar SSL**: Configurar HTTPS para FreePBX y ARI

6. **Monitoreo**: Integrar Prometheus + Grafana para métricas de Asterisk

---

## Recursos Adicionales

- [Documentación ARI](https://docs.asterisk.org/Configuration/Interfaces/Asterisk-REST-Interface-ARI/)
- [FreePBX Wiki](https://wiki.freepbx.org/)
- [Sangoma DAHDI](https://www.freepbx.org/sngfd12/)
- [Cliente ARI Python](services/backend/ari_client.py)

---

## Soporte

Si encuentras problemas:

1. Revisa los logs
2. Verifica la configuración paso a paso
3. Consulta la documentación oficial
4. Revisa [INTEGRACION_FREEPBX_ARI_GATEWAY.md](INTEGRACION_FREEPBX_ARI_GATEWAY.md) para arquitectura detallada

---

Creado: 2026-01-29
Versión: 1.0
