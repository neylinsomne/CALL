#!/bin/bash
# =============================================================================
# Test de Latencia Continuo para VoIP
# =============================================================================
# Ejecuta un test de latencia prolongado y genera estadísticas.
#
# USO: ./test-latency.sh <IP_DESTINO> [DURACION_MINUTOS]
# Ejemplo: ./test-latency.sh 200.100.50.1 5
# =============================================================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

# Parámetros
TARGET_IP="${1:-8.8.8.8}"
DURATION_MINUTES="${2:-1}"
INTERVAL="0.5"  # Segundos entre pings

# Calcular número de pings
TOTAL_PINGS=$(echo "$DURATION_MINUTES * 60 / $INTERVAL" | bc)

# Archivo temporal
TEMP_FILE="/tmp/latency_test_$$.txt"

# Función para limpiar al salir
cleanup() {
    rm -f "$TEMP_FILE"
    echo ""
    echo -e "${BLUE}Test interrumpido.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Header
clear
echo ""
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}           TEST DE LATENCIA CONTINUO PARA VOIP                 ${NC}"
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Destino: ${BOLD}${TARGET_IP}${NC}"
echo -e "  Duración: ${BOLD}${DURATION_MINUTES} minuto(s)${NC}"
echo -e "  Pings totales: ${BOLD}${TOTAL_PINGS}${NC}"
echo -e "  Intervalo: ${BOLD}${INTERVAL}s${NC}"
echo ""
echo -e "${YELLOW}Presiona Ctrl+C para detener en cualquier momento${NC}"
echo ""
echo -e "${BLUE}─────────────────────────────────────────────────────────────────${NC}"
echo ""

# Ejecutar ping
echo -e "Iniciando test..."
echo ""

ping -c "$TOTAL_PINGS" -i "$INTERVAL" "$TARGET_IP" 2>&1 | tee "$TEMP_FILE" | while read line; do
    # Mostrar solo las líneas con tiempo
    if echo "$line" | grep -q "time="; then
        TIME=$(echo "$line" | grep -oP 'time=\K[0-9.]+')

        # Colorear según latencia
        if (( $(echo "$TIME < 50" | bc -l) )); then
            COLOR=$GREEN
            STATUS="EXCELENTE"
        elif (( $(echo "$TIME < 100" | bc -l) )); then
            COLOR=$YELLOW
            STATUS="BUENO"
        elif (( $(echo "$TIME < 150" | bc -l) )); then
            COLOR=$YELLOW
            STATUS="ACEPTABLE"
        else
            COLOR=$RED
            STATUS="ALTO"
        fi

        echo -e "  ${COLOR}●${NC} ${TIME}ms ${COLOR}[${STATUS}]${NC}"
    fi
done

# Esperar a que termine el ping
wait

# Mostrar estadísticas finales
echo ""
echo -e "${BLUE}─────────────────────────────────────────────────────────────────${NC}"
echo -e "${BLUE}${BOLD}                    RESULTADOS FINALES                          ${NC}"
echo -e "${BLUE}─────────────────────────────────────────────────────────────────${NC}"
echo ""

# Extraer estadísticas
if [[ -f "$TEMP_FILE" ]]; then
    STATS=$(tail -2 "$TEMP_FILE")
    echo "$STATS"
    echo ""

    # Extraer valores
    TRANSMITTED=$(grep -oP '\d+(?= packets transmitted)' "$TEMP_FILE" || echo "0")
    RECEIVED=$(grep -oP '\d+(?= received)' "$TEMP_FILE" || echo "0")
    LOSS=$(grep -oP '\d+(?=% packet loss)' "$TEMP_FILE" || echo "0")

    # RTT stats
    MIN=$(grep -oP 'min/avg/max/mdev = \K[0-9.]+' "$TEMP_FILE" || echo "0")
    AVG=$(grep -oP 'min/avg/max/mdev = [^/]+/\K[0-9.]+' "$TEMP_FILE" || echo "0")
    MAX=$(grep -oP 'min/avg/max/mdev = [^/]+/[^/]+/\K[0-9.]+' "$TEMP_FILE" || echo "0")
    JITTER=$(grep -oP 'min/avg/max/mdev = [^/]+/[^/]+/[^/]+/\K[0-9.]+' "$TEMP_FILE" || echo "0")

    echo -e "${BOLD}Análisis para VoIP:${NC}"
    echo ""

    # Packet Loss
    if [[ "$LOSS" == "0" ]]; then
        echo -e "  ${GREEN}✓${NC} Packet Loss: ${LOSS}% - ${GREEN}PERFECTO${NC}"
    elif [[ "$LOSS" -lt "1" ]]; then
        echo -e "  ${YELLOW}⚠${NC} Packet Loss: ${LOSS}% - ${YELLOW}ACEPTABLE${NC}"
    else
        echo -e "  ${RED}✗${NC} Packet Loss: ${LOSS}% - ${RED}PROBLEMATICO${NC}"
    fi

    # Latencia promedio
    AVG_INT=${AVG%.*}
    if [[ "$AVG_INT" -lt "50" ]]; then
        echo -e "  ${GREEN}✓${NC} Latencia Promedio: ${AVG}ms - ${GREEN}EXCELENTE para IA${NC}"
    elif [[ "$AVG_INT" -lt "100" ]]; then
        echo -e "  ${GREEN}✓${NC} Latencia Promedio: ${AVG}ms - ${GREEN}BUENO${NC}"
    elif [[ "$AVG_INT" -lt "150" ]]; then
        echo -e "  ${YELLOW}⚠${NC} Latencia Promedio: ${AVG}ms - ${YELLOW}ACEPTABLE${NC}"
    else
        echo -e "  ${RED}✗${NC} Latencia Promedio: ${AVG}ms - ${RED}ALTO${NC}"
    fi

    # Latencia máxima
    MAX_INT=${MAX%.*}
    if [[ "$MAX_INT" -lt "100" ]]; then
        echo -e "  ${GREEN}✓${NC} Latencia Máxima: ${MAX}ms - ${GREEN}ESTABLE${NC}"
    elif [[ "$MAX_INT" -lt "200" ]]; then
        echo -e "  ${YELLOW}⚠${NC} Latencia Máxima: ${MAX}ms - ${YELLOW}PICOS OCASIONALES${NC}"
    else
        echo -e "  ${RED}✗${NC} Latencia Máxima: ${MAX}ms - ${RED}INESTABLE${NC}"
    fi

    # Jitter
    JITTER_INT=${JITTER%.*}
    if [[ "$JITTER_INT" -lt "10" ]]; then
        echo -e "  ${GREEN}✓${NC} Jitter: ${JITTER}ms - ${GREEN}EXCELENTE${NC}"
    elif [[ "$JITTER_INT" -lt "30" ]]; then
        echo -e "  ${YELLOW}⚠${NC} Jitter: ${JITTER}ms - ${YELLOW}ACEPTABLE${NC}"
    else
        echo -e "  ${RED}✗${NC} Jitter: ${JITTER}ms - ${RED}VOZ ROBOTIZADA PROBABLE${NC}"
    fi

    echo ""
    echo -e "${BOLD}Recomendación:${NC}"

    # Veredicto final
    if [[ "$LOSS" == "0" ]] && [[ "$AVG_INT" -lt "100" ]] && [[ "$JITTER_INT" -lt "30" ]]; then
        echo -e "  ${GREEN}${BOLD}✓ CONEXIÓN APTA PARA VOIP CON IA${NC}"
    elif [[ "$LOSS" -lt "2" ]] && [[ "$AVG_INT" -lt "150" ]]; then
        echo -e "  ${YELLOW}${BOLD}⚠ CONEXIÓN ACEPTABLE - Monitorear en producción${NC}"
    else
        echo -e "  ${RED}${BOLD}✗ CONEXIÓN NO RECOMENDADA - Revisar red${NC}"
    fi
fi

# Limpiar
rm -f "$TEMP_FILE"

echo ""
echo -e "${BLUE}─────────────────────────────────────────────────────────────────${NC}"
echo ""
