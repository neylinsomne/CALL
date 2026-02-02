# Sistema de Gestión de Licencias - Guía Completa

## Índice

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Configuración del Servidor de Licencias](#configuración-del-servidor-de-licencias)
3. [Generación de Licencias](#generación-de-licencias)
4. [Deployment a Clientes](#deployment-a-clientes)
5. [Monitoreo y Telemetría](#monitoreo-y-telemetría)
6. [Troubleshooting](#troubleshooting)

---

## Arquitectura del Sistema

### Componentes

```
┌─────────────────────────────────────────────────────────┐
│                  TU INFRAESTRUCTURA                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────┐      │
│  │ License Server (Internal)                    │      │
│  │ - Genera licencias                           │      │
│  │ - Valida requests                            │      │
│  │ - Recibe heartbeats                          │      │
│  │ - Almacena telemetría                        │      │
│  └──────────────────────────────────────────────┘      │
│                      ▲                                  │
│                      │ HTTPS                            │
└──────────────────────┼──────────────────────────────────┘
                       │
                       │ Validación
                       │ Heartbeat (cada 5 min)
                       │
┌──────────────────────┼──────────────────────────────────┐
│              CLIENTE ON-PREMISE                         │
├──────────────────────┼──────────────────────────────────┤
│                      ▼                                  │
│  ┌──────────────────────────────────────────────┐      │
│  │ License Validator                            │      │
│  │ - Valida online/offline                      │      │
│  │ - Vincula a hardware                         │      │
│  │ - Envía heartbeat                            │      │
│  │ - Reporta uso                                │      │
│  └──────────────────────────────────────────────┘      │
│                      │                                  │
│  ┌──────────────────┴───────────────────────────┐      │
│  │ Backend (Código Ofuscado con PyArmor)        │      │
│  │ - Verifica licencia al iniciar               │      │
│  │ - Limita llamadas concurrentes               │      │
│  │ - Rechaza si excede límites                  │      │
│  └──────────────────────────────────────────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Capas de Protección

1. **Licensing**: Validación online con servidor central
2. **Hardware Binding**: Vinculación a hardware específico (MAC + CPU + Motherboard)
3. **Code Obfuscation**: PyArmor protege el código Python
4. **Telemetry**: Heartbeat automático detecta uso no autorizado
5. **Call Limits**: Middleware rechaza llamadas que excedan licencia

---

## Configuración del Servidor de Licencias

### 1. Despliegue del Servidor

El servidor de licencias debe correr en **TU infraestructura**, no en la del cliente.

```bash
# En tu servidor interno
cd /opt/callcenter-license-server

# Iniciar solo el license server
docker-compose --profile internal up -d license_server
```

### 2. Configurar DNS/SSL

El servidor debe ser accesible via HTTPS:

```bash
# Ejemplo con Let's Encrypt
certbot certonly --standalone -d license.callcenter-ai.com

# Actualizar docker-compose.yml
# Agregar volúmenes para certificados SSL
volumes:
  - /etc/letsencrypt/live/license.callcenter-ai.com:/certs:ro
```

### 3. Configurar Base de Datos

Por defecto usa SQLite. Para producción, usa PostgreSQL:

```bash
# .env del license server
LICENSE_DATABASE_URL=postgresql://user:pass@db:5432/licenses
```

### 4. Verificar que funciona

```bash
# Health check
curl https://license.callcenter-ai.com/health

# Debe retornar:
# {"status": "healthy", "timestamp": "..."}
```

---

## Generación de Licencias

### Método 1: API directa (Recomendado para scripts)

```bash
# Generar licencia via API
curl -X POST https://license.callcenter-ai.com/api/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Empresa XYZ S.A.",
    "client_email": "admin@empresa-xyz.com",
    "max_concurrent_calls": 20,
    "max_agents": 50,
    "validity_days": 365,
    "is_trial": false
  }'

# Respuesta:
{
  "success": true,
  "license_key": "A1B2-C3D4-E5F6-G7H8-I9J0-K1L2-M3N4-O5P6",
  "client_name": "Empresa XYZ S.A.",
  "expires_at": "2027-01-29T00:00:00",
  "max_concurrent_calls": 20,
  "max_agents": 50,
  "is_trial": false
}
```

### Método 2: Dashboard de Admin

```bash
# Desde el backend con autenticación
curl -X POST http://localhost:8000/api/admin/licenses/generate \
  -H "X-API-Key: your-admin-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Empresa XYZ S.A.",
    "client_email": "admin@empresa-xyz.com",
    "max_concurrent_calls": 20,
    "max_agents": 50,
    "validity_days": 365,
    "is_trial": false
  }'
```

### Tipos de Licencias

#### Trial (Prueba)

```json
{
  "is_trial": true,
  "validity_days": 30,
  "max_concurrent_calls": 5,
  "max_agents": 10
}
```

#### Básica

```json
{
  "is_trial": false,
  "validity_days": 365,
  "max_concurrent_calls": 10,
  "max_agents": 20
}
```

#### Enterprise

```json
{
  "is_trial": false,
  "validity_days": 365,
  "max_concurrent_calls": 100,
  "max_agents": 500
}
```

---

## Deployment a Clientes

### 1. Build del Paquete

```bash
# Generar build para cliente
cd /opt/callcenter-ai
./scripts/build_for_client.sh "empresa-xyz"

# Esto genera:
# - build/empresa-xyz/
#   ├── docker-images/
#   │   └── callcenter-ai-1.0.0.tar.gz  (Imágenes Docker)
#   ├── obfuscated/                     (Código ofuscado)
#   ├── install.sh                      (Script de instalación)
#   ├── docker-compose.yml
#   └── README.md
```

### 2. Transferir al Cliente

```bash
# Comprimir
tar -czf empresa-xyz.tar.gz build/empresa-xyz/

# Transferir via:
# - USB/Disco externo (para máxima seguridad)
# - SFTP/SCP con cifrado
# - Portal de descarga con autenticación

scp empresa-xyz.tar.gz admin@cliente-server.com:/tmp/
```

### 3. Instalación en Cliente

El cliente ejecuta:

```bash
# Descomprimir
tar -xzf empresa-xyz.tar.gz
cd build/empresa-xyz/

# Ejecutar instalación
./install.sh

# El script pedirá:
# - LICENSE_KEY: A1B2-C3D4-E5F6-G7H8-I9J0-K1L2-M3N4-O5P6
# - LICENSE_SERVER_URL: https://license.callcenter-ai.com
```

### 4. Primera Activación

En la primera ejecución:

1. Backend obtiene Hardware ID del servidor del cliente
2. Envía `LICENSE_KEY + Hardware ID` al license server
3. License server vincula la licencia a ese hardware específico
4. Guarda en cache local (grace period de 24 horas)

```bash
# Verificar activación
docker-compose exec backend curl http://localhost:8000/license/status

# Debe mostrar:
{
  "valid": true,
  "active_calls": 0,
  "max_concurrent_calls": 20,
  "license_info": {
    "client_name": "Empresa XYZ S.A.",
    "expires_at": "2027-01-29T00:00:00",
    "days_remaining": 365
  }
}
```

---

## Monitoreo y Telemetría

### Heartbeat Automático

Cada 5 minutos, el cliente envía:

```json
{
  "license_key": "A1B2-C3D4-...",
  "active_calls": 5,
  "active_agents": 12,
  "server_ip": "192.168.1.100",
  "version": "1.0.0",
  "cpu_usage": 45,
  "memory_usage": 62,
  "disk_usage": 38
}
```

### Ver Actividad de una Licencia

```bash
# Ver información detallada
curl https://license.callcenter-ai.com/api/license/A1B2-C3D4-.../info

# Respuesta incluye:
{
  "license_key": "A1B2-C3D4-...",
  "client_name": "Empresa XYZ S.A.",
  "last_heartbeat": "2026-01-29T10:30:00",
  "total_calls": 15234,
  "total_minutes": 245678,
  "recent_heartbeats": [
    {
      "timestamp": "2026-01-29T10:30:00",
      "active_calls": 5,
      "active_agents": 12,
      "server_ip": "192.168.1.100"
    }
  ]
}
```

### Dashboard de Estadísticas

```bash
# Resumen de todas las licencias
curl -H "X-API-Key: your-admin-key" \
  http://localhost:8000/api/admin/licenses/stats/summary

# Respuesta:
{
  "total_licenses": 45,
  "active_licenses": 38,
  "expired_licenses": 3,
  "expiring_soon": 5,
  "trial_licenses": 8,
  "inactive_licenses": 4,
  "total_calls_processed": 1234567
}
```

### Detectar Uso No Autorizado

Si una licencia está activa en múltiples servidores:

1. Heartbeats muestran IPs diferentes
2. Hardware ID no coincide
3. Actividad simultánea imposible

```bash
# Buscar licencias con múltiples IPs
curl https://license.callcenter-ai.com/api/licenses/list | \
  jq '.licenses[] | select(.recent_heartbeats | map(.server_ip) | unique | length > 1)'
```

---

## Operaciones Comunes

### Extender Licencia

```bash
curl -X PUT https://license.callcenter-ai.com/api/license/A1B2-C3D4-.../extend \
  -H "X-API-Key: your-admin-key" \
  -d '{"days": 365}'
```

### Desactivar Licencia

```bash
curl -X PUT https://license.callcenter-ai.com/api/license/A1B2-C3D4-.../deactivate \
  -H "X-API-Key: your-admin-key"

# El cliente dejará de funcionar inmediatamente
```

### Listar Todas las Licencias

```bash
curl -H "X-API-Key: your-admin-key" \
  http://localhost:8000/api/admin/licenses/list?limit=100
```

---

## Troubleshooting

### Cliente: "License validation failed"

**Síntomas**: Backend no arranca, muestra error de licencia

**Causas Comunes**:
1. LICENSE_KEY incorrecto
2. Servidor de licencias no accesible
3. Licencia expirada
4. Hardware cambió (nueva instalación)

**Solución**:

```bash
# Verificar conectividad
curl -v https://license.callcenter-ai.com/health

# Ver logs del backend
docker-compose logs backend | grep -i license

# Verificar variables de entorno
docker-compose exec backend env | grep LICENSE

# Forzar revalidación
docker-compose exec backend rm -rf /var/lib/callcenter/license/*
docker-compose restart backend
```

### Cliente: "License limit exceeded"

**Síntomas**: Llamadas son rechazadas

**Causas**:
- Llamadas concurrentes exceden límite de licencia

**Solución**:

```bash
# Ver llamadas activas
curl http://localhost:8000/license/status

# Aumentar límite de la licencia
curl -X PUT https://license.callcenter-ai.com/api/license/A1B2-C3D4-.../extend \
  -H "X-API-Key: admin-key" \
  -d '{"max_concurrent_calls": 50}'
```

### Servidor: No recibe heartbeats

**Síntomas**: `last_heartbeat` es muy antiguo

**Causas**:
1. Cliente offline
2. Firewall bloqueando
3. SSL/certificado inválido

**Solución**:

```bash
# En el cliente, verificar conectividad
docker-compose exec backend curl https://license.callcenter-ai.com/api/license/heartbeat \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"license_key": "A1B2-...", "active_calls": 0}'

# Si falla, verificar firewall
# Permitir salida HTTPS (443) hacia license server
```

### Hardware cambió (reinstalación)

**Síntomas**: "Hardware not authorized"

**Causa**: Cliente reinstalado en nuevo servidor

**Solución**:

```bash
# Opción 1: Resetear hardware binding en la licencia (manual en DB)
# Opción 2: Generar nueva licencia para el nuevo hardware
# Opción 3: Transferir licencia (requiere aprobación)

# Obtener nuevo hardware ID
docker-compose exec backend python -c \
  "from license_validator import LicenseValidator; print(LicenseValidator().get_hardware_id())"

# Actualizar en servidor de licencias (manual en DB o API futura)
```

---

## Mejores Prácticas

### Seguridad

1. **Nunca compartas el ADMIN_API_KEY** con clientes
2. **Usa HTTPS** para el license server (obligatorio)
3. **Rota admin keys** regularmente
4. **Monitorea heartbeats** para detectar piratería
5. **Backup de la base de datos** de licencias diariamente

### Deployment

1. **Siempre ofusca** el código antes de enviar
2. **Verifica checksums** del paquete antes de transferir
3. **Documenta** cada licencia generada (cliente, fecha, límites)
4. **Testea** el paquete en VM antes de enviar al cliente
5. **Incluye README** con instrucciones específicas

### Soporte

1. **Grace period de 24h** permite operación offline temporal
2. **Logs detallados** para troubleshooting
3. **Endpoint de health** para monitoreo
4. **Telemetría automática** reduce llamadas de soporte

---

## Archivos de Referencia

### Servidor de Licencias
- [services/license_server/main.py](services/license_server/main.py) - Servidor FastAPI
- [services/license_server/requirements.txt](services/license_server/requirements.txt)

### Cliente
- [services/backend/license_validator.py](services/backend/license_validator.py) - Validador
- [services/backend/license_admin.py](services/backend/license_admin.py) - API admin
- [services/backend/main.py](services/backend/main.py) - Integración

### Scripts
- [scripts/build_for_client.sh](scripts/build_for_client.sh) - Build script
- [docker-compose.yml](docker-compose.yml) - Configuración Docker

### Documentación
- [PROTECCION_CODIGO_ONPREMISE.md](PROTECCION_CODIGO_ONPREMISE.md) - Arquitectura detallada
- [GUIA_SISTEMA_LICENCIAS.md](GUIA_SISTEMA_LICENCIAS.md) - Esta guía

---

## API Reference

### License Server Endpoints

| Endpoint | Método | Autenticación | Descripción |
|----------|--------|---------------|-------------|
| `/api/license/generate` | POST | Internal | Genera nueva licencia |
| `/api/license/validate` | POST | Public | Valida licencia (clientes) |
| `/api/license/heartbeat` | POST | Public | Recibe heartbeat |
| `/api/license/{key}/info` | GET | Internal | Info detallada |
| `/api/license/{key}/deactivate` | PUT | Internal | Desactiva licencia |
| `/api/license/{key}/extend` | PUT | Internal | Extiende validez |
| `/api/licenses/list` | GET | Internal | Lista todas |

### Backend Endpoints (Cliente)

| Endpoint | Método | Autenticación | Descripción |
|----------|--------|---------------|-------------|
| `/license/status` | GET | None | Estado de licencia local |
| `/api/admin/licenses/generate` | POST | API Key | Proxy a license server |
| `/api/admin/licenses/list` | GET | API Key | Proxy a license server |
| `/api/admin/licenses/{key}` | GET | API Key | Proxy a license server |

---

**Última actualización**: 2026-01-29
**Versión del sistema**: 1.0.0
**Documentación completa**: [PROTECCION_CODIGO_ONPREMISE.md](PROTECCION_CODIGO_ONPREMISE.md)
