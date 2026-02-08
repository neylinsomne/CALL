# Requisitos de Conexión Telefónica - Call Center AI

## Resumen Ejecutivo

Este documento detalla las dos opciones disponibles para conectar tu sistema de Call Center AI a la red telefónica:

| Opción | Descripción | Mejor para |
|--------|-------------|------------|
| **SIP Trunk** | Líneas virtuales por internet | Nuevas instalaciones, oficinas distribuidas |
| **Gateway FXO** | Convertidor de líneas fijas existentes | Aprovechar líneas analógicas ya contratadas |

---

## Diagrama de Conexión

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    OPCIONES DE CONEXIÓN TELEFÓNICA                       │
└─────────────────────────────────────────────────────────────────────────┘

                OPCIÓN A: SIP TRUNK                    OPCIÓN B: GATEWAY FXO
                (Internet/VoIP)                        (Líneas Fijas Locales)

    ┌─────────────────────┐                    ┌─────────────────────────┐
    │   Proveedor VoIP    │                    │    Líneas Telefónicas   │
    │  (Twilio, Vonage,   │                    │    Analógicas (PSTN)    │
    │   Telnyx, etc.)     │                    │                         │
    └──────────┬──────────┘                    └────────────┬────────────┘
               │                                            │
               │ SIP/RTP                                    │ Cables RJ11
               │ (Puerto 5060)                              │
               │                                            ▼
               │                               ┌─────────────────────────┐
               │                               │   Gateway FXO/FXS       │
               │                               │  (Grandstream, Cisco)   │
               │                               │                         │
               │                               │  • Convierte analógico  │
               │                               │    a SIP                │
               │                               │  • Alimentación PoE     │
               │                               └────────────┬────────────┘
               │                                            │ SIP/RTP
               │                                            │ (Puerto 5060)
               │                                            │
               ▼                                            ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                                                                     │
    │                        SERVIDOR CALL CENTER AI                      │
    │                                                                     │
    │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │
    │   │  Asterisk   │◄──►│   Backend   │◄──►│   STT / LLM / TTS   │   │
    │   │   (PBX)     │    │  (FastAPI)  │    │   (AI Processing)   │   │
    │   └─────────────┘    └─────────────┘    └─────────────────────┘   │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## Opción A: SIP Trunk (Líneas Virtuales por Internet)

### ¿Qué es?

Un **SIP Trunk** es un servicio de telefonía IP que entrega líneas telefónicas virtuales a través de internet. No requiere hardware adicional, solo conexión a internet estable.

### Proveedores Compatibles

| Proveedor | País/Región | Canales | Precio Aproximado |
|-----------|-------------|---------|-------------------|
| **Twilio** | Global | Ilimitados | $0.0085/min entrante |
| **Vonage** | Global | Por bundle | $0.0049/min |
| **Telnyx** | Global | Ilimitados | $0.0070/min |
| **Plivo** | Global | Ilimitados | $0.0050/min |
| **VoIP.ms** | Norte América | Ilimitados | $0.0085/min |
| **Didww** | Global | Por DID | Variable |
| **Flowroute** | USA | Ilimitados | $0.0098/min |
| **Voz.io** | LATAM | Por plan | Consultar |
| **Netelip** | España/LATAM | Por plan | Desde €5/mes |

### Requisitos de Red

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| **Ancho de banda** | 100 Kbps por canal | 256 Kbps por canal |
| **Latencia** | < 150ms | < 50ms |
| **Jitter** | < 30ms | < 10ms |
| **Pérdida de paquetes** | < 1% | 0% |
| **IP Pública** | Estática recomendada | Estática |

### Puertos a Abrir en Firewall

```
ENTRANTE:
├── UDP 5060     → Señalización SIP
├── UDP 5061     → SIP sobre TLS (opcional)
├── UDP 10000-20000 → RTP (audio)
└── TCP 5060     → SIP sobre TCP (respaldo)

SALIENTE:
└── Permitir conexiones a IPs del proveedor SIP
```

### Configuración en el Sistema

**Variables de entorno (.env):**
```bash
# Configuración SIP Trunk
SIP_TRUNK_ENABLED=true
SIP_TRUNK_HOST=sip.proveedor.com
SIP_TRUNK_USER=tu_usuario
SIP_TRUNK_PASSWORD=tu_password
SIP_TRUNK_DID=+1234567890
SIP_TRUNK_CODECS=opus,g722,ulaw,alaw

# Opciones avanzadas
SIP_TRUNK_REGISTER=true
SIP_TRUNK_OUTBOUND_PROXY=
SIP_TRUNK_FROM_DOMAIN=
```

### Ventajas y Desventajas

**Ventajas:**
- Sin hardware adicional
- Escalabilidad inmediata (agregar canales en minutos)
- Números de cualquier país/ciudad (DIDs)
- Failover automático (múltiples proveedores)
- Estadísticas y grabaciones en la nube
- Precios competitivos por minuto

**Desventajas:**
- Dependencia de calidad de internet
- Costos variables por uso
- Posibles bloqueos de puertos por ISP
- Requiere IP pública (o configuración NAT)

### Checklist de Implementación SIP Trunk

- [ ] Contratar servicio SIP Trunk con proveedor
- [ ] Obtener credenciales (usuario, password, host)
- [ ] Adquirir DID(s) - números telefónicos
- [ ] Configurar firewall (puertos SIP/RTP)
- [ ] Verificar calidad de internet (speedtest + jitter test)
- [ ] Configurar variables en .env
- [ ] Ejecutar wizard de configuración
- [ ] Realizar llamada de prueba entrante
- [ ] Realizar llamada de prueba saliente

---

## Opción B: Gateway FXO (Líneas Fijas Locales)

### ¿Qué es?

Un **Gateway FXO** es un dispositivo que convierte líneas telefónicas analógicas tradicionales (PSTN) en señalización SIP, permitiendo conectarlas al sistema de Call Center AI.

### Hardware Recomendado

| Modelo | Puertos | Tipo | Precio Aprox. | Uso Recomendado |
|--------|---------|------|---------------|-----------------|
| **Grandstream GXW4104** | 4 FXO | Analógico | $150-200 USD | Oficina pequeña |
| **Grandstream GXW4108** | 8 FXO | Analógico | $250-350 USD | Oficina mediana |
| **Grandstream GXW4224** | 24 FXO | Analógico | $400-500 USD | Call center |
| **Cisco SPA112** | 2 FXS | Analógico | $60-80 USD | Teléfonos analógicos |
| **Cisco SPA122** | 2 FXS + Router | Analógico | $80-100 USD | Home office |
| **Dinstar MTG200** | 4-8 FXO | Analógico | $200-300 USD | Oficina |
| **AudioCodes MP-11x** | 4-8 FXO | Analógico | $300-400 USD | Empresarial |

### Diferencia FXO vs FXS

| Tipo | Función | Conexión |
|------|---------|----------|
| **FXO** (Foreign Exchange Office) | Recibe líneas telefónicas | Conecta a la línea de la compañía telefónica |
| **FXS** (Foreign Exchange Station) | Entrega línea a dispositivos | Conecta teléfonos analógicos, fax, etc. |

**Para Call Center AI necesitas FXO** (recibir llamadas de líneas existentes).

### Diagrama de Conexión Física

```
┌───────────────────┐
│  Roseta Telefónica│
│  (Pared)          │
└────────┬──────────┘
         │ Cable telefónico RJ11
         │
         ▼
┌───────────────────┐     Cable Ethernet
│  Gateway FXO      │     (RJ45)
│  Grandstream      │◄────────────────────┐
│  GXW4104          │                     │
│                   │                     │
│  [FXO1][FXO2]...  │                     │
│  [PWR] [LAN]      │                     │
└───────────────────┘                     │
                                          │
                                          ▼
                              ┌───────────────────┐
                              │   Switch/Router   │
                              │   de red local    │
                              └─────────┬─────────┘
                                        │
                                        ▼
                              ┌───────────────────┐
                              │   Servidor Call   │
                              │   Center AI       │
                              └───────────────────┘
```

### Requisitos de Red Local

| Recurso | Requisito |
|---------|-----------|
| **Dirección IP** | IP estática en red local (ej: 192.168.1.100) |
| **Puerto** | Gateway y servidor en misma VLAN/subred |
| **Alimentación** | PoE o adaptador de corriente incluido |
| **Cables** | RJ11 (teléfono) + RJ45 (red) |

### Configuración del Gateway (Grandstream)

**1. Acceder al panel web del Gateway:**
```
http://192.168.1.100  (IP por defecto o asignada por DHCP)
Usuario: admin
Password: admin (cambiar inmediatamente)
```

**2. Configurar perfil SIP (Profile 1):**
```
Primary SIP Server: 192.168.1.50:5060  (IP del servidor Call Center)
Outbound Proxy: (dejar vacío)
SIP User ID: gateway
Authenticate ID: gateway
Authenticate Password: [password_seguro]
```

**3. Configurar canales FXO:**
```
Channel 1-4:
  - Profile: Profile 1
  - Unconditional Call Forward: [extensión del IVR]
  - Call Progress Tone: [Seleccionar país]
```

### Configuración en el Sistema

**Variables de entorno (.env):**
```bash
# Configuración Gateway FXO
GATEWAY_FXO_ENABLED=true
GATEWAY_FXO_IP=192.168.1.100
GATEWAY_FXO_USER=gateway
GATEWAY_FXO_PASSWORD=tu_password_seguro
GATEWAY_FXO_CHANNELS=4
GATEWAY_FXO_CONTEXT=from-pstn-gateway
```

### Ventajas y Desventajas

**Ventajas:**
- Aprovecha líneas existentes (sin costo adicional de minutos)
- No depende de calidad de internet para las llamadas
- Números locales ya establecidos (sin portabilidad)
- Funciona sin internet (llamadas internas)
- Costo fijo mensual conocido

**Desventajas:**
- Hardware adicional ($150-500 USD)
- Limitado a número de puertos físicos
- Configuración inicial más compleja
- Escalabilidad limitada
- Dependencia de infraestructura telefónica local

### Checklist de Implementación Gateway FXO

- [ ] Adquirir Gateway FXO (Grandstream GXW4104 recomendado)
- [ ] Identificar líneas telefónicas a conectar
- [ ] Asignar IP estática al Gateway
- [ ] Conectar cables telefónicos (RJ11) al Gateway
- [ ] Conectar Gateway a la red local (RJ45)
- [ ] Acceder a panel web del Gateway
- [ ] Configurar perfil SIP apuntando al servidor
- [ ] Configurar variables en .env del servidor
- [ ] Reiniciar servicios de Asterisk
- [ ] Realizar llamada de prueba entrante
- [ ] Verificar CallerID correcto

---

## Comparación Detallada

| Aspecto | SIP Trunk | Gateway FXO |
|---------|-----------|-------------|
| **Costo inicial** | $0 | $150-500 USD |
| **Costo operativo** | Por minuto ($0.005-0.02) | Tarifa fija de líneas |
| **Instalación** | Configuración software | Hardware + software |
| **Tiempo de setup** | 30 minutos | 2-4 horas |
| **Escalabilidad** | Instantánea | Requiere más hardware |
| **Redundancia** | Multi-proveedor fácil | Requiere múltiples gateways |
| **Calidad de voz** | Depende de internet | Consistente (línea dedicada) |
| **Números (DIDs)** | Cualquier país | Solo líneas locales |
| **Llamadas entrantes** | Ilimitadas (típico) | Según líneas contratadas |
| **Llamadas salientes** | Por minuto | Según plan telefónico |
| **Grabaciones cloud** | Disponible | No incluido |
| **Portabilidad** | Números portables | Números fijos existentes |
| **Dependencia internet** | Alta | Baja (solo red local) |

---

## Recomendaciones por Caso de Uso

### Caso 1: Nueva Empresa / Startup
**Recomendación: SIP Trunk**
- Sin infraestructura telefónica existente
- Necesita escalar rápidamente
- Equipos distribuidos/remotos
- Presupuesto inicial limitado

**Proveedor sugerido:** Twilio o Telnyx (documentación clara, APIs robustas)

### Caso 2: Empresa con Líneas Existentes
**Recomendación: Gateway FXO**
- Ya tiene líneas telefónicas contratadas
- Números conocidos por clientes
- Evitar cambio de números
- Internet poco confiable

**Hardware sugerido:** Grandstream GXW4104 (4 líneas) o GXW4108 (8 líneas)

### Caso 3: Híbrido (Redundancia)
**Recomendación: Ambos**
- Gateway FXO como línea principal
- SIP Trunk como respaldo/overflow
- Asterisk configura failover automático

```
Llamada entrante → Gateway FXO (primario)
                       │
                       ├── Si líneas ocupadas → SIP Trunk (overflow)
                       │
                       └── Si Gateway falla → SIP Trunk (failover)
```

### Caso 4: Call Center Alto Volumen (>8 líneas simultáneas)
**Recomendación: SIP Trunk o Tarjeta E1/PRI**
- Gateway FXO limitado a ~24 líneas
- SIP Trunk escala sin límite
- Considerar Tarjeta Sangoma A104 para E1/PRI

---

## Configuración del Wizard

El asistente de configuración (`/setup`) en el dashboard permite configurar cualquiera de las dos opciones de forma visual:

### Paso 1: Seleccionar Tipo de Conexión
```
┌─────────────────────────────────────────┐
│  ¿Cómo deseas conectar la telefonía?    │
│                                         │
│  ○ SIP Trunk (Líneas por Internet)      │
│  ○ Gateway FXO (Líneas Fijas Locales)   │
│  ○ Ambos (Configuración Híbrida)        │
│                                         │
└─────────────────────────────────────────┘
```

### Paso 2: Configurar Credenciales
**Para SIP Trunk:**
- Host del proveedor SIP
- Usuario y contraseña
- DID (número telefónico)

**Para Gateway FXO:**
- IP del Gateway en la red
- Usuario y contraseña configurados en Gateway
- Número de canales

### Paso 3: Prueba de Conexión
- El sistema verifica conectividad
- Muestra estado de registro SIP
- Permite llamada de prueba

---

## Troubleshooting

### SIP Trunk: Problemas Comunes

| Problema | Causa Probable | Solución |
|----------|---------------|----------|
| No registra | Firewall bloqueando | Abrir puertos 5060 UDP/TCP |
| Audio solo un sentido | NAT mal configurado | Configurar `force_rport=yes` |
| Calidad pobre | Ancho de banda insuficiente | Usar codec g729 o opus |
| Llamadas cortadas | Timeout SIP | Aumentar `session_timers` |

### Gateway FXO: Problemas Comunes

| Problema | Causa Probable | Solución |
|----------|---------------|----------|
| No detecta línea | Cable mal conectado | Verificar RJ11 en puerto FXO |
| No recibe CallerID | Formato incorrecto | Configurar "Call Progress Tone" del país |
| Eco en llamadas | Cancelación deshabilitada | Activar "Echo Cancellation" en Gateway |
| Gateway no responde | IP incorrecta | Verificar IP con `arp -a` |

---

## Anexo: Scripts de Documentación

El proyecto incluye scripts para generar documentación en formato PDF:

### Script: Generar PDF de Documentación

```bash
# scripts/generate_docs_pdf.sh
# Genera PDFs de la documentación para entregar al cliente
```

**Documentos generados:**
- `REQUISITOS_CONEXION_TELEFONICA.pdf`
- `GUIA_INSTALACION.pdf`
- `API_REFERENCE.pdf`
- `TERMINOS_USO_API.pdf`

---

## Soporte

Para asistencia con la configuración:

- **Documentación:** Ver archivos `README_*.md` en el repositorio
- **Wizard:** Acceder a `/setup` en el dashboard
- **Logs:** `docker-compose logs -f asterisk`
- **Estado SIP:** `docker exec asterisk asterisk -rx "pjsip show registrations"`

---

**Versión:** 1.0
**Última actualización:** 2026-02-05
