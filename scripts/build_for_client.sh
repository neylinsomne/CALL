#!/bin/bash
#
# Build Script para Deployment On-Premise
# ========================================
#
# Este script:
# 1. Ofusca el código Python con PyArmor
# 2. Construye imágenes Docker
# 3. Exporta las imágenes para transferir al cliente
# 4. Genera archivo de configuración de licencia
#

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuración
CLIENT_NAME="${1:-demo-client}"
OUTPUT_DIR="./build/${CLIENT_NAME}"
DOCKER_REGISTRY="callcenter-ai"
VERSION="1.0.0"

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}Build for Client: ${CLIENT_NAME}${NC}"
echo -e "${GREEN}=======================================${NC}"

# Verificar que PyArmor está instalado
if ! command -v pyarmor &> /dev/null; then
    echo -e "${RED}❌ PyArmor no está instalado${NC}"
    echo -e "${YELLOW}Instalando PyArmor...${NC}"
    pip install pyarmor
fi

# Crear directorio de salida
echo -e "\n${YELLOW}1. Creando directorio de salida...${NC}"
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}/obfuscated"
mkdir -p "${OUTPUT_DIR}/docker-images"

# Ofuscar código del backend
echo -e "\n${YELLOW}2. Ofuscando código del backend con PyArmor...${NC}"
cd services/backend

# Generar proyecto PyArmor
pyarmor gen \
    --output "../../${OUTPUT_DIR}/obfuscated/backend" \
    --platform linux.x86_64 \
    --restrict \
    --private \
    --enable-jit \
    *.py

echo -e "${GREEN}✅ Backend ofuscado${NC}"

cd ../..

# Ofuscar otros servicios críticos
echo -e "\n${YELLOW}3. Ofuscando servicios adicionales...${NC}"

# LLM service
if [ -d "services/llm" ]; then
    cd services/llm
    pyarmor gen \
        --output "../../${OUTPUT_DIR}/obfuscated/llm" \
        --platform linux.x86_64 \
        --restrict \
        *.py
    cd ../..
    echo -e "${GREEN}✅ LLM service ofuscado${NC}"
fi

# STT service
if [ -d "services/stt" ]; then
    cd services/stt
    pyarmor gen \
        --output "../../${OUTPUT_DIR}/obfuscated/stt" \
        --platform linux.x86_64 \
        --restrict \
        *.py
    cd ../..
    echo -e "${GREEN}✅ STT service ofuscado${NC}"
fi

# TTS service
if [ -d "services/tts" ]; then
    cd services/tts
    pyarmor gen \
        --output "../../${OUTPUT_DIR}/obfuscated/tts" \
        --platform linux.x86_64 \
        --restrict \
        *.py
    cd ../..
    echo -e "${GREEN}✅ TTS service ofuscado${NC}"
fi

# Copiar archivos que no se ofuscan
echo -e "\n${YELLOW}4. Copiando archivos adicionales...${NC}"

# Dockerfiles
cp -r docker "${OUTPUT_DIR}/"
cp docker-compose.yml "${OUTPUT_DIR}/"

# Configuraciones de Asterisk
cp -r services/asterisk "${OUTPUT_DIR}/"

# Frontend (Dashboard)
cp -r services/dashboard "${OUTPUT_DIR}/"

# Requirements
find services -name "requirements.txt" -exec cp {} "${OUTPUT_DIR}/" \;

echo -e "${GREEN}✅ Archivos copiados${NC}"

# Construir imágenes Docker
echo -e "\n${YELLOW}5. Construyendo imágenes Docker...${NC}"

# Build backend con código ofuscado
echo -e "   Construyendo backend..."
docker build \
    -t ${DOCKER_REGISTRY}/backend:${VERSION} \
    -f docker/Dockerfile.backend \
    --build-arg OBFUSCATED_CODE="${OUTPUT_DIR}/obfuscated/backend" \
    .

# Build otros servicios
echo -e "   Construyendo llm..."
docker build \
    -t ${DOCKER_REGISTRY}/llm:${VERSION} \
    -f docker/Dockerfile.llm \
    .

echo -e "   Construyendo stt..."
docker build \
    -t ${DOCKER_REGISTRY}/stt:${VERSION} \
    -f docker/Dockerfile.stt \
    .

echo -e "   Construyendo tts..."
docker build \
    -t ${DOCKER_REGISTRY}/tts:${VERSION} \
    -f docker/Dockerfile.tts \
    .

echo -e "   Construyendo dashboard..."
docker build \
    -t ${DOCKER_REGISTRY}/dashboard:${VERSION} \
    -f docker/Dockerfile.dashboard \
    .

echo -e "   Construyendo asterisk..."
docker build \
    -t ${DOCKER_REGISTRY}/asterisk:${VERSION} \
    -f docker/Dockerfile.asterisk \
    .

echo -e "${GREEN}✅ Imágenes construidas${NC}"

# Exportar imágenes Docker
echo -e "\n${YELLOW}6. Exportando imágenes Docker...${NC}"

docker save \
    ${DOCKER_REGISTRY}/backend:${VERSION} \
    ${DOCKER_REGISTRY}/llm:${VERSION} \
    ${DOCKER_REGISTRY}/stt:${VERSION} \
    ${DOCKER_REGISTRY}/tts:${VERSION} \
    ${DOCKER_REGISTRY}/dashboard:${VERSION} \
    ${DOCKER_REGISTRY}/asterisk:${VERSION} \
    | gzip > "${OUTPUT_DIR}/docker-images/callcenter-ai-${VERSION}.tar.gz"

echo -e "${GREEN}✅ Imágenes exportadas a ${OUTPUT_DIR}/docker-images/${NC}"

# Generar script de instalación para el cliente
echo -e "\n${YELLOW}7. Generando script de instalación...${NC}"

cat > "${OUTPUT_DIR}/install.sh" <<'INSTALL_SCRIPT'
#!/bin/bash
#
# Installation Script - Call Center AI On-Premise
# ================================================
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}Call Center AI - Installation${NC}"
echo -e "${GREEN}=======================================${NC}"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker no encontrado. Por favor instala Docker primero.${NC}"
    exit 1
fi

# Cargar imágenes
echo -e "\n${YELLOW}1. Cargando imágenes Docker...${NC}"
docker load < docker-images/callcenter-ai-*.tar.gz
echo -e "${GREEN}✅ Imágenes cargadas${NC}"

# Configurar licencia
echo -e "\n${YELLOW}2. Configuración de licencia${NC}"
read -p "Ingresa tu LICENSE_KEY: " LICENSE_KEY
read -p "Ingresa la URL del servidor de licencias [https://license.callcenter-ai.com]: " LICENSE_SERVER_URL
LICENSE_SERVER_URL=${LICENSE_SERVER_URL:-https://license.callcenter-ai.com}

# Crear archivo .env
cat > .env <<ENV
# License Configuration
LICENSE_KEY=${LICENSE_KEY}
LICENSE_SERVER_URL=${LICENSE_SERVER_URL}

# Database
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# ARI Configuration
ARI_USERNAME=callcenter-ai
ARI_PASSWORD=$(openssl rand -base64 16)

# AMI Configuration
FREEPBX_AMI_PASSWORD=$(openssl rand -base64 16)

# MariaDB for FreePBX
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32)
ENV

echo -e "${GREEN}✅ Configuración guardada en .env${NC}"

# Iniciar servicios
echo -e "\n${YELLOW}3. Iniciando servicios...${NC}"
docker-compose up -d

echo -e "\n${GREEN}=======================================${NC}"
echo -e "${GREEN}✅ Instalación completada${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo "Dashboard disponible en: http://localhost:3000"
echo "FreePBX disponible en: http://localhost:8080"
echo "API disponible en: http://localhost:8000"
echo ""
echo "Para ver los logs: docker-compose logs -f"
echo "Para detener: docker-compose stop"
echo ""
INSTALL_SCRIPT

chmod +x "${OUTPUT_DIR}/install.sh"

echo -e "${GREEN}✅ Script de instalación generado${NC}"

# Generar documentación de deployment
echo -e "\n${YELLOW}8. Generando documentación...${NC}"

cat > "${OUTPUT_DIR}/README.md" <<README
# Call Center AI - On-Premise Deployment

## Contenido del Paquete

Este paquete contiene todo lo necesario para instalar Call Center AI en tu infraestructura:

- **docker-images/**: Imágenes Docker pre-construidas
- **install.sh**: Script de instalación automática
- **docker-compose.yml**: Configuración de servicios
- **asterisk/**: Configuración de Asterisk
- **dashboard/**: Frontend web
- **API_REFERENCE.md**: Documentación de la API para integraciones
- **TERMINOS_USO_API.md**: Términos y condiciones de uso de la API

## Requisitos del Sistema

### Hardware Mínimo

- CPU: 8 cores (16 recomendado)
- RAM: 16GB (32GB recomendado para >10 llamadas concurrentes)
- Disco: 100GB SSD
- GPU: NVIDIA con 8GB VRAM (para modelos de voz)

### Software

- Ubuntu 20.04+ o Debian 11+
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit (si usas GPU)

## Instalación

### 1. Instalar Docker

\`\`\`bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker \$USER
newgrp docker
\`\`\`

### 2. Instalar NVIDIA Container Toolkit (si tienes GPU)

\`\`\`bash
distribution=\$(. /etc/os-release;echo \$ID\$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/\$distribution/nvidia-docker.list | \\
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
\`\`\`

### 3. Ejecutar Instalación

\`\`\`bash
chmod +x install.sh
./install.sh
\`\`\`

El script te pedirá:
- **LICENSE_KEY**: Tu clave de licencia (proporcionada por Call Center AI)
- **LICENSE_SERVER_URL**: URL del servidor de licencias

### 4. Verificar Instalación

\`\`\`bash
# Ver logs
docker-compose logs -f backend

# Verificar licencia
curl http://localhost:8000/license/status
\`\`\`

## Configuración

### Configurar SIP Trunk

1. Accede al dashboard: http://localhost:3000
2. Ve a "Configuración" > "Wizard"
3. Sigue el asistente de configuración

### Configurar FreePBX

1. Accede a FreePBX: http://localhost:8080
2. Usuario: admin
3. Password: (ver en \`.env\` → FREEPBX_ADMIN_PASSWORD)

## Solución de Problemas

### Verificar Estado de Licencia

\`\`\`bash
docker-compose exec backend python -c "from license_validator import get_license_validator; import asyncio; asyncio.run(get_license_validator().validate())"
\`\`\`

### Logs de Servicios

\`\`\`bash
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo asterisk
docker-compose logs -f asterisk
\`\`\`

### Reiniciar Servicios

\`\`\`bash
# Reiniciar todo
docker-compose restart

# Reiniciar solo backend
docker-compose restart backend
\`\`\`

## Soporte

Para soporte técnico, contacta a:
- Email: support@callcenter-ai.com
- Web: https://callcenter-ai.com/support

## Licencia

Este software está protegido por licencia comercial.
La redistribución no autorizada está prohibida.

**Client:** ${CLIENT_NAME}
**Version:** ${VERSION}
**Build Date:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
README

echo -e "${GREEN}✅ README generado${NC}"

# Generar documentación de API y cláusulas
echo -e "\n${YELLOW}8b. Generando documentación de API y cláusulas...${NC}"

cat > "${OUTPUT_DIR}/API_REFERENCE.md" <<'APIREF'
# Call Center AI - Referencia de API para Clientes

## Autenticación

Todos los endpoints de la API requieren un token de acceso en el header HTTP:

```
Authorization: Bearer cc_XXXXXXXX_YYYYYYYYYYYYYYYYYYYYYY
```

El token es proporcionado por Call Center AI al momento de la activación del servicio.

---

## Endpoints Disponibles

### Información de la Cuenta

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/me` | Información de su organización |

### Agentes

| Método | Endpoint | Scope requerido | Descripción |
|--------|----------|-----------------|-------------|
| GET | `/api/v1/agents` | `agent:read` | Listar sus agentes |
| GET | `/api/v1/agents/{id}` | `agent:read` | Detalle de un agente |
| PUT | `/api/v1/agents/{id}/config` | `agent:write` | Configurar agente |

### Historial de Llamadas

| Método | Endpoint | Scope requerido | Descripción |
|--------|----------|-----------------|-------------|
| GET | `/api/v1/calls` | `calls:read` | Listar llamadas |
| GET | `/api/v1/calls/{id}` | `calls:read` | Detalle con mensajes |
| GET | `/api/v1/calls/metrics/summary` | `calls:read` | Métricas agregadas |

### Calidad (QA)

| Método | Endpoint | Scope requerido | Descripción |
|--------|----------|-----------------|-------------|
| GET | `/api/v1/qa/evaluations` | `qa:read` | Listar evaluaciones |
| GET | `/api/v1/qa/evaluations/{id}` | `qa:read` | Detalle con scores |
| POST | `/api/v1/qa/evaluations` | `qa:write` | Crear evaluación manual |
| GET | `/api/v1/qa/criteria` | `qa:read` | Criterios disponibles |

---

## Códigos de Respuesta

| Código | Significado |
|--------|-------------|
| 200 | Operación exitosa |
| 401 | Token inválido, expirado o ausente |
| 403 | Permisos insuficientes para esta operación |
| 404 | Recurso no encontrado |
| 429 | Demasiadas solicitudes (rate limit) |
| 500 | Error interno del servidor |

---

## Token de API

### Formato

```
cc_XXXXXXXX_YYYYYYYYYYYYYYYYYYYYYY
```

### Vigencia

- Los tokens tienen una vigencia de **90 días**
- Al expirar, el token deja de funcionar automáticamente
- Debe contactar a Call Center AI para obtener un nuevo token
- El token anterior queda permanentemente invalidado

### Recomendaciones

1. Almacene el token en variables de entorno, nunca en código fuente
2. No comparta el token entre aplicaciones distintas
3. Notifique inmediatamente si sospecha que el token fue comprometido
4. Solicite renovación al menos 1 semana antes del vencimiento

APIREF

cat > "${OUTPUT_DIR}/TERMINOS_USO_API.md" <<'TERMS'
# Términos y Condiciones de Uso de la API

## 1. Definiciones

- **"Servicio"**: La plataforma Call Center AI y todos sus componentes
- **"Cliente"**: La organización que contrata el servicio
- **"Token de API"**: Credencial de acceso proporcionada al Cliente
- **"Datos"**: Toda información procesada a través del Servicio

## 2. Acceso y Autenticación

2.1. El acceso a la API se realiza exclusivamente mediante tokens de autenticación emitidos por Call Center AI.

2.2. Cada token está asociado a una única organización y tiene permisos (scopes) específicos según el plan contratado.

2.3. Los tokens tienen una vigencia de 90 días calendario. La renovación requiere contacto directo con Call Center AI.

2.4. El Cliente es responsable de la custodia y confidencialidad del token de API. Cualquier operación realizada con el token se atribuye al Cliente.

## 3. Aislamiento de Datos

3.1. Cada organización opera en un entorno aislado. Los datos de una organización no son accesibles por ninguna otra organización.

3.2. Las consultas a la API están automáticamente filtradas por organización. No es posible acceder a datos de otras organizaciones.

## 4. Límites del Servicio

4.1. Los límites de uso están determinados por el plan contratado:

| Recurso | Basic | Professional | Enterprise |
|---------|-------|-------------|------------|
| Agentes simultáneos | 5 | 20 | Según contrato |
| Rate limit (req/min) | 60 | 300 | 1,000 |

4.2. Exceder los límites de rate limiting resultará en respuestas HTTP 429.

4.3. Intentar registrar agentes por encima del límite del plan resultará en error HTTP 403.

## 5. Uso Aceptable

5.1. La API debe ser utilizada exclusivamente para la integración con los sistemas propios del Cliente.

5.2. Queda prohibido:
  - Redistribuir el acceso a la API a terceros
  - Realizar scraping masivo o automatizado fuera de los usos normales
  - Intentar eludir los límites de rate limiting
  - Intentar acceder a datos de otras organizaciones
  - Compartir tokens de API con terceros no autorizados

## 6. Disponibilidad

6.1. Call Center AI se compromete a mantener una disponibilidad según el SLA del plan contratado.

6.2. Los mantenimientos programados se notificarán con un mínimo de 48 horas de anticipación.

6.3. En caso de mantenimiento de emergencia, se notificará lo antes posible.

## 7. Suspensión y Terminación

7.1. Call Center AI se reserva el derecho de suspender o revocar tokens de API en los siguientes casos:
  - Impago del servicio
  - Violación de estos términos de uso
  - Actividad sospechosa o abusiva detectada
  - Solicitud expresa del Cliente

7.2. La suspensión de tokens es efectiva de forma inmediata.

7.3. Los datos del Cliente se conservarán por un período de 30 días tras la terminación del servicio.

## 8. Confidencialidad

8.1. El token de API tiene carácter confidencial. El Cliente debe tratarlo con el mismo nivel de seguridad que una contraseña.

8.2. En caso de compromiso o sospecha de compromiso del token, el Cliente debe notificar inmediatamente a Call Center AI para su revocación.

## 9. Limitación de Responsabilidad

9.1. Call Center AI no se responsabiliza por el uso indebido del token de API por parte del Cliente o terceros que hayan obtenido acceso al mismo.

9.2. El Cliente es responsable de implementar las medidas de seguridad adecuadas en sus sistemas para proteger el token.

## 10. Modificaciones

10.1. Call Center AI puede modificar estos términos con previo aviso de 30 días.

10.2. Los cambios en los endpoints de la API se comunicarán con un mínimo de 15 días de anticipación.

---

**Versión**: 1.0
**Fecha de emisión**: $(date -u +"%Y-%m-%d")
**Válido para el contrato de**: ${CLIENT_NAME}
TERMS

echo -e "${GREEN}✅ Documentación de API y cláusulas generadas${NC}"

# Crear checksum
echo -e "\n${YELLOW}9. Generando checksums...${NC}"
cd "${OUTPUT_DIR}"
find . -type f -exec sha256sum {} \; > checksums.txt
cd ..

echo -e "${GREEN}✅ Checksums generados${NC}"

# Resumen final
echo -e "\n${GREEN}=======================================${NC}"
echo -e "${GREEN}✅ Build Completado${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo -e "Cliente: ${YELLOW}${CLIENT_NAME}${NC}"
echo -e "Directorio: ${YELLOW}${OUTPUT_DIR}${NC}"
echo -e "Tamaño: ${YELLOW}$(du -sh ${OUTPUT_DIR} | cut -f1)${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "1. Comprimir el directorio para envío:"
echo "   tar -czf ${CLIENT_NAME}.tar.gz ${OUTPUT_DIR}"
echo ""
echo "2. Transferir al cliente via:"
echo "   - USB/Disco externo"
echo "   - SFTP/SCP seguro"
echo "   - Portal de descarga protegido"
echo ""
echo "3. El cliente debe ejecutar:"
echo "   tar -xzf ${CLIENT_NAME}.tar.gz"
echo "   cd ${OUTPUT_DIR}"
echo "   ./install.sh"
echo ""
