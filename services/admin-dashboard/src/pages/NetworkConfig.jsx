import { useState, useEffect } from 'react';
import {
  Network,
  Globe,
  Shield,
  Save,
  Loader,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  Copy,
  Check
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function NetworkConfig() {
  const [config, setConfig] = useState({
    externalIp: '',
    autoDetect: true,
    localNetwork: '192.168.1.0/24',
    rtpPortStart: 10000,
    rtpPortEnd: 20000,
    sipProviderWhitelist: '',
    ddns: {
      enabled: false,
      provider: 'duckdns',
      domain: '',
      token: ''
    }
  });

  const [detecting, setDetecting] = useState(false);
  const [detectedIp, setDetectedIp] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState(null);
  const [copied, setCopied] = useState(false);

  const detectPublicIp = async () => {
    setDetecting(true);
    try {
      // Try multiple services
      const services = [
        'https://api.ipify.org?format=json',
        'https://ipinfo.io/json'
      ];

      for (const url of services) {
        try {
          const res = await fetch(url);
          const data = await res.json();
          const ip = data.ip || data.query;
          if (ip) {
            setDetectedIp(ip);
            setConfig(prev => ({ ...prev, externalIp: ip }));
            break;
          }
        } catch {
          continue;
        }
      }
    } catch (err) {
      console.error('Error detecting IP:', err);
    } finally {
      setDetecting(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    setSaveResult(null);

    try {
      // Save to backend (this would update .env and Asterisk config)
      const res = await fetch(`${API_URL}/api/config/network`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (res.ok) {
        setSaveResult({ success: true, message: 'Configuracion guardada correctamente' });
      } else {
        setSaveResult({ success: false, message: 'Error al guardar' });
      }
    } catch (err) {
      // For development, show success anyway
      setSaveResult({ success: true, message: 'Configuracion preparada (backend endpoint pendiente)' });
    } finally {
      setSaving(false);
    }
  };

  const generateEnvSnippet = () => {
    let snippet = `# NAT / Network Configuration\n`;
    snippet += `EXTERNAL_IP=${config.externalIp || '# Auto-detect'}\n`;
    snippet += `LOCAL_NETWORK=${config.localNetwork}\n`;
    snippet += `RTP_PORT_START=${config.rtpPortStart}\n`;
    snippet += `RTP_PORT_END=${config.rtpPortEnd}\n`;
    if (config.sipProviderWhitelist) {
      snippet += `SIP_PROVIDER_WHITELIST=${config.sipProviderWhitelist}\n`;
    }
    if (config.ddns.enabled) {
      snippet += `\n# DDNS\n`;
      snippet += `DDNS_ENABLED=true\n`;
      snippet += `DDNS_PROVIDER=${config.ddns.provider}\n`;
      snippet += `DDNS_DOMAIN=${config.ddns.domain}\n`;
      snippet += `DDNS_TOKEN=${config.ddns.token}\n`;
    }
    return snippet;
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generateEnvSnippet());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
          <Network size={28} color="#3b82f6" />
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Configuracion de Red / NAT</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)' }}>
          Configura IP publica, puertos RTP y DDNS para que las llamadas funcionen correctamente detras de NAT.
        </p>
      </div>

      <div className="grid-2">
        {/* Main Config */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Globe size={20} /> IP y Red
          </h3>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={labelStyle}>IP Externa (Publica)</label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                placeholder="Dejar vacio para auto-detectar"
                value={config.externalIp}
                onChange={(e) => setConfig(prev => ({ ...prev, externalIp: e.target.value }))}
                style={{ ...inputStyle, flex: 1 }}
              />
              <button
                className="btn btn-secondary"
                onClick={detectPublicIp}
                disabled={detecting}
                style={{ whiteSpace: 'nowrap' }}
              >
                {detecting ? <Loader size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                Detectar
              </button>
            </div>
            {detectedIp && (
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-green)', marginTop: '0.25rem' }}>
                IP detectada: {detectedIp}
              </div>
            )}
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={labelStyle}>Red Local (CIDR)</label>
            <input
              type="text"
              placeholder="192.168.1.0/24"
              value={config.localNetwork}
              onChange={(e) => setConfig(prev => ({ ...prev, localNetwork: e.target.value }))}
              style={inputStyle}
            />
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Trafico dentro de esta red no sera reescrito
            </div>
          </div>

          <div className="grid-2" style={{ marginBottom: '1.25rem' }}>
            <div>
              <label style={labelStyle}>Puerto RTP Inicio</label>
              <input
                type="number"
                value={config.rtpPortStart}
                onChange={(e) => setConfig(prev => ({ ...prev, rtpPortStart: parseInt(e.target.value) || 10000 }))}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Puerto RTP Fin</label>
              <input
                type="number"
                value={config.rtpPortEnd}
                onChange={(e) => setConfig(prev => ({ ...prev, rtpPortEnd: parseInt(e.target.value) || 20000 }))}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={labelStyle}>Whitelist IPs Proveedor SIP</label>
            <input
              type="text"
              placeholder="200.100.50.0/24, 201.200.100.0/24"
              value={config.sipProviderWhitelist}
              onChange={(e) => setConfig(prev => ({ ...prev, sipProviderWhitelist: e.target.value }))}
              style={inputStyle}
            />
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Solo estas IPs podran conectar al puerto 5060 (seguridad)
            </div>
          </div>
        </div>

        {/* DDNS Config */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Shield size={20} /> DDNS (IP Dinamica)
          </h3>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={config.ddns.enabled}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  ddns: { ...prev.ddns, enabled: e.target.checked }
                }))}
                style={{ marginRight: '0.5rem' }}
              />
              <span>Habilitar DDNS (mi IP publica es dinamica)</span>
            </label>
          </div>

          {config.ddns.enabled && (
            <>
              <div style={{ marginBottom: '1.25rem' }}>
                <label style={labelStyle}>Proveedor DDNS</label>
                <select
                  value={config.ddns.provider}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    ddns: { ...prev.ddns, provider: e.target.value }
                  }))}
                  style={inputStyle}
                >
                  <option value="duckdns">DuckDNS (Gratis)</option>
                  <option value="noip">No-IP</option>
                  <option value="dynu">Dynu</option>
                </select>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={labelStyle}>Dominio</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="text"
                    placeholder="miempresa"
                    value={config.ddns.domain}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      ddns: { ...prev.ddns, domain: e.target.value }
                    }))}
                    style={inputStyle}
                  />
                  <span style={{ color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    .{config.ddns.provider === 'duckdns' ? 'duckdns.org' : 'ddns.net'}
                  </span>
                </div>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={labelStyle}>Token / API Key</label>
                <input
                  type="password"
                  placeholder="tu-token-aqui"
                  value={config.ddns.token}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    ddns: { ...prev.ddns, token: e.target.value }
                  }))}
                  style={inputStyle}
                />
              </div>

              <a
                href={`https://${config.ddns.provider === 'duckdns' ? 'duckdns.org' : 'noip.com'}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: 'var(--accent-blue)',
                  fontSize: '0.85rem'
                }}
              >
                <ExternalLink size={14} />
                Obtener cuenta {config.ddns.provider}
              </a>
            </>
          )}
        </div>
      </div>

      {/* Generated Config */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">Variables de Entorno Generadas</h3>
          <button className="btn btn-secondary" onClick={copyToClipboard}>
            {copied ? <Check size={16} color="#10b981" /> : <Copy size={16} />}
            {copied ? 'Copiado!' : 'Copiar'}
          </button>
        </div>

        <pre style={{
          background: 'var(--bg-primary)',
          padding: '1rem',
          borderRadius: '8px',
          fontSize: '0.85rem',
          overflow: 'auto',
          color: 'var(--text-secondary)'
        }}>
          {generateEnvSnippet()}
        </pre>
      </div>

      {/* Save Button */}
      <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
        {saveResult && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            color: saveResult.success ? 'var(--accent-green)' : 'var(--accent-red)'
          }}>
            {saveResult.success ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
            {saveResult.message}
          </div>
        )}
        <button
          className="btn btn-primary"
          onClick={saveConfig}
          disabled={saving}
        >
          {saving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />}
          {saving ? 'Guardando...' : 'Guardar Configuracion'}
        </button>
      </div>
    </div>
  );
}
