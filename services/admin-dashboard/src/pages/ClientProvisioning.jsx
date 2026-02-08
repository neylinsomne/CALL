import { useState } from 'react';
import {
  Users,
  Building2,
  Network,
  CheckCircle,
  ChevronRight,
  ChevronLeft,
  Download,
  Copy,
  Check,
  Key,
  Globe,
  Server,
  Shield,
  Loader,
  AlertCircle,
  Trash2
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

// Password generator
const generatePassword = (length = 16) => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%';
  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
};

const generateExtension = (prefix, index) => `${prefix}${String(index).padStart(2, '0')}`;

export default function ClientProvisioning() {
  const [currentStep, setCurrentStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState(null);
  const [copiedField, setCopiedField] = useState(null);

  const [client, setClient] = useState({
    company: { name: '', contactName: '', contactEmail: '', contactPhone: '', notes: '' },
    agents: { count: 5, extensionPrefix: '10', generatePasswords: true, extensions: [] },
    network: {
      connectionType: 'sip_trunk',
      externalIp: '',
      localNetwork: '192.168.1.0/24',
      rtpPortStart: 10000,
      rtpPortEnd: 20000,
      sipProviderWhitelist: '',
      ddns: { enabled: false, provider: 'duckdns', domain: '', token: '' },
      sipTrunk: { host: '', user: '', password: '', outboundCallerId: '' },
      gateway: { ip: '', user: 'gateway', password: '', fxoPorts: 4 }
    }
  });

  const steps = [
    { id: 'company', label: 'Cliente', icon: Building2 },
    { id: 'agents', label: 'Agentes', icon: Users },
    { id: 'network', label: 'Red', icon: Network },
    { id: 'review', label: 'Generar', icon: CheckCircle }
  ];

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
    setClient(prev => ({ ...prev, agents: { ...prev.agents, extensions } }));
  };

  const validateStep = (step) => {
    switch (step) {
      case 0: return client.company.name.trim().length > 0;
      case 1: return client.agents.count > 0 && client.agents.extensionPrefix.length > 0;
      case 2:
        if (client.network.connectionType === 'sip_trunk') {
          return client.network.sipTrunk.host.trim().length > 0;
        }
        return client.network.gateway.ip.trim().length > 0;
      default: return true;
    }
  };

  const nextStep = () => {
    if (currentStep === 1 && client.agents.extensions.length === 0) generateExtensions();
    if (currentStep < steps.length - 1) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  const copyToClipboard = (text, fieldName) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const generateConfigFile = () => {
    let config = `# Configuracion para: ${client.company.name}\n`;
    config += `# Generado: ${new Date().toISOString()}\n\n`;
    config += `COMPANY_NAME="${client.company.name}"\nCONTACT_EMAIL="${client.company.contactEmail}"\n\n`;
    config += `EXTERNAL_IP=${client.network.externalIp || '# Auto-detectar'}\n`;
    config += `LOCAL_NETWORK=${client.network.localNetwork}\n`;
    config += `RTP_PORT_START=${client.network.rtpPortStart}\nRTP_PORT_END=${client.network.rtpPortEnd}\n\n`;

    if (client.network.connectionType === 'sip_trunk') {
      config += `SIP_TRUNK_HOST=${client.network.sipTrunk.host}\n`;
      config += `SIP_TRUNK_USER=${client.network.sipTrunk.user}\n`;
      config += `SIP_TRUNK_PASSWORD=${client.network.sipTrunk.password}\n`;
    } else {
      config += `GATEWAY_FXO_IP=${client.network.gateway.ip}\n`;
      config += `GATEWAY_FXO_USER=${client.network.gateway.user}\n`;
      config += `GATEWAY_FXO_PASSWORD=${client.network.gateway.password}\n`;
    }

    config += '\n# EXTENSIONES\n';
    client.agents.extensions.forEach((ext, i) => {
      config += `AGENT_${i + 1}_EXT=${ext.extension}\nAGENT_${i + 1}_PASS=${ext.password}\n`;
    });

    return config;
  };

  const downloadConfig = () => {
    const config = generateConfigFile();
    const blob = new Blob([config], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${client.company.name.replace(/\s+/g, '_')}_config.env`;
    a.click();
    URL.revokeObjectURL(url);
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
        setSaveResult({ success: true, message: data.message || 'Cliente guardado', clientId: data.client_id });
      } else {
        setSaveResult({ success: false, message: data.detail || 'Error' });
      }
    } catch {
      setSaveResult({ success: true, message: 'Config generada (guardar localmente)' });
    } finally {
      setSaving(false);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: '0.625rem 0.875rem',
    background: 'var(--bg-primary)',
    border: '1px solid var(--border-color)',
    borderRadius: '8px',
    color: 'var(--text-primary)',
    fontSize: '0.9rem'
  };

  const labelStyle = {
    display: 'block',
    fontSize: '0.875rem',
    fontWeight: 500,
    marginBottom: '0.375rem',
    color: 'var(--text-secondary)'
  };

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <Users size={28} color="#10b981" />
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Provisionar Nuevo Cliente</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)' }}>
          Configura datos del cliente, extensiones y red para generar archivo de deployment.
        </p>
      </div>

      {/* Steps */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', position: 'relative' }}>
        <div style={{ position: 'absolute', top: '20px', left: '40px', right: '40px', height: '2px', background: 'var(--border-color)' }} />
        <div style={{ position: 'absolute', top: '20px', left: '40px', width: `${(currentStep / (steps.length - 1)) * 85}%`, height: '2px', background: 'var(--accent-blue)', transition: 'width 0.3s' }} />
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          return (
            <div key={step.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2 }}>
              <div style={{
                width: '40px', height: '40px', borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: isCompleted || isActive ? 'var(--accent-blue)' : 'var(--bg-secondary)',
                border: `2px solid ${isCompleted || isActive ? 'var(--accent-blue)' : 'var(--border-color)'}`,
                color: isCompleted || isActive ? '#fff' : 'var(--text-muted)'
              }}>
                {isCompleted ? <Check size={20} /> : <Icon size={20} />}
              </div>
              <span style={{ marginTop: '0.5rem', fontSize: '0.8rem', fontWeight: isActive ? 600 : 400, color: isActive ? 'var(--accent-blue)' : 'var(--text-muted)' }}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Content */}
      <div className="card" style={{ minHeight: '400px', marginBottom: '1.5rem' }}>
        {/* Step 1: Company */}
        {currentStep === 0 && (
          <div>
            <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Building2 size={20} color="var(--accent-blue)" /> Datos del Cliente
            </h3>
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div>
                <label style={labelStyle}>Nombre de la Empresa *</label>
                <input type="text" placeholder="Empresa ABC" value={client.company.name}
                  onChange={(e) => setClient(prev => ({ ...prev, company: { ...prev.company, name: e.target.value } }))}
                  style={inputStyle} />
              </div>
              <div className="grid-2">
                <div>
                  <label style={labelStyle}>Contacto</label>
                  <input type="text" placeholder="Juan Perez" value={client.company.contactName}
                    onChange={(e) => setClient(prev => ({ ...prev, company: { ...prev.company, contactName: e.target.value } }))}
                    style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle}>Email</label>
                  <input type="email" placeholder="contacto@empresa.com" value={client.company.contactEmail}
                    onChange={(e) => setClient(prev => ({ ...prev, company: { ...prev.company, contactEmail: e.target.value } }))}
                    style={inputStyle} />
                </div>
              </div>
              <div>
                <label style={labelStyle}>Notas</label>
                <textarea placeholder="Observaciones..." value={client.company.notes}
                  onChange={(e) => setClient(prev => ({ ...prev, company: { ...prev.company, notes: e.target.value } }))}
                  style={{ ...inputStyle, minHeight: '80px', resize: 'vertical' }} />
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Agents */}
        {currentStep === 1 && (
          <div>
            <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Users size={20} color="var(--accent-blue)" /> Agentes / Extensiones
            </h3>
            <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
              <div>
                <label style={labelStyle}>Numero de Agentes</label>
                <input type="number" min="1" max="50" value={client.agents.count}
                  onChange={(e) => setClient(prev => ({ ...prev, agents: { ...prev.agents, count: parseInt(e.target.value) || 1, extensions: [] } }))}
                  style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Prefijo Extension</label>
                <input type="text" placeholder="10" value={client.agents.extensionPrefix}
                  onChange={(e) => setClient(prev => ({ ...prev, agents: { ...prev.agents, extensionPrefix: e.target.value, extensions: [] } }))}
                  style={inputStyle} />
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Ej: {client.agents.extensionPrefix}01, {client.agents.extensionPrefix}02...
                </div>
              </div>
              <div style={{ paddingTop: '1.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input type="checkbox" checked={client.agents.generatePasswords}
                    onChange={(e) => setClient(prev => ({ ...prev, agents: { ...prev.agents, generatePasswords: e.target.checked, extensions: [] } }))}
                    style={{ marginRight: '0.5rem' }} />
                  <span>Generar passwords</span>
                </label>
              </div>
            </div>
            <button className="btn btn-primary" onClick={generateExtensions} style={{ marginBottom: '1rem' }}>
              <Key size={16} /> Generar {client.agents.count} Extensiones
            </button>
            {client.agents.extensions.length > 0 && (
              <div style={{ background: 'var(--bg-primary)', borderRadius: '8px', overflow: 'hidden' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr 180px 40px', padding: '0.75rem 1rem', background: 'var(--bg-secondary)', fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  <span>Ext.</span><span>Nombre</span><span>Password</span><span></span>
                </div>
                <div style={{ maxHeight: '250px', overflow: 'auto' }}>
                  {client.agents.extensions.map((ext, index) => (
                    <div key={index} style={{ display: 'grid', gridTemplateColumns: '80px 1fr 180px 40px', padding: '0.5rem 1rem', borderTop: '1px solid var(--border-color)', alignItems: 'center' }}>
                      <span style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{ext.extension}</span>
                      <input type="text" value={ext.name}
                        onChange={(e) => {
                          const newExts = [...client.agents.extensions];
                          newExts[index].name = e.target.value;
                          setClient(prev => ({ ...prev, agents: { ...prev.agents, extensions: newExts } }));
                        }}
                        style={{ ...inputStyle, padding: '0.375rem 0.5rem', fontSize: '0.85rem' }} />
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <code style={{ fontSize: '0.75rem', background: 'var(--bg-secondary)', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>{ext.password}</code>
                        <button onClick={() => copyToClipboard(ext.password, `pass-${index}`)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem' }}>
                          {copiedField === `pass-${index}` ? <Check size={14} color="#10b981" /> : <Copy size={14} color="#6b7280" />}
                        </button>
                      </div>
                      <button onClick={() => {
                        const newExts = client.agents.extensions.filter((_, i) => i !== index);
                        setClient(prev => ({ ...prev, agents: { ...prev.agents, extensions: newExts } }));
                      }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}>
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
            <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Network size={20} color="var(--accent-blue)" /> Configuracion de Red
            </h3>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={labelStyle}>Tipo de Conexion</label>
              <div className="grid-2">
                <button onClick={() => setClient(prev => ({ ...prev, network: { ...prev.network, connectionType: 'sip_trunk' } }))}
                  style={{ padding: '1rem', border: `2px solid ${client.network.connectionType === 'sip_trunk' ? 'var(--accent-blue)' : 'var(--border-color)'}`, borderRadius: '8px', background: client.network.connectionType === 'sip_trunk' ? 'rgba(59,130,246,0.1)' : 'var(--bg-primary)', cursor: 'pointer', textAlign: 'left', color: 'var(--text-primary)' }}>
                  <Globe size={24} color={client.network.connectionType === 'sip_trunk' ? 'var(--accent-blue)' : 'var(--text-muted)'} />
                  <div style={{ fontWeight: 600, marginTop: '0.5rem' }}>SIP Trunk</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Proveedor VoIP cloud</div>
                </button>
                <button onClick={() => setClient(prev => ({ ...prev, network: { ...prev.network, connectionType: 'gateway_fxo' } }))}
                  style={{ padding: '1rem', border: `2px solid ${client.network.connectionType === 'gateway_fxo' ? 'var(--accent-blue)' : 'var(--border-color)'}`, borderRadius: '8px', background: client.network.connectionType === 'gateway_fxo' ? 'rgba(59,130,246,0.1)' : 'var(--bg-primary)', cursor: 'pointer', textAlign: 'left', color: 'var(--text-primary)' }}>
                  <Server size={24} color={client.network.connectionType === 'gateway_fxo' ? 'var(--accent-blue)' : 'var(--text-muted)'} />
                  <div style={{ fontWeight: 600, marginTop: '0.5rem' }}>Gateway FXO</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Lineas analogicas</div>
                </button>
              </div>
            </div>
            {client.network.connectionType === 'sip_trunk' ? (
              <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={labelStyle}>Host Proveedor *</label>
                  <input type="text" placeholder="sip.proveedor.com" value={client.network.sipTrunk.host}
                    onChange={(e) => setClient(prev => ({ ...prev, network: { ...prev.network, sipTrunk: { ...prev.network.sipTrunk, host: e.target.value } } }))}
                    style={inputStyle} />
                </div>
                <div className="grid-2">
                  <div>
                    <label style={labelStyle}>Usuario SIP</label>
                    <input type="text" placeholder="usuario" value={client.network.sipTrunk.user}
                      onChange={(e) => setClient(prev => ({ ...prev, network: { ...prev.network, sipTrunk: { ...prev.network.sipTrunk, user: e.target.value } } }))}
                      style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Password SIP</label>
                    <input type="password" placeholder="********" value={client.network.sipTrunk.password}
                      onChange={(e) => setClient(prev => ({ ...prev, network: { ...prev.network, sipTrunk: { ...prev.network.sipTrunk, password: e.target.value } } }))}
                      style={inputStyle} />
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                <div className="grid-2" style={{ marginBottom: '1rem' }}>
                  <div>
                    <label style={labelStyle}>IP Gateway *</label>
                    <input type="text" placeholder="192.168.1.100" value={client.network.gateway.ip}
                      onChange={(e) => setClient(prev => ({ ...prev, network: { ...prev.network, gateway: { ...prev.network.gateway, ip: e.target.value } } }))}
                      style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Puertos FXO</label>
                    <input type="number" min="1" max="24" value={client.network.gateway.fxoPorts}
                      onChange={(e) => setClient(prev => ({ ...prev, network: { ...prev.network, gateway: { ...prev.network.gateway, fxoPorts: parseInt(e.target.value) || 4 } } }))}
                      style={inputStyle} />
                  </div>
                </div>
              </div>
            )}
            <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Shield size={16} /> NAT
              </h4>
              <div className="grid-2">
                <div>
                  <label style={labelStyle}>IP Externa</label>
                  <input type="text" placeholder="Auto-detectar" value={client.network.externalIp}
                    onChange={(e) => setClient(prev => ({ ...prev, network: { ...prev.network, externalIp: e.target.value } }))}
                    style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle}>Red Local</label>
                  <input type="text" placeholder="192.168.1.0/24" value={client.network.localNetwork}
                    onChange={(e) => setClient(prev => ({ ...prev, network: { ...prev.network, localNetwork: e.target.value } }))}
                    style={inputStyle} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {currentStep === 3 && (
          <div>
            <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle size={20} color="#10b981" /> Resumen
            </h3>
            <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
              <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Cliente</div>
                <div style={{ fontWeight: 600 }}>{client.company.name || 'Sin nombre'}</div>
              </div>
              <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Extensiones</div>
                <div style={{ fontWeight: 600 }}>{client.agents.extensions.length}</div>
              </div>
              <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Conexion</div>
                <div style={{ fontWeight: 600 }}>{client.network.connectionType === 'sip_trunk' ? 'SIP Trunk' : 'Gateway FXO'}</div>
              </div>
              <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Host/IP</div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{client.network.connectionType === 'sip_trunk' ? client.network.sipTrunk.host : client.network.gateway.ip}</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <button className="btn btn-secondary" onClick={downloadConfig}>
                <Download size={16} /> Descargar .env
              </button>
              <button className="btn btn-secondary" onClick={() => copyToClipboard(generateConfigFile(), 'config')}>
                {copiedField === 'config' ? <Check size={16} color="#10b981" /> : <Copy size={16} />}
                {copiedField === 'config' ? 'Copiado!' : 'Copiar Config'}
              </button>
              <button className="btn btn-success" onClick={saveClient} disabled={saving}>
                {saving ? <Loader size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                {saving ? 'Guardando...' : 'Guardar en Backend'}
              </button>
            </div>
            {saveResult && (
              <div style={{ padding: '1rem', borderRadius: '8px', background: saveResult.success ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', border: `1px solid ${saveResult.success ? '#10b981' : '#ef4444'}`, display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                {saveResult.success ? <CheckCircle size={20} color="#10b981" /> : <AlertCircle size={20} color="#ef4444" />}
                <span>{saveResult.message}</span>
                {saveResult.clientId && <code style={{ marginLeft: 'auto', fontSize: '0.8rem' }}>ID: {saveResult.clientId}</code>}
              </div>
            )}
            <pre style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', fontSize: '0.8rem', overflow: 'auto', maxHeight: '200px', color: 'var(--text-secondary)' }}>
              {generateConfigFile()}
            </pre>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button className="btn btn-secondary" onClick={prevStep} disabled={currentStep === 0}>
          <ChevronLeft size={18} /> Anterior
        </button>
        {currentStep < steps.length - 1 ? (
          <button className="btn btn-primary" onClick={nextStep} disabled={!validateStep(currentStep)}>
            Siguiente <ChevronRight size={18} />
          </button>
        ) : (
          <button className="btn btn-success" onClick={() => window.location.reload()}>
            Nuevo Cliente
          </button>
        )}
      </div>
    </div>
  );
}
