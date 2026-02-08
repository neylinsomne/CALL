# Guía de Configuración de Red para VoIP/SIP

## Índice

1. [Conceptos Fundamentales](#1-conceptos-fundamentales)
2. [Configuración del Router/Firewall](#2-configuración-del-routerfirewall)
3. [Configuración de Asterisk](#3-configuración-de-asterisk)
4. [Diagnóstico de Red](#4-diagnóstico-de-red)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Conceptos Fundamentales

### ¿Por qué la NAT "rompe" la voz?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EL PROBLEMA DE LA NAT                               │
└─────────────────────────────────────────────────────────────────────────────┘

    TU OFICINA                           INTERNET                    PROVEEDOR SIP
    ──────────                           ────────                    ─────────────

┌─────────────────┐                                              ┌─────────────────┐
│    Servidor     │                                              │   Proveedor     │
│   Call Center   │                                              │   SIP (Claro,   │
│                 │                                              │   Movistar...)  │
│  IP: 192.168.1.50│                                             │                 │
│  (IP PRIVADA)   │                                              │  IP: 200.x.x.x  │
└────────┬────────┘                                              └────────┬────────┘
         │                                                                │
         │ "Envíame el audio                                              │
         │  a 192.168.1.50"                                               │
         │      ❌                                                        │
         ▼                                                                │
┌─────────────────┐          ┌─────────────────┐                         │
│     Router      │          │                 │                         │
│   NAT/Firewall  │◄────────►│    INTERNET     │◄────────────────────────┘
│                 │          │                 │
│  IP Pública:    │          │                 │     ❓ "¿192.168.1.50?
│  181.x.x.x      │          │                 │        No sé dónde está"
└─────────────────┘          └─────────────────┘
```

### El Problema Explicado

1. **Tu servidor** tiene una IP Privada (ej: `192.168.1.50`) dentro de tu red local.

2. **El protocolo SIP** envía la dirección IP **dentro del cuerpo del mensaje** (no solo en los headers de red).

3. **Cuando tu servidor responde** al proveedor SIP, el mensaje dice:
   ```
   INVITE sip:proveedor@200.x.x.x
   ...
   c=IN IP4 192.168.1.50    ← ¡AQUÍ ESTÁ EL PROBLEMA!
   m=audio 10000 RTP/AVP 0
   ```

4. **El proveedor recibe** el mensaje pero la IP `192.168.1.50` es **inalcanzable desde internet**.

5. **Resultado:** La señalización funciona (el teléfono timbra) pero el audio no llega (silencio o audio unidireccional).

### La Solución: Reescritura NAT

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LA SOLUCIÓN                                         │
└─────────────────────────────────────────────────────────────────────────────┘

                    CONFIGURACIÓN CORRECTA
                    ─────────────────────

┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│    Servidor     │          │     Router      │          │   Proveedor     │
│   Asterisk      │          │   NAT/Firewall  │          │      SIP        │
│                 │          │                 │          │                 │
│ Sabe que está   │          │ Port Forwarding │          │ Recibe:         │
│ detrás de NAT   │──────────│ 5060 → Server   │──────────│ "Envíame audio  │
│                 │          │ 10000-20000     │          │  a 181.x.x.x"   │
│ externaddr=     │          │ → Server        │          │      ✅         │
│ 181.x.x.x       │          │                 │          │                 │
└─────────────────┘          └─────────────────┘          └─────────────────┘
         │                            │
         │                            │
         ▼                            ▼
    Asterisk                    El Router
    reescribe                   reenvía el
    la IP en                    tráfico al
    los mensajes                servidor
    SIP
```

---

## 2. Configuración del Router/Firewall

### 2.1 Reserva de IP (DHCP Static Lease)

**Objetivo:** Asegurar que tu servidor siempre tenga la misma IP local.

**Pasos:**
1. Obtén la **MAC Address** de tu servidor:
   ```bash
   # Linux
   ip link show | grep ether

   # Windows
   ipconfig /all | findstr "Physical"
   ```

2. Entra al panel de administración de tu router (generalmente `192.168.1.1`)

3. Busca la sección **DHCP** → **Static Lease** o **Address Reservation**

4. Asigna una IP fija a la MAC de tu servidor:
   | MAC Address | IP Asignada | Descripción |
   |-------------|-------------|-------------|
   | `AA:BB:CC:DD:EE:FF` | `192.168.1.200` | Servidor Call Center |

### 2.2 Port Forwarding (Reenvío de Puertos)

**Reglas a configurar:**

| Protocolo | Puerto Externo | Puerto Interno | IP Destino | Propósito |
|-----------|----------------|----------------|------------|-----------|
| **UDP** | 5060 | 5060 | 192.168.1.200 | Señalización SIP |
| **UDP** | 5061 | 5061 | 192.168.1.200 | SIP sobre TLS |
| **TCP** | 5060 | 5060 | 192.168.1.200 | SIP TCP (respaldo) |
| **UDP** | 10000-20000 | 10000-20000 | 192.168.1.200 | RTP (Audio) |

**Diagrama de flujo:**

```
INTERNET                          ROUTER                         LAN
─────────                         ──────                         ───

Proveedor SIP                                               Tu Servidor
200.x.x.x:5060  ──────►  181.x.x.x:5060  ──────►  192.168.1.200:5060
                         (Tu IP Pública)          (Tu IP Privada)


       Audio RTP                                            Audio RTP
200.x.x.x:xxxxx  ──────►  181.x.x.x:10000-20000  ──────►  192.168.1.200:10000-20000
```

### 2.3 Lista Blanca (Whitelist) - CRÍTICO

**¡NUNCA abras el puerto 5060 a todo internet!**

Los hackers escanean constantemente el puerto 5060 buscando servidores SIP vulnerables.

**Configuración:**

En la regla de Port Forwarding, busca:
- "Source IP" / "IP de Origen"
- "Allowed IPs" / "IPs Permitidas"
- "Access Control"

**Qué poner:**

| Proveedor | IPs a Permitir |
|-----------|----------------|
| **Twilio** | [Ver lista actualizada](https://www.twilio.com/docs/sip-trunking/ip-addresses) |
| **Vonage** | Consultar documentación del proveedor |
| **Telnyx** | `64.125.111.0/24`, `185.246.0.0/16` (verificar) |
| **Tu proveedor local** | Solicitar rangos de IP al soporte técnico |

**Ejemplo de regla de firewall (iptables):**

```bash
# Permitir solo IPs del proveedor SIP
iptables -A INPUT -p udp --dport 5060 -s 200.100.50.0/24 -j ACCEPT
iptables -A INPUT -p udp --dport 5060 -j DROP
```

### 2.4 Desactivar SIP ALG

**¿Qué es SIP ALG?**

Es una "ayuda" que algunos routers ofrecen para manejar NAT con SIP. El problema es que suele **corromper los paquetes** en lugar de ayudar.

**Síntomas de SIP ALG activo:**
- Audio unidireccional
- Llamadas que se cortan a los 30 segundos
- Registro SIP que falla intermitentemente

**Cómo desactivarlo:**

| Router | Ubicación |
|--------|-----------|
| **TP-Link** | Advanced → NAT → ALG → Desmarcar SIP |
| **Netgear** | Advanced → WAN Setup → Disable SIP ALG |
| **Linksys** | Security → Firewall → SIP ALG → Off |
| **pfSense** | System → Advanced → Firewall → Disable SIP ALG |
| **Mikrotik** | IP → Firewall → Service Ports → SIP → Disabled |

---

## 3. Configuración de Asterisk

### 3.1 Configuración PJSIP para NAT

Archivo: `pjsip.conf` o via FreePBX

```ini
; ===========================================
; TRANSPORT CON NAT
; ===========================================
[transport-udp-nat]
type=transport
protocol=udp
bind=0.0.0.0:5060

; Tu IP Pública (o dominio DDNS si es dinámica)
external_media_address=181.123.456.789
external_signaling_address=181.123.456.789

; Tu red local (para que Asterisk sepa qué NO reescribir)
local_net=192.168.1.0/24
local_net=10.0.0.0/8
local_net=172.16.0.0/12
local_net=127.0.0.1/32
```

### 3.2 Si tienes IP Pública Dinámica (DDNS)

Si tu IP pública cambia (conexión residencial típica), usa un servicio DDNS:

1. **Registra un dominio DDNS** (No-IP, DuckDNS, Dynu, etc.)
   - Ejemplo: `micallcenter.ddns.net`

2. **Instala el cliente DDNS** en tu servidor:
   ```bash
   # DuckDNS (ejemplo)
   echo url="https://www.duckdns.org/update?domains=micallcenter&token=TU_TOKEN" | curl -k -o /dev/null -K -
   ```

3. **Configura Asterisk para resolver el DDNS:**
   ```ini
   [transport-udp-nat]
   type=transport
   protocol=udp
   bind=0.0.0.0:5060

   ; Usar DDNS en lugar de IP fija
   external_media_address=micallcenter.ddns.net
   external_signaling_address=micallcenter.ddns.net

   local_net=192.168.1.0/24
   ```

### 3.3 Configuración del Endpoint con NAT

```ini
[trunk-proveedor]
type=endpoint
transport=transport-udp-nat
context=from-trunk
disallow=all
allow=ulaw
allow=alaw

; Opciones NAT críticas
direct_media=no           ; Forzar media a través de Asterisk
force_rport=yes           ; Usar puerto de respuesta real
rewrite_contact=yes       ; Reescribir el header Contact
rtp_symmetric=yes         ; Usar RTP simétrico

; Autenticación
outbound_auth=trunk-auth
aors=trunk-aor
```

### 3.4 Configuración via FreePBX

Si usas FreePBX, ve a:

**Settings → Asterisk SIP Settings → NAT Settings:**

| Campo | Valor | Descripción |
|-------|-------|-------------|
| External Address | `181.123.456.789` o `micallcenter.ddns.net` | Tu IP pública |
| Local Networks | `192.168.1.0/24` | Tu red local |
| NAT | Yes | Habilitar NAT |
| IP Configuration | Static IP o Dynamic DNS | Según tu caso |

---

## 4. Diagnóstico de Red

### 4.1 Scripts de Diagnóstico

Ejecuta los scripts incluidos en `scripts/`:

```bash
# Diagnóstico completo
./scripts/network-diagnostic.sh

# Test de latencia específico
./scripts/test-latency.sh 200.100.50.1

# Verificar puertos
./scripts/check-ports.sh
```

### 4.2 Test Manual de Latencia

```bash
# Ping básico (50 paquetes)
ping -c 50 [IP_DEL_PROVEEDOR]

# Ejemplo de resultado bueno:
# --- 200.100.50.1 ping statistics ---
# 50 packets transmitted, 50 received, 0% packet loss
# rtt min/avg/max/mdev = 15.234/18.456/25.123/2.345 ms
```

**Criterios de aceptación:**

| Métrica | Aceptable | Ideal | Crítico |
|---------|-----------|-------|---------|
| **Latencia (avg)** | < 150ms | < 50ms | > 200ms |
| **Packet Loss** | 0% | 0% | > 1% |
| **Jitter (mdev)** | < 30ms | < 10ms | > 50ms |

### 4.3 Traceroute (Verificar Ruta)

```bash
# Linux
tracepath [IP_DEL_PROVEEDOR]

# O con traceroute
traceroute -n [IP_DEL_PROVEEDOR]
```

**Interpretar resultados:**

```
 1:  192.168.1.1      0.5ms   ← Tu router
 2:  10.0.0.1         5.2ms   ← ISP local
 3:  200.50.100.1    15.3ms   ← Backbone ISP
 4:  200.100.50.1    18.7ms   ← Proveedor SIP ✅
```

- **Menos de 10 saltos:** Excelente
- **10-15 saltos:** Aceptable
- **Más de 15 saltos:** Posible latencia alta

### 4.4 Verificar Puertos Abiertos (Desde Afuera)

**Opción 1: Usar tu celular con datos móviles**
1. Desconecta el Wi-Fi del celular
2. Usa una app de escaneo de puertos (ej: "Port Scanner")
3. Escanea tu IP pública en el puerto 5060

**Opción 2: Usar un servicio web**
- https://www.yougetsignal.com/tools/open-ports/
- https://portchecker.co/

**Resultado esperado (con whitelist activa):**
- Puerto 5060: **CERRADO** o **TIMEOUT** ✅
  - Esto significa que el firewall está bloqueando IPs no autorizadas

**Si sale ABIERTO desde tu celular:**
- La whitelist NO está funcionando ⚠️
- Revisa la configuración del firewall

---

## 5. Troubleshooting

### Problema: Audio Unidireccional

**Síntoma:** Tú escuchas pero ellos no (o viceversa)

**Causas comunes:**
1. ❌ NAT mal configurado
2. ❌ Puertos RTP no reenviados
3. ❌ SIP ALG activo

**Solución:**
```bash
# Verificar configuración NAT en Asterisk
asterisk -rx "pjsip show transport transport-udp-nat"

# Verificar que external_address esté correcto
# Verificar que local_net incluya tu red
```

### Problema: Registro SIP Falla

**Síntoma:** Error 401/403/408 en los logs

**Verificar:**
```bash
# Ver estado de registros
asterisk -rx "pjsip show registrations"

# Ver logs en tiempo real
asterisk -rvvv
```

**Causas:**
- Credenciales incorrectas
- IP pública bloqueada por el proveedor
- Firewall bloqueando la respuesta

### Problema: Llamadas se Cortan a los 30 Segundos

**Síntoma:** La llamada conecta pero se corta exactamente a los 30-32 segundos

**Causa:** Session Timers mal negociados o NAT perdiendo el estado

**Solución:**
```ini
; En pjsip.conf
[trunk-proveedor]
type=endpoint
; ... otras opciones ...
timers=no                    ; Deshabilitar session timers
; O configurar un valor mayor:
timers_sess_expires=1800
```

### Problema: Eco en las Llamadas

**Causas:**
- Cancelación de eco no configurada
- Latencia muy alta
- Problemas de hardware (gateway FXO)

**Solución:**
```ini
; En chan_dahdi.conf (si usas gateway FXO)
echocancel=yes
echocancelwhenbridged=yes
echotraining=800
```

---

## Archivos de Referencia

| Archivo | Descripción |
|---------|-------------|
| [templates/pjsip-nat.conf](templates/pjsip-nat.conf) | Template configuración NAT PJSIP |
| [templates/firewall-rules.sh](templates/firewall-rules.sh) | Reglas iptables ejemplo |
| [scripts/network-diagnostic.sh](scripts/network-diagnostic.sh) | Script diagnóstico completo |
| [scripts/test-latency.sh](scripts/test-latency.sh) | Test de latencia |
| [guides/router-tp-link.md](guides/router-tp-link.md) | Guía específica TP-Link |
| [guides/router-mikrotik.md](guides/router-mikrotik.md) | Guía específica Mikrotik |
| [CHECKLIST.md](CHECKLIST.md) | Checklist de verificación |

---

## Soporte

Si tienes problemas después de seguir esta guía:

1. Ejecuta el diagnóstico: `./scripts/network-diagnostic.sh`
2. Guarda la salida en un archivo
3. Contacta soporte con los resultados

---

**Versión:** 1.0
**Última actualización:** 2026-02-08
