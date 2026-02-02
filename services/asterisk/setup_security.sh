#!/bin/bash
#
# Script de Setup de Seguridad para Asterisk
# ===========================================
#
# Se ejecuta al iniciar el contenedor
# Genera certificados si no existen
# Configura TLS/SRTP
#

set -e

CERT_DIR="/etc/asterisk/keys"

echo "🔒 Setup de Seguridad de Asterisk"
echo "=================================="

# Verificar si ya existen certificados
if [ -f "$CERT_DIR/asterisk.crt" ] && [ -f "$CERT_DIR/asterisk.key" ]; then
    echo "✅ Certificados existentes encontrados"

    # Verificar validez
    if openssl x509 -checkend 86400 -noout -in "$CERT_DIR/asterisk.crt" > /dev/null 2>&1; then
        echo "✅ Certificados válidos (>24 horas restantes)"
    else
        echo "⚠️  Certificados por expirar, regenerando..."
        /usr/local/bin/generate_certificates.sh
    fi
else
    echo "📝 No se encontraron certificados, generando nuevos..."
    /usr/local/bin/generate_certificates.sh
fi

# Verificar configuración de TLS en pjsip.conf
PJSIP_CONF="/etc/asterisk/pjsip.conf"

if [ -f "$PJSIP_CONF" ]; then
    if grep -q "transport-tls" "$PJSIP_CONF"; then
        echo "✅ Transport TLS configurado en pjsip.conf"
    else
        echo "⚠️  Transport TLS NO encontrado en pjsip.conf"
        echo "   Asegúrate de tener [transport-tls] configurado"
    fi
fi

# Verificar puertos
echo ""
echo "Puertos de seguridad:"
echo "  • 5061/tcp - SIPS (TLS)"
echo "  • 8089/tcp - HTTPS (ARI/AMI)"
echo "  • 8189/tcp - WSS (WebRTC)"
echo ""

echo "✅ Setup de seguridad completado"
