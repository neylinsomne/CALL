#!/bin/bash
# =============================================================================
# Asterisk Entrypoint Script
# =============================================================================
# Este script:
# 1. Auto-detecta la IP pública si no está configurada
# 2. Sustituye variables de entorno en los templates
# 3. Inicia Asterisk
# =============================================================================

set -e

echo "========================================"
echo "  Asterisk Entrypoint - Call Center AI"
echo "========================================"

# ===========================================
# 1. AUTO-DETECCIÓN DE IP PÚBLICA (NAT)
# ===========================================
if [ -z "$EXTERNAL_IP" ]; then
    echo "[NAT] EXTERNAL_IP no configurada, intentando auto-detectar..."

    # Intentar múltiples servicios de detección
    DETECTED_IP=$(curl -s --max-time 5 https://api.ipify.org 2>/dev/null || \
                  curl -s --max-time 5 https://ifconfig.me 2>/dev/null || \
                  curl -s --max-time 5 https://icanhazip.com 2>/dev/null || \
                  echo "")

    if [ -n "$DETECTED_IP" ]; then
        export EXTERNAL_IP="$DETECTED_IP"
        echo "[NAT] IP Pública detectada: $EXTERNAL_IP"
    else
        echo "[NAT] ADVERTENCIA: No se pudo detectar IP pública"
        echo "[NAT] Las llamadas pueden tener problemas de audio si estás detrás de NAT"
        echo "[NAT] Configura EXTERNAL_IP manualmente en .env"
        # Dejar vacío para que Asterisk use la IP local
        export EXTERNAL_IP=""
    fi
else
    echo "[NAT] Usando EXTERNAL_IP configurada: $EXTERNAL_IP"
fi

# ===========================================
# 2. VALIDAR RED LOCAL
# ===========================================
if [ -z "$LOCAL_NETWORK" ]; then
    # Intentar detectar la red local automáticamente
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "192.168.1.1")
    # Asumir /24 como máscara por defecto
    export LOCAL_NETWORK="${LOCAL_IP%.*}.0/24"
    echo "[NAT] Red local detectada: $LOCAL_NETWORK"
else
    echo "[NAT] Usando LOCAL_NETWORK configurada: $LOCAL_NETWORK"
fi

# ===========================================
# 3. CONFIGURAR RTP PORTS
# ===========================================
export RTP_PORT_START="${RTP_PORT_START:-10000}"
export RTP_PORT_END="${RTP_PORT_END:-20000}"
echo "[RTP] Rango de puertos: $RTP_PORT_START - $RTP_PORT_END"

# Configurar rtp.conf dinámicamente
cat > /etc/asterisk/rtp.conf << EOF
[general]
rtpstart=${RTP_PORT_START}
rtpend=${RTP_PORT_END}
; Opciones para NAT
strictrtp=yes
icesupport=yes
stunaddr=stun.l.google.com:19302
EOF

echo "[RTP] Configuración de rtp.conf generada"

# ===========================================
# 4. ACTUALIZAR DDNS (si está habilitado)
# ===========================================
if [ "$DDNS_ENABLED" = "true" ] && [ -n "$DDNS_TOKEN" ]; then
    echo "[DDNS] Actualizando IP dinámica..."

    case "$DDNS_PROVIDER" in
        duckdns)
            curl -s "https://www.duckdns.org/update?domains=${DDNS_DOMAIN}&token=${DDNS_TOKEN}&ip=" > /dev/null
            ;;
        noip)
            # No-IP requiere autenticación diferente
            echo "[DDNS] No-IP configurado - usar cliente externo"
            ;;
        *)
            echo "[DDNS] Proveedor no soportado: $DDNS_PROVIDER"
            ;;
    esac
fi

# ===========================================
# 5. GENERAR CONFIGURACIONES DESDE TEMPLATES
# ===========================================
echo "[CONFIG] Sustituyendo variables en templates..."

# Lista de variables a exportar para envsubst
export ASTERISK_USER="${ASTERISK_USER:-agent}"
export ASTERISK_PASSWORD="${ASTERISK_PASSWORD:-agent123}"
export SIP_TRUNK_HOST="${SIP_TRUNK_HOST:-}"
export SIP_TRUNK_USER="${SIP_TRUNK_USER:-}"
export SIP_TRUNK_PASSWORD="${SIP_TRUNK_PASSWORD:-}"
export GATEWAY_FXO_IP="${GATEWAY_FXO_IP:-192.168.1.100}"
export GATEWAY_FXO_USER="${GATEWAY_FXO_USER:-gateway}"
export GATEWAY_FXO_PASSWORD="${GATEWAY_FXO_PASSWORD:-gateway123}"
export WEBRTC_PASSWORD="${WEBRTC_PASSWORD:-webrtc123}"

# Generar pjsip.conf desde template
if [ -f /etc/asterisk/custom/pjsip.conf.template ]; then
    envsubst < /etc/asterisk/custom/pjsip.conf.template > /etc/asterisk/pjsip.conf
    echo "[CONFIG] pjsip.conf generado"
fi

# Generar extensions.conf desde template
if [ -f /etc/asterisk/custom/extensions.conf.template ]; then
    envsubst < /etc/asterisk/custom/extensions.conf.template > /etc/asterisk/extensions.conf
    echo "[CONFIG] extensions.conf generado"
fi

# Copiar otros archivos de configuración
for conf in modules.conf http.conf ari.conf manager.conf chan_dahdi.conf; do
    if [ -f "/etc/asterisk/custom/$conf" ]; then
        cp "/etc/asterisk/custom/$conf" "/etc/asterisk/$conf"
        echo "[CONFIG] $conf copiado"
    fi
done

# ===========================================
# 6. MOSTRAR RESUMEN DE CONFIGURACIÓN
# ===========================================
echo ""
echo "========================================"
echo "  Resumen de Configuración NAT"
echo "========================================"
echo "  IP Externa:    ${EXTERNAL_IP:-'(no configurada)'}"
echo "  Red Local:     $LOCAL_NETWORK"
echo "  Puertos RTP:   $RTP_PORT_START - $RTP_PORT_END"
echo "  SIP Trunk:     ${SIP_TRUNK_HOST:-'(no configurado)'}"
echo "  Gateway FXO:   ${GATEWAY_FXO_IP}"
echo "========================================"
echo ""

# ===========================================
# 7. INICIAR ASTERISK
# ===========================================
echo "[ASTERISK] Iniciando Asterisk..."
exec "$@"
