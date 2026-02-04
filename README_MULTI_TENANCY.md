# Sistema Multi-Tenancy y API de Clientes

## Resumen Ejecutivo

El sistema Call Center AI opera bajo un modelo **multi-tenant**: multiples organizaciones (empresas clientes) comparten la misma infraestructura pero con **aislamiento total de datos**. Cada cliente accede unicamente a sus agentes, llamadas y configuraciones a traves de tokens de API autenticados.

---

## Arquitectura de Acceso

```
                    NUESTRA INFRAESTRUCTURA
                    ========================

  +-----------+     +-------------------+     +------------------+
  | Dashboard |---->|   Backend API     |---->|  PostgreSQL      |
  | (React)   |     |   FastAPI         |     |  (datos locales) |
  +-----------+     +---+--------+------+     +------------------+
                        |        |
                  Admin API   Client API
                  (nosotros)  (clientes)
                        |        |
                   X-API-Key  Bearer Token
                        |        |
              +---------|--------|--------+
              |                           |
         ADMIN PANEL              CLIENTE EXTERNO
         (interno)                (su sistema)
```

### Dos niveles de acceso:

| Nivel | Autenticacion | Quien la usa | Para que |
|-------|---------------|--------------|----------|
| **Admin** | Header `X-API-Key` | Solo nosotros (internos) | Crear orgs, generar tokens, gestionar agentes |
| **Cliente** | Header `Authorization: Bearer <token>` | El cliente | Ver sus agentes, llamadas, metricas, QA |

---

## Ciclo de Vida del Cliente

### 1. Registro de la Organizacion (lo hacemos nosotros)

```bash
curl -X POST https://api.callcenter-ai.com/api/admin/orgs \
  -H "X-API-Key: ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Empresa XYZ S.A.",
    "domain": "empresa-xyz.com",
    "plan_type": "professional",
    "max_agents": 10
  }'
```

**Planes disponibles:**

| Plan | Agentes Max | Scopes por defecto |
|------|-------------|-------------------|
| `basic` | 5 | agent:read, calls:read |
| `professional` | 20 | agent:read, agent:write, calls:read, qa:read |
| `enterprise` | 500 | Todos los scopes |

### 2. Generacion del Token (lo hacemos nosotros)

```bash
curl -X POST https://api.callcenter-ai.com/api/admin/tokens \
  -H "X-API-Key: ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "uuid-de-la-org",
    "name": "Token Principal",
    "scope": "agent:read,agent:write,calls:read,qa:read,qa:write"
  }'
```

**Respuesta (unica vez que se muestra el token):**

```json
{
  "id": "token-uuid",
  "raw_token": "cc_a1b2c3d4_e5f6g7h8i9j0k1l2m3n4o5p6",
  "token_prefix": "a1b2c3d4",
  "expires_at": "2026-05-03T00:00:00",
  "scope": "agent:read,agent:write,calls:read,qa:read,qa:write"
}
```

> **IMPORTANTE**: El campo `raw_token` solo se muestra UNA vez en el momento de creacion. Debe ser entregado al cliente de forma segura.

### 3. Entrega al Cliente

Se le entrega al cliente:
- El **token de API** (formato: `cc_XXXXXXXX_YYYYYYYYYYYYYYYYYYYYYYYY`)
- La **URL base** de la API: `https://api.callcenter-ai.com/api/v1/`
- La **documentacion de endpoints** disponibles segun su plan

### 4. Renovacion (cada 90 dias)

Los tokens expiran automaticamente cada 90 dias. El cliente debe contactarnos para obtener uno nuevo.

```bash
# Nosotros rotamos el token:
curl -X POST https://api.callcenter-ai.com/api/admin/tokens/{token_id}/rotate \
  -H "X-API-Key: ADMIN_SECRET"
```

El token anterior se invalida inmediatamente. El nuevo token se entrega al cliente.

---

## Guia para el Cliente: API Reference

### Autenticacion

Todos los endpoints requieren el header:

```
Authorization: Bearer cc_XXXXXXXX_YYYYYYYYYYYYYYYYYYYYYY
```

### Endpoints Disponibles

#### Informacion de la Cuenta

```
GET /api/v1/me
```

Retorna informacion de la organizacion, plan, scopes disponibles y cantidad de agentes.

---

#### Agentes

**Listar agentes** (scope: `agent:read`)

```
GET /api/v1/agents
```

```json
[
  {
    "id": "agent-uuid",
    "name": "Agente Ventas 1",
    "status": "idle",
    "sip_port": 5070,
    "ws_port": 8070
  }
]
```

**Detalle de agente** (scope: `agent:read`)

```
GET /api/v1/agents/{agent_id}
```

Incluye configuracion de voz y contexto asignados.

**Configurar agente** (scope: `agent:write`)

```
PUT /api/v1/agents/{agent_id}/config

{
  "assigned_voice_id": "voice-uuid",
  "context_profile_id": "context-uuid",
  "config": { "custom_setting": "value" }
}
```

---

#### Historial de Llamadas

**Listar llamadas** (scope: `calls:read`)

```
GET /api/v1/calls?skip=0&limit=50&status=ended
```

**Detalle de llamada** (scope: `calls:read`)

```
GET /api/v1/calls/{conversation_id}
```

Retorna la conversacion completa con mensajes y metricas de latencia.

**Resumen de metricas** (scope: `calls:read`)

```
GET /api/v1/calls/metrics/summary?days=7
```

```json
{
  "period_days": 7,
  "total_calls": 150,
  "active_calls": 3,
  "ended_calls": 147,
  "agents_count": 5
}
```

---

#### QA (Calidad de Llamadas)

**Listar evaluaciones** (scope: `qa:read`)

```
GET /api/v1/qa/evaluations?agent_id={optional}
```

**Detalle de evaluacion** (scope: `qa:read`)

```
GET /api/v1/qa/evaluations/{evaluation_id}
```

Incluye scores individuales por criterio (saludo, resolucion, empatia, etc.).

**Criterios de evaluacion** (scope: `qa:read`)

```
GET /api/v1/qa/criteria
```

**Crear evaluacion manual** (scope: `qa:write`)

```
POST /api/v1/qa/evaluations

{
  "conversation_id": "conv-uuid",
  "scores": [
    {"criterion_id": "crit-uuid", "score": 8.5, "notes": "Buen saludo"},
    {"criterion_id": "crit-uuid", "score": 7.0, "evidence": "Resolvio el problema"}
  ],
  "notes": "Evaluacion de revision"
}
```

---

## Tabla de Scopes

| Scope | Descripcion | Endpoints |
|-------|-------------|-----------|
| `agent:read` | Ver agentes y su estado | GET /agents, GET /agents/{id} |
| `agent:write` | Configurar agentes | PUT /agents/{id}/config |
| `calls:read` | Ver historial y metricas | GET /calls, GET /calls/{id}, GET /calls/metrics |
| `qa:read` | Ver evaluaciones QA | GET /qa/evaluations, GET /qa/criteria |
| `qa:write` | Crear evaluaciones QA | POST /qa/evaluations |

---

## Seguridad del Token

### Formato del Token

```
cc_XXXXXXXX_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
 |  |         |
 |  |         +-- Secreto (32 chars) - solo almacenado como SHA-256
 |  +------------ Prefijo (8 chars) - para busqueda rapida
 +--------------- Identificador fijo "cc_"
```

### Almacenamiento

- El token completo **nunca se almacena** en la base de datos
- Se almacena un **hash SHA-256** del token completo
- El **prefijo** (8 chars) se almacena en texto plano para busqueda rapida
- La validacion: buscar por prefijo -> comparar hash

### Expiracion y Rotacion

| Parametro | Valor por defecto |
|-----------|------------------|
| Duracion del token | 90 dias |
| Verificacion de expiracion | Cada hora (automatica) |
| Rotacion | Manual, por solicitud del cliente |

**Flujo de rotacion:**
1. El token actual vence o se acerca al vencimiento
2. El cliente nos contacta
3. Nosotros ejecutamos la rotacion en el admin
4. El token anterior se invalida **inmediatamente**
5. Se genera uno nuevo con los mismos permisos
6. Se entrega el nuevo token al cliente

### Buenas Practicas para el Cliente

1. **No hardcodear** el token en el codigo fuente
2. **Usar variables de entorno** o un vault de secretos
3. **No compartir** el token entre aplicaciones diferentes
4. **Avisar inmediatamente** si sospecha que el token fue comprometido
5. **Renovar a tiempo** - contactar al menos 1 semana antes del vencimiento

---

## Clausulas de Uso de la API

### 1. Aislamiento de Datos

Cada organizacion solo tiene acceso a sus propios datos. Intentar acceder a recursos de otra organizacion resultara en error 404 (no 403) para no revelar la existencia de otros clientes.

### 2. Limites por Plan

| Limite | Basic | Professional | Enterprise |
|--------|-------|-------------|------------|
| Agentes max | 5 | 20 | 500 |
| Tokens activos | 2 | 5 | Ilimitado |
| Llamadas concurrentes | 5 | 20 | Segun licencia |
| QA evaluaciones/mes | 100 | 1,000 | Ilimitado |
| Rate limit (req/min) | 60 | 300 | 1,000 |

### 3. Responsabilidades del Token

- El token es **confidencial** y equivale a una credencial de acceso
- El cliente es responsable de la custodia del token
- Cualquier operacion realizada con el token se atribuye al cliente
- En caso de compromiso, se debe notificar inmediatamente para revocacion

### 4. Disponibilidad de la API

- SLA segun plan contratado
- Mantenimientos programados con aviso previo de 48 horas
- Los tokens expirados no se renuevan automaticamente - requiere contacto

### 5. Uso Aceptable

- La API es para integracion con los sistemas del cliente
- No se permite redistribuir acceso a terceros
- No se permite realizar scraping masivo o uso abusivo de los endpoints
- El rate limiting aplica segun el plan contratado

### 6. Desactivacion

Nos reservamos el derecho de desactivar organizaciones o tokens en caso de:
- Impago
- Violacion de terminos de uso
- Actividad sospechosa o abusiva
- Solicitud del cliente

---

## Codigos de Error

| HTTP Code | Significado | Accion del Cliente |
|-----------|-------------|-------------------|
| 401 | Token invalido, expirado o ausente | Verificar token, contactar admin |
| 403 | Permisos insuficientes (scope) | Solicitar scope adicional |
| 404 | Recurso no encontrado o de otra org | Verificar IDs |
| 409 | Conflicto (ej. dominio duplicado) | Solo admin |
| 429 | Rate limit excedido | Reducir frecuencia de requests |

---

## Archivos de Referencia

| Archivo | Descripcion |
|---------|-------------|
| [services/backend/auth.py](services/backend/auth.py) | Modulo de autenticacion y validacion de tokens |
| [services/backend/admin_api.py](services/backend/admin_api.py) | Endpoints de administracion |
| [services/backend/client_api.py](services/backend/client_api.py) | Endpoints para clientes |
| [services/backend/database/models_local.py](services/backend/database/models_local.py) | Modelos ORM (OrganizationLocal, ApiTokenLocal) |
| [services/backend/database/sql/local_schema.sql](services/backend/database/sql/local_schema.sql) | Schema SQL (organizations, api_tokens) |

---

**Ultima actualizacion**: 2026-02-02
**Estado**: Fase 1 completada y verificada
