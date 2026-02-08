#!/bin/bash
# =============================================================================
# Verificador de Puertos para VoIP
# =============================================================================
# Verifica que los puertos necesarios estén abiertos y accesibles.
#
# USO: ./check-ports.sh [IP_SERVIDOR]
# =============================================================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

# IP del servidor (por defecto localhost)
SERVER_IP="${1:-127.0.0.1}"

# Puertos a verificar
declare -A PORTS=(
    ["5060/udp"]="SIP UDP (Señalización)"
    ["5060/tcp"]="SIP TCP (Señalización)"
    ["5061/tcp"]="SIP TLS (Señalización Segura)"
    ["8088/tcp"]="WebSocket (WebRTC)"
    ["8089/tcp"]="WebSocket Secure (WebRTC TLS)"
    ["5038/tcp"]="AMI (Asterisk Manager)"
    ["8000/tcp"]="Backend API"
    ["8080/tcp"]="FreePBX Web"
    ["3000/tcp"]="Dashboard"
    ["5432/tcp"]="PostgreSQL"
)

# Header
echo ""
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}           VERIFICADOR DE PUERTOS VOIP                          ${NC}"
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Servidor: ${BOLD}${SERVER_IP}${NC}"
echo ""

# Función para verificar puerto TCP
check_tcp_port() {
    local ip=$1
    local port=$2

    if command -v nc &> /dev/null; then
        nc -z -w2 "$ip" "$port" 2>/dev/null
        return $?
    elif command -v timeout &> /dev/null; then
        timeout 2 bash -c "echo >/dev/tcp/$ip/$port" 2>/dev/null
        return $?
    else
        # Fallback con /dev/tcp
        (echo >/dev/tcp/$ip/$port) 2>/dev/null
        return $?
    fi
}

# Función para verificar puerto UDP (más difícil, usamos ss/netstat)
check_udp_port() {
    local port=$1

    if command -v ss &> /dev/null; then
        ss -uln 2>/dev/null | grep -q ":${port} "
        return $?
    elif command -v netstat &> /dev/null; then
        netstat -uln 2>/dev/null | grep -q ":${port} "
        return $?
    fi
    return 1
}

# ===========================================
# VERIFICAR PUERTOS LOCALES (listening)
# ===========================================
echo -e "${BLUE}▶ PUERTOS EN ESCUCHA (LOCALES)${NC}"
echo -e "${BLUE}─────────────────────────────────────────────────────────────────${NC}"
echo ""

for port_proto in "${!PORTS[@]}"; do
    PORT="${port_proto%/*}"
    PROTO="${port_proto#*/}"
    DESC="${PORTS[$port_proto]}"

    if [[ "$PROTO" == "udp" ]]; then
        if check_udp_port "$PORT"; then
            echo -e "  ${GREEN}✓${NC} ${PORT}/${PROTO} - ${DESC}"
        else
            echo -e "  ${RED}✗${NC} ${PORT}/${PROTO} - ${DESC} ${RED}(NO ESCUCHANDO)${NC}"
        fi
    else
        if [[ "$SERVER_IP" == "127.0.0.1" ]]; then
            # Verificar si está escuchando localmente
            if ss -tln 2>/dev/null | grep -q ":${PORT} " || \
               netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
                echo -e "  ${GREEN}✓${NC} ${PORT}/${PROTO} - ${DESC}"
            else
                echo -e "  ${YELLOW}○${NC} ${PORT}/${PROTO} - ${DESC} ${YELLOW}(no activo)${NC}"
            fi
        else
            # Verificar conexión remota
            if check_tcp_port "$SERVER_IP" "$PORT"; then
                echo -e "  ${GREEN}✓${NC} ${PORT}/${PROTO} - ${DESC}"
            else
                echo -e "  ${RED}✗${NC} ${PORT}/${PROTO} - ${DESC} ${RED}(NO ACCESIBLE)${NC}"
            fi
        fi
    fi
done

# ===========================================
# VERIFICAR RANGO RTP
# ===========================================
echo ""
echo -e "${BLUE}▶ RANGO RTP (10000-20000/UDP)${NC}"
echo -e "${BLUE}─────────────────────────────────────────────────────────────────${NC}"
echo ""

# Verificar si hay puertos RTP en uso
RTP_PORTS=$(ss -uln 2>/dev/null | grep -E ":(1[0-9]{4}|20000) " | wc -l || echo "0")
if [[ "$RTP_PORTS" -gt "0" ]]; then
    echo -e "  ${GREEN}✓${NC} Puertos RTP en uso: ${RTP_PORTS}"
else
    echo -e "  ${YELLOW}○${NC} No hay puertos RTP activos actualmente"
    echo -e "    ${BLUE}ℹ${NC} (Normal si no hay llamadas en curso)"
fi

# ===========================================
# SERVICIOS DOCKER
# ===========================================
echo ""
echo -e "${BLUE}▶ CONTENEDORES DOCKER${NC}"
echo -e "${BLUE}─────────────────────────────────────────────────────────────────${NC}"
echo ""

if command -v docker &> /dev/null && docker ps &> /dev/null; then
    # Mostrar contenedores relevantes
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | \
        grep -E "asterisk|backend|tts|stt|llm|dashboard|freepbx|postgres" || \
        echo "  No hay contenedores de Call Center corriendo"
else
    echo -e "  ${YELLOW}○${NC} Docker no disponible o no está corriendo"
fi

# ===========================================
# VERIFICAR DESDE INTERNET (información)
# ===========================================
echo ""
echo -e "${BLUE}▶ VERIFICACIÓN EXTERNA${NC}"
echo -e "${BLUE}─────────────────────────────────────────────────────────────────${NC}"
echo ""

PUBLIC_IP=$(curl -s --max-time 5 https://api.ipify.org 2>/dev/null || echo "No detectada")

if [[ "$PUBLIC_IP" != "No detectada" ]]; then
    echo -e "  Tu IP Pública: ${BOLD}${PUBLIC_IP}${NC}"
    echo ""
    echo -e "  ${YELLOW}⚠${NC} Para verificar puertos desde internet:"
    echo ""
    echo -e "     1. Usa tu celular con ${BOLD}datos móviles${NC} (no Wi-Fi)"
    echo -e "     2. Instala una app de escaneo de puertos"
    echo -e "     3. Escanea: ${BOLD}${PUBLIC_IP}:5060${NC}"
    echo ""
    echo -e "  ${BLUE}ℹ${NC} O usa estos servicios web:"
    echo "     - https://www.yougetsignal.com/tools/open-ports/"
    echo "     - https://portchecker.co/"
    echo ""
    echo -e "  ${GREEN}✓${NC} Si configuraste whitelist, el puerto debería aparecer ${BOLD}CERRADO${NC}"
    echo -e "     (Esto es bueno - significa que el firewall está bloqueando)"
else
    echo -e "  ${RED}✗${NC} No se pudo detectar IP pública"
fi

# ===========================================
# RESUMEN
# ===========================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BOLD}Puertos críticos para VoIP:${NC}"
echo ""
echo "  SIP Señalización:  5060/UDP, 5060/TCP"
echo "  SIP Seguro:        5061/TCP (TLS)"
echo "  RTP Audio:         10000-20000/UDP"
echo "  WebRTC:            8088/TCP, 8089/TCP"
echo ""
