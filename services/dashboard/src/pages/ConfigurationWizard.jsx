import React, { useState, useEffect } from 'react';
import {
  Settings,
  Phone,
  Wifi,
  HardDrive,
  Mic,
  Volume2,
  Brain,
  CheckCircle,
  AlertCircle,
  Loader,
  ArrowRight,
  ArrowLeft,
  ExternalLink
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Wizard de Configuración Inicial
 *
 * Flujo:
 * 1. ¿Usa SIP TRUNK?
 *    - Sí → Configuración manual
 *    - No → Detección automática de hardware
 * 2. Configurar servicios de IA (TTS, STT, LLM)
 * 3. Configurar entrenamiento de voz
 * 4. Resumen y guardar
 */
const ConfigurationWizard = () => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Estado de configuración
  const [config, setConfig] = useState({
    // Paso 1: Telefonía
    telephony: {
      useSipTrunk: null, // null | true | false
      sipTrunk: {
        host: '',
        user: '',
        password: '',
        outboundCallerId: ''
      },
      hardware: {
        type: null, // "gateway" | "dahdi" | "both" | "sip_only"
        gateway: {
          ip: '',
          user: '',
          password: ''
        },
        pstnChannels: 0
      }
    },

    // Paso 2: Servicios de IA
    aiServices: {
      stt: {
        enabled: true,
        port: 8002,
        model: 'large-v3',
        device: 'cuda',
        language: 'es'
      },
      tts: {
        enabled: true,
        port: 8001,
        model: 'jpgallegoar/F5-Spanish',
        device: 'cuda'
      },
      llm: {
        enabled: true,
        port: 8003,
        model: 'local-model',
        provider: 'lm-studio' // "lm-studio" | "openai" | "anthropic"
      }
    },

    // Paso 2.5: Seguridad (Cifrado)
    security: {
      enableTLS: true,
      enableSRTP: true,
      certificateType: 'self-signed', // "self-signed" | "letsencrypt" | "custom"
      domain: '',
      forceSecure: true // Rechazar llamadas sin cifrado
    },

    // Paso 3: Entrenamiento de voz
    voiceTraining: {
      enabled: false,
      referenceAudio: null,
      targetSpeaker: ''
    }
  });

  const [detectionResult, setDetectionResult] = useState(null);
  const [errors, setErrors] = useState({});

  // ============================================
  // PASO 1: DETECCIÓN DE HARDWARE
  // ============================================

  const detectHardware = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/config/detect-hardware`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) throw new Error('Error detectando hardware');

      const result = await response.json();
      setDetectionResult(result);

      // Actualizar config con resultado
      setConfig(prev => ({
        ...prev,
        telephony: {
          ...prev.telephony,
          hardware: {
            type: result.hardware_type,
            pstnChannels: result.pstn_channels,
            gateway: result.gateway_detected ? {
              ip: result.gateway_ip || '',
              user: 'gateway',
              password: ''
            } : prev.telephony.hardware.gateway
          }
        }
      }));

    } catch (error) {
      console.error('Error:', error);
      setErrors({ hardware: 'No se pudo detectar el hardware. Verifica la conexión.' });
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // VALIDACIÓN
  // ============================================

  const validateStep = (stepNumber) => {
    const newErrors = {};

    if (stepNumber === 1) {
      if (config.telephony.useSipTrunk === null) {
        newErrors.sipTrunk = 'Selecciona una opción';
      }

      if (config.telephony.useSipTrunk === true) {
        if (!config.telephony.sipTrunk.host) {
          newErrors.sipHost = 'El host del SIP trunk es requerido';
        }
        if (!config.telephony.sipTrunk.user) {
          newErrors.sipUser = 'El usuario es requerido';
        }
        if (!config.telephony.sipTrunk.password) {
          newErrors.sipPassword = 'La contraseña es requerida';
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(step)) {
      setStep(step + 1);
    }
  };

  const prevStep = () => {
    setStep(step - 1);
  };

  // ============================================
  // GUARDAR CONFIGURACIÓN
  // ============================================

  const saveConfiguration = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/config/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (!response.ok) throw new Error('Error guardando configuración');

      const result = await response.json();

      // Mostrar éxito y redirigir
      alert('✅ Configuración guardada correctamente');
      window.location.href = '/dashboard';

    } catch (error) {
      console.error('Error:', error);
      setErrors({ save: 'No se pudo guardar la configuración' });
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // RENDERIZADO POR PASOS
  // ============================================

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <Phone className="mx-auto h-12 w-12 text-blue-600" />
        <h2 className="mt-4 text-2xl font-bold text-gray-900">Configuración de Telefonía</h2>
        <p className="mt-2 text-gray-600">¿Cómo recibirás las llamadas?</p>
      </div>

      {/* Opción: ¿Usa SIP TRUNK? */}
      <div className="space-y-4">
        <label className="block text-sm font-medium text-gray-700">
          ¿Vas a usar SIP TRUNK (llamadas por internet)?
        </label>

        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setConfig(prev => ({
              ...prev,
              telephony: { ...prev.telephony, useSipTrunk: true }
            }))}
            className={`p-4 border-2 rounded-lg transition ${
              config.telephony.useSipTrunk === true
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-300 hover:border-blue-400'
            }`}
          >
            <Wifi className="mx-auto h-8 w-8 mb-2" />
            <div className="font-medium">Sí, SIP TRUNK</div>
            <div className="text-xs text-gray-500 mt-1">Llamadas por internet</div>
          </button>

          <button
            onClick={() => {
              setConfig(prev => ({
                ...prev,
                telephony: { ...prev.telephony, useSipTrunk: false }
              }));
              // Auto-detectar hardware
              detectHardware();
            }}
            className={`p-4 border-2 rounded-lg transition ${
              config.telephony.useSipTrunk === false
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-300 hover:border-blue-400'
            }`}
          >
            <HardDrive className="mx-auto h-8 w-8 mb-2" />
            <div className="font-medium">No, líneas fijas</div>
            <div className="text-xs text-gray-500 mt-1">Gateway o tarjeta DAHDI</div>
          </button>
        </div>

        {errors.sipTrunk && (
          <p className="text-red-600 text-sm">{errors.sipTrunk}</p>
        )}
      </div>

      {/* Formulario SIP TRUNK (si seleccionó Sí) */}
      {config.telephony.useSipTrunk === true && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900">Configuración de SIP Trunk</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Host del Proveedor SIP
            </label>
            <input
              type="text"
              placeholder="sip.proveedor.com"
              value={config.telephony.sipTrunk.host}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                telephony: {
                  ...prev.telephony,
                  sipTrunk: { ...prev.telephony.sipTrunk, host: e.target.value }
                }
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
            {errors.sipHost && <p className="text-red-600 text-sm mt-1">{errors.sipHost}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Usuario
              </label>
              <input
                type="text"
                placeholder="usuario_sip"
                value={config.telephony.sipTrunk.user}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  telephony: {
                    ...prev.telephony,
                    sipTrunk: { ...prev.telephony.sipTrunk, user: e.target.value }
                  }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
              {errors.sipUser && <p className="text-red-600 text-sm mt-1">{errors.sipUser}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contraseña
              </label>
              <input
                type="password"
                placeholder="••••••••"
                value={config.telephony.sipTrunk.password}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  telephony: {
                    ...prev.telephony,
                    sipTrunk: { ...prev.telephony.sipTrunk, password: e.target.value }
                  }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
              {errors.sipPassword && <p className="text-red-600 text-sm mt-1">{errors.sipPassword}</p>}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Caller ID Saliente (opcional)
            </label>
            <input
              type="text"
              placeholder="+1234567890"
              value={config.telephony.sipTrunk.outboundCallerId}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                telephony: {
                  ...prev.telephony,
                  sipTrunk: { ...prev.telephony.sipTrunk, outboundCallerId: e.target.value }
                }
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>
      )}

      {/* Link a configuración avanzada de telefonía */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-blue-900">Configuración Avanzada de Telefonía</p>
            <p className="text-xs text-blue-700 mt-1">
              Gateway FXO, Carrier Grade, DIDs, pruebas de conectividad y más
            </p>
          </div>
          <a
            href="/telephony"
            className="flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
          >
            Abrir
            <ExternalLink className="h-3 w-3 ml-1.5" />
          </a>
        </div>
      </div>

      {/* Resultado de detección de hardware (si seleccionó No) */}
      {config.telephony.useSipTrunk === false && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          {loading ? (
            <div className="text-center py-8">
              <Loader className="animate-spin mx-auto h-8 w-8 text-blue-600" />
              <p className="mt-2 text-gray-600">Detectando hardware...</p>
            </div>
          ) : detectionResult ? (
            <div>
              <div className="flex items-center mb-4">
                <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
                <h3 className="font-medium text-gray-900">Hardware Detectado</h3>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Tipo:</span>
                  <span className="font-medium">{detectionResult.hardware_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Canales PSTN:</span>
                  <span className="font-medium">{detectionResult.pstn_channels}</span>
                </div>
                {detectionResult.gateway_detected && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Gateway IP:</span>
                    <span className="font-medium">{detectionResult.gateway_ip}</span>
                  </div>
                )}
                {detectionResult.dahdi_detected && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">DAHDI Canales:</span>
                    <span className="font-medium">{detectionResult.dahdi_channels?.length || 0}</span>
                  </div>
                )}
              </div>

              {/* Configuración manual de Gateway si fue detectado */}
              {detectionResult.gateway_detected && (
                <div className="mt-4 space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Contraseña del Gateway
                  </label>
                  <input
                    type="password"
                    placeholder="Contraseña del gateway"
                    value={config.telephony.hardware.gateway.password}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      telephony: {
                        ...prev.telephony,
                        hardware: {
                          ...prev.telephony.hardware,
                          gateway: { ...prev.telephony.hardware.gateway, password: e.target.value }
                        }
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              )}
            </div>
          ) : errors.hardware ? (
            <div className="flex items-center text-red-600">
              <AlertCircle className="h-6 w-6 mr-2" />
              <p>{errors.hardware}</p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <Brain className="mx-auto h-12 w-12 text-blue-600" />
        <h2 className="mt-4 text-2xl font-bold text-gray-900">Servicios de IA</h2>
        <p className="mt-2 text-gray-600">Configuración de STT, TTS y LLM</p>
      </div>

      {/* STT (Speech-to-Text) */}
      <div className="p-4 border border-gray-300 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Mic className="h-6 w-6 text-blue-600 mr-2" />
            <h3 className="font-medium text-gray-900">Speech-to-Text (STT)</h3>
          </div>
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.aiServices.stt.enabled}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                aiServices: {
                  ...prev.aiServices,
                  stt: { ...prev.aiServices.stt, enabled: e.target.checked }
                }
              }))}
              className="mr-2"
            />
            <span className="text-sm">Habilitado</span>
          </label>
        </div>

        {config.aiServices.stt.enabled && (
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-gray-700 mb-1">Puerto</label>
                <input
                  type="number"
                  value={config.aiServices.stt.port}
                  readOnly
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-gray-700 mb-1">Dispositivo</label>
                <select
                  value={config.aiServices.stt.device}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    aiServices: {
                      ...prev.aiServices,
                      stt: { ...prev.aiServices.stt, device: e.target.value }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="cuda">CUDA (GPU)</option>
                  <option value="cpu">CPU</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-gray-700 mb-1">Modelo</label>
              <select
                value={config.aiServices.stt.model}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  aiServices: {
                    ...prev.aiServices,
                    stt: { ...prev.aiServices.stt, model: e.target.value }
                  }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="large-v3">Whisper Large V3 (Mejor calidad)</option>
                <option value="medium">Whisper Medium (Balanceado)</option>
                <option value="small">Whisper Small (Más rápido)</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* TTS (Text-to-Speech) */}
      <div className="p-4 border border-gray-300 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Volume2 className="h-6 w-6 text-blue-600 mr-2" />
            <h3 className="font-medium text-gray-900">Text-to-Speech (TTS)</h3>
          </div>
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.aiServices.tts.enabled}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                aiServices: {
                  ...prev.aiServices,
                  tts: { ...prev.aiServices.tts, enabled: e.target.checked }
                }
              }))}
              className="mr-2"
            />
            <span className="text-sm">Habilitado</span>
          </label>
        </div>

        {config.aiServices.tts.enabled && (
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-gray-700 mb-1">Puerto</label>
                <input
                  type="number"
                  value={config.aiServices.tts.port}
                  readOnly
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-gray-700 mb-1">Dispositivo</label>
                <select
                  value={config.aiServices.tts.device}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    aiServices: {
                      ...prev.aiServices,
                      tts: { ...prev.aiServices.tts, device: e.target.value }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="cuda">CUDA (GPU)</option>
                  <option value="cpu">CPU</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-gray-700 mb-1">Modelo</label>
              <input
                type="text"
                value={config.aiServices.tts.model}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
              />
              <p className="text-xs text-gray-500 mt-1">F5-TTS Español optimizado</p>
            </div>
          </div>
        )}
      </div>

      {/* LLM */}
      <div className="p-4 border border-gray-300 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Brain className="h-6 w-6 text-blue-600 mr-2" />
            <h3 className="font-medium text-gray-900">Large Language Model (LLM)</h3>
          </div>
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.aiServices.llm.enabled}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                aiServices: {
                  ...prev.aiServices,
                  llm: { ...prev.aiServices.llm, enabled: e.target.checked }
                }
              }))}
              className="mr-2"
            />
            <span className="text-sm">Habilitado</span>
          </label>
        </div>

        {config.aiServices.llm.enabled && (
          <div className="space-y-3 text-sm">
            <div>
              <label className="block text-gray-700 mb-1">Proveedor</label>
              <select
                value={config.aiServices.llm.provider}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  aiServices: {
                    ...prev.aiServices,
                    llm: { ...prev.aiServices.llm, provider: e.target.value }
                  }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="lm-studio">LM Studio (Local)</option>
                <option value="openai">OpenAI API</option>
                <option value="anthropic">Anthropic (Claude)</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-700 mb-1">Puerto</label>
              <input
                type="number"
                value={config.aiServices.llm.port}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
              />
            </div>
          </div>
        )}
      </div>

      {/* Seguridad y Cifrado */}
      <div className="p-4 border-2 border-yellow-400 rounded-lg bg-yellow-50">
        <div className="flex items-center mb-4">
          <div className="flex items-center flex-1">
            <svg className="h-6 w-6 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <h3 className="font-medium text-gray-900">🔒 Seguridad y Cifrado</h3>
          </div>
          <span className="px-3 py-1 bg-yellow-200 text-yellow-800 text-xs font-semibold rounded-full">
            RECOMENDADO
          </span>
        </div>

        <div className="mb-4 p-3 bg-white rounded-md">
          <p className="text-sm text-gray-700 mb-2">
            <strong>⚠️ Sin cifrado:</strong> Cualquiera puede interceptar tus llamadas por internet.
          </p>
          <p className="text-sm text-green-700">
            <strong>✅ Con TLS+SRTP:</strong> Tráfico cifrado (como HTTPS). Imposible de interceptar.
          </p>
        </div>

        <div className="space-y-3">
          <label className="flex items-start cursor-pointer">
            <input
              type="checkbox"
              checked={config.security.enableTLS}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                security: { ...prev.security, enableTLS: e.target.checked }
              }))}
              className="mt-1 mr-3"
            />
            <div className="flex-1">
              <span className="font-medium text-gray-900">Habilitar TLS/SIPS</span>
              <p className="text-xs text-gray-600 mt-1">
                Cifra la señalización SIP (quién llama, passwords, etc.). Puerto 5061.
              </p>
            </div>
          </label>

          <label className="flex items-start cursor-pointer">
            <input
              type="checkbox"
              checked={config.security.enableSRTP}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                security: { ...prev.security, enableSRTP: e.target.checked }
              }))}
              className="mt-1 mr-3"
            />
            <div className="flex-1">
              <span className="font-medium text-gray-900">Habilitar SRTP</span>
              <p className="text-xs text-gray-600 mt-1">
                Cifra el audio de las conversaciones con AES-128. Requiere TLS.
              </p>
            </div>
          </label>

          {config.security.enableTLS && (
            <div className="ml-6 mt-3 space-y-3 p-3 bg-white rounded-md">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Certificado SSL
                </label>
                <select
                  value={config.security.certificateType}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    security: { ...prev.security, certificateType: e.target.value }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="self-signed">Autofirmado (desarrollo/testing)</option>
                  <option value="letsencrypt">Let's Encrypt (producción - gratis)</option>
                  <option value="custom">Personalizado (sube tus propios certificados)</option>
                </select>
              </div>

              {config.security.certificateType === 'letsencrypt' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Dominio Público
                  </label>
                  <input
                    type="text"
                    placeholder="asterisk.tudominio.com"
                    value={config.security.domain}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      security: { ...prev.security, domain: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Requiere que el dominio apunte a este servidor
                  </p>
                </div>
              )}

              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.security.forceSecure}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    security: { ...prev.security, forceSecure: e.target.checked }
                  }))}
                  className="mt-1 mr-2"
                />
                <div className="flex-1">
                  <span className="text-sm font-medium text-gray-900">Forzar cifrado</span>
                  <p className="text-xs text-gray-600 mt-1">
                    Rechazar llamadas que no usen TLS+SRTP (más seguro)
                  </p>
                </div>
              </label>
            </div>
          )}
        </div>

        <div className="mt-4 p-3 bg-blue-50 rounded-md">
          <p className="text-xs text-blue-800">
            💡 <strong>Nota:</strong> Los certificados se generarán automáticamente al guardar.
            {config.security.enableTLS && config.security.enableSRTP
              ? ' Tu configuración es segura ✅'
              : ' Se recomienda habilitar ambos para máxima seguridad ⚠️'}
          </p>
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <Mic className="mx-auto h-12 w-12 text-blue-600" />
        <h2 className="mt-4 text-2xl font-bold text-gray-900">Entrenamiento de Voz</h2>
        <p className="mt-2 text-gray-600">Clonación de voz personalizada (opcional)</p>
      </div>

      <div className="p-4 border border-gray-300 rounded-lg">
        <label className="flex items-center cursor-pointer mb-4">
          <input
            type="checkbox"
            checked={config.voiceTraining.enabled}
            onChange={(e) => setConfig(prev => ({
              ...prev,
              voiceTraining: { ...prev.voiceTraining, enabled: e.target.checked }
            }))}
            className="mr-2"
          />
          <span className="font-medium">Habilitar clonación de voz personalizada</span>
        </label>

        {config.voiceTraining.enabled && (
          <div className="space-y-4 pt-4 border-t border-gray-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Audio de Referencia
              </label>
              <p className="text-xs text-gray-500 mb-2">
                Sube un audio de 10-30 segundos de la voz que quieres clonar
              </p>
              <input
                type="file"
                accept="audio/*"
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  voiceTraining: { ...prev.voiceTraining, referenceAudio: e.target.files[0] }
                }))}
                className="w-full text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre del Speaker
              </label>
              <input
                type="text"
                placeholder="Ej: Agente Virtual Empresa"
                value={config.voiceTraining.targetSpeaker}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  voiceTraining: { ...prev.voiceTraining, targetSpeaker: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div className="bg-blue-50 p-3 rounded-md">
              <p className="text-xs text-blue-800">
                💡 El entrenamiento puede tardar 10-30 minutos. Se ejecutará en segundo plano.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-600" />
        <h2 className="mt-4 text-2xl font-bold text-gray-900">Resumen de Configuración</h2>
        <p className="mt-2 text-gray-600">Revisa y confirma tu configuración</p>
      </div>

      {/* Resumen de Telefonía */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium text-gray-900 mb-3 flex items-center">
          <Phone className="h-5 w-5 mr-2" />
          Telefonía
        </h3>
        <div className="space-y-2 text-sm">
          {config.telephony.useSipTrunk ? (
            <>
              <div className="flex justify-between">
                <span className="text-gray-600">Tipo:</span>
                <span className="font-medium">SIP Trunk</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Host:</span>
                <span className="font-medium">{config.telephony.sipTrunk.host}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Usuario:</span>
                <span className="font-medium">{config.telephony.sipTrunk.user}</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex justify-between">
                <span className="text-gray-600">Hardware:</span>
                <span className="font-medium">{config.telephony.hardware.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Canales PSTN:</span>
                <span className="font-medium">{config.telephony.hardware.pstnChannels}</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Resumen de Servicios IA */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium text-gray-900 mb-3 flex items-center">
          <Brain className="h-5 w-5 mr-2" />
          Servicios de IA
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">STT (Whisper):</span>
            <span className={`font-medium ${config.aiServices.stt.enabled ? 'text-green-600' : 'text-red-600'}`}>
              {config.aiServices.stt.enabled ? '✓ Habilitado' : '✗ Deshabilitado'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">TTS (F5-TTS):</span>
            <span className={`font-medium ${config.aiServices.tts.enabled ? 'text-green-600' : 'text-red-600'}`}>
              {config.aiServices.tts.enabled ? '✓ Habilitado' : '✗ Deshabilitado'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">LLM:</span>
            <span className={`font-medium ${config.aiServices.llm.enabled ? 'text-green-600' : 'text-red-600'}`}>
              {config.aiServices.llm.enabled ? `✓ ${config.aiServices.llm.provider}` : '✗ Deshabilitado'}
            </span>
          </div>
        </div>
      </div>

      {/* Resumen de Seguridad */}
      <div className={`p-4 rounded-lg ${
        config.security.enableTLS && config.security.enableSRTP
          ? 'bg-green-50 border border-green-200'
          : 'bg-yellow-50 border border-yellow-200'
      }`}>
        <h3 className="font-medium text-gray-900 mb-3 flex items-center">
          <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Seguridad
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">TLS/SIPS (Señalización):</span>
            <span className={`font-medium ${config.security.enableTLS ? 'text-green-600' : 'text-red-600'}`}>
              {config.security.enableTLS ? '✓ Habilitado (Puerto 5061)' : '✗ Deshabilitado'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">SRTP (Audio cifrado):</span>
            <span className={`font-medium ${config.security.enableSRTP ? 'text-green-600' : 'text-red-600'}`}>
              {config.security.enableSRTP ? '✓ Habilitado (AES-128)' : '✗ Deshabilitado'}
            </span>
          </div>
          {config.security.enableTLS && (
            <>
              <div className="flex justify-between">
                <span className="text-gray-600">Certificado:</span>
                <span className="font-medium">
                  {config.security.certificateType === 'self-signed' && 'Autofirmado'}
                  {config.security.certificateType === 'letsencrypt' && 'Let\'s Encrypt'}
                  {config.security.certificateType === 'custom' && 'Personalizado'}
                </span>
              </div>
              {config.security.certificateType === 'letsencrypt' && config.security.domain && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Dominio:</span>
                  <span className="font-medium">{config.security.domain}</span>
                </div>
              )}
            </>
          )}
        </div>
        {config.security.enableTLS && config.security.enableSRTP ? (
          <div className="mt-3 p-2 bg-green-100 rounded text-xs text-green-800">
            ✅ Configuración segura - Llamadas completamente cifradas
          </div>
        ) : (
          <div className="mt-3 p-2 bg-yellow-100 rounded text-xs text-yellow-800">
            ⚠️ Sin cifrado completo - Las llamadas pueden ser interceptadas
          </div>
        )}
      </div>

      {/* Resumen de Voice Training */}
      {config.voiceTraining.enabled && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-3 flex items-center">
            <Mic className="h-5 w-5 mr-2" />
            Clonación de Voz
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Audio de referencia:</span>
              <span className="font-medium">{config.voiceTraining.referenceAudio?.name || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Speaker:</span>
              <span className="font-medium">{config.voiceTraining.targetSpeaker || 'N/A'}</span>
            </div>
          </div>
        </div>
      )}

      {errors.save && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600 text-sm">{errors.save}</p>
        </div>
      )}
    </div>
  );

  // ============================================
  // RENDER PRINCIPAL
  // ============================================

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-center mb-4">
            <Settings className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Configuración Inicial</h1>
          </div>

          {/* Progress Bar */}
          <div className="flex items-center justify-between mb-2">
            {[1, 2, 3, 4].map((stepNum) => (
              <div key={stepNum} className="flex items-center flex-1">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    step >= stepNum
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-300 text-gray-600'
                  }`}
                >
                  {stepNum}
                </div>
                {stepNum < 4 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${
                      step > stepNum ? 'bg-blue-600' : 'bg-gray-300'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-between text-xs text-gray-600">
            <span>Telefonía</span>
            <span>Servicios IA</span>
            <span>Voz</span>
            <span>Resumen</span>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
          {step === 4 && renderStep4()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={prevStep}
            disabled={step === 1}
            className="flex items-center px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Anterior
          </button>

          {step < 4 ? (
            <button
              onClick={nextStep}
              className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Siguiente
              <ArrowRight className="h-4 w-4 ml-2" />
            </button>
          ) : (
            <button
              onClick={saveConfiguration}
              disabled={loading}
              className="flex items-center px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin h-4 w-4 mr-2" />
                  Guardando...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Guardar y Finalizar
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConfigurationWizard;
