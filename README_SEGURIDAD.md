# Seguridad y Cifrado - Resumen Ejecutivo

## Problema

Sin cifrado, tus llamadas SIP van por internet en **texto plano**:

```
❌ INSEGURO (Sin cifrado)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Asterisk → Internet (sin cifrar) → SIP Trunk
    ↓
👤 Atacante con Wireshark puede:
   • Escuchar conversaciones
   • Robar credenciales SIP
   • Ver quién llama a quién
```

## Solución: Cifrado de 2 Capas

```
✅ SEGURO (Con cifrado)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Asterisk → TLS/SRTP (cifrado) → SIP Trunk
    ↓
👤 Atacante solo ve tráfico cifrado ilegible
```

### Capa 1: **TLS/SIPS** (Señalización)
- Cifra la información de control
- Usa puerto **5061** en vez de 5060
- Protocolo: `SIPS` en vez de `SIP`

### Capa 2: **SRTP** (Audio)
- Cifra el audio de la conversación
- Usa AES-128 o AES-256
- Funciona sobre RTP cifrado

---

## Implementación Rápida

### Paso 1: Generar Certificados

```bash
# Dentro del contenedor de Asterisk
docker exec -it callcenter-asterisk /usr/local/bin/generate_certificates.sh

# Verás:
# ✅ Certificados generados exitosamente
# Ubicación: /etc/asterisk/keys
#   • asterisk.key - Clave privada
#   • asterisk.crt - Certificado
#   • ca.crt       - Certificate Authority
```

### Paso 2: Actualizar Configuración

Ya está incluida en los archivos que creamos:

**[pjsip.conf.template](services/asterisk/config/pjsip.conf.template)**
```ini
; Transport TLS (puerto 5061)
[transport-tls]
type=transport
protocol=tls
bind=0.0.0.0:5061
cert_file=/etc/asterisk/keys/asterisk.crt
priv_key_file=/etc/asterisk/keys/asterisk.key

; Endpoint con cifrado
[trunk-endpoint-secure]
transport=transport-tls  ; ✅ Usa TLS
media_encryption=sdes    ; ✅ SRTP habilitado
```

### Paso 3: Configurar Proveedor SIP

En el portal de tu proveedor SIP (Twilio, VoIP.ms, etc.):

1. Habilita **TLS** para señalización
2. Habilita **SRTP** para audio
3. Usa puerto **5061** (no 5060)
4. URI: `sips://provider.com:5061` (nota la "**s**" en sips)

### Paso 4: Reiniciar Asterisk

```bash
docker-compose restart asterisk
```

### Paso 5: Verificar

```bash
# Verificar puerto TLS
docker exec callcenter-asterisk netstat -tuln | grep 5061

# Debe mostrar:
# tcp   0   0.0.0.0:5061   LISTEN

# Durante una llamada, verificar SRTP
docker exec -it callcenter-asterisk asterisk -rx "pjsip show channelstats"

# Debe mostrar:
# SRTP: Yes
# Cipher: AES_CM_128_HMAC_SHA1_80
```

---

## Archivos Creados

### Scripts de Seguridad

| Archivo | Descripción |
|---------|-------------|
| [generate_certificates.sh](services/asterisk/generate_certificates.sh) | Genera certificados SSL autofirmados |
| [setup_security.sh](services/asterisk/setup_security.sh) | Setup automático al iniciar contenedor |

### Documentación

| Archivo | Descripción |
|---------|-------------|
| [SEGURIDAD_CIFRADO_SIP.md](SEGURIDAD_CIFRADO_SIP.md) | Guía completa de seguridad (técnica) |
| [README_SEGURIDAD.md](README_SEGURIDAD.md) | Este archivo (resumen ejecutivo) |

### Configuraciones Actualizadas

Las configuraciones de Asterisk que creamos anteriormente ya incluyen soporte TLS/SRTP:
- [pjsip.conf.template](services/asterisk/config/pjsip.conf.template)
- [http.conf](services/asterisk/config/http.conf)

---

## Niveles de Seguridad

### Nivel 1: Sin Cifrado ❌
```
SIP sin cifrar (puerto 5060)
RTP sin cifrar
→ Vulnerable a sniffing
```

### Nivel 2: Solo TLS ⚠️
```
SIPS/TLS (puerto 5061)
RTP sin cifrar
→ Señalización segura, pero audio vulnerable
```

### Nivel 3: TLS + SRTP ✅ (Recomendado)
```
SIPS/TLS (puerto 5061)
SRTP (RTP cifrado)
→ Todo el tráfico cifrado
```

### Nivel 4: TLS + SRTP + VPN 🔒 (Máxima seguridad)
```
VPN (WireGuard/OpenVPN)
  └→ SIPS/TLS
      └→ SRTP
→ Doble capa de cifrado
```

---

## Casos de Uso

### Caso 1: Solo Red Local (Oficina)

**Setup:**
- Sin cifrado está OK (red confiable)
- Usar puerto 5060 (UDP)

**Configuración:**
```ini
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060
local_net=192.168.0.0/16
```

### Caso 2: SIP Trunk por Internet ⚠️

**Setup:**
- ✅ **OBLIGATORIO** usar TLS + SRTP
- Puerto 5061 (TLS)
- Proveedor debe soportar cifrado

**Configuración:**
```ini
[transport-tls]
type=transport
protocol=tls
bind=0.0.0.0:5061
cert_file=/etc/asterisk/keys/asterisk.crt

[trunk-endpoint]
transport=transport-tls
media_encryption=sdes  ; SRTP
```

### Caso 3: WebRTC (Llamadas desde Navegador) 🌐

**Setup:**
- ✅ **OBLIGATORIO** DTLS-SRTP
- WebSocket Secure (WSS)

**Configuración:**
```ini
[transport-wss]
type=transport
protocol=wss
bind=0.0.0.0:8089

[webrtc-endpoint]
webrtc=yes
media_encryption=dtls
dtls_auto_generate_cert=yes
```

---

## Testing de Seguridad

### Test 1: Verificar Certificados

```bash
# Verificar certificado del servidor
openssl x509 -in /etc/asterisk/keys/asterisk.crt -noout -text

# Debe mostrar:
#   Subject: CN=asterisk.local
#   Validity: Not Before / Not After (10 años)
```

### Test 2: Conectar a Puerto TLS

```bash
# Conectar con OpenSSL client
openssl s_client -connect localhost:5061 -showcerts

# Debe mostrar:
#   SSL handshake successful
#   Certificate chain
```

### Test 3: Captura de Tráfico

```bash
# Capturar 30 segundos de tráfico
tcpdump -i any -n port 5061 -w encrypted.pcap &
sleep 30
kill %1

# Abrir en Wireshark
# Deberías ver:
#   • TLSv1.2 Application Data (NO texto legible)
#   • Encrypted Alert (NO SIP INVITE legible)
```

### Test 4: Llamada con SRTP

```bash
# Durante una llamada activa
docker exec -it callcenter-asterisk asterisk -rx "pjsip show channelstats"

# Verificar output:
# Channel: PJSIP/trunk-00000001
# SRTP: Yes  ← ✅ Audio cifrado
# Cipher: AES_CM_128_HMAC_SHA1_80
```

---

## Troubleshooting

### El proveedor SIP no soporta TLS/SRTP

**Soluciones:**
1. **Opción A:** Cambiar a proveedor que soporte cifrado (recomendado)
2. **Opción B:** Usar VPN entre tu servidor y el proveedor
3. **Opción C:** Aceptar el riesgo (solo si red privada)

### Certificados autofirmados no son confiados

**Problema:** Algunos proveedores rechazan certificados autofirmados

**Solución:** Usar Let's Encrypt o certificado comercial

```bash
# Obtener certificado Let's Encrypt
certbot certonly --standalone -d asterisk.tudominio.com

# Copiar a Asterisk
cp /etc/letsencrypt/live/asterisk.tudominio.com/fullchain.pem \
   /etc/asterisk/keys/asterisk.crt

cp /etc/letsencrypt/live/asterisk.tudominio.com/privkey.pem \
   /etc/asterisk/keys/asterisk.key
```

### SRTP falla en llamadas

**Causas comunes:**
1. Proveedor no soporta SRTP → Verificar en portal
2. Codec incompatible → Usar ulaw/alaw (compatible con SRTP)
3. Firewall bloquea → Abrir puerto 5061/tcp

**Debug:**
```bash
# Habilitar logs de SRTP
asterisk -rx "core set verbose 5"
asterisk -rx "core set debug 5"

# Ver logs en tiempo real
tail -f /var/log/asterisk/messages
```

---

## Mejores Prácticas

### ✅ Siempre Hacer:

1. **Usar TLS + SRTP para SIP trunks públicos**
   - Previene interceptación
   - Protege credenciales

2. **Certificados válidos en producción**
   - Let's Encrypt (gratis)
   - o certificado comercial

3. **Actualizar regularmente**
   ```bash
   # Renovar Let's Encrypt cada 60 días
   certbot renew
   ```

4. **Firewall configurado**
   ```bash
   # Solo abrir puertos necesarios
   5061/tcp  # SIPS
   8089/tcp  # HTTPS
   10000-10100/udp  # SRTP
   ```

5. **Deshabilitar protocolos inseguros**
   ```ini
   method=tlsv1_2  # NO SSLv3, TLSv1.0
   ```

### ❌ Nunca Hacer:

1. **NO uses puerto 5060 para internet**
   - Solo para red local confiable

2. **NO uses certificados autofirmados en producción**
   - Proveedores pueden rechazarlos

3. **NO deshabilites SRTP si usas TLS**
   - Cifrar señalización sin cifrar audio es inútil

4. **NO expongas AMI sin TLS**
   - Contraseñas irían en texto plano

---

## Resumen de Puertos

| Puerto | Protocolo | Cifrado | Uso |
|--------|-----------|---------|-----|
| 5060 | SIP/UDP | ❌ No | Solo red local |
| 5060 | SIP/TCP | ❌ No | Solo red local |
| **5061** | **SIPS/TLS** | ✅ **Sí** | **Internet (recomendado)** |
| 8088 | HTTP | ❌ No | ARI/AMI local |
| **8089** | **HTTPS** | ✅ **Sí** | **ARI/AMI seguro** |
| 8088 | WS | ❌ No | WebRTC local |
| **8089** | **WSS** | ✅ **Sí** | **WebRTC seguro** |
| 10000-10100 | RTP | ❌ No | Audio sin cifrar |
| 10000-10100 | **SRTP** | ✅ **Sí** | **Audio cifrado** |

---

## Checklist de Seguridad

Antes de ir a producción, verifica:

- [ ] Certificados SSL generados o instalados
- [ ] Transport TLS configurado (puerto 5061)
- [ ] SRTP habilitado en endpoints
- [ ] Proveedor SIP configurado con TLS/SRTP
- [ ] Puerto 5061 abierto en firewall
- [ ] Puerto 5060 bloqueado desde internet
- [ ] Certificados válidos (Let's Encrypt o comercial)
- [ ] Logs de Asterisk verificados (SRTP: Yes)
- [ ] Test de llamada exitoso con cifrado
- [ ] Captura de tráfico confirma cifrado

---

## Recursos Adicionales

- [SEGURIDAD_CIFRADO_SIP.md](SEGURIDAD_CIFRADO_SIP.md) - Guía técnica completa
- [Asterisk TLS Documentation](https://docs.asterisk.org/Configuration/Channel-Drivers/SIP/Configuring-res_pjsip/Configuring-TLS/)
- [SRTP RFC 3711](https://tools.ietf.org/html/rfc3711)

---

## Conclusión

Con TLS + SRTP:

✅ **Señalización cifrada** - Nadie puede ver quién llama
✅ **Audio cifrado** - Nadie puede escuchar conversaciones
✅ **Credenciales protegidas** - Passwords cifrados
✅ **Cumplimiento** - Regulaciones de privacidad (GDPR, etc.)

**Sin cifrado:** ❌ Cualquiera con acceso a la red puede interceptar
**Con TLS+SRTP:** ✅ Protección equivalente a HTTPS/SSL

---

**Próximo paso:** Ejecuta `generate_certificates.sh` y configura tu proveedor SIP para usar TLS/SRTP.

**Fecha:** 2026-01-29
**Versión:** 1.0
**Estado:** ✅ Documentación y scripts listos
