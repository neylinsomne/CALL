#!/bin/bash
#
# Script para Generar Certificados SSL para Asterisk
# =====================================================
#
# Genera certificados autofirmados para TLS/SRTP
# Válido para 10 años
#

set -e  # Exit on error

# Configuración
CERT_DIR="/etc/asterisk/keys"
COUNTRY="US"
STATE="State"
CITY="City"
ORGANIZATION="Call Center AI"
COMMON_NAME="${ASTERISK_DOMAIN:-asterisk.local}"
DAYS_VALID=3650  # 10 años

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}Generador de Certificados SSL${NC}"
echo -e "${GREEN}=======================================${NC}"

# Crear directorio si no existe
echo -e "\n${YELLOW}1. Creando directorio de certificados...${NC}"
mkdir -p "$CERT_DIR"

# Generar clave privada del servidor
echo -e "\n${YELLOW}2. Generando clave privada (4096 bits)...${NC}"
openssl genrsa -out "$CERT_DIR/asterisk.key" 4096

# Generar certificado autofirmado
echo -e "\n${YELLOW}3. Generando certificado autofirmado...${NC}"
openssl req -new -x509 -days $DAYS_VALID \
  -key "$CERT_DIR/asterisk.key" \
  -out "$CERT_DIR/asterisk.crt" \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORGANIZATION/CN=$COMMON_NAME"

# Generar CA (Certificate Authority)
echo -e "\n${YELLOW}4. Generando Certificate Authority...${NC}"
openssl genrsa -out "$CERT_DIR/ca.key" 4096

openssl req -new -x509 -days $DAYS_VALID \
  -key "$CERT_DIR/ca.key" \
  -out "$CERT_DIR/ca.crt" \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORGANIZATION CA/CN=CA-$COMMON_NAME"

# Configurar permisos
echo -e "\n${YELLOW}5. Configurando permisos...${NC}"
chmod 600 "$CERT_DIR"/*.key
chmod 644 "$CERT_DIR"/*.crt
chown -R asterisk:asterisk "$CERT_DIR" 2>/dev/null || true

# Verificar certificados
echo -e "\n${YELLOW}6. Verificando certificados...${NC}"
openssl x509 -in "$CERT_DIR/asterisk.crt" -noout -text | grep -E "(Subject:|Issuer:|Not Before|Not After)"

# Resumen
echo -e "\n${GREEN}✅ Certificados generados exitosamente${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo "Ubicación: $CERT_DIR"
echo ""
echo "Archivos generados:"
echo "  • asterisk.key - Clave privada del servidor"
echo "  • asterisk.crt - Certificado del servidor"
echo "  • ca.key       - Clave privada de CA"
echo "  • ca.crt       - Certificado de CA"
echo ""
echo "Common Name: $COMMON_NAME"
echo "Válido por: $DAYS_VALID días (~10 años)"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "  - Estos son certificados AUTOFIRMADOS"
echo "  - OK para desarrollo/testing"
echo "  - Para producción, usa Let's Encrypt o certificado comercial"
echo ""
echo "Para verificar TLS, ejecuta:"
echo "  openssl s_client -connect localhost:5061 -showcerts"
echo ""
