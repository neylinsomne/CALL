# Guía Genérica de Configuración de Router

## Introducción

Esta guía aplica a la mayoría de routers domésticos y empresariales. Los pasos son similares aunque los menús pueden variar.

---

## 1. Acceder al Panel de Administración

**Pasos típicos:**

1. Conecta tu computador al router (WiFi o cable)
2. Abre un navegador web
3. Ingresa la IP del router:
   - Generalmente: `192.168.1.1` o `192.168.0.1`
   - Algunos: `10.0.0.1` o `192.168.100.1`

4. Ingresa credenciales:
   - Usuario: `admin`
   - Password: `admin`, `password`, o el que esté en la etiqueta del router

**Encontrar la IP del router (gateway):**

```bash
# Windows
ipconfig | findstr "Gateway"

# Linux/Mac
ip route | grep default
# o
netstat -rn | grep default
```

---

## 2. Reserva de IP (DHCP Static Lease)

**Ubicación típica:**
`LAN Settings` → `DHCP` → `Address Reservation` / `Static Lease`

**Datos necesarios:**

| Campo | Valor | Cómo obtenerlo |
|-------|-------|----------------|
| MAC Address | `AA:BB:CC:DD:EE:FF` | `ip link show` o `ipconfig /all` |
| IP a asignar | `192.168.1.200` | Elige una fuera del rango DHCP |
| Descripción | `Servidor Call Center` | Opcional |

**Configuración:**

1. Encuentra la sección DHCP
2. Busca "Address Reservation" o "Static Lease"
3. Agrega nueva entrada:
   ```
   MAC: AA:BB:CC:DD:EE:FF
   IP:  192.168.1.200
   Name: callcenter-server
   ```
4. Guarda y reinicia el servidor para que tome la nueva IP

---

## 3. Port Forwarding (Reenvío de Puertos)

**Ubicación típica:**
`NAT` → `Port Forwarding` / `Virtual Servers` / `Applications`

**Reglas a crear:**

### Regla 1: SIP UDP
```
Nombre:          SIP-UDP
Protocolo:       UDP
Puerto Externo:  5060
Puerto Interno:  5060
IP Destino:      192.168.1.200
Habilitado:      Sí
```

### Regla 2: SIP TCP
```
Nombre:          SIP-TCP
Protocolo:       TCP
Puerto Externo:  5060
Puerto Interno:  5060
IP Destino:      192.168.1.200
Habilitado:      Sí
```

### Regla 3: SIP TLS
```
Nombre:          SIP-TLS
Protocolo:       TCP
Puerto Externo:  5061
Puerto Interno:  5061
IP Destino:      192.168.1.200
Habilitado:      Sí
```

### Regla 4: RTP (Audio)
```
Nombre:          RTP-Audio
Protocolo:       UDP
Puerto Externo:  10000-20000 (o como rango)
Puerto Interno:  10000-20000
IP Destino:      192.168.1.200
Habilitado:      Sí
```

**Nota sobre rangos:**
- Algunos routers no soportan rangos, deberás crear reglas individuales
- Alternativa: Usar "DMZ" (menos seguro, no recomendado)

---

## 4. Whitelist (Lista Blanca de IPs)

**Ubicación típica:**
`Firewall` → `Access Control` / `IP Filter` / `Security`

Esta es la configuración MÁS IMPORTANTE para seguridad.

**Objetivo:** Solo permitir tráfico SIP desde las IPs de tu proveedor.

**Cómo hacerlo:**

### Opción A: En la regla de Port Forwarding
Algunos routers permiten especificar "Source IP" en cada regla:
```
Regla: SIP-UDP
  Puerto: 5060
  Destino: 192.168.1.200
  Source IP: 200.100.50.0/24  ← Solo este rango puede conectar
```

### Opción B: Reglas de Firewall separadas
1. Crear regla ALLOW:
   ```
   Acción:     ALLOW
   Protocolo:  UDP
   Puerto:     5060
   Source:     200.100.50.0/24 (IP de tu proveedor)
   Destino:    192.168.1.200
   ```

2. Crear regla DENY (después del ALLOW):
   ```
   Acción:     DENY
   Protocolo:  UDP
   Puerto:     5060
   Source:     Any/0.0.0.0
   Destino:    192.168.1.200
   ```

**IPs de proveedores comunes:**

| Proveedor | IPs/Rangos |
|-----------|------------|
| Twilio | [Ver documentación](https://www.twilio.com/docs/sip-trunking/ip-addresses) |
| Telnyx | Consultar dashboard |
| Vonage | Consultar documentación |
| Local | Solicitar al proveedor |

---

## 5. Desactivar SIP ALG

**Ubicación típica:**
`Advanced` → `NAT` → `ALG` / `Application Layer Gateway`

O buscar en:
`Firewall` → `SIP ALG`

**Acción:**
Desmarcar/Deshabilitar "SIP ALG" o "SIP Passthrough"

**Por qué:**
SIP ALG intenta "ayudar" modificando los paquetes SIP, pero casi siempre causa problemas:
- Audio unidireccional
- Llamadas que se cortan
- Registros que fallan

---

## 6. Configuración de DNS

**Ubicación típica:**
`Network` → `WAN` → `DNS`

**Recomendación:**
Usar DNS públicos rápidos:
```
DNS Primario:    1.1.1.1 (Cloudflare)
DNS Secundario:  8.8.8.8 (Google)
```

O:
```
DNS Primario:    8.8.8.8 (Google)
DNS Secundario:  8.8.4.4 (Google)
```

---

## 7. QoS (Quality of Service) - Opcional

**Ubicación típica:**
`Advanced` → `QoS` / `Traffic Control` / `Bandwidth Control`

Si tu conexión es compartida con otras actividades, prioriza el tráfico VoIP:

```
Regla: Prioridad VoIP
  Protocolo: UDP
  Puerto: 5060, 10000-20000
  Prioridad: Alta / Real-time
```

---

## 8. Guardar y Reiniciar

**Importante:**
1. Guarda todos los cambios
2. Reinicia el router
3. Reinicia el servidor (para tomar la nueva IP)
4. Verifica con los scripts de diagnóstico

---

## Troubleshooting

### No puedo acceder al router
- Verifica la IP del gateway
- Prueba con otro navegador
- Intenta en modo incógnito
- Resetea el router si olvidaste la contraseña

### El port forwarding no funciona
- Verifica que el servidor tenga la IP correcta
- Verifica que el servicio esté escuchando en el puerto
- Algunos ISPs bloquean ciertos puertos (contactar ISP)
- Prueba cambiando a un puerto no estándar

### No encuentro la opción de whitelist
- Busca en "Firewall" → "Access Rules"
- Busca en "Security" → "IP Filter"
- Algunos routers no lo soportan (usar firewall en el servidor)

### Tengo doble NAT
Si tu módem del ISP también hace NAT:
1. Opción A: Poner módem en modo "Bridge"
2. Opción B: Configurar port forwarding en AMBOS dispositivos
3. Opción C: Solicitar IP pública directa al ISP

---

## Verificación Final

Ejecuta desde el servidor:
```bash
# Verificar IP pública
curl https://api.ipify.org

# Verificar que el puerto está escuchando
ss -uln | grep 5060

# Test de conectividad
./scripts/network-diagnostic.sh [IP_PROVEEDOR]
```

Ejecuta desde internet (celular con datos):
```
Escanear IP_PUBLICA:5060
- Si tienes whitelist: Debe aparecer CERRADO ✓
- Si no tienes whitelist: Aparecerá ABIERTO (¡configurar!)
```
