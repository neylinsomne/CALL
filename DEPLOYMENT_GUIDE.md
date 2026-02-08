# Guia de Despliegue - AI Call Center

## Arquitectura de Frontends

El sistema cuenta con DOS dashboards separados:

| Dashboard | Puerto | Proposito | Acceso |
|-----------|--------|-----------|--------|
| **Client Dashboard** | 3001 | Para usuarios finales (clientes) | Publico |
| **Admin Dashboard** | 3002 | Para equipo tecnico (instaladores) | Solo interno |

---

## Metodologia de Despliegue

### 1. Despliegue para Clientes (Produccion)

Para desplegar **solo el dashboard del cliente** (sin admin-dashboard ni license_server):

```bash
# Despliegue normal - NO incluye servicios internos
docker compose up -d
```

Esto levanta:
- Dashboard cliente (:3001)
- Backend API (:8000)
- PostgreSQL, MariaDB
- Asterisk + FreePBX
- Servicios de IA (TTS, STT, LLM)

**NO se levantan:**
- admin-dashboard (puerto 3002)
- license_server (puerto 8100)
- voice_distillation

### 2. Despliegue Interno (Para tu Equipo)

Para levantar **todos los servicios incluyendo admin-dashboard**:

```bash
# Incluye servicios internos (admin-dashboard, license_server)
docker compose --profile internal up -d
```

O de forma selectiva:

```bash
# Solo admin-dashboard
docker compose --profile internal up -d admin-dashboard

# Solo license-server
docker compose --profile internal up -d license_server
```

### 3. Entrenamiento de Voz

Para el pipeline de destilacion de voz:

```bash
docker compose --profile training up -d voice_distillation
```

---

## Seguridad

### Admin Dashboard

El admin-dashboard esta protegido con:

1. **Profile de Docker**: Solo se levanta con `--profile internal`
2. **API Key**: Requiere `ADMIN_API_KEY` para autenticarse
3. **Puerto separado**: No comparte puerto con el dashboard cliente

Configuracion en `.env`:

```env
# Clave para acceder al admin dashboard
# IMPORTANTE: Cambiar en produccion!
ADMIN_API_KEY=change-me-in-production

# Puerto del admin dashboard (solo para uso interno)
ADMIN_DASHBOARD_PORT=3002
```

### Client Dashboard

El dashboard del cliente usa:

1. **Tokens JWT**: Generados por organizacion
2. **Scopes**: Permisos granulares por token
3. **Rate Limiting**: En el backend

---

## Puertos

| Servicio | Puerto | Notas |
|----------|--------|-------|
| Backend API | 8000 | API principal |
| Dashboard Cliente | 3001 | Frontend para clientes |
| Admin Dashboard | 3002 | Solo con `--profile internal` |
| FreePBX | 8080/8443 | UI de gestion PBX |
| Asterisk SIP | 5060 | UDP/TCP |
| Asterisk WSS | 8089 | WebRTC |
| TTS | 8001 | Text-to-Speech |
| STT | 8002 | Speech-to-Text |
| LLM | 8003 | Modelo de lenguaje |
| PostgreSQL | 5432 | Base de datos principal |
| MariaDB | 3306 | Base de datos FreePBX |
| License Server | 8100 | Solo con `--profile internal` |

---

## Checklist de Seguridad

### Antes de desplegar a produccion:

- [ ] Cambiar `ADMIN_API_KEY` a un valor seguro
- [ ] Cambiar todas las contrasenas por defecto:
  - [ ] `POSTGRES_PASSWORD`
  - [ ] `MYSQL_ROOT_PASSWORD`
  - [ ] `FREEPBX_ADMIN_PASSWORD`
  - [ ] `ARI_PASSWORD`
  - [ ] `GATEWAY_FXO_PASSWORD`
- [ ] Configurar TLS/SRTP para comunicaciones seguras
- [ ] Verificar que `--profile internal` NO esta incluido
- [ ] Configurar firewall para solo exponer puertos necesarios

### Red

```bash
# Puertos a exponer para clientes
TCP: 443 (HTTPS), 5061 (SIP TLS), 8089 (WebRTC WSS)
UDP: 10000-20000 (RTP)

# Puertos internos (NO exponer a internet)
TCP: 5432, 3306, 8000, 8001, 8002, 8003, 3002, 8100
```

---

## Ejemplo: Preparar imagen para cliente

```bash
# 1. Generar configuracion del cliente desde admin-dashboard
#    (Esto crea el archivo .env especifico)

# 2. Copiar docker-compose.yml y .env al servidor del cliente

# 3. Desplegar SIN profiles internos
docker compose up -d

# 4. Verificar que admin-dashboard NO esta corriendo
docker ps | grep admin-dashboard
# (debe estar vacio)
```

---

## Variables de Entorno Criticas

```env
# ================================
# OBLIGATORIAS PARA PRODUCCION
# ================================
POSTGRES_PASSWORD=<password-seguro>
MYSQL_ROOT_PASSWORD=<password-seguro>
ADMIN_API_KEY=<clave-api-segura-32-chars-min>
LICENSE_KEY=<licencia-del-cliente>

# ================================
# CONFIGURACION DE RED
# ================================
EXTERNAL_IP=<ip-publica-del-servidor>
LOCAL_NETWORK=192.168.1.0/24
RTP_PORT_START=10000
RTP_PORT_END=20000

# DDNS (si IP dinamica)
DDNS_ENABLED=true
DDNS_PROVIDER=duckdns
DDNS_DOMAIN=mi-cliente.duckdns.org
DDNS_TOKEN=<token-ddns>

# ================================
# TELEFONIA
# ================================
# Opcion A: SIP Trunk
SIP_TRUNK_HOST=sip.proveedor.com
SIP_TRUNK_USER=usuario
SIP_TRUNK_PASSWORD=<password>

# Opcion B: Gateway FXO
GATEWAY_FXO_IP=192.168.1.100
GATEWAY_FXO_USER=gateway
GATEWAY_FXO_PASSWORD=<password>
```

---

## Soporte

Para agregar nuevos clientes o gestionar licencias, usa el **Admin Dashboard** en `http://localhost:3002` (solo desde la red interna de tu empresa).
