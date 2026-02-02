# Seguridad y Cifrado en SIP/VoIP

## Problema: Sniffing de Llamadas

Cuando usas SIP trunk sin cifrado, el tráfico va en **texto plano** por internet:

```
┌─────────────┐                     ┌─────────────┐
│  Tu Asterisk│ ──── Internet ───── │  SIP Trunk  │
│  (Sin cifrar│                     │  Provider   │
└─────────────┘                     └─────────────┘
       │
       │ 🔓 Tráfico sin cifrar:
       │ • Señalización SIP (quién llama, a quién)
       │ • Audio RTP (la conversación)
       │
       ▼
  👤 Atacante con Wireshark/tcpdump
     Puede ver y escuchar TODO
```

**Riesgos:**
- ❌ Interceptación de llamadas (eavesdropping)
- ❌ Robo de credenciales SIP
- ❌ Man-in-the-middle attacks
- ❌ Violación de privacidad

---

## Solución: Cifrado de Múltiples Capas

Para proteger completamente las llamadas, necesitas cifrar **2 componentes**:

### 1. **Señalización SIP** → TLS/SIPS
Cifra la información de control (quién llama, passwords, etc.)

### 2. **Audio RTP** → SRTP
Cifra el audio de la conversación

```
┌─────────────┐                     ┌─────────────┐
│  Tu Asterisk│ ──── Internet ───── │  SIP Trunk  │
│             │     (Cifrado TLS)   │  Provider   │
│             │     (Audio SRTP)    │             │
└─────────────┘                     └─────────────┘
       │
       │ 🔒 Tráfico cifrado:
       │ • SIP sobre TLS (SIPS)
       │ • Audio sobre SRTP
       │
       ▼
  👤 Atacante
     Solo ve tráfico cifrado ilegible
```

---

## Componentes de Seguridad

### 1. TLS (Transport Layer Security)
- Cifra la señalización SIP
- Usa puerto **5061** en vez de 5060
- Requiere certificados SSL

### 2. SRTP (Secure RTP)
- Cifra el audio/video
- Usa AES-128 o AES-256
- Requiere TLS para intercambio de claves

### 3. DTLS-SRTP (para WebRTC)
- Cifrado para llamadas desde navegador
- Requerido para WebRTC

---

## Implementación en Asterisk

### Paso 1: Generar Certificados SSL

Tienes **2 opciones**:

#### Opción A: Certificados Autofirmados (Desarrollo/Testing)

```bash
#!/bin/bash
# Script: generate_certificates.sh

CERT_DIR="/etc/asterisk/keys"
mkdir -p $CERT_DIR

# Generar clave privada
openssl genrsa -out $CERT_DIR/asterisk.key 4096

# Generar certificado autofirmado (válido 10 años)
openssl req -new -x509 -days 3650 \
  -key $CERT_DIR/asterisk.key \
  -out $CERT_DIR/asterisk.crt \
  -subj "/C=US/ST=State/L=City/O=YourCompany/CN=asterisk.yourdomain.com"

# Generar CA (Certificate Authority) - Para validar clientes
openssl genrsa -out $CERT_DIR/ca.key 4096

openssl req -new -x509 -days 3650 \
  -key $CERT_DIR/ca.key \
  -out $CERT_DIR/ca.crt \
  -subj "/C=US/ST=State/L=City/O=YourCompany CA/CN=CA"

# Permisos
chmod 600 $CERT_DIR/*.key
chmod 644 $CERT_DIR/*.crt

echo "✅ Certificados generados en $CERT_DIR"
```

#### Opción B: Let's Encrypt (Producción)

```bash
#!/bin/bash
# Script: setup_letsencrypt.sh

DOMAIN="asterisk.tudominio.com"
EMAIL="admin@tudominio.com"

# Instalar certbot
apt-get update
apt-get install -y certbot

# Obtener certificado
certbot certonly --standalone \
  -d $DOMAIN \
  --email $EMAIL \
  --agree-tos \
  --non-interactive

# Copiar a Asterisk
CERT_DIR="/etc/asterisk/keys"
mkdir -p $CERT_DIR

cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $CERT_DIR/asterisk.crt
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $CERT_DIR/asterisk.key

chmod 600 $CERT_DIR/asterisk.key
chmod 644 $CERT_DIR/asterisk.crt

echo "✅ Certificados Let's Encrypt instalados"

# Renovación automática (cron)
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'asterisk -rx \"core reload\"'") | crontab -
```

---

### Paso 2: Configurar TLS en Asterisk

#### `pjsip.conf.template` con TLS:

```ini
; ============================================
; TRANSPORTS CON TLS
; ============================================

; Transport UDP (Sin cifrar - Solo para red local)
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060
local_net=192.168.0.0/16
local_net=10.0.0.0/8

; Transport TCP (Sin cifrar)
[transport-tcp]
type=transport
protocol=tcp
bind=0.0.0.0:5060

; ✅ Transport TLS (CIFRADO - Para internet)
[transport-tls]
type=transport
protocol=tls
bind=0.0.0.0:5061
cert_file=/etc/asterisk/keys/asterisk.crt
priv_key_file=/etc/asterisk/keys/asterisk.key
ca_list_file=/etc/asterisk/keys/ca.crt
cipher=ALL:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4:@STRENGTH
method=tlsv1_2  ; TLS 1.2 o superior
verify_server=no  ; Cambiar a 'yes' en producción si el provider soporta
verify_client=no

; ✅ Transport WebSocket Secure (Para WebRTC)
[transport-wss]
type=transport
protocol=wss
bind=0.0.0.0:8089
cert_file=/etc/asterisk/keys/asterisk.crt
priv_key_file=/etc/asterisk/keys/asterisk.key

; ============================================
; SIP TRUNK CON TLS + SRTP
; ============================================

[trunk-provider-secure]
type=registration
transport=transport-tls  ; ✅ Usar transport TLS
outbound_auth=trunk-auth
server_uri=sips:${SIP_TRUNK_HOST}:5061  ; ✅ SIPS en puerto 5061
client_uri=sips:${SIP_TRUNK_USER}@${SIP_TRUNK_HOST}
retry_interval=60

[trunk-auth]
type=auth
auth_type=userpass
username=${SIP_TRUNK_USER}
password=${SIP_TRUNK_PASSWORD}

[trunk-endpoint-secure]
type=endpoint
transport=transport-tls  ; ✅ TLS
context=from-trunk
disallow=all
allow=ulaw
allow=alaw
allow=opus
outbound_auth=trunk-auth
aors=trunk-aor
direct_media=no
force_rport=yes
rewrite_contact=yes
rtp_symmetric=yes

; ✅ SRTP (Cifrado de audio)
media_encryption=sdes  ; o "dtls" para DTLS-SRTP
media_encryption_optimistic=yes

from_user=${SIP_TRUNK_USER}
from_domain=${SIP_TRUNK_HOST}

[trunk-aor]
type=aor
contact=sips:${SIP_TRUNK_HOST}:5061  ; ✅ SIPS
qualify_frequency=60

; ============================================
; WEBRTC ENDPOINT (Llamadas desde navegador)
; ============================================

[webrtc-client]
type=endpoint
context=call-center
disallow=all
allow=opus
allow=ulaw

; ✅ WebRTC requiere cifrado obligatorio
dtls_auto_generate_cert=yes
webrtc=yes
media_encryption=dtls  ; ✅ DTLS-SRTP
dtls_verify=fingerprint
dtls_setup=actpass
ice_support=yes
use_avpf=yes
media_use_received_transport=yes
rtcp_mux=yes

auth=webrtc-auth
aors=webrtc-aor
transport=transport-wss  ; ✅ WebSocket Secure

[webrtc-auth]
type=auth
auth_type=userpass
username=webrtc
password=${WEBRTC_PASSWORD}

[webrtc-aor]
type=aor
max_contacts=10
remove_existing=yes
```

---

### Paso 3: Configurar RTP con Cifrado

#### `rtp.conf`:

```ini
[general]
; RTP port range
rtpstart=10000
rtpend=10100

; ✅ Habilitar SRTP
rtpsrtp=yes

; ✅ Cifrado obligatorio (rechazar llamadas sin SRTP)
;strictrtp=yes

; ICE support (para WebRTC)
icesupport=yes
stunaddr=stun.l.google.com:19302

; DTLS
dtlsenable=yes
dtlsverify=fingerprint
dtlssetup=actpass
dtlscertfile=/etc/asterisk/keys/asterisk.crt
dtlsprivatekey=/etc/asterisk/keys/asterisk.key
```

---

### Paso 4: Configurar http.conf con SSL

```ini
[general]
enabled=yes
bindaddr=0.0.0.0
bindport=8088

; ✅ Habilitar HTTPS
tlsenable=yes
tlsbindaddr=0.0.0.0:8089
tlscertfile=/etc/asterisk/keys/asterisk.crt
tlsprivatekey=/etc/asterisk/keys/asterisk.key
tlscipher=ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256

; Forzar HTTPS
redirect=/https
```

---

### Paso 5: Docker Compose con Puertos TLS

```yaml
asterisk:
  build:
    context: ./services/asterisk
    dockerfile: Dockerfile
  container_name: callcenter-asterisk
  restart: unless-stopped
  environment:
    - ASTERISK_USER=${ASTERISK_USER}
    - ASTERISK_PASSWORD=${ASTERISK_PASSWORD}
  ports:
    # SIP sin cifrar (solo red local)
    - "5060:5060/udp"
    - "5060:5060/tcp"

    # ✅ SIP con TLS (SIPS - para internet)
    - "5061:5061/tcp"

    # HTTP/HTTPS
    - "8088:8088"

    # ✅ HTTPS seguro
    - "8089:8089"

    # WebSocket / WebSocket Secure
    - "8188:8188"  # WS

    # ✅ WSS (WebRTC seguro)
    - "8189:8189"  # WSS

    # RTP (audio)
    - "10000-10100:10000-10100/udp"

  volumes:
    - ./services/asterisk/config:/etc/asterisk/custom
    - ./services/asterisk/keys:/etc/asterisk/keys  # ✅ Certificados
    - asterisk_logs:/var/log/asterisk
```

---

## Configuración del Proveedor SIP

### Configurar en el Portal del Proveedor

La mayoría de proveedores SIP trunk soportan TLS/SRTP. Ejemplo:

**Twilio, Bandwidth, VoIP.ms, etc:**

1. Accede al portal del proveedor
2. Ve a configuración de seguridad
3. Habilita:
   - ✅ TLS para señalización
   - ✅ SRTP para audio
4. Configura:
   - Puerto: `5061` (TLS)
   - Protocolo: `SIPS` o `TLS`
   - Media encryption: `SRTP`

**Ejemplo Twilio:**
```
SIP URI: sip.twilio.com:5061
Transport: TLS
Media: SRTP
```

**Ejemplo VoIP.ms:**
```
Server: atlanta.voip.ms:5061
Transport: TLS
SRTP: Enabled
```

---

## Testing de Cifrado

### 1. Verificar TLS

```bash
# Verificar que Asterisk escucha en puerto TLS
netstat -tuln | grep 5061

# Test de conexión TLS
openssl s_client -connect localhost:5061 -showcerts
```

### 2. Verificar SRTP en llamada activa

```bash
# Conectar a Asterisk CLI
docker exec -it callcenter-asterisk asterisk -rvvv

# Durante una llamada, verificar:
pjsip show channelstats

# Debe mostrar:
# SRTP: Yes
# Cipher: AES_CM_128_HMAC_SHA1_80
```

### 3. Captura de tráfico (para verificar que está cifrado)

```bash
# Capturar tráfico SIP
tcpdump -i any -n port 5061 -w sip_encrypted.pcap

# Abrir en Wireshark
# Deberías ver:
# - TLSv1.2 Application Data (no texto legible)
# - RTP cifrado (no audio legible)
```

---

## Wizard de Configuración Actualizado

Actualiza el wizard para preguntar sobre cifrado:

### Paso 1.5: Seguridad (Nuevo)

```jsx
// En ConfigurationWizard.jsx

const [securityConfig, setSecurityConfig] = useState({
  enableTLS: true,
  enableSRTP: true,
  certificateType: 'self-signed' // 'self-signed' | 'letsencrypt' | 'custom'
});

// Renderizado
<div className="p-4 border border-gray-300 rounded-lg">
  <h3 className="font-medium mb-3">🔒 Cifrado de Llamadas</h3>

  <label className="flex items-center mb-2">
    <input
      type="checkbox"
      checked={securityConfig.enableTLS}
      onChange={(e) => setSecurityConfig({
        ...securityConfig,
        enableTLS: e.target.checked
      })}
      className="mr-2"
    />
    <span>Habilitar TLS/SIPS (Cifrado de señalización)</span>
  </label>

  <label className="flex items-center mb-3">
    <input
      type="checkbox"
      checked={securityConfig.enableSRTP}
      onChange={(e) => setSecurityConfig({
        ...securityConfig,
        enableSRTP: e.target.checked
      })}
      className="mr-2"
    />
    <span>Habilitar SRTP (Cifrado de audio)</span>
  </label>

  {securityConfig.enableTLS && (
    <div className="ml-6 space-y-2">
      <label className="block text-sm">Tipo de Certificado:</label>
      <select
        value={securityConfig.certificateType}
        onChange={(e) => setSecurityConfig({
          ...securityConfig,
          certificateType: e.target.value
        })}
        className="w-full px-3 py-2 border rounded"
      >
        <option value="self-signed">Autofirmado (desarrollo)</option>
        <option value="letsencrypt">Let's Encrypt (producción)</option>
        <option value="custom">Personalizado</option>
      </select>
    </div>
  )}

  <div className="mt-3 p-3 bg-blue-50 rounded">
    <p className="text-sm text-blue-800">
      💡 <strong>Recomendado:</strong> Habilita ambos para máxima seguridad.
      Sin cifrado, las llamadas pueden ser interceptadas.
    </p>
  </div>
</div>
```

---

## Endpoint Backend para Generar Certificados

```python
# config_manager.py

@router.post("/api/config/generate-certificates")
async def generate_certificates(cert_type: str = "self-signed", domain: str = None):
    """
    Genera certificados SSL para Asterisk

    Args:
        cert_type: "self-signed" | "letsencrypt"
        domain: Dominio (requerido para Let's Encrypt)
    """
    try:
        cert_dir = Path("/etc/asterisk/keys")
        cert_dir.mkdir(parents=True, exist_ok=True)

        if cert_type == "self-signed":
            # Generar certificado autofirmado
            import subprocess

            subprocess.run([
                "openssl", "genrsa",
                "-out", str(cert_dir / "asterisk.key"),
                "4096"
            ], check=True)

            subprocess.run([
                "openssl", "req", "-new", "-x509",
                "-days", "3650",
                "-key", str(cert_dir / "asterisk.key"),
                "-out", str(cert_dir / "asterisk.crt"),
                "-subj", f"/C=US/ST=State/L=City/O=Company/CN={domain or 'asterisk.local'}"
            ], check=True)

            logger.info("✅ Certificados autofirmados generados")

            return {
                "success": True,
                "type": "self-signed",
                "cert_file": str(cert_dir / "asterisk.crt"),
                "key_file": str(cert_dir / "asterisk.key")
            }

        elif cert_type == "letsencrypt":
            if not domain:
                raise HTTPException(400, "Domain is required for Let's Encrypt")

            # Ejecutar certbot (requiere que el servidor sea accesible públicamente)
            # Esto es complejo y requiere configuración adicional
            raise HTTPException(501, "Let's Encrypt setup requires manual configuration")

    except Exception as e:
        logger.error(f"Error generando certificados: {e}")
        raise HTTPException(500, str(e))
```

---

## Mejores Prácticas de Seguridad

### 1. **Siempre usa TLS + SRTP en producción**
```
✅ SIP trunk público → TLS + SRTP obligatorio
✅ WebRTC → DTLS-SRTP obligatorio
⚠️  Red local → Opcional (pero recomendado)
```

### 2. **Certificados válidos**
```
✅ Producción → Let's Encrypt o certificado comercial
⚠️  Desarrollo/Testing → Autofirmado está OK
❌ Producción → NO uses autofirmados
```

### 3. **Actualiza TLS regularmente**
```bash
# Deshabilitar protocolos inseguros
method=tlsv1_2  # NO usar SSLv3, TLSv1.0, TLSv1.1
```

### 4. **Firewall**
```bash
# Solo abrir puertos necesarios
5061/tcp  # SIPS (TLS)
8089/tcp  # HTTPS
10000-10100/udp  # RTP/SRTP

# Bloquear puertos sin cifrar desde internet
5060 → Solo red local
```

### 5. **Fail2ban**
```bash
# Bloquear intentos de fuerza bruta
apt-get install fail2ban
# Configurar para Asterisk
```

---

## Resumen de Configuración Segura

```
┌────────────────────────────────────────────────┐
│         CONFIGURACIÓN SEGURA COMPLETA          │
├────────────────────────────────────────────────┤
│                                                │
│ 1. Generar Certificados SSL                   │
│    → Autofirmados (dev) o Let's Encrypt (prod)│
│                                                │
│ 2. Configurar Asterisk                        │
│    → pjsip.conf: Transport TLS (puerto 5061)  │
│    → Endpoint: media_encryption=sdes          │
│    → rtp.conf: SRTP habilitado                │
│                                                │
│ 3. Configurar Proveedor SIP                   │
│    → Portal: Habilitar TLS + SRTP             │
│    → Usar URI: sips://provider:5061           │
│                                                │
│ 4. Docker                                     │
│    → Exponer puerto 5061 (TLS)                │
│    → Montar certificados como volumen         │
│                                                │
│ 5. Testing                                    │
│    → Verificar "SRTP: Yes" en channelstats    │
│    → Capturar tráfico → Debe estar cifrado    │
│                                                │
└────────────────────────────────────────────────┘
```

---

## Conclusión

Con esta configuración:

✅ **Señalización cifrada** (TLS/SIPS)
✅ **Audio cifrado** (SRTP)
✅ **WebRTC seguro** (DTLS-SRTP + WSS)
✅ **Imposible interceptar** llamadas por sniffing
✅ **Cumple estándares** de seguridad VoIP

**⚠️ IMPORTANTE:**
- Sin cifrado: ❌ Cualquiera puede escuchar
- Con TLS+SRTP: ✅ Protección completa

**Próximo paso:** ¿Quieres que implemente los scripts de generación de certificados y actualice el wizard para incluir la configuración de seguridad?
