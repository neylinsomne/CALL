# Sistema de Licencias - Resumen Ejecutivo

## ¿Qué es esto?

Un sistema completo de **gestión de licencias** para proteger tus instalaciones on-premise de Call Center AI.

### Problema que Resuelve

Sin un sistema de licencias:
- ❌ Clientes pueden copiar la instalación a múltiples servidores
- ❌ No sabes cuántas llamadas realmente procesan
- ❌ Código Python es fácil de leer y modificar
- ❌ No hay control sobre uso después de venta

Con este sistema:
- ✅ Cada instalación requiere licencia única
- ✅ Licencia vinculada a hardware específico (no transferible)
- ✅ Telemetría automática reporta uso real
- ✅ Código ofuscado con PyArmor (difícil de reverse engineer)
- ✅ Control remoto de llamadas concurrentes

---

## Quick Start

### 1. Iniciar Servidor de Licencias (Una vez, en tu infraestructura)

```bash
# Iniciar solo el license server
docker-compose --profile internal up -d license_server

# Verificar
curl http://localhost:8100/health
```

### 2. Generar Licencia para Cliente

```bash
curl -X POST http://localhost:8100/api/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Empresa XYZ",
    "client_email": "admin@xyz.com",
    "max_concurrent_calls": 20,
    "max_agents": 50,
    "validity_days": 365
  }'

# Respuesta:
{
  "license_key": "A1B2-C3D4-E5F6-G7H8-I9J0-K1L2-M3N4-O5P6",
  "expires_at": "2027-01-29"
}
```

### 3. Build para Cliente

```bash
# Ofuscar código y empaquetar
./scripts/build_for_client.sh "empresa-xyz"

# Comprimir
tar -czf empresa-xyz.tar.gz build/empresa-xyz/

# Enviar al cliente
```

### 4. Cliente Instala

```bash
# En servidor del cliente
tar -xzf empresa-xyz.tar.gz
cd build/empresa-xyz/
./install.sh

# Cuando pida:
# LICENSE_KEY: A1B2-C3D4-E5F6-G7H8-I9J0-K1L2-M3N4-O5P6
# LICENSE_SERVER_URL: https://license.callcenter-ai.com
```

---

## Arquitectura

```
┌────────────────────────────────────────────────┐
│  TU SERVIDOR (Internal)                       │
│  ┌──────────────────────────────────────────┐ │
│  │ License Server                           │ │
│  │ - Genera licencias                       │ │
│  │ - Valida hardware binding                │ │
│  │ - Recibe telemetría                      │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
                    ▲
                    │ HTTPS (cada 5 min)
                    │
┌────────────────────────────────────────────────┐
│  CLIENTE ON-PREMISE                            │
│  ┌──────────────────────────────────────────┐ │
│  │ Backend (Código Ofuscado)                │ │
│  │ - Valida licencia al iniciar             │ │
│  │ - Limita llamadas concurrentes           │ │
│  │ - Envía heartbeat automático             │ │
│  │ - Reporta uso                            │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

---

## Capas de Protección

### 1. Licensing Online

- Validación contra servidor central
- Hardware binding (MAC + CPU + Motherboard)
- Grace period de 24h para operación offline

### 2. Code Obfuscation

```bash
# Código original (legible)
def process_call(audio):
    return ai_response

# Código ofuscado (ilegible)
__pyarmor__(__name__, __file__, b'\x50\x59\x41...')
```

### 3. Call Limits

```python
# En cada llamada
if not license_validator.can_accept_call():
    reject_call()
```

### 4. Telemetry

Cada 5 minutos envía:
- Llamadas activas
- Agentes activos
- IP del servidor
- Uso de CPU/RAM/Disco

### 5. Remote Control

Puedes desactivar licencia remotamente:

```bash
curl -X PUT https://license.callcenter-ai.com/api/license/A1B2-.../deactivate

# El cliente deja de funcionar inmediatamente
```

---

## Flujo de Validación

```
┌─────────────────────────────────────────────────────────┐
│ 1. PRIMERA INSTALACIÓN                                  │
└─────────────────────────────────────────────────────────┘

Cliente ejecuta: ./install.sh
   ↓
Pide LICENSE_KEY: A1B2-C3D4-...
   ↓
Backend inicia y:
   1. Calcula Hardware ID (MAC+CPU+Board)
   2. Envía (LICENSE_KEY + Hardware ID) al servidor
   3. Servidor vincula licencia a ese hardware
   4. Guarda en cache local (/var/lib/callcenter/license/)
   ↓
Sistema funciona ✅

┌─────────────────────────────────────────────────────────┐
│ 2. VALIDACIÓN CONTINUA                                  │
└─────────────────────────────────────────────────────────┘

Cada 1 hora:
   - Revalida online
   - Si falla: usa cache (24h grace period)

Cada 5 minutos:
   - Envía heartbeat con telemetría
   - Servidor detecta si se exceden límites

┌─────────────────────────────────────────────────────────┐
│ 3. INTENTO DE CLONAR                                    │
└─────────────────────────────────────────────────────────┘

Cliente intenta copiar a otro servidor:
   1. Nuevo servidor tiene diferente Hardware ID
   2. Validación falla: "Hardware not authorized"
   3. Sistema no arranca ❌

Tu puedes ver:
   - Múltiples IPs en heartbeats
   - Actividad simultánea imposible
   - Alert de uso no autorizado
```

---

## Archivos Creados

### Core del Sistema

| Archivo | Descripción |
|---------|-------------|
| [services/license_server/main.py](services/license_server/main.py) | Servidor de licencias FastAPI |
| [services/backend/license_validator.py](services/backend/license_validator.py) | Validador cliente |
| [services/backend/license_admin.py](services/backend/license_admin.py) | Endpoints admin |

### Scripts

| Archivo | Descripción |
|---------|-------------|
| [scripts/build_for_client.sh](scripts/build_for_client.sh) | Build y ofuscación |

### Documentación

| Archivo | Descripción |
|---------|-------------|
| [PROTECCION_CODIGO_ONPREMISE.md](PROTECCION_CODIGO_ONPREMISE.md) | Arquitectura completa |
| [GUIA_SISTEMA_LICENCIAS.md](GUIA_SISTEMA_LICENCIAS.md) | Guía operativa |
| [README_LICENCIAS.md](README_LICENCIAS.md) | Este resumen |

---

## Casos de Uso

### Generar Licencia Trial (30 días)

```bash
curl -X POST http://localhost:8100/api/license/generate \
  -d '{
    "client_name": "Demo Corp",
    "client_email": "demo@corp.com",
    "max_concurrent_calls": 5,
    "max_agents": 10,
    "validity_days": 30,
    "is_trial": true
  }'
```

### Monitorear Uso de Cliente

```bash
curl http://localhost:8100/api/license/A1B2-C3D4-.../info

# Ver:
# - Llamadas totales procesadas
# - Última conexión (heartbeat)
# - IP del servidor
# - Uso de recursos
```

### Extender Licencia

```bash
curl -X PUT http://localhost:8100/api/license/A1B2-C3D4-.../extend \
  -d '{"days": 365}'
```

### Desactivar por Falta de Pago

```bash
curl -X PUT http://localhost:8100/api/license/A1B2-C3D4-.../deactivate
```

---

## FAQ

### ¿Qué pasa si el cliente no tiene internet?

Grace period de **24 horas**. Después rechaza llamadas.

### ¿Pueden desofuscar el código?

PyArmor usa:
- Bytecode cifrado
- JIT compilation
- Anti-debug
- Binding a plataforma específica

Es **muy difícil** (no imposible, pero requiere expertise y tiempo).

### ¿Qué pasa si cambian el hardware?

La licencia deja de funcionar. Deben contactarte para:
- Resetear hardware binding (manual)
- Generar nueva licencia

### ¿Pueden modificar el código para saltarse la validación?

El código está **ofuscado** con PyArmor. Modificar es muy difícil.

Además, el heartbeat constante alertará de uso anómalo.

### ¿Cuántos clientes puedes gestionar?

El license server es ligero. Con SQLite: **cientos**.
Con PostgreSQL: **miles**.

---

## Mejores Prácticas

### DO ✅

1. **Siempre ofusca** antes de deployment
2. **Monitorea heartbeats** semanalmente
3. **Backup** de base de datos de licencias
4. **HTTPS obligatorio** para license server
5. **Documenta** cada licencia generada

### DON'T ❌

1. **NO compartas** ADMIN_API_KEY con clientes
2. **NO deploys** license server en infraestructura del cliente
3. **NO uses** HTTP sin SSL (inseguro)
4. **NO olvides** configurar firewall (solo puerto 443 salida)
5. **NO ignores** alertas de heartbeat faltante

---

## Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| "License validation failed" | Verificar LICENSE_KEY en `.env` |
| "License limit exceeded" | Aumentar `max_concurrent_calls` |
| "Hardware not authorized" | Reinstalación - resetear binding |
| No recibe heartbeats | Firewall bloquea HTTPS salida |
| Código no ofuscado | Ejecutar `build_for_client.sh` |

---

## Próximos Pasos

### Para Desplegar a Primer Cliente

1. **Configurar License Server**
   ```bash
   docker-compose --profile internal up -d license_server
   ```

2. **Generar Licencia**
   ```bash
   curl -X POST http://localhost:8100/api/license/generate \
     -d '{"client_name": "Cliente 1", ...}'
   ```

3. **Build Paquete**
   ```bash
   ./scripts/build_for_client.sh "cliente-1"
   ```

4. **Transferir y Documentar**
   - Comprimir: `tar -czf cliente-1.tar.gz build/cliente-1/`
   - Enviar vía SFTP/USB
   - Incluir LICENSE_KEY en email aparte

### Para Monitorear Clientes

```bash
# Dashboard de estadísticas
curl http://localhost:8000/api/admin/licenses/stats/summary

# Lista de licencias
curl http://localhost:8000/api/admin/licenses/list

# Detalle de una licencia
curl http://localhost:8100/api/license/A1B2-C3D4-.../info
```

---

## Soporte

**Documentación Completa**:
- [PROTECCION_CODIGO_ONPREMISE.md](PROTECCION_CODIGO_ONPREMISE.md) - Arquitectura técnica
- [GUIA_SISTEMA_LICENCIAS.md](GUIA_SISTEMA_LICENCIAS.md) - Guía operativa completa

**Archivos de Código**:
- [services/license_server/](services/license_server/) - Servidor de licencias
- [services/backend/license_validator.py](services/backend/license_validator.py) - Validador
- [scripts/build_for_client.sh](scripts/build_for_client.sh) - Build script

---

**Versión**: 1.0.0
**Última Actualización**: 2026-01-29
**Estado**: ✅ Sistema completo implementado
