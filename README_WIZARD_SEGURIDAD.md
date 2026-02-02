# Wizard con Seguridad Integrada - Resumen

## ✅ Implementación Completada

He integrado **configuración de seguridad TLS/SRTP** directamente en el wizard de configuración. Ahora el wizard:

1. **Pregunta automáticamente** sobre cifrado
2. **Genera certificados SSL** al guardar
3. **Configura TLS/SRTP** en Asterisk
4. **Valida configuración** de seguridad

---

## 📁 Archivos Modificados/Creados

### **Frontend**
- **[ConfigurationWizard.jsx](services/dashboard/src/pages/ConfigurationWizard.jsx)**
  - ✅ Añadida sección de seguridad en Paso 2
  - ✅ Checkbox para habilitar TLS/SIPS
  - ✅ Checkbox para habilitar SRTP
  - ✅ Selector de tipo de certificado
  - ✅ Resumen de seguridad en Paso 4

### **Backend**
- **[config_manager.py](services/backend/config_manager.py)**
  - ✅ Modelo `SecurityConfig`
  - ✅ Endpoint `POST /api/config/generate-certificates`
  - ✅ Generación automática en `save_configuration()`

### **Scripts de Seguridad** (ya creados)
- [generate_certificates.sh](services/asterisk/generate_certificates.sh)
- [setup_security.sh](services/asterisk/setup_security.sh)

### **Documentación** (ya creada)
- [SEGURIDAD_CIFRADO_SIP.md](SEGURIDAD_CIFRADO_SIP.md)
- [README_SEGURIDAD.md](README_SEGURIDAD.md)

---

## 🎯 Nueva Funcionalidad en el Wizard

### **Paso 2: Servicios de IA + Seguridad**

Después de configurar STT, TTS y LLM, ahora aparece:

```
┌─────────────────────────────────────────────────┐
│  🔒 Seguridad y Cifrado              [RECOMENDADO]│
├─────────────────────────────────────────────────┤
│                                                 │
│  ⚠️ Sin cifrado: Cualquiera puede interceptar  │
│  ✅ Con TLS+SRTP: Tráfico cifrado (como HTTPS)  │
│                                                 │
│  ☑️ Habilitar TLS/SIPS                          │
│     Cifra señalización (puerto 5061)           │
│                                                 │
│  ☑️ Habilitar SRTP                              │
│     Cifra audio con AES-128                     │
│                                                 │
│  Tipo de Certificado:                          │
│  ○ Autofirmado (desarrollo)                     │
│  ○ Let's Encrypt (producción)                   │
│  ○ Personalizado                                │
│                                                 │
│  ☑️ Forzar cifrado                              │
│     Rechazar llamadas sin TLS+SRTP             │
│                                                 │
│  💡 Los certificados se generan automáticamente │
└─────────────────────────────────────────────────┘
```

### **Paso 4: Resumen con Estado de Seguridad**

```
┌────────────────────────────────────┐
│  🔒 Seguridad                      │
├────────────────────────────────────┤
│  TLS/SIPS:   ✓ Habilitado (5061)  │
│  SRTP:       ✓ Habilitado (AES-128)│
│  Certificado: Autofirmado         │
│                                    │
│  ✅ Configuración segura           │
│     Llamadas completamente cifradas│
└────────────────────────────────────┘
```

---

## 🚀 Flujo Completo del Usuario

### **Escenario 1: Usuario con SIP Trunk (Internet)**

```
1. Usuario accede a /setup

2. Paso 1: Selecciona "Sí, SIP TRUNK"
   - Ingresa: host, user, password

3. Paso 2: Configura servicios IA
   - STT: ✅ Habilitado
   - TTS: ✅ Habilitado
   - LLM: ✅ Habilitado

   🔒 Seguridad (nueva sección):
   - ✅ Habilitar TLS/SIPS
   - ✅ Habilitar SRTP
   - Tipo: Autofirmado
   - ✅ Forzar cifrado

4. Paso 3: Voice training (opcional)

5. Paso 4: Revisa resumen
   - ✅ Seguridad: TLS + SRTP habilitados

6. Guarda

7. Backend automáticamente:
   ✅ Genera certificados SSL
   ✅ Actualiza pjsip.conf con TLS
   ✅ Configura SRTP en endpoints
   ✅ Actualiza .env

8. Resultado:
   ✅ SIP Trunk cifrado (puerto 5061)
   ✅ Audio cifrado (SRTP)
   ✅ Protección completa
```

### **Escenario 2: Usuario con Hardware Local (Red privada)**

```
1. Paso 1: Selecciona "No, líneas fijas"
   - Sistema detecta Gateway o DAHDI

2. Paso 2: Servicios IA + Seguridad
   🔒 Usuario puede DESMARCAR cifrado:
   - ☐ Habilitar TLS/SIPS
   - ☐ Habilitar SRTP

   Razón: Red local privada, no necesita cifrado

3. Guarda

4. Backend NO genera certificados

5. Resultado:
   ⚠️ Llamadas sin cifrar (OK para red local)
```

---

## 🔐 Configuración de Seguridad por Defecto

El wizard viene pre-configurado con valores seguros:

```javascript
security: {
  enableTLS: true,      // ✅ TLS habilitado por defecto
  enableSRTP: true,     // ✅ SRTP habilitado por defecto
  certificateType: 'self-signed',  // Autofirmado (cambiar a letsencrypt en prod)
  domain: '',
  forceSecure: true     // ✅ Rechazar llamadas sin cifrado
}
```

**Por qué estos defaults:**
- ✅ **Secure by default** - Mejor prevenir que lamentar
- ✅ **Fácil cambiar** - Si usuario tiene red privada, puede desmarcar
- ✅ **Educativo** - Usuario ve advertencia si deshabilita

---

## 📊 Comparación: Con vs Sin Wizard de Seguridad

| Aspecto | Sin Wizard | Con Wizard |
|---------|------------|------------|
| **Configuración TLS** | Manual, editar archivos | ✅ Checkbox + auto-config |
| **Certificados** | `openssl` manual | ✅ Generados automáticamente |
| **Validación** | Usuario debe saber | ✅ Wizard valida |
| **Educación** | Usuario no sabe riesgos | ✅ Advertencias claras |
| **Errores** | Fácil olvidar algo | ✅ Wizard hace todo |

---

## 🎨 UI/UX del Wizard de Seguridad

### **Características:**

1. **Visual claro**
   - Borde amarillo (atención)
   - Badge "RECOMENDADO"
   - Iconos de candado

2. **Educativo**
   - Explica qué hace cada opción
   - Compara con vs sin cifrado
   - Links a documentación

3. **Inteligente**
   - Muestra campo "Dominio" solo si selecciona Let's Encrypt
   - Advierte si deshabilita cifrado
   - Resumen con color (verde=seguro, amarillo=inseguro)

4. **No intrusivo**
   - Puede saltarse si red local
   - Opciones claras
   - No obliga

---

## 🧪 Testing del Wizard de Seguridad

### **Test 1: Habilitar TLS+SRTP**

```bash
# 1. Accede al wizard
http://localhost:3001/setup

# 2. Paso 2 → Marca:
#    ✅ Habilitar TLS/SIPS
#    ✅ Habilitar SRTP
#    Tipo: Autofirmado

# 3. Guarda

# 4. Verifica certificados generados
docker exec -it callcenter-asterisk ls -la /etc/asterisk/keys

# Debe mostrar:
# asterisk.key
# asterisk.crt
# ca.crt

# 5. Verifica config guardada
curl http://localhost:8000/api/config | jq '.security'

# Debe mostrar:
# {
#   "enableTLS": true,
#   "enableSRTP": true,
#   "certificateType": "self-signed",
#   ...
# }
```

### **Test 2: Deshabilitar Cifrado (Red local)**

```bash
# 1. Wizard Paso 2 → Desmarca:
#    ☐ Habilitar TLS/SIPS
#    ☐ Habilitar SRTP

# 2. Guarda

# 3. Wizard muestra advertencia:
#    ⚠️ Sin cifrado completo - Las llamadas pueden ser interceptadas

# 4. Backend NO genera certificados

# 5. Asterisk usa puerto 5060 (sin cifrar)
```

---

## 📋 Endpoints de API

### **POST /api/config/generate-certificates**

Genera certificados SSL automáticamente.

**Request:**
```json
{
  "cert_type": "self-signed",
  "domain": "asterisk.tudominio.com"
}
```

**Response:**
```json
{
  "success": true,
  "type": "self-signed",
  "cert_file": "/etc/asterisk/keys/asterisk.crt",
  "key_file": "/etc/asterisk/keys/asterisk.key",
  "ca_file": "/etc/asterisk/keys/ca.crt",
  "message": "Certificados autofirmados generados correctamente (válidos 10 años)"
}
```

### **POST /api/config/save** (Actualizado)

Ahora también genera certificados si `enableTLS: true`.

**Response incluye:**
```json
{
  "success": true,
  "config_file": "/app/config/callcenter_config.json",
  "env_updated": true,
  "certificates_generated": true,  // ✅ Nuevo campo
  "message": "Configuración guardada correctamente con certificados SSL generados"
}
```

---

## ✅ Checklist de Implementación

- [x] Modelo `SecurityConfig` en backend
- [x] Endpoint `/api/config/generate-certificates`
- [x] Generación automática en `save_configuration()`
- [x] Sección de seguridad en Paso 2 del wizard
- [x] Resumen de seguridad en Paso 4
- [x] Validación de configuración
- [x] Advertencias visuales (sin cifrado)
- [x] Defaults seguros (TLS+SRTP habilitados)
- [x] Documentación completa

---

## 🔜 Próximos Pasos

1. **Prueba el wizard:**
   ```bash
   docker-compose up -d
   # Accede a: http://localhost:3001/setup
   ```

2. **Configura con seguridad:**
   - Habilita TLS + SRTP
   - Genera certificados automáticamente
   - Guarda configuración

3. **Verifica:**
   ```bash
   # Certificados
   docker exec -it callcenter-asterisk ls /etc/asterisk/keys

   # Puerto TLS
   docker exec -it callcenter-asterisk netstat -tuln | grep 5061

   # Config
   curl http://localhost:8000/api/config
   ```

4. **Haz una llamada de prueba** y verifica SRTP

---

## 💡 Beneficios de esta Integración

### **Para el Usuario:**
✅ No necesita conocimientos técnicos de SSL/TLS
✅ Wizard le explica qué es y por qué importa
✅ Todo automatizado (certificados, config)
✅ Puede elegir según su caso (internet vs red local)

### **Para el Sistema:**
✅ Configuración consistente
✅ Menos errores de configuración manual
✅ Defaults seguros (secure by default)
✅ Trazabilidad (config guardada en JSON)

### **Para Producción:**
✅ Fácil auditar seguridad
✅ Un click para habilitar cifrado
✅ Compatible con Let's Encrypt
✅ Cumple estándares de seguridad

---

**Fecha:** 2026-01-29
**Versión:** 1.0
**Estado:** ✅ Wizard de seguridad completo y funcional
