# Integración FreePBX + ARI + Gateway/Tarjetas Digium

## Descripción General

Este documento detalla la integración de **FreePBX**, **Asterisk REST Interface (ARI)** mejorado, y soporte para **líneas fijas** (PSTN) mediante Gateway FXO/FXS o tarjetas PCIe Digium en tu sistema de Call Center con IA.

---

## Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────────┐
│                     ENTRADA DE LLAMADAS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  SIP TRUNK   │  │   Gateway    │  │  Tarjeta Digium     │   │
│  │  (Internet)  │  │  FXO/FXS     │  │  PCIe (DAHDI)       │   │
│  │              │  │  (Línea fija)│  │  (Líneas analógicas)│   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────────────┘   │
│         │                 │                  │                   │
└─────────┼─────────────────┼──────────────────┼───────────────────┘
          │                 │                  │
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ASTERISK PBX                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • PJSIP (SIP Trunks + Gateway VoIP)                      │  │
│  │  • DAHDI (Tarjetas Digium - Líneas analógicas/digitales)  │  │
│  │  • AudioSocket (Streaming a Backend IA)                   │  │
│  │  • AMI (Asterisk Manager Interface)                       │  │
│  │  • ARI (Asterisk REST Interface)                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────┬────────────────────────┬─────────────────────────┘
               │                        │
               │                        │
       ┌───────▼──────┐        ┌───────▼──────────┐
       │   FreePBX    │        │  Backend FastAPI │
       │  (Web GUI)   │        │   (Control ARI)  │
       │              │        │                  │
       │ • Gestión PBX│        │ • WebSocket      │
       │ • IVR        │        │ • STT/TTS/LLM    │
       │ • Rutas      │        │ • AudioSocket    │
       │ • Extensiones│        │ • ARI Control    │
       └──────────────┘        └──────────────────┘
               │                        │
               │                        │
       ┌───────▼────────────────────────▼─────┐
       │        MariaDB / PostgreSQL          │
       │  • FreePBX Config (MariaDB)          │
       │  • Call Logs (PostgreSQL)            │
       └──────────────────────────────────────┘
```

---

## Componentes de la Integración

### 1. FreePBX (Interfaz de Gestión)

**¿Qué es?**
- Interfaz web para administrar Asterisk sin editar archivos de configuración
- Gestión visual de extensiones, rutas, IVR, colas, etc.

**¿Para qué lo necesitas?**
- Configurar fácilmente el Gateway FXO/FXS y tarjetas Digium
- Gestionar rutas de llamadas entrantes/salientes
- Monitoreo en tiempo real de llamadas activas
- Configuración de IVR y menús telefónicos

**Requerimientos:**
- MariaDB (base de datos para FreePBX)
- Apache/Nginx + PHP
- Asterisk con módulos AMI y ARI habilitados

---

### 2. Asterisk REST Interface (ARI) Mejorado

**Estado Actual:**
Tu configuración actual de ARI es básica ([ari.conf](services/asterisk/config/ari.conf)):
```ini
[general]
enabled=yes
pretty=yes

[asterisk]
type=user
read_only=no
password=asterisk
```

**Mejoras Necesarias:**
- Configurar WebSocket para eventos en tiempo real
- Configurar aplicaciones ARI específicas para tu backend
- Habilitar CORS para acceso desde dashboard
- Configurar múltiples usuarios ARI con permisos granulares

**Casos de Uso ARI en tu Sistema:**
1. **Control programático de llamadas** desde tu backend Python
2. **Eventos en tiempo real** (llamada entrante, colgado, DTMF, etc.)
3. **Bridges dinámicos** (unir/separar llamadas)
4. **Grabación selectiva** de llamadas
5. **Transferencias programáticas** a agente humano
6. **Generación de llamadas outbound** desde tu API

---

### 3. Soporte para Líneas Fijas (PSTN)

Hay **dos opciones** para conectar líneas telefónicas fijas:

#### Opción A: Gateway VoIP FXO/FXS (Recomendado para empezar)

**¿Qué es?**
- Dispositivo externo que convierte líneas analógicas en SIP
- Se conecta a Asterisk como un endpoint SIP normal

**Ejemplos:**
- **Grandstream GXW4104** (4 puertos FXO - para líneas entrantes)
- **Cisco SPA112** (2 puertos FXS - para teléfonos analógicos)
- **Dinstar MTG** (hasta 32 puertos)

**Ventajas:**
- No requiere hardware especial en el servidor
- Fácil configuración (solo PJSIP)
- Puede estar físicamente separado del servidor

**Configuración:**
Se configura en PJSIP como un trunk más:
```ini
[gateway-fxo]
type=endpoint
transport=transport-udp
context=from-pstn
aors=gateway-fxo-aor
auth=gateway-fxo-auth
disallow=all
allow=ulaw
allow=alaw
direct_media=no

[gateway-fxo-auth]
type=auth
auth_type=userpass
username=gateway
password=tu_password

[gateway-fxo-aor]
type=aor
contact=sip:192.168.1.100:5060
qualify_frequency=30
```

#### Opción B: Tarjetas PCIe Digium/Sangoma (Para producción)

**¿Qué es?**
- Tarjeta PCIe que se instala en el servidor
- Se conecta directamente a líneas analógicas (FXO/FXS) o digitales (E1/T1/PRI)

**Modelos Compatibles:**
- **Sangoma A200/A400** (Analog FXO/FXS - 2 a 24 puertos)
- **Digium TDM400P** (legacy)
- **Sangoma A104** (Digital E1/T1/PRI - 4 puertos)

**Ventajas:**
- Mejor calidad de voz
- Menor latencia
- Más escalable (hasta 120 canales simultáneos)
- Detección de tono de marcado

**Requerimientos:**
- Driver DAHDI (Digium Asterisk Hardware Device Interface)
- Kernel Linux con módulos DAHDI compilados
- Acceso directo al hardware del servidor (no funciona bien en VM)

**Configuración:**
Requiere configurar DAHDI + chan_dahdi en Asterisk:
```ini
; /etc/dahdi/system.conf
fxsks=1-4  # 4 puertos FXO (líneas entrantes)

; /etc/asterisk/chan_dahdi.conf
[channels]
context=from-pstn
signalling=fxs_ks
channel => 1-4
```

**IMPORTANTE:** Si usas Docker, necesitarás:
- Acceso privilegiado al contenedor (`--privileged`)
- Mapear dispositivos DAHDI (`--device /dev/dahdi`)
- Compilar módulos DAHDI en el host

---

## Comparación: Gateway vs Tarjeta PCIe

| Característica | Gateway FXO/FXS | Tarjeta Digium PCIe |
|----------------|-----------------|---------------------|
| **Instalación** | Plug & Play, red | Requiere slot PCIe |
| **Configuración** | PJSIP (fácil) | DAHDI + chan_dahdi |
| **Docker** | Compatible | Requiere privilegios |
| **Costo** | $100-500 | $300-2000+ |
| **Escalabilidad** | Limitado (4-32 líneas) | Alto (120+ canales) |
| **Latencia** | ~10-30ms más | Mínima |
| **Mantenimiento** | Bajo | Medio |
| **Uso Recomendado** | Oficinas pequeñas | Call centers grandes |

**Recomendación para tu caso:**
- Si tienes **1-8 líneas fijas**: Usa **Gateway** (Grandstream GXW4104/4108)
- Si tienes **más de 8 líneas** o **líneas digitales E1/PRI**: Usa **Tarjeta Digium/Sangoma**

---

## Flujo de Llamadas con la Nueva Integración

### Llamada Entrante (PSTN → AI)

```
Línea Fija → Gateway FXO → Asterisk PJSIP
                                │
                                ▼
                        [from-pstn context]
                                │
                                ▼
                        Validación de caller ID
                                │
                                ▼
                        AudioSocket → Backend IA
                                │
                                ▼
                        STT → LLM → TTS
                                │
                                ▼
                        AudioSocket → Asterisk
                                │
                                ▼
                        Gateway → Línea Fija → Cliente
```

### Llamada Saliente (AI → PSTN)

```
Backend API → ARI Channel Originate
                    │
                    ▼
            Asterisk crea canal DAHDI/PJSIP
                    │
                    ▼
            Gateway FXO marca número PSTN
                    │
                    ▼
            Cliente contesta → AudioSocket IA
```

### Transferencia a Agente Humano

```
Cliente en llamada con IA
        │
        ▼
Usuario dice "hablar con agente"
        │
        ▼
LLM detecta intención → Backend
        │
        ▼
Backend llama ARI → Bridge
        │
        ▼
Asterisk: Bridge(canal_cliente, extension_200)
        │
        ▼
Cola de agentes humanos (Queue)
        │
        ▼
Agente disponible → Conectado
```

---

## Plan de Implementación

### Fase 1: Preparación de Infraestructura

1. **Añadir MariaDB al docker-compose.yml**
2. **Añadir FreePBX como contenedor**
3. **Configurar volúmenes persistentes**

### Fase 2: Configuración de Asterisk

1. **Habilitar módulos necesarios** (AMI, ARI mejorado, chan_dahdi si aplica)
2. **Configurar AMI** (manager.conf)
3. **Mejorar ARI** (websocket, aplicaciones)
4. **Configurar http.conf** para FreePBX

### Fase 3: Integración FreePBX

1. **Instalar FreePBX** en contenedor
2. **Conectar a Asterisk vía AMI**
3. **Importar configuración existente**
4. **Configurar permisos**

### Fase 4: Configuración de Gateway/Tarjetas

**Si usas Gateway FXO:**
1. Conectar Gateway a red y líneas telefónicas
2. Configurar Gateway (IP, SIP credentials)
3. Añadir endpoint en pjsip.conf
4. Crear rutas en extensions.conf

**Si usas Tarjeta Digium:**
1. Instalar tarjeta en servidor
2. Instalar drivers DAHDI en host
3. Configurar /etc/dahdi/system.conf
4. Configurar chan_dahdi.conf
5. Modificar Dockerfile Asterisk para DAHDI
6. Mapear dispositivos en docker-compose

### Fase 5: Integración ARI con Backend

1. **Crear cliente ARI en Python** (biblioteca: `ari-py`)
2. **Subscribirse a eventos WebSocket**
3. **Implementar handlers** para eventos (StasisStart, ChannelHangup, etc.)
4. **Integrar con flujo actual** de AudioSocket

### Fase 6: Pruebas

1. Llamada entrante desde PSTN → AI
2. Llamada saliente desde AI → PSTN
3. Transferencia a agente humano
4. Llamada directa entre extensiones
5. Gestión desde FreePBX

---

## Archivos de Configuración Necesarios

A continuación se listan los archivos que necesitarás crear o modificar:

### 1. docker-compose.yml (añadir servicios)
- MariaDB para FreePBX
- FreePBX container

### 2. services/asterisk/config/manager.conf
- Configuración AMI para FreePBX

### 3. services/asterisk/config/ari.conf (mejorado)
- Websocket habilitado
- Múltiples aplicaciones ARI

### 4. services/asterisk/config/http.conf
- HTTP server para FreePBX y ARI

### 5. services/asterisk/config/pjsip.conf.template (añadir)
- Endpoints para Gateway FXO/FXS

### 6. services/asterisk/config/chan_dahdi.conf (si usas tarjeta)
- Configuración de canales DAHDI

### 7. services/asterisk/config/extensions.conf.template (modificar)
- Nuevo contexto [from-pstn] para llamadas de línea fija
- Rutas para llamadas salientes a PSTN

### 8. services/backend/ari_client.py (nuevo)
- Cliente Python para ARI
- Event handlers

### 9. .env (añadir variables)
- Configuración de Gateway
- Credenciales FreePBX

---

## Próximos Pasos

Necesito que confirmes algunas cosas antes de continuar con la implementación:

### Preguntas Clave:

1. **¿Cuántas líneas fijas necesitas conectar?**
   - 1-4 líneas → Gateway simple
   - 5-8 líneas → Gateway multipuerto
   - Más de 8 → Considerar tarjeta Digium

2. **¿Ya tienes el hardware?**
   - ¿Tienes un Gateway? (marca/modelo)
   - ¿Tienes tarjeta Digium instalada?
   - ¿O necesitas recomendaciones?

3. **¿Tipo de líneas?**
   - Analógicas (FXO/FXS)
   - Digitales (E1/T1/PRI)

4. **¿Docker o instalación nativa?**
   - ¿Quieres seguir usando Docker? (más fácil con Gateway)
   - ¿O prefieres instalación nativa? (necesario para tarjetas Digium)

5. **¿Servidor físico o VM?**
   - Las tarjetas PCIe funcionan mejor en servidores físicos
   - Los Gateways funcionan igual en ambos

6. **¿Quieres FreePBX?**
   - Para gestión visual y simplificar configuración → Sí
   - Solo programático vía ARI → No (más ligero)

---

## Recursos Adicionales

### Documentación Oficial:
- [FreePBX System Requirements](https://www.freepbx.org/get-started/)
- [Asterisk ARI Getting Started](https://docs.asterisk.org/Configuration/Interfaces/Asterisk-REST-Interface-ARI/Getting-Started-with-ARI/)
- [Sangoma DAHDI](https://www.freepbx.org/sngfd12/)
- [ARI API Reference](https://docs.asterisk.org/Asterisk_18_Documentation/API_Documentation/Asterisk_REST_Interface/)

### Bibliotecas Python:
- **ari-py**: Cliente oficial ARI para Python
  ```bash
  pip install ari
  ```

### Ejemplos de Código ARI:
```python
import ari

# Conectar a ARI
client = ari.connect('http://localhost:8088', 'asterisk', 'asterisk')

# Subscribirse a eventos
def on_start(channel, event):
    print(f"Llamada entrante de {channel.json['caller']['number']}")
    channel.answer()
    channel.play(media='sound:welcome')

client.on_channel_event('StasisStart', on_start)
client.run(apps='callcenter-ai')
```

---

## Autor
Integración diseñada para el sistema de Call Center con IA
Fecha: 2026-01-29
