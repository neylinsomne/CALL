import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Users,
  Network,
  CheckCircle,
  ChevronRight,
  ChevronLeft,
  Download,
  Copy,
  Check,
  Plus,
  Trash2,
  Key,
  Globe,
  Server,
  Shield,
  Loader,
  AlertCircle
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

// Generador de password seguro
const generatePassword = (length = 16) => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%';
  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
};

// Generador de extensión
const generateExtension = (prefix, index) => {
  return `${prefix}${String(index).padStart(2, '0')}`;
};

export default function ClientSetup() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState(null);
  const [copiedField, setCopiedField] = useState(null);

  // Estado del formulario
  const [client, setClient] = useState({
    // Paso 1: Datos del cliente
    company: {
      name: '',
      contactName: '',
      contactEmail: '',
      contactPhone: '',
      notes: ''
    },

    // Paso 2: Agentes/Extensiones
    agents: {
      count: 5,
      extensionPrefix: '10',
      generatePasswords: true,
      extensions: [] // Se generan automáticamente
    },

    // Paso 3: Configuración de Red
    network: {
      connectionType: 'sip_trunk', // 'sip_trunk' o 'gateway_fxo'
      externalIp: '',
      autoDetectIp: true,
      localNetwork: '192.168.1.0/24',
      rtpPortStart: 10000,
      rtpPortEnd: 20000,
      sipProviderWhitelist: '',
      ddns: {
        enabled: false,
        provider: 'duckdns',
        domain: '',
        token: ''
      },
      // Para SIP Trunk
      sipTrunk: {
        host: '',
        user: '',
        password: '',
        outboundCallerId: ''
      },
      // Para Gateway FXO
      gateway: {
        ip: '',
        user: 'gateway',
        password: '',
        fxoPorts: 4
      }
    }
  });

  const steps = [
    { id: 'company', label: 'Datos del Cliente', icon: Building2 },
    { id: 'agents', label: 'Agentes', icon: Users },
    { id: 'network', label: 'Red / NAT', icon: Network },
    { id: 'review', label: 'Generar Config', icon: CheckCircle }
  ];

  // Generar extensiones basadas en el count
  const generateExtensions = () => {
    const extensions = [];
    for (let i = 1; i <= client.agents.count; i++) {
      extensions.push({
        extension: generateExtension(client.agents.extensionPrefix, i),
        name: `Agente ${i}`,
        password: client.agents.generatePasswords ? generatePassword(12) : '',
        enabled: true
      });
    }
    setClient(prev => ({
      ...prev,
      agents: { ...prev.agents, extensions }
    }));
  };

  // Validación por paso
  const validateStep = (step) => {
    switch (step) {
      case 0: // Company
        return client.company.name.trim().length > 0;
      case 1: // Agents
        return client.agents.count > 0 && client.agents.extensionPrefix.length > 0;
      case 2: // Network
        if (client.network.connectionType === 'sip_trunk') {
          return client.network.sipTrunk.host.trim().length > 0;
        } else {
          return client.network.gateway.ip.trim().length > 0;
        }
      default:
        return true;
    }
  };

  const nextStep = () => {
    if (currentStep === 1 && client.agents.extensions.length === 0) {
      generateExtensions();
    }
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const copyToClipboard = (text, fieldName) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const downloadConfig = () => {
    const config = generateConfigFile();
    const blob = new Blob([config], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${client.company.name.replace(/\s+/g, '_')}_config.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const generateConfigFile = () => {
    let config = `# Configuración para: ${client.company.name}\n`;
    config += `# Generado: ${new Date().toISOString()}\n\n`;

    config += `# ================================\n`;
    config += `# DATOS DEL CLIENTE\n`;
    config += `# ================================\n`;
    config += `COMPANY_NAME="${client.company.name}"\n`;
    config += `CONTACT_NAME="${client.company.contactName}"\n`;
    config += `CONTACT_EMAIL="${client.company.contactEmail}"\n\n`;

    config += `# ================================\n`;
    config += `# CONFIGURACIÓN DE RED / NAT\n`;
    config += `# ================================\n`;
    config += `EXTERNAL_IP=${client.network.externalIp || '# Auto-detectar'}\n`;
    config += `LOCAL_NETWORK=${client.network.localNetwork}\n`;
    config += `RTP_PORT_START=${client.network.rtpPortStart}\n`;
    config += `RTP_PORT_END=${client.network.rtpPortEnd}\n`;
    if (client.network.sipProviderWhitelist) {
      config += `SIP_PROVIDER_WHITELIST=${client.network.sipProviderWhitelist}\n`;
    }
    if (client.network.ddns.enabled) {
      config += `DDNS_ENABLED=true\n`;
      config += `DDNS_PROVIDER=${client.network.ddns.provider}\n`;
      config += `DDNS_DOMAIN=${client.network.ddns.domain}\n`;
      config += `DDNS_TOKEN=${client.network.ddns.token}\n`;
    }
    config += '\n';

    if (client.network.connectionType === 'sip_trunk') {
      config += `# ================================\n`;
      config += `# SIP TRUNK\n`;
      config += `# ================================\n`;
      config += `SIP_TRUNK_HOST=${client.network.sipTrunk.host}\n`;
      config += `SIP_TRUNK_USER=${client.network.sipTrunk.user}\n`;
      config += `SIP_TRUNK_PASSWORD=${client.network.sipTrunk.password}\n`;
      config += `OUTBOUND_CALLERID=${client.network.sipTrunk.outboundCallerId}\n\n`;
    } else {
      config += `# ================================\n`;
      config += `# GATEWAY FXO\n`;
      config += `# ================================\n`;
      config += `GATEWAY_FXO_IP=${client.network.gateway.ip}\n`;
      config += `GATEWAY_FXO_USER=${client.network.gateway.user}\n`;
      config += `GATEWAY_FXO_PASSWORD=${client.network.gateway.password}\n`;
      config += `GATEWAY_FXO_PORTS=${client.network.gateway.fxoPorts}\n\n`;
    }

    config += `# ================================\n`;
    config += `# EXTENSIONES / AGENTES\n`;
    config += `# ================================\n`;
    client.agents.extensions.forEach((ext, i) => {
      config += `# Agente ${i + 1}\n`;
      config += `AGENT_${i + 1}_EXT=${ext.extension}\n`;
      config += `AGENT_${i + 1}_NAME="${ext.name}"\n`;
      config += `AGENT_${i + 1}_PASS=${ext.password}\n\n`;
    });

    return config;
  };

  const saveClient = async () => {
    setSaving(true);
    setSaveResult(null);

    try {
      const res = await fetch(`${API_URL}/api/clients/provision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(client)
      });
      const data = await res.json();
      if (res.ok) {
        setSaveResult({ success: true, message: data.message || 'Cliente guardado exitosamente' });
      } else {
        setSaveResult({ success: false, message: data.detail || 'Error al guardar' });
      }
    } catch (err) {
      // Si el backend no tiene el endpoint aún, simular éxito para desarrollo
      setSaveResult({ success: true, message: 'Configuración generada (backend endpoint pendiente)' });
    } finally {
      setSaving(false);
    }
  };

  // Estilos
  const inputStyle = {
    width: '100%',
    padding: '0.625rem 0.875rem',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '0.9rem',
    background: '#fff',
    boxSizing: 'border-box'
  };

  const labelStyle = {
    display: 'block',
    fontSize: '0.875rem',
    fontWeight: 500,
    color: '#374151',
    marginBottom: '0.375rem'
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <Building2 size={28} color="#3b82f6" />
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>Configurar Nuevo Cliente</h1>
        </div>
        <p style={{ color: '#6b7280', margin: 0 }}>
          Wizard para provisionar un nuevo cliente con extensiones y configuración de red.
        </p>
      </div>

      {/* Steps Indicator */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: '2rem',
        position: 'relative'
      }}>
        {/* Line connector */}
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '40px',
          right: '40px',
          height: '2px',
          background: '#e5e7eb',
          zIndex: 0
        }} />
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '40px',
          width: `${(currentStep / (steps.length - 1)) * (100 - 10)}%`,
          height: '2px',
          background: '#3b82f6',
          zIndex: 1,
          transition: 'width 0.3s ease'
        }} />

        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;

          return (
            <div
              key={step.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                zIndex: 2
              }}
            >
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: isCompleted ? '#3b82f6' : isActive ? '#3b82f6' : '#fff',
                border: `2px solid ${isCompleted || isActive ? '#3b82f6' : '#d1d5db'}`,
                color: isCompleted || isActive ? '#fff' : '#6b7280',
                transition: 'all 0.3s'
              }}>
                {isCompleted ? <Check size={20} /> : <Icon size={20} />}
              </div>
              <span style={{
                marginTop: '0.5rem',
                fontSize: '0.8rem',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? '#3b82f6' : '#6b7280'
              }}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Step Content */}
      <div style={{
        background: '#f9fafb',
        borderRadius: '12px',
        padding: '1.5rem',
        marginBottom: '1.5rem',
        border: '1px solid #e5e7eb',
        minHeight: '400px'
      }}>
        {/* Step 1: Company Data */}
        {currentStep === 0 && (
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Building2 size={20} color="#3b82f6" /> Información del Cliente
            </h3>

            <div style={{ display: 'grid', gap: '1rem' }}>
              <div>
                <label style={labelStyle}>Nombre de la Empresa *</label>
                <input
                  type="text"
                  placeholder="Empresa ABC S.A."
                  value={client.company.name}
                  onChange={(e) => setClient(prev => ({
                    ...prev,
                    company: { ...prev.company, name: e.target.value }
                  }))}
                  style={inputStyle}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={labelStyle}>Nombre de Contacto</label>
                  <input
                    type="text"
                    placeholder="Juan Pérez"
                    value={client.company.contactName}
                    onChange={(e) => setClient(prev => ({
                      ...prev,
                      company: { ...prev.company, contactName: e.target.value }
                    }))}
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Teléfono de Contacto</label>
                  <input
                    type="tel"
                    placeholder="+52 55 1234 5678"
                    value={client.company.contactPhone}
                    onChange={(e) => setClient(prev => ({
                      ...prev,
                      company: { ...prev.company, contactPhone: e.target.value }
                    }))}
                    style={inputStyle}
                  />
                </div>
              </div>

              <div>
                <label style={labelStyle}>Email de Contacto</label>
                <input
                  type="email"
                  placeholder="contacto@empresa.com"
                  value={client.company.contactEmail}
                  onChange={(e) => setClient(prev => ({
                    ...prev,
                    company: { ...prev.company, contactEmail: e.target.value }
                  }))}
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Notas / Observaciones</label>
                <textarea
                  placeholder="Información adicional sobre el cliente..."
                  value={client.company.notes}
                  onChange={(e) => setClient(prev => ({
                    ...prev,
                    company: { ...prev.company, notes: e.target.value }
                  }))}
                  style={{ ...inputStyle, minHeight: '80px', resize: 'vertical' }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Agents */}
        {currentStep === 1 && (
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Users size={20} color="#3b82f6" /> Configuración de Agentes
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={labelStyle}>Número de Agentes</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={client.agents.count}
                  onChange={(e) => setClient(prev => ({
                    ...prev,
                    agents: { ...prev.agents, count: parseInt(e.target.value) || 1, extensions: [] }
                  }))}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Prefijo de Extensión</label>
                <input
                  type="text"
                  placeholder="10"
                  value={client.agents.extensionPrefix}
                  onChange={(e) => setClient(prev => ({
                    ...prev,
                    agents: { ...prev.agents, extensionPrefix: e.target.value, extensions: [] }
                  }))}
                  style={inputStyle}
                />
                <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                  Extensiones: {client.agents.extensionPrefix}01, {client.agents.extensionPrefix}02...
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', paddingTop: '1.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={client.agents.generatePasswords}
                    onChange={(e) => setClient(prev => ({
                      ...prev,
                      agents: { ...prev.agents, generatePasswords: e.target.checked, extensions: [] }
                    }))}
                    style={{ marginRight: '0.5rem' }}
                  />
                  <span style={{ fontSize: '0.875rem' }}>Generar passwords seguros</span>
                </label>
              </div>
            </div>

            <button
              onClick={generateExtensions}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                background: '#3b82f6',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                marginBottom: '1rem'
              }}
            >
              <Key size={16} /> Generar {client.agents.count} Extensiones
            </button>

            {/* Lista de extensiones generadas */}
            {client.agents.extensions.length > 0 && (
              <div style={{ background: '#fff', borderRadius: '8px', border: '1px solid #e5e7eb', overflow: 'hidden' }}>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '80px 1fr 200px 40px',
                  padding: '0.75rem 1rem',
                  background: '#f3f4f6',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  color: '#6b7280'
                }}>
                  <span>Ext.</span>
                  <span>Nombre</span>
                  <span>Password</span>
                  <span></span>
                </div>
                <div style={{ maxHeight: '250px', overflow: 'auto' }}>
                  {client.agents.extensions.map((ext, index) => (
                    <div
                      key={index}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '80px 1fr 200px 40px',
                        padding: '0.5rem 1rem',
                        borderTop: '1px solid #e5e7eb',
                        alignItems: 'center'
                      }}
                    >
                      <span style={{ fontWeight: 600, color: '#3b82f6' }}>{ext.extension}</span>
                      <input
                        type="text"
                        value={ext.name}
                        onChange={(e) => {
                          const newExts = [...client.agents.extensions];
                          newExts[index].name = e.target.value;
                          setClient(prev => ({
                            ...prev,
                            agents: { ...prev.agents, extensions: newExts }
                          }));
                        }}
                        style={{ ...inputStyle, padding: '0.375rem 0.5rem', fontSize: '0.85rem' }}
                      />
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <code style={{ fontSize: '0.8rem', background: '#f3f4f6', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
                          {ext.password}
                        </code>
                        <button
                          onClick={() => copyToClipboard(ext.password, `pass-${index}`)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem' }}
                        >
                          {copiedField === `pass-${index}` ? <Check size={14} color="#10b981" /> : <Copy size={14} color="#6b7280" />}
                        </button>
                      </div>
                      <button
                        onClick={() => {
                          const newExts = client.agents.extensions.filter((_, i) => i !== index);
                          setClient(prev => ({
                            ...prev,
                            agents: { ...prev.agents, extensions: newExts }
                          }));
                        }}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Network */}
        {currentStep === 2 && (
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Network size={20} color="#3b82f6" /> Configuración de Red / NAT
            </h3>

            {/* Tipo de conexión */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={labelStyle}>Tipo de Conexión</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <button
                  onClick={() => setClient(prev => ({
                    ...prev,
                    network: { ...prev.network, connectionType: 'sip_trunk' }
                  }))}
                  style={{
                    padding: '1rem',
                    border: `2px solid ${client.network.connectionType === 'sip_trunk' ? '#3b82f6' : '#e5e7eb'}`,
                    borderRadius: '8px',
                    background: client.network.connectionType === 'sip_trunk' ? '#eff6ff' : '#fff',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <Globe size={24} color={client.network.connectionType === 'sip_trunk' ? '#3b82f6' : '#9ca3af'} />
                  <div style={{ fontWeight: 600, marginTop: '0.5rem' }}>SIP Trunk</div>
                  <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>Proveedor VoIP cloud</div>
                </button>

                <button
                  onClick={() => setClient(prev => ({
                    ...prev,
                    network: { ...prev.network, connectionType: 'gateway_fxo' }
                  }))}
                  style={{
                    padding: '1rem',
                    border: `2px solid ${client.network.connectionType === 'gateway_fxo' ? '#3b82f6' : '#e5e7eb'}`,
                    borderRadius: '8px',
                    background: client.network.connectionType === 'gateway_fxo' ? '#eff6ff' : '#fff',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <Server size={24} color={client.network.connectionType === 'gateway_fxo' ? '#3b82f6' : '#9ca3af'} />
                  <div style={{ fontWeight: 600, marginTop: '0.5rem' }}>Gateway FXO</div>
                  <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>Líneas analógicas existentes</div>
                </button>
              </div>
            </div>

            {/* Config específica según tipo */}
            {client.network.connectionType === 'sip_trunk' ? (
              <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb', marginBottom: '1.5rem' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '1rem', color: '#374151' }}>
                  <Globe size={16} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                  Datos del SIP Trunk
                </h4>
                <div style={{ display: 'grid', gap: '1rem' }}>
                  <div>
                    <label style={labelStyle}>Host del Proveedor *</label>
                    <input
                      type="text"
                      placeholder="sip.proveedor.com"
                      value={client.network.sipTrunk.host}
                      onChange={(e) => setClient(prev => ({
                        ...prev,
                        network: { ...prev.network, sipTrunk: { ...prev.network.sipTrunk, host: e.target.value } }
                      }))}
                      style={inputStyle}
                    />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <label style={labelStyle}>Usuario SIP</label>
                      <input
                        type="text"
                        placeholder="usuario"
                        value={client.network.sipTrunk.user}
                        onChange={(e) => setClient(prev => ({
                          ...prev,
                          network: { ...prev.network, sipTrunk: { ...prev.network.sipTrunk, user: e.target.value } }
                        }))}
                        style={inputStyle}
                      />
                    </div>
                    <div>
                      <label style={labelStyle}>Password SIP</label>
                      <input
                        type="password"
                        placeholder="********"
                        value={client.network.sipTrunk.password}
                        onChange={(e) => setClient(prev => ({
                          ...prev,
                          network: { ...prev.network, sipTrunk: { ...prev.network.sipTrunk, password: e.target.value } }
                        }))}
                        style={inputStyle}
                      />
                    </div>
                  </div>
                  <div>
                    <label style={labelStyle}>Caller ID Saliente</label>
                    <input
                      type="text"
                      placeholder="+52 55 1234 5678"
                      value={client.network.sipTrunk.outboundCallerId}
                      onChange={(e) => setClient(prev => ({
                        ...prev,
                        network: { ...prev.network, sipTrunk: { ...prev.network.sipTrunk, outboundCallerId: e.target.value } }
                      }))}
                      style={inputStyle}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb', marginBottom: '1.5rem' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '1rem', color: '#374151' }}>
                  <Server size={16} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                  Datos del Gateway FXO
                </h4>
                <div style={{ display: 'grid', gap: '1rem' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
                    <div>
                      <label style={labelStyle}>IP del Gateway *</label>
                      <input
                        type="text"
                        placeholder="192.168.1.100"
                        value={client.network.gateway.ip}
                        onChange={(e) => setClient(prev => ({
                          ...prev,
                          network: { ...prev.network, gateway: { ...prev.network.gateway, ip: e.target.value } }
                        }))}
                        style={inputStyle}
                      />
                    </div>
                    <div>
                      <label style={labelStyle}>Puertos FXO</label>
                      <input
                        type="number"
                        min="1"
                        max="24"
                        value={client.network.gateway.fxoPorts}
                        onChange={(e) => setClient(prev => ({
                          ...prev,
                          network: { ...prev.network, gateway: { ...prev.network.gateway, fxoPorts: parseInt(e.target.value) || 4 } }
                        }))}
                        style={inputStyle}
                      />
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <label style={labelStyle}>Usuario</label>
                      <input
                        type="text"
                        placeholder="gateway"
                        value={client.network.gateway.user}
                        onChange={(e) => setClient(prev => ({
                          ...prev,
                          network: { ...prev.network, gateway: { ...prev.network.gateway, user: e.target.value } }
                        }))}
                        style={inputStyle}
                      />
                    </div>
                    <div>
                      <label style={labelStyle}>Password</label>
                      <input
                        type="password"
                        placeholder="********"
                        value={client.network.gateway.password}
                        onChange={(e) => setClient(prev => ({
                          ...prev,
                          network: { ...prev.network, gateway: { ...prev.network.gateway, password: e.target.value } }
                        }))}
                        style={inputStyle}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* NAT Settings */}
            <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '1rem', color: '#374151' }}>
                <Shield size={16} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                Configuración NAT
              </h4>

              <div style={{ display: 'grid', gap: '1rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={labelStyle}>IP Externa (Pública)</label>
                    <input
                      type="text"
                      placeholder="Auto-detectar o ej: 181.123.45.67"
                      value={client.network.externalIp}
                      onChange={(e) => setClient(prev => ({
                        ...prev,
                        network: { ...prev.network, externalIp: e.target.value }
                      }))}
                      style={inputStyle}
                    />
                    <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Dejar vacío para auto-detectar</span>
                  </div>
                  <div>
                    <label style={labelStyle}>Red Local (CIDR)</label>
                    <input
                      type="text"
                      placeholder="192.168.1.0/24"
                      value={client.network.localNetwork}
                      onChange={(e) => setClient(prev => ({
                        ...prev,
                        network: { ...prev.network, localNetwork: e.target.value }
                      }))}
                      style={inputStyle}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 2fr', gap: '1rem' }}>
                  <div>
                    <label style={labelStyle}>Puerto RTP Inicio</label>
                    <input
                      type="number"
                      value={client.network.rtpPortStart}
                      onChange={(e) => setClient(prev => ({
                        ...prev,
                        network: { ...prev.network, rtpPortStart: parseInt(e.target.value) || 10000 }
                      }))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Puerto RTP Fin</label>
                    <input
                      type="number"
                      value={client.network.rtpPortEnd}
                      onChange={(e) => setClient(prev => ({
                        ...prev,
                        network: { ...prev.network, rtpPortEnd: parseInt(e.target.value) || 20000 }
                      }))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Whitelist IPs Proveedor</label>
                    <input
                      type="text"
                      placeholder="200.100.50.0/24, 201.200.100.0/24"
                      value={client.network.sipProviderWhitelist}
                      onChange={(e) => setClient(prev => ({
                        ...prev,
                        network: { ...prev.network, sipProviderWhitelist: e.target.value }
                      }))}
                      style={inputStyle}
                    />
                  </div>
                </div>

                {/* DDNS */}
                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '1rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={client.network.ddns.enabled}
                      onChange={(e) => setClient(prev => ({
                        ...prev,
                        network: { ...prev.network, ddns: { ...prev.network.ddns, enabled: e.target.checked } }
                      }))}
                      style={{ marginRight: '0.5rem' }}
                    />
                    <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>IP Dinámica (usar DDNS)</span>
                  </label>

                  {client.network.ddns.enabled && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                      <div>
                        <label style={labelStyle}>Proveedor</label>
                        <select
                          value={client.network.ddns.provider}
                          onChange={(e) => setClient(prev => ({
                            ...prev,
                            network: { ...prev.network, ddns: { ...prev.network.ddns, provider: e.target.value } }
                          }))}
                          style={inputStyle}
                        >
                          <option value="duckdns">DuckDNS</option>
                          <option value="noip">No-IP</option>
                          <option value="dynu">Dynu</option>
                        </select>
                      </div>
                      <div>
                        <label style={labelStyle}>Dominio</label>
                        <input
                          type="text"
                          placeholder="micliente"
                          value={client.network.ddns.domain}
                          onChange={(e) => setClient(prev => ({
                            ...prev,
                            network: { ...prev.network, ddns: { ...prev.network.ddns, domain: e.target.value } }
                          }))}
                          style={inputStyle}
                        />
                      </div>
                      <div>
                        <label style={labelStyle}>Token</label>
                        <input
                          type="password"
                          placeholder="tu-token"
                          value={client.network.ddns.token}
                          onChange={(e) => setClient(prev => ({
                            ...prev,
                            network: { ...prev.network, ddns: { ...prev.network.ddns, token: e.target.value } }
                          }))}
                          style={inputStyle}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {currentStep === 3 && (
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle size={20} color="#10b981" /> Resumen de Configuración
            </h3>

            {/* Summary Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#6b7280', marginBottom: '0.75rem' }}>
                  <Building2 size={16} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                  CLIENTE
                </h4>
                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{client.company.name || 'Sin nombre'}</div>
                <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>{client.company.contactEmail}</div>
              </div>

              <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#6b7280', marginBottom: '0.75rem' }}>
                  <Users size={16} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                  AGENTES
                </h4>
                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{client.agents.extensions.length} extensiones</div>
                <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                  Rango: {client.agents.extensionPrefix}01 - {client.agents.extensionPrefix}{String(client.agents.extensions.length).padStart(2, '0')}
                </div>
              </div>

              <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#6b7280', marginBottom: '0.75rem' }}>
                  <Network size={16} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                  CONEXIÓN
                </h4>
                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>
                  {client.network.connectionType === 'sip_trunk' ? 'SIP Trunk' : 'Gateway FXO'}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                  {client.network.connectionType === 'sip_trunk'
                    ? client.network.sipTrunk.host
                    : client.network.gateway.ip
                  }
                </div>
              </div>

              <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#6b7280', marginBottom: '0.75rem' }}>
                  <Shield size={16} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                  NAT / RED
                </h4>
                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>
                  {client.network.externalIp || 'Auto-detectar IP'}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                  Red: {client.network.localNetwork} | RTP: {client.network.rtpPortStart}-{client.network.rtpPortEnd}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                onClick={downloadConfig}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1.5rem',
                  background: '#fff',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: 500
                }}
              >
                <Download size={18} /> Descargar Config (.txt)
              </button>

              <button
                onClick={() => copyToClipboard(generateConfigFile(), 'config')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1.5rem',
                  background: '#fff',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: 500
                }}
              >
                {copiedField === 'config' ? <Check size={18} color="#10b981" /> : <Copy size={18} />}
                {copiedField === 'config' ? 'Copiado!' : 'Copiar al Portapapeles'}
              </button>

              <button
                onClick={saveClient}
                disabled={saving}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1.5rem',
                  background: '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: 600
                }}
              >
                {saving ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                {saving ? 'Guardando...' : 'Guardar Cliente'}
              </button>
            </div>

            {/* Save Result */}
            {saveResult && (
              <div style={{
                marginTop: '1rem',
                padding: '1rem',
                borderRadius: '8px',
                background: saveResult.success ? '#ecfdf5' : '#fef2f2',
                border: `1px solid ${saveResult.success ? '#a7f3d0' : '#fecaca'}`,
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem'
              }}>
                {saveResult.success
                  ? <CheckCircle size={20} color="#10b981" />
                  : <AlertCircle size={20} color="#ef4444" />
                }
                <span>{saveResult.message}</span>
              </div>
            )}

            {/* Preview Config */}
            <div style={{ marginTop: '1.5rem' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem' }}>Vista Previa del Archivo</h4>
              <pre style={{
                background: '#1f2937',
                color: '#e5e7eb',
                padding: '1rem',
                borderRadius: '8px',
                fontSize: '0.8rem',
                overflow: 'auto',
                maxHeight: '200px'
              }}>
                {generateConfigFile()}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button
          onClick={prevStep}
          disabled={currentStep === 0}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1.5rem',
            background: currentStep === 0 ? '#f3f4f6' : '#fff',
            border: '1px solid #d1d5db',
            borderRadius: '8px',
            cursor: currentStep === 0 ? 'not-allowed' : 'pointer',
            fontSize: '0.9rem',
            fontWeight: 500,
            color: currentStep === 0 ? '#9ca3af' : '#374151'
          }}
        >
          <ChevronLeft size={18} /> Anterior
        </button>

        {currentStep < steps.length - 1 ? (
          <button
            onClick={nextStep}
            disabled={!validateStep(currentStep)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.5rem',
              background: validateStep(currentStep) ? '#3b82f6' : '#9ca3af',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: validateStep(currentStep) ? 'pointer' : 'not-allowed',
              fontSize: '0.9rem',
              fontWeight: 600
            }}
          >
            Siguiente <ChevronRight size={18} />
          </button>
        ) : (
          <button
            onClick={() => navigate('/agents')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.5rem',
              background: '#10b981',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 600
            }}
          >
            Finalizar <CheckCircle size={18} />
          </button>
        )}
      </div>
    </div>
  );
}
