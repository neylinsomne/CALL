# Fases Pendientes - AI Call Center

Estado del sistema al 2026-02-02. Schema de base de datos completo (20 tablas locales + 5 Supabase), pgvector activo, Triton para STT implementado.

---

## Fase 1: Multi-Tenancy Core (PRIORIDAD ALTA)

Sin esto no se puede comercializar. Habilita que multiples empresas usen el sistema de forma aislada.

### 1.1 Middleware de Autenticacion
- Interceptar cada request con header `Authorization: Bearer <token>`
- Validar token contra `api_tokens` (hash match, no expirado, activo)
- Inyectar `org_id` en el request context para que todos los endpoints filtren por organizacion
- Requests sin token valido reciben 401

### 1.2 Rotacion de Tokens
- Tokens expiran automaticamente cada 90 dias (`expires_at`)
- Background task (scheduler) que marca tokens expirados como `is_active=false`
- Endpoint `POST /admin/tokens/rotate` genera token nuevo e invalida el anterior
- El cliente debe contactarnos para obtener el nuevo token (control comercial)
- Historial de tokens por org para auditoria

### 1.3 API de Administracion (solo nosotros)
- CRUD organizaciones: crear cliente, activar/desactivar, cambiar plan
- CRUD tokens: generar, rotar, revocar, listar por org
- CRUD agentes: registrar, provisionar, ver estado
- Protegido con `ADMIN_API_KEY` (header separado)

### 1.4 API de Clientes (endpoints publicos con permisos)
- Cada token tiene `scope` que define que puede hacer:
  - `agent:read` - Ver estado de sus agentes
  - `agent:write` - Configurar agentes (voz, contexto, RAG)
  - `calls:read` - Ver historial y metricas de llamadas
  - `qa:read` - Ver evaluaciones QA
  - `qa:write` - Crear evaluaciones manuales
- Endpoint decorator `@require_scope("agent:read")` valida permisos
- Toda query filtra por `org_id` del token (aislamiento total)

---

## Fase 2: Monitoring y Rendimiento

### 2.1 Prometheus + Grafana
- Agregar servicio `prometheus` al docker-compose
- Exportar metricas desde cada servicio:
  - Backend: requests/s, latencia, WebSockets activos, agentes por estado
  - STT: inferencias/s, latencia, queue depth, modo Triton vs local
  - TTS: inferencias/s, latencia
  - LLM: tokens/s, latencia
- Grafana con dashboards predefinidos

### 2.2 Indicadores de Capacidad
- Endpoint `GET /admin/capacity` que retorna:
  - Agentes activos vs max permitidos
  - VRAM usada vs disponible
  - Latencia promedio por servicio (ultimos 5 min)
  - Estimacion de agentes adicionales soportados
- Basado en metricas reales de `process_metadata`

### 2.3 Health Checks Mejorados
- `GET /health/detailed` con status de cada servicio:
  - PostgreSQL: conectado, latencia
  - Supabase: conectado o modo local-only
  - STT: online, modo (triton/local), modelo cargado
  - TTS: online, device (cpu/cuda)
  - LLM: online, modelo
  - Asterisk: conectado, extensiones activas

---

## Fase 3: AI Pipeline

### 3.1 RAG Pipeline Completo
- Endpoint `POST /agents/{id}/rag/upload` para subir documentos
- Pipeline: archivo -> chunking (por parrafos/tokens) -> embedding (sentence-transformers) -> INSERT en `rag_chunks` con vector
- Busqueda: query -> embedding -> `SELECT ... ORDER BY embedding <=> query_vec LIMIT k`
- Filtrado por categoria: buscar solo en `products`, o solo en `company_history`
- Inyeccion en el prompt del LLM como contexto

### 3.2 QA Automatico
- Al terminar cada llamada, el LLM evalua la conversacion contra `qa_criteria`
- Genera `qa_evaluation` + `qa_scores` automaticamente
- Configurable por org (cuales criterios, pesos, prompts de evaluacion)
- Dashboard para ver tendencias de calidad por agente/periodo

### 3.3 Triton para TTS (opcional)
- Similar a STT: Python Backend con F5-TTS
- Solo si la carga de TTS se convierte en cuello de botella
- Con el i9-14900K en CPU probablemente no sea necesario pronto

---

## Fase 4: Deployment y Escalabilidad

### 4.1 Installer / Provisioner
- Script `scripts/provision.sh` que:
  - Detecta hardware (GPU, RAM, CPU)
  - Genera `.env` optimizado para ese hardware
  - Configura puertos para N agentes
  - Registra el servidor en Supabase (`organization_servers`)
  - Descarga modelos necesarios
  - Ejecuta `docker compose up -d`

### 4.2 Multi-Server
- Cada servidor se registra con su IP en `organization_servers`
- Load balancer (nginx/HAProxy) distribuye llamadas entre servidores
- Supabase centraliza el registro de que agente esta en que servidor
- Metricas agregadas cross-server en Grafana

### 4.3 Documentacion de API Publica
- OpenAPI/Swagger generado automaticamente por FastAPI
- Guia de integracion para clientes
- Ejemplos de uso con curl/Python
- Rate limiting por org/plan

---

## Diagrama de Dependencias

```
Fase 1 (Multi-Tenancy)
  |
  +-- Fase 2 (Monitoring) -- necesita auth para proteger endpoints admin
  |
  +-- Fase 3 (AI Pipeline) -- necesita org isolation para RAG por cliente
  |
  +-- Fase 4 (Deployment)  -- necesita todo lo anterior funcionando
```

Fase 1 es prerequisito de todo lo demas.
