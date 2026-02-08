# Guía de Configuración Mikrotik para VoIP

## Introducción

Mikrotik RouterOS es muy popular en entornos empresariales por su flexibilidad. Esta guía cubre la configuración completa para VoIP.

---

## 1. Acceso al Router

### Via Winbox (Recomendado)
1. Descarga Winbox: https://mikrotik.com/download
2. Ejecuta y conecta por MAC o IP
3. Usuario: `admin`, Password: (vacío o el configurado)

### Via Web
1. Navega a `http://192.168.88.1` (IP por defecto)
2. Login con credenciales

### Via SSH
```bash
ssh admin@192.168.88.1
```

---

## 2. Reserva de IP (DHCP Lease)

### Via Winbox/Web
`IP` → `DHCP Server` → `Leases`

1. Encuentra el servidor por su MAC
2. Click derecho → `Make Static`
3. O agrega manual:
   - `Add New`
   - Address: `192.168.88.200`
   - MAC Address: `AA:BB:CC:DD:EE:FF`
   - Server: `dhcp1`
   - Comment: `Servidor Call Center`

### Via Terminal
```bash
/ip dhcp-server lease add address=192.168.88.200 mac-address=AA:BB:CC:DD:EE:FF server=dhcp1 comment="Servidor Call Center"
```

---

## 3. NAT - Port Forwarding (dst-nat)

### Via Winbox/Web
`IP` → `Firewall` → `NAT`

**Regla 1: SIP UDP**
```
Chain:        dstnat
Protocol:     udp
Dst. Port:    5060
In. Interface: ether1-wan (tu interfaz WAN)
Action:       dst-nat
To Address:   192.168.88.200
To Ports:     5060
Comment:      SIP-UDP
```

**Regla 2: SIP TCP**
```
Chain:        dstnat
Protocol:     tcp
Dst. Port:    5060
Action:       dst-nat
To Address:   192.168.88.200
To Ports:     5060
Comment:      SIP-TCP
```

**Regla 3: RTP Audio**
```
Chain:        dstnat
Protocol:     udp
Dst. Port:    10000-20000
Action:       dst-nat
To Address:   192.168.88.200
To Ports:     10000-20000
Comment:      RTP-Audio
```

### Via Terminal
```bash
# SIP UDP
/ip firewall nat add chain=dstnat protocol=udp dst-port=5060 in-interface=ether1-wan action=dst-nat to-addresses=192.168.88.200 to-ports=5060 comment="SIP-UDP"

# SIP TCP
/ip firewall nat add chain=dstnat protocol=tcp dst-port=5060 in-interface=ether1-wan action=dst-nat to-addresses=192.168.88.200 to-ports=5060 comment="SIP-TCP"

# SIP TLS
/ip firewall nat add chain=dstnat protocol=tcp dst-port=5061 in-interface=ether1-wan action=dst-nat to-addresses=192.168.88.200 to-ports=5061 comment="SIP-TLS"

# RTP
/ip firewall nat add chain=dstnat protocol=udp dst-port=10000-20000 in-interface=ether1-wan action=dst-nat to-addresses=192.168.88.200 to-ports=10000-20000 comment="RTP-Audio"
```

---

## 4. Firewall - Whitelist (MUY IMPORTANTE)

### Crear Address List con IPs del Proveedor

`IP` → `Firewall` → `Address Lists`

```bash
# Via terminal - agregar IPs de tu proveedor SIP
/ip firewall address-list add list=sip-providers address=200.100.50.0/24 comment="Proveedor SIP Principal"
/ip firewall address-list add list=sip-providers address=201.200.100.0/24 comment="Proveedor SIP Backup"

# Twilio (ejemplo - verificar lista actualizada)
/ip firewall address-list add list=sip-providers address=54.172.60.0/23 comment="Twilio"
/ip firewall address-list add list=sip-providers address=34.203.250.0/23 comment="Twilio"
```

### Reglas de Firewall (Filter)

`IP` → `Firewall` → `Filter Rules`

```bash
# Permitir SIP SOLO desde proveedores en la lista
/ip firewall filter add chain=forward protocol=udp dst-port=5060 src-address-list=sip-providers action=accept comment="Allow SIP from providers" place-before=0

/ip firewall filter add chain=forward protocol=tcp dst-port=5060 src-address-list=sip-providers action=accept comment="Allow SIP TCP from providers" place-before=1

# Bloquear SIP de cualquier otra IP
/ip firewall filter add chain=forward protocol=udp dst-port=5060 action=drop log=yes log-prefix="SIP-BLOCKED:" comment="Block SIP from others"

/ip firewall filter add chain=forward protocol=tcp dst-port=5060 action=drop log=yes log-prefix="SIP-BLOCKED:" comment="Block SIP TCP from others"

# Permitir RTP solo desde proveedores
/ip firewall filter add chain=forward protocol=udp dst-port=10000-20000 src-address-list=sip-providers action=accept comment="Allow RTP from providers"
```

### Ordenar Reglas

Las reglas se procesan en orden. Asegúrate de que:
1. ACCEPT de proveedores esté ANTES
2. DROP general esté DESPUÉS

```bash
# Ver orden actual
/ip firewall filter print

# Mover regla (ejemplo: mover regla 5 a posición 0)
/ip firewall filter move 5 0
```

---

## 5. Desactivar SIP ALG

Mikrotik tiene SIP ALG en el "connection tracking helper":

`IP` → `Firewall` → `Service Ports`

### Via Winbox/Web
Encuentra "sip" y deshabilítalo (desmarca "Enabled")

### Via Terminal
```bash
# Deshabilitar SIP helper
/ip firewall service-port set sip disabled=yes

# Verificar
/ip firewall service-port print
```

---

## 6. Configuración de Connection Tracking

Para VoIP, es importante tener suficientes conexiones:

```bash
# Aumentar límites de conexiones
/ip firewall connection tracking set tcp-established-timeout=1d
/ip firewall connection tracking set udp-timeout=30s
/ip firewall connection tracking set udp-stream-timeout=3m

# Ver conexiones activas
/ip firewall connection print where protocol=udp and dst-port=5060
```

---

## 7. Queue (QoS) para Priorizar VoIP

### Marcar tráfico VoIP
```bash
# Mangle - marcar paquetes VoIP
/ip firewall mangle add chain=prerouting protocol=udp dst-port=5060 action=mark-packet new-packet-mark=voip-packets passthrough=yes comment="Mark SIP"

/ip firewall mangle add chain=prerouting protocol=udp dst-port=10000-20000 action=mark-packet new-packet-mark=voip-packets passthrough=yes comment="Mark RTP"
```

### Crear Queue con prioridad
```bash
# Simple queue con prioridad para VoIP
/queue simple add name="VoIP-Priority" target=192.168.88.200/32 packet-marks=voip-packets priority=1/1 queue=default/default max-limit=10M/10M comment="VoIP Priority Queue"
```

---

## 8. Logging y Monitoreo

### Habilitar logs de firewall
```bash
# Crear topic de logging
/system logging add topics=firewall action=memory

# Ver logs en tiempo real
/log print follow where topics~"firewall"
```

### Monitorear conexiones SIP
```bash
# Conexiones activas al puerto 5060
/ip firewall connection print where dst-port=5060

# Contador de paquetes por regla
/ip firewall filter print stats
```

---

## 9. Script de Configuración Completo

Copia y pega este script completo en la terminal de Mikrotik:

```bash
# ==========================================
# CONFIGURACIÓN VOIP COMPLETA PARA MIKROTIK
# ==========================================
# EDITAR: Cambia estas variables según tu caso
# ==========================================

:local serverIP "192.168.88.200"
:local wanInterface "ether1"
:local providerIP1 "200.100.50.0/24"
:local providerIP2 "201.200.100.0/24"

# Deshabilitar SIP ALG
/ip firewall service-port set sip disabled=yes

# Crear lista de proveedores SIP
/ip firewall address-list add list=sip-providers address=$providerIP1 comment="Proveedor SIP 1"
/ip firewall address-list add list=sip-providers address=$providerIP2 comment="Proveedor SIP 2"

# NAT - Port Forwarding
/ip firewall nat add chain=dstnat protocol=udp dst-port=5060 in-interface=$wanInterface action=dst-nat to-addresses=$serverIP to-ports=5060 comment="SIP-UDP"
/ip firewall nat add chain=dstnat protocol=tcp dst-port=5060 in-interface=$wanInterface action=dst-nat to-addresses=$serverIP to-ports=5060 comment="SIP-TCP"
/ip firewall nat add chain=dstnat protocol=tcp dst-port=5061 in-interface=$wanInterface action=dst-nat to-addresses=$serverIP to-ports=5061 comment="SIP-TLS"
/ip firewall nat add chain=dstnat protocol=udp dst-port=10000-20000 in-interface=$wanInterface action=dst-nat to-addresses=$serverIP to-ports=10000-20000 comment="RTP"

# Firewall - Whitelist
/ip firewall filter add chain=forward protocol=udp dst-port=5060 src-address-list=sip-providers action=accept comment="Allow SIP UDP from providers" place-before=0
/ip firewall filter add chain=forward protocol=tcp dst-port=5060 src-address-list=sip-providers action=accept comment="Allow SIP TCP from providers"
/ip firewall filter add chain=forward protocol=udp dst-port=10000-20000 src-address-list=sip-providers action=accept comment="Allow RTP from providers"
/ip firewall filter add chain=forward protocol=udp dst-port=5060 action=drop log=yes log-prefix="SIP-BLOCKED:" comment="Block SIP from others"
/ip firewall filter add chain=forward protocol=tcp dst-port=5060 action=drop log=yes log-prefix="SIP-BLOCKED:" comment="Block SIP from others"

:log info "VoIP configuration completed!"
```

---

## 10. Verificación

```bash
# Ver reglas NAT
/ip firewall nat print where comment~"SIP" or comment~"RTP"

# Ver reglas de filtro
/ip firewall filter print where comment~"SIP" or comment~"RTP"

# Ver address list
/ip firewall address-list print where list=sip-providers

# Verificar que SIP ALG está deshabilitado
/ip firewall service-port print where name=sip

# Test de conexión desde el servidor
# (ejecutar en el servidor, no en Mikrotik)
ping 200.100.50.1
```

---

## Troubleshooting Mikrotik

### No llegan las llamadas
```bash
# Ver si hay tráfico llegando
/tool sniffer quick port=5060

# Ver conexiones activas
/ip firewall connection print where dst-port=5060
```

### Ver intentos bloqueados
```bash
/log print where message~"SIP-BLOCKED"
```

### Exportar configuración (backup)
```bash
/export file=voip-config
```

---

## Recursos Adicionales

- [Wiki Mikrotik - VoIP](https://wiki.mikrotik.com/wiki/VoIP)
- [Foro Mikrotik](https://forum.mikrotik.com/)
