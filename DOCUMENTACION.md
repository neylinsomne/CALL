# Documentación Principal - AI Call Center

## Índice General

Este documento sirve como guía de navegación para toda la documentación del proyecto AI Call Center.

---

## Mapa de Documentación

```
                              DOCUMENTACIÓN AI CALL CENTER
                              ════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                            1. INICIO RÁPIDO                                  │
│                         README.md (Este archivo)                             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│   2. INSTALACIÓN      │ │    3. TELEFONÍA       │ │    4. IA / VOZ        │
│   Y CONFIGURACIÓN     │ │    Y CONECTIVIDAD     │ │    Y ENTRENAMIENTO    │
└───────────┬───────────┘ └───────────┬───────────┘ └───────────┬───────────┘
            │                         │                         │
            ▼                         ▼                         ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│ • README_SISTEMA_     │ │ • REQUISITOS_CONEXION │ │ • MODELOS_TRATAMIENTO │
│   COMPLETO            │ │ • network-setup/      │ │ • ACTIVAR_VOZ_        │
│ • GUIA_WIZARD         │ │ • INTEGRACION_FREEPBX │ │   CONTEXTUAL          │
│ • ARQUITECTURA        │ │ • SEGURIDAD_CIFRADO   │ │ • voice_distillation/ │
└───────────────────────┘ └───────────────────────┘ └───────────────────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │     5. SEGURIDAD Y LICENCIAS      │
                    │   • README_SEGURIDAD              │
                    │   • README_LICENCIAS              │
                    │   • PROTECCION_CODIGO             │
                    └───────────────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │     6. PRODUCCIÓN Y ESCALA        │
                    │   • ARQUITECTURA_Y_ESCALABILIDAD  │
                    │   • README_MULTI_TENANCY          │
                    │   • build_for_client.sh           │
                    └───────────────────────────────────┘
```

---

## 1. Inicio Rápido

| Documento | Descripción | Prioridad |
|-----------|-------------|-----------|
| [README.md](README.md) | Inicio rápido, estructura del proyecto, requisitos mínimos | **Leer primero** |
| [README_SISTEMA_COMPLETO.md](README_SISTEMA_COMPLETO.md) | Visión general completa del sistema | Esencial |

---

## 2. Instalación y Configuración

### 2.1 Configuración Inicial

| Documento | Descripción |
|-----------|-------------|
| [GUIA_WIZARD_CONFIGURACION.md](GUIA_WIZARD_CONFIGURACION.md) | Guía del asistente de configuración en el dashboard |
| [README_WIZARD.md](README_WIZARD.md) | Referencia técnica del wizard |
| [README_WIZARD_SEGURIDAD.md](README_WIZARD_SEGURIDAD.md) | Configuración de seguridad en el wizard |

### 2.2 Arquitectura del Sistema

| Documento | Descripción |
|-----------|-------------|
| [ARQUITECTURA_Y_ESCALABILIDAD.md](ARQUITECTURA_Y_ESCALABILIDAD.md) | Diseño de arquitectura, escalabilidad, patrones |
| [ARQUITECTURA_AVANZADA_ARI.md](ARQUITECTURA_AVANZADA_ARI.md) | Arquitectura de Asterisk REST Interface |

### 2.3 Variables de Entorno

| Archivo | Descripción |
|---------|-------------|
| [.env.example](.env.example) | Template de todas las variables de configuración |

---

## 3. Telefonía y Conectividad

### 3.1 Conexión de Red / NAT (¡Leer primero!)

| Documento | Descripción |
|-----------|-------------|
| [REQUISITOS_CONEXION_TELEFONICA.md](REQUISITOS_CONEXION_TELEFONICA.md) | **SIP Trunk vs Gateway FXO** - Opciones de conexión |
| [docs/network-setup/README.md](docs/network-setup/README.md) | Guía completa de configuración NAT |
| [docs/network-setup/CHECKLIST.md](docs/network-setup/CHECKLIST.md) | Lista de verificación para deployment |
| [docs/network-setup/guides/router-generic.md](docs/network-setup/guides/router-generic.md) | Configuración de router genérico |
| [docs/network-setup/guides/router-mikrotik.md](docs/network-setup/guides/router-mikrotik.md) | Configuración específica Mikrotik |

### 3.2 Asterisk y FreePBX

| Documento | Descripción |
|-----------|-------------|
| [GUIA_INSTALACION_FREEPBX_ARI.md](GUIA_INSTALACION_FREEPBX_ARI.md) | Instalación paso a paso de FreePBX + ARI |
| [INTEGRACION_FREEPBX_ARI_GATEWAY.md](INTEGRACION_FREEPBX_ARI_GATEWAY.md) | Integración completa con Gateway/DAHDI |
| [README_INTEGRACION_FREEPBX.md](README_INTEGRACION_FREEPBX.md) | Referencia rápida de integración |

### 3.3 Seguridad VoIP

| Documento | Descripción |
|-----------|-------------|
| [SEGURIDAD_CIFRADO_SIP.md](SEGURIDAD_CIFRADO_SIP.md) | TLS, SRTP, certificados para SIP seguro |

---

## 4. Inteligencia Artificial y Voz

### 4.1 Modelos de Voz (TTS/STT)

| Documento | Descripción |
|-----------|-------------|
| [MODELOS_TRATAMIENTO_VOZ.md](MODELOS_TRATAMIENTO_VOZ.md) | Comparativa de modelos de voz disponibles |
| [ACTIVAR_VOZ_CONTEXTUAL.md](ACTIVAR_VOZ_CONTEXTUAL.md) | Activación de voz contextual/emotiva |
| [MANEJO_VOZ_Y_CONTEXTO.md](MANEJO_VOZ_Y_CONTEXTO.md) | Manejo avanzado de contexto en conversaciones |

### 4.2 Speech-to-Text (STT)

| Documento | Descripción |
|-----------|-------------|
| [ACTIVAR_STT_MEJORADO.md](ACTIVAR_STT_MEJORADO.md) | Activación de mejoras en transcripción |
| [OPTIMIZACION_STT_ESTADO_DEL_ARTE.md](OPTIMIZACION_STT_ESTADO_DEL_ARTE.md) | Optimizaciones avanzadas de STT |
| [METODOS_CLASIFICACION_ERRORES.md](METODOS_CLASIFICACION_ERRORES.md) | Clasificación y corrección de errores |

### 4.3 Voice Distillation (Clonación de Voz)

| Documento | Descripción |
|-----------|-------------|
| [services/voice_distillation/README.md](services/voice_distillation/README.md) | Pipeline F5-TTS → Kokoro para voces personalizadas |
| [services/training/README.md](services/training/README.md) | Corpus Sharvard y entrenamiento |

### 4.4 Procesamiento Híbrido

| Documento | Descripción |
|-----------|-------------|
| [SISTEMA_HIBRIDO_ONLINE_OFFLINE.md](SISTEMA_HIBRIDO_ONLINE_OFFLINE.md) | Procesamiento online + offline |
| [INICIO_RAPIDO_SISTEMA_HIBRIDO.md](INICIO_RAPIDO_SISTEMA_HIBRIDO.md) | Quick start del sistema híbrido |

---

## 5. Seguridad y Licencias

### 5.1 Seguridad General

| Documento | Descripción |
|-----------|-------------|
| [README_SEGURIDAD.md](README_SEGURIDAD.md) | Guía completa de seguridad |
| [SEGURIDAD_CIFRADO_SIP.md](SEGURIDAD_CIFRADO_SIP.md) | Cifrado de comunicaciones SIP |

### 5.2 Sistema de Licencias

| Documento | Descripción |
|-----------|-------------|
| [README_LICENCIAS.md](README_LICENCIAS.md) | Sistema de licencias para clientes |
| [GUIA_SISTEMA_LICENCIAS.md](GUIA_SISTEMA_LICENCIAS.md) | Guía de implementación de licencias |

### 5.3 Protección del Código

| Documento | Descripción |
|-----------|-------------|
| [PROTECCION_CODIGO_ONPREMISE.md](PROTECCION_CODIGO_ONPREMISE.md) | Ofuscación y protección para on-premise |

---

## 6. Producción y Escalabilidad

### 6.1 Arquitectura de Producción

| Documento | Descripción |
|-----------|-------------|
| [ARQUITECTURA_Y_ESCALABILIDAD.md](ARQUITECTURA_Y_ESCALABILIDAD.md) | Patrones de escalabilidad |
| [README_MULTI_TENANCY.md](README_MULTI_TENANCY.md) | Arquitectura multi-tenant |

### 6.2 Build para Clientes

| Archivo | Descripción |
|---------|-------------|
| [scripts/build_for_client.sh](scripts/build_for_client.sh) | Script de build para deployments on-premise |
| [scripts/generate_docs_pdf.sh](scripts/generate_docs_pdf.sh) | Generador de PDFs de documentación |

### 6.3 Fases Pendientes

| Documento | Descripción |
|-----------|-------------|
| [FASES_PENDIENTES.md](FASES_PENDIENTES.md) | Roadmap y fases futuras |
| [MEJORAS_IMPLEMENTADAS.md](MEJORAS_IMPLEMENTADAS.md) | Historial de mejoras |
| [RESUMEN_MEJORAS_COMPLETAS.md](RESUMEN_MEJORAS_COMPLETAS.md) | Resumen consolidado |

---

## 7. Servicios Internos

| Servicio | README | Descripción |
|----------|--------|-------------|
| Backend | `services/backend/` | API FastAPI + WebSocket |
| TTS | `services/tts/` | F5-TTS / Kokoro |
| STT | `services/stt/` | Faster-Whisper |
| LLM | `services/llm/` | LangChain + LM Studio |
| Asterisk | `services/asterisk/` | PBX VoIP |
| Voice Distillation | [services/voice_distillation/README.md](services/voice_distillation/README.md) | Pipeline de clonación |
| Training | [services/training/README.md](services/training/README.md) | Corpus y entrenamiento |
| Quotation | [services/quotation/README.md](services/quotation/README.md) | Sistema de cotizaciones |

---

## Flujo de Lectura Recomendado

### Para Nuevos Usuarios

```
1. README.md                          → Visión general
2. REQUISITOS_CONEXION_TELEFONICA.md  → Elegir SIP Trunk o Gateway
3. docs/network-setup/README.md       → Configurar NAT
4. GUIA_WIZARD_CONFIGURACION.md       → Usar el wizard
5. README_SEGURIDAD.md                → Asegurar el sistema
```

### Para Desarrolladores

```
1. README_SISTEMA_COMPLETO.md         → Arquitectura completa
2. ARQUITECTURA_Y_ESCALABILIDAD.md    → Patrones de diseño
3. INTEGRACION_FREEPBX_ARI_GATEWAY.md → Integración Asterisk
4. services/voice_distillation/README → Pipeline de voz
```

### Para Operaciones / DevOps

```
1. docs/network-setup/CHECKLIST.md    → Verificar red
2. README_LICENCIAS.md                → Sistema de licencias
3. scripts/build_for_client.sh        → Build para clientes
4. PROTECCION_CODIGO_ONPREMISE.md     → Proteger código
```

### Para Clientes On-Premise

```
1. REQUISITOS_CONEXION_TELEFONICA.md  → Requisitos de red
2. docs/network-setup/CHECKLIST.md    → Checklist de configuración
3. README_WIZARD.md                   → Configuración inicial
4. README_SEGURIDAD.md                → Buenas prácticas
```

---

## Scripts Útiles

| Script | Ubicación | Descripción |
|--------|-----------|-------------|
| `network-diagnostic.sh` | `docs/network-setup/scripts/` | Diagnóstico completo de red |
| `test-latency.sh` | `docs/network-setup/scripts/` | Test de latencia VoIP |
| `check-ports.sh` | `docs/network-setup/scripts/` | Verificar puertos abiertos |
| `build_for_client.sh` | `scripts/` | Build para deployment |
| `generate_docs_pdf.sh` | `scripts/` | Generar PDFs |

---

## Estructura de Carpetas

```
c:\dev\Call\
├── docs/
│   └── network-setup/          # Documentación de red/NAT
│       ├── README.md
│       ├── CHECKLIST.md
│       ├── guides/             # Guías por router
│       ├── scripts/            # Scripts de diagnóstico
│       └── templates/          # Templates de configuración
│
├── scripts/                    # Scripts de build y utilidades
│
├── services/
│   ├── asterisk/              # Configuración Asterisk
│   ├── backend/               # API FastAPI
│   ├── dashboard/             # React Dashboard
│   ├── llm/                   # Servicio LLM
│   ├── stt/                   # Speech-to-Text
│   ├── tts/                   # Text-to-Speech
│   ├── voice_distillation/    # Pipeline de voces
│   └── training/              # Entrenamiento
│
├── shared/
│   ├── audio/                 # Audio compartido
│   └── models/                # Modelos compartidos
│
├── .env.example               # Template de configuración
├── docker-compose.yml         # Orquestación Docker
├── DOCUMENTACION.md           # ← ESTE ARCHIVO
└── *.md                       # Documentación temática
```

---

## Convenciones de Nombres

| Prefijo | Significado |
|---------|-------------|
| `README_*` | Documentación principal de un tema |
| `GUIA_*` | Guía paso a paso |
| `ARQUITECTURA_*` | Documentación de arquitectura |
| `ACTIVAR_*` | Cómo activar una característica |
| `SEGURIDAD_*` | Relacionado con seguridad |
| `REQUISITOS_*` | Requisitos previos |

---

## Soporte y Contacto

- **Issues:** [github.com/tu-repo/issues](https://github.com/tu-repo/issues)
- **Documentación Online:** [docs.callcenter-ai.com](https://docs.callcenter-ai.com)
- **Email:** support@callcenter-ai.com

---

**Última actualización:** 2026-02-08
**Versión de documentación:** 1.0
