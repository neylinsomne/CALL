#!/bin/bash
# =============================================================================
# Firewall Rules Template para VoIP/SIP
# =============================================================================
# Este script configura iptables para proteger tu servidor SIP.
#
# USO:
#   1. Edita las variables de configuración
#   2. Ejecuta con sudo: sudo ./firewall-rules.sh
#   3. Para hacer las reglas persistentes: sudo iptables-save > /etc/iptables.rules
#
# IMPORTANTE: Modifica las IPs según tu proveedor SIP antes de ejecutar.
# =============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ===========================================
# CONFIGURACIÓN - EDITAR SEGÚN TU CASO
# ===========================================

# Tu interfaz de red (eth0, ens33, etc.)
NETWORK_INTERFACE="eth0"

# IPs de tu proveedor SIP (whitelist)
# Agrega todas las IPs o rangos que te proporcione tu proveedor
SIP_PROVIDER_IPS=(
    # Ejemplo Twilio (verificar lista actualizada)
    # "54.172.60.0/23"
    # "34.203.250.0/23"

    # Ejemplo Telnyx
    # "64.125.111.0/24"

    # Tu proveedor local - EDITAR
    "200.100.50.0/24"
    "201.200.100.0/24"
)

# Puertos SIP
SIP_PORT="5060"
SIP_TLS_PORT="5061"

# Rango de puertos RTP
RTP_PORT_START="10000"
RTP_PORT_END="20000"

# Puerto AMI (solo acceso local)
AMI_PORT="5038"

# Puerto HTTP (FreePBX)
HTTP_PORT="80"
HTTPS_PORT="443"
FREEPBX_PORT="8080"

# Tu red local (para acceso a servicios internos)
LOCAL_NETWORK="192.168.1.0/24"

# ===========================================
# FUNCIONES
# ===========================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ===========================================
# SCRIPT PRINCIPAL
# ===========================================

echo ""
echo "========================================"
echo "  Configuración de Firewall para VoIP"
echo "========================================"
echo ""

# Verificar root
if [[ $EUID -ne 0 ]]; then
    log_error "Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Confirmar antes de aplicar
log_warn "Este script modificará las reglas de iptables."
log_warn "IPs de proveedor SIP configuradas:"
for ip in "${SIP_PROVIDER_IPS[@]}"; do
    echo "  - $ip"
done
echo ""
read -p "¿Continuar? (s/N): " confirm
if [[ ! "$confirm" =~ ^[sS]$ ]]; then
    log_info "Cancelado por el usuario."
    exit 0
fi

# ===========================================
# LIMPIAR REGLAS EXISTENTES
# ===========================================
log_info "Limpiando reglas existentes..."
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# ===========================================
# POLÍTICAS POR DEFECTO
# ===========================================
log_info "Configurando políticas por defecto..."
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# ===========================================
# REGLAS BÁSICAS
# ===========================================
log_info "Aplicando reglas básicas..."

# Permitir loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Permitir conexiones establecidas y relacionadas
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Permitir ping (ICMP)
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-reply -j ACCEPT

# ===========================================
# ACCESO SSH (solo red local por seguridad)
# ===========================================
log_info "Configurando acceso SSH..."
iptables -A INPUT -p tcp --dport 22 -s ${LOCAL_NETWORK} -j ACCEPT
# Opcional: permitir SSH desde cualquier lugar (menos seguro)
# iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# ===========================================
# SIP - SOLO IPs DEL PROVEEDOR (WHITELIST)
# ===========================================
log_info "Configurando reglas SIP con whitelist..."

for provider_ip in "${SIP_PROVIDER_IPS[@]}"; do
    log_info "  Permitiendo SIP desde: $provider_ip"

    # UDP SIP
    iptables -A INPUT -p udp --dport ${SIP_PORT} -s ${provider_ip} -j ACCEPT

    # TCP SIP
    iptables -A INPUT -p tcp --dport ${SIP_PORT} -s ${provider_ip} -j ACCEPT

    # TLS SIP
    iptables -A INPUT -p tcp --dport ${SIP_TLS_PORT} -s ${provider_ip} -j ACCEPT
done

# Loggear y dropear intentos SIP no autorizados
iptables -A INPUT -p udp --dport ${SIP_PORT} -j LOG --log-prefix "SIP_BLOCKED: " --log-level 4
iptables -A INPUT -p udp --dport ${SIP_PORT} -j DROP
iptables -A INPUT -p tcp --dport ${SIP_PORT} -j LOG --log-prefix "SIP_BLOCKED: " --log-level 4
iptables -A INPUT -p tcp --dport ${SIP_PORT} -j DROP

# ===========================================
# RTP (Audio) - SOLO IPs DEL PROVEEDOR
# ===========================================
log_info "Configurando reglas RTP..."

for provider_ip in "${SIP_PROVIDER_IPS[@]}"; do
    iptables -A INPUT -p udp --dport ${RTP_PORT_START}:${RTP_PORT_END} -s ${provider_ip} -j ACCEPT
done

# ===========================================
# SERVICIOS INTERNOS (Solo red local)
# ===========================================
log_info "Configurando acceso a servicios internos..."

# AMI (Asterisk Manager Interface)
iptables -A INPUT -p tcp --dport ${AMI_PORT} -s ${LOCAL_NETWORK} -j ACCEPT
iptables -A INPUT -p tcp --dport ${AMI_PORT} -s 127.0.0.1 -j ACCEPT

# FreePBX Web Interface
iptables -A INPUT -p tcp --dport ${FREEPBX_PORT} -s ${LOCAL_NETWORK} -j ACCEPT

# HTTP/HTTPS (si tienes servicios web)
iptables -A INPUT -p tcp --dport ${HTTP_PORT} -s ${LOCAL_NETWORK} -j ACCEPT
iptables -A INPUT -p tcp --dport ${HTTPS_PORT} -s ${LOCAL_NETWORK} -j ACCEPT

# API Backend (puerto 8000)
iptables -A INPUT -p tcp --dport 8000 -s ${LOCAL_NETWORK} -j ACCEPT

# Dashboard (puerto 3000/3001)
iptables -A INPUT -p tcp --dport 3000:3001 -s ${LOCAL_NETWORK} -j ACCEPT

# PostgreSQL (solo local)
iptables -A INPUT -p tcp --dport 5432 -s ${LOCAL_NETWORK} -j ACCEPT
iptables -A INPUT -p tcp --dport 5432 -s 127.0.0.1 -j ACCEPT

# ===========================================
# DOCKER (si usas Docker)
# ===========================================
log_info "Configurando reglas para Docker..."

# Permitir tráfico del bridge de Docker
iptables -A INPUT -i docker0 -j ACCEPT
iptables -A FORWARD -i docker0 -j ACCEPT
iptables -A FORWARD -o docker0 -j ACCEPT

# ===========================================
# PROTECCIÓN ADICIONAL
# ===========================================
log_info "Aplicando protecciones adicionales..."

# Protección contra SYN flood
iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# Protección contra escaneo de puertos
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP

# Bloquear paquetes inválidos
iptables -A INPUT -m state --state INVALID -j DROP

# ===========================================
# GUARDAR REGLAS
# ===========================================
log_info "Guardando reglas..."

# Debian/Ubuntu
if command -v netfilter-persistent &> /dev/null; then
    netfilter-persistent save
# CentOS/RHEL
elif command -v iptables-save &> /dev/null; then
    iptables-save > /etc/sysconfig/iptables
fi

# Backup manual
iptables-save > /root/iptables.backup.$(date +%Y%m%d_%H%M%S)

# ===========================================
# MOSTRAR RESUMEN
# ===========================================
echo ""
echo "========================================"
echo "  Configuración Completada"
echo "========================================"
echo ""
log_info "Reglas aplicadas:"
iptables -L INPUT -n -v --line-numbers | head -30
echo ""
log_info "Para ver todas las reglas: iptables -L -n -v"
log_info "Para ver logs de bloqueos: tail -f /var/log/syslog | grep SIP_BLOCKED"
log_info "Backup guardado en: /root/iptables.backup.*"
echo ""
log_warn "IMPORTANTE: Verifica que puedes hacer llamadas antes de desconectarte!"
echo ""
