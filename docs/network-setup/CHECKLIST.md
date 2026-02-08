# Checklist de Configuración de Red para VoIP

## Instrucciones
Marca cada item conforme lo completes. Todos los items deben estar marcados antes de poner en producción.

---

## 1. Información Preliminar

### Datos del Servidor
- [ ] IP Local del servidor definida: `________________`
- [ ] MAC Address del servidor: `________________`
- [ ] Sistema operativo: `________________`

### Datos de Red
- [ ] IP del Router/Gateway: `________________`
- [ ] Rango de red local: `________________` (ej: 192.168.1.0/24)
- [ ] IP Pública: `________________`
- [ ] ¿IP Pública es estática? [ ] Sí [ ] No → Si No, configurar DDNS

### Datos del Proveedor SIP
- [ ] Nombre del proveedor: `________________`
- [ ] Host SIP: `________________`
- [ ] Usuario SIP: `________________`
- [ ] Password SIP: (guardado de forma segura)
- [ ] DID/Número telefónico: `________________`
- [ ] IPs del proveedor para whitelist:
  - [ ] `________________`
  - [ ] `________________`
  - [ ] `________________`

---

## 2. Configuración del Router

### 2.1 DHCP Static Lease
- [ ] MAC del servidor identificada
- [ ] IP estática asignada en DHCP
- [ ] Servidor reiniciado con nueva IP
- [ ] Ping exitoso a nueva IP desde otro dispositivo

### 2.2 Port Forwarding
- [ ] Regla SIP UDP 5060 creada
- [ ] Regla SIP TCP 5060 creada
- [ ] Regla SIP TLS 5061 creada (si aplica)
- [ ] Regla RTP 10000-20000 UDP creada
- [ ] Todas las reglas apuntan a IP correcta del servidor

### 2.3 Whitelist/Firewall
- [ ] IPs del proveedor SIP identificadas
- [ ] Reglas de whitelist configuradas
- [ ] Regla de bloqueo para IPs no autorizadas
- [ ] Logging activado para intentos bloqueados

### 2.4 SIP ALG
- [ ] SIP ALG encontrado en configuración del router
- [ ] SIP ALG **DESACTIVADO**
- [ ] Router reiniciado después del cambio

### 2.5 Verificación del Router
- [ ] Configuración guardada
- [ ] Router reiniciado
- [ ] Verificado que la configuración persiste tras reinicio

---

## 3. Configuración de Asterisk/PJSIP

### 3.1 NAT Settings
- [ ] `external_media_address` configurado con IP pública o DDNS
- [ ] `external_signaling_address` configurado
- [ ] `local_net` incluye la red local
- [ ] `local_net` incluye 127.0.0.1/32

### 3.2 Endpoint Settings
- [ ] `direct_media=no` configurado
- [ ] `force_rport=yes` configurado
- [ ] `rewrite_contact=yes` configurado
- [ ] `rtp_symmetric=yes` configurado

### 3.3 Trunk Registration
- [ ] Credenciales del trunk configuradas
- [ ] Registro exitoso (verificar con `pjsip show registrations`)
- [ ] Estado: "Registered"

### 3.4 Test de Llamada
- [ ] Llamada entrante funciona
- [ ] Llamada saliente funciona
- [ ] Audio bidireccional confirmado
- [ ] No hay eco excesivo
- [ ] Llamada no se corta a los 30 segundos

---

## 4. Diagnóstico de Red

### 4.1 Latencia
- [ ] Script de diagnóstico ejecutado: `./scripts/network-diagnostic.sh`
- [ ] Latencia promedio < 150ms: ____ms
- [ ] Packet loss = 0%: ____%
- [ ] Jitter < 30ms: ____ms

### 4.2 Traceroute
- [ ] Traceroute al proveedor ejecutado
- [ ] Número de saltos < 15: ____ saltos
- [ ] Sin timeouts intermedios

### 4.3 Puertos
- [ ] Puerto 5060 escuchando localmente (verificado con `ss -uln`)
- [ ] Puerto 5060 accesible desde proveedor SIP
- [ ] Puerto 5060 **NO** accesible desde IPs no autorizadas
- [ ] Rango RTP (10000-20000) disponible

---

## 5. Seguridad

### 5.1 Firewall del Servidor (iptables/ufw)
- [ ] Reglas de firewall del servidor configuradas
- [ ] Solo IPs del proveedor pueden acceder a SIP
- [ ] SSH restringido a red local o VPN
- [ ] Logging de intentos bloqueados activado

### 5.2 Credenciales
- [ ] Contraseñas seguras (mínimo 16 caracteres)
- [ ] Contraseñas diferentes para cada servicio
- [ ] Credenciales NO almacenadas en código (usar variables de entorno)
- [ ] Archivo .env con permisos restrictivos (600)

### 5.3 Actualizaciones
- [ ] Sistema operativo actualizado
- [ ] Asterisk/FreePBX actualizado
- [ ] Reglas de firewall revisadas

---

## 6. Monitoreo

### 6.1 Logs
- [ ] Logs de Asterisk accesibles
- [ ] Logs de firewall accesibles
- [ ] Alertas configuradas para fallos de registro SIP

### 6.2 Backups
- [ ] Backup de configuración del router
- [ ] Backup de configuración de Asterisk
- [ ] Backup de configuración de firewall

---

## 7. Documentación

- [ ] IP del servidor documentada
- [ ] Credenciales guardadas en gestor de contraseñas
- [ ] IPs del proveedor documentadas
- [ ] Diagrama de red actualizado
- [ ] Contacto de soporte del proveedor SIP guardado

---

## 8. Prueba Final

### Test de Carga
- [ ] 1 llamada simultánea: ✓ Funciona
- [ ] 5 llamadas simultáneas: ✓ Funciona
- [ ] Máximo esperado de llamadas: ____ llamadas testeadas

### Test de Failover (si aplica)
- [ ] Corte de internet simulado
- [ ] Reconexión automática verificada
- [ ] Tiempo de reconexión: ____ segundos

---

## Firma de Verificación

| Campo | Valor |
|-------|-------|
| Fecha de configuración | ________________ |
| Configurado por | ________________ |
| Verificado por | ________________ |
| Versión de este checklist | 1.0 |

---

## Notas Adicionales

```
Espacio para notas sobre la configuración específica de este deployment:

_____________________________________________________________

_____________________________________________________________

_____________________________________________________________

_____________________________________________________________

_____________________________________________________________
```

---

## En Caso de Problemas

1. Ejecutar diagnóstico: `./scripts/network-diagnostic.sh`
2. Verificar logs: `docker-compose logs -f asterisk`
3. Revisar esta checklist
4. Contactar soporte con los resultados del diagnóstico
