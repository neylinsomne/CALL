#!/bin/bash
# =============================================================================
# Network Diagnostic Script para VoIP/SIP
# =============================================================================
# Este script realiza un diagnóstico completo de la conectividad de red
# para asegurar que tu sistema está listo para VoIP.
#
# USO: ./network-diagnostic.sh [IP_PROVEEDOR_SIP]
# =============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Configuración por defecto
SIP_PROVIDER_IP="${1:-8.8.8.8}"
OUTPUT_FILE="network-diagnostic-$(date +%Y%m%d_%H%M%S).log"

# ===========================================
# FUNCIONES
# ===========================================

print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}  $1${NC}"
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}▶ $1${NC}"
    echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"
}

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
}

check_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
}

check_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

# ===========================================
# SCRIPT PRINCIPAL
# ===========================================

# Inicio
clear
print_header "DIAGNÓSTICO DE RED PARA VOIP/SIP"

echo -e "Fecha: $(date)"
echo -e "IP Proveedor SIP: ${BOLD}${SIP_PROVIDER_IP}${NC}"
echo -e "Resultados se guardarán en: ${BOLD}${OUTPUT_FILE}${NC}"

# Guardar también en archivo
exec > >(tee -a "$OUTPUT_FILE") 2>&1

# ===========================================
# 1. INFORMACIÓN DEL SISTEMA
# ===========================================
print_section "1. INFORMACIÓN DEL SISTEMA"

echo "  Hostname: $(hostname)"
echo "  Sistema: $(uname -a)"
echo "  Uptime: $(uptime -p 2>/dev/null || uptime)"

# ===========================================
# 2. INTERFACES DE RED
# ===========================================
print_section "2. INTERFACES DE RED"

if command -v ip &> /dev/null; then
    echo ""
    ip -br addr show 2>/dev/null || ip addr show
else
    ifconfig 2>/dev/null || echo "No se puede obtener info de interfaces"
fi

# ===========================================
# 3. IP PÚBLICA
# ===========================================
print_section "3. DETECCIÓN DE IP PÚBLICA"

PUBLIC_IP=$(curl -s --max-time 5 https://api.ipify.org 2>/dev/null || \
            curl -s --max-time 5 https://ifconfig.me 2>/dev/null || \
            curl -s --max-time 5 https://icanhazip.com 2>/dev/null || \
            echo "No detectada")

if [[ "$PUBLIC_IP" != "No detectada" ]]; then
    check_pass "IP Pública: ${BOLD}${PUBLIC_IP}${NC}"
else
    check_fail "No se pudo detectar la IP pública"
fi

# ===========================================
# 4. DNS
# ===========================================
print_section "4. RESOLUCIÓN DNS"

echo "  Servidores DNS configurados:"
if [[ -f /etc/resolv.conf ]]; then
    grep nameserver /etc/resolv.conf | while read line; do
        echo "    $line"
    done
fi

echo ""
echo "  Test de resolución DNS:"
for domain in "google.com" "cloudflare.com"; do
    if nslookup "$domain" &> /dev/null || host "$domain" &> /dev/null; then
        check_pass "$domain resuelve correctamente"
    else
        check_fail "$domain NO resuelve"
    fi
done

# ===========================================
# 5. CONECTIVIDAD BÁSICA
# ===========================================
print_section "5. CONECTIVIDAD BÁSICA"

echo "  Test de ping a servicios conocidos:"
for target in "8.8.8.8" "1.1.1.1" "google.com"; do
    result=$(ping -c 3 -W 2 "$target" 2>&1)
    if echo "$result" | grep -q "bytes from"; then
        avg=$(echo "$result" | grep -oP 'avg[^=]*= *\K[0-9.]+' 2>/dev/null || echo "?")
        check_pass "$target - Latencia: ${avg}ms"
    else
        check_fail "$target - Sin respuesta"
    fi
done

# ===========================================
# 6. TEST DE LATENCIA AL PROVEEDOR SIP
# ===========================================
print_section "6. LATENCIA AL PROVEEDOR SIP (${SIP_PROVIDER_IP})"

echo "  Ejecutando 50 pings..."
echo ""

if ping -c 50 -i 0.2 "$SIP_PROVIDER_IP" &> /tmp/ping_result.txt; then
    # Extraer estadísticas
    STATS=$(tail -2 /tmp/ping_result.txt)
    echo "$STATS"
    echo ""

    # Analizar resultados
    LOSS=$(echo "$STATS" | grep -oP '\d+(?=% packet loss)' || echo "100")
    AVG=$(grep -oP 'avg[^=]*= *\K[0-9.]+' /tmp/ping_result.txt 2>/dev/null || echo "0")
    JITTER=$(grep -oP 'mdev = [^/]+/[^/]+/[^/]+/\K[0-9.]+' /tmp/ping_result.txt 2>/dev/null || echo "0")

    echo "  Análisis:"

    # Packet Loss
    if [[ "$LOSS" == "0" ]]; then
        check_pass "Packet Loss: ${LOSS}%"
    elif [[ "$LOSS" -lt "2" ]]; then
        check_warn "Packet Loss: ${LOSS}% (aceptable pero no ideal)"
    else
        check_fail "Packet Loss: ${LOSS}% (CRÍTICO - afectará calidad de voz)"
    fi

    # Latencia
    AVG_INT=${AVG%.*}
    if [[ "$AVG_INT" -lt "50" ]]; then
        check_pass "Latencia promedio: ${AVG}ms (Excelente)"
    elif [[ "$AVG_INT" -lt "150" ]]; then
        check_warn "Latencia promedio: ${AVG}ms (Aceptable)"
    else
        check_fail "Latencia promedio: ${AVG}ms (ALTA - puede afectar IA)"
    fi

    # Jitter
    JITTER_INT=${JITTER%.*}
    if [[ "$JITTER_INT" -lt "10" ]]; then
        check_pass "Jitter (variación): ${JITTER}ms (Excelente)"
    elif [[ "$JITTER_INT" -lt "30" ]]; then
        check_warn "Jitter (variación): ${JITTER}ms (Aceptable)"
    else
        check_fail "Jitter (variación): ${JITTER}ms (ALTO - voz robotizada)"
    fi
else
    check_fail "No se puede alcanzar ${SIP_PROVIDER_IP}"
fi

rm -f /tmp/ping_result.txt

# ===========================================
# 7. TRACEROUTE
# ===========================================
print_section "7. RUTA AL PROVEEDOR SIP"

echo "  Trazando ruta a ${SIP_PROVIDER_IP}..."
echo ""

if command -v tracepath &> /dev/null; then
    timeout 30 tracepath -n "$SIP_PROVIDER_IP" 2>/dev/null | head -20
elif command -v traceroute &> /dev/null; then
    timeout 30 traceroute -n -m 15 "$SIP_PROVIDER_IP" 2>/dev/null
else
    check_warn "tracepath/traceroute no disponible"
fi

# Contar saltos
HOPS=$(tracepath -n "$SIP_PROVIDER_IP" 2>/dev/null | grep -c "^ [0-9]" || echo "?")
echo ""
if [[ "$HOPS" != "?" ]]; then
    if [[ "$HOPS" -lt "10" ]]; then
        check_pass "Número de saltos: ${HOPS} (Excelente)"
    elif [[ "$HOPS" -lt "15" ]]; then
        check_warn "Número de saltos: ${HOPS} (Aceptable)"
    else
        check_fail "Número de saltos: ${HOPS} (Muchos - posible latencia)"
    fi
fi

# ===========================================
# 8. PUERTOS LOCALES
# ===========================================
print_section "8. PUERTOS LOCALES EN USO"

echo "  Puertos SIP/RTP:"
if command -v ss &> /dev/null; then
    ss -tulnp 2>/dev/null | grep -E "5060|5061|10000|20000" || echo "    Ningún servicio SIP detectado"
elif command -v netstat &> /dev/null; then
    netstat -tulnp 2>/dev/null | grep -E "5060|5061|10000|20000" || echo "    Ningún servicio SIP detectado"
fi

# ===========================================
# 9. FIREWALL
# ===========================================
print_section "9. ESTADO DEL FIREWALL"

echo "  Reglas iptables (INPUT):"
if command -v iptables &> /dev/null; then
    sudo iptables -L INPUT -n 2>/dev/null | head -15 || echo "    No se puede leer iptables (requiere sudo)"
fi

echo ""
echo "  UFW status:"
if command -v ufw &> /dev/null; then
    sudo ufw status 2>/dev/null || echo "    UFW no activo o requiere sudo"
fi

# ===========================================
# 10. VERIFICACIÓN DE ASTERISK (si existe)
# ===========================================
print_section "10. ESTADO DE ASTERISK"

if command -v asterisk &> /dev/null || docker ps 2>/dev/null | grep -q asterisk; then
    echo "  Asterisk detectado. Verificando..."

    # Via Docker
    if docker ps 2>/dev/null | grep -q asterisk; then
        echo ""
        echo "  Registros SIP:"
        docker exec callcenter-asterisk asterisk -rx "pjsip show registrations" 2>/dev/null || echo "    No disponible"

        echo ""
        echo "  Endpoints:"
        docker exec callcenter-asterisk asterisk -rx "pjsip show endpoints" 2>/dev/null | head -10 || echo "    No disponible"
    # Instalación local
    elif command -v asterisk &> /dev/null; then
        echo ""
        echo "  Registros SIP:"
        asterisk -rx "pjsip show registrations" 2>/dev/null || echo "    No disponible"
    fi
else
    check_info "Asterisk no detectado en este sistema"
fi

# ===========================================
# 11. ANCHO DE BANDA (opcional)
# ===========================================
print_section "11. ESTIMACIÓN DE ANCHO DE BANDA"

echo "  Requisitos por llamada simultánea:"
echo "    - G.711 (ulaw/alaw): ~87 Kbps por dirección"
echo "    - G.722: ~64 Kbps por dirección"
echo "    - Opus: ~32-64 Kbps variable"
echo ""
echo "  Ejemplo para 10 llamadas simultáneas (G.711):"
echo "    - Upload necesario: ~870 Kbps = ~1 Mbps"
echo "    - Download necesario: ~870 Kbps = ~1 Mbps"
echo ""

# Test rápido de velocidad (si está disponible)
if command -v speedtest-cli &> /dev/null; then
    echo "  Ejecutando test de velocidad..."
    speedtest-cli --simple 2>/dev/null || echo "    Test de velocidad falló"
else
    check_info "Instala speedtest-cli para test de velocidad automático"
    echo "    sudo apt install speedtest-cli"
fi

# ===========================================
# RESUMEN
# ===========================================
print_header "RESUMEN DE DIAGNÓSTICO"

echo -e "  IP Pública detectada: ${BOLD}${PUBLIC_IP}${NC}"
echo -e "  Proveedor SIP testeado: ${BOLD}${SIP_PROVIDER_IP}${NC}"
echo ""

# Generar veredicto
echo -e "${BOLD}Veredicto:${NC}"

if [[ "$LOSS" == "0" ]] && [[ "${AVG_INT:-999}" -lt "100" ]]; then
    echo -e "  ${GREEN}${BOLD}✓ RED APTA PARA VOIP${NC}"
    echo "    La conexión cumple los requisitos mínimos para voz sobre IP."
else
    echo -e "  ${YELLOW}${BOLD}⚠ REVISAR ANTES DE PRODUCCIÓN${NC}"
    echo "    Hay métricas fuera de los valores ideales."
fi

echo ""
echo -e "Resultados guardados en: ${BOLD}${OUTPUT_FILE}${NC}"
echo ""
