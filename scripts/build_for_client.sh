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

echo -e "${GREEN}✅ Documentación generada${NC}"

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
