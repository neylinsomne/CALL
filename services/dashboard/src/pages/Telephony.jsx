import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Phone,
  PhoneIncoming,
  Wifi,
  HardDrive,
  Save,
  Loader,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus,
  Trash2,
  Zap,
  Globe,
  Server,
  Activity
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function Telephony() {
  const navigate = useNavigate();
  const [config, setConfig] = useState({
    method: '',
    fxo_gateway: {
      ip: '',
      sip_port: 5060,
      user: 'gateway',
      password: '',
      fxo_ports: 4,
      codec: 'ulaw',
      dids: []
    },
    carrier_grade: {
      host: '',
      user: '',
      password: '',
      outbound_caller_id: '',
      auth_type: 'register',
      dids: []
    }
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saveResult, setSaveResult] = useState(null);
  const [errors, setErrors] = useState({});

  // Cargar configuracion existente
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/config/telephony`);
      if (res.ok) {
        const data = await res.json();
        if (data.method) {
          setConfig(prev => ({ ...prev, ...data }));
        }
      }
    } catch (err) {
      console.error('Error cargando configuracion:', err);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    setSaveResult(null);
    setErrors({});

    // Validacion basica
    const errs = {};
    if (!config.method) {
      errs.method = 'Selecciona un metodo de recepcion';
    }
    if (config.method === 'fxo_gateway' && !config.fxo_gateway.ip) {
      errs.gateway_ip = 'IP del gateway es requerida';
    }
    if (config.method === 'carrier_grade' && !config.carrier_grade.host) {
      errs.carrier_host = 'Host del proveedor SIP es requerido';
    }
    if (config.method === 'carrier_grade' && !config.carrier_grade.user) {
      errs.carrier_user = 'Usuario SIP es requerido';
    }

    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      setSaving(false);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/config/telephony/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const data = await res.json();
      if (res.ok) {
        setSaveResult({ success: true, message: data.message });
      } else {
        setSaveResult({ success: false, message: data.detail || 'Error al guardar' });
      }
    } catch (err) {
      setSaveResult({ success: false, message: 'Error de conexion con el backend' });
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(`${API_URL}/api/config/telephony/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const data = await res.json();
      setTestResult(data);
    } catch (err) {
      setTestResult({ reachable: false, message: 'Error de conexion con el backend' });
    } finally {
      setTesting(false);
    }
  };

  // Helpers para DIDs
  const addDID = (method) => {
    setConfig(prev => ({
      ...prev,
      [method]: {
        ...prev[method],
        dids: [...prev[method].dids, { number: '', label: '', active: true }]
      }
    }));
  };

  const removeDID = (method, index) => {
    setConfig(prev => ({
      ...prev,
      [method]: {
        ...prev[method],
        dids: prev[method].dids.filter((_, i) => i !== index)
      }
    }));
  };

  const updateDID = (method, index, field, value) => {
    setConfig(prev => ({
      ...prev,
      [method]: {
        ...prev[method],
        dids: prev[method].dids.map((did, i) =>
          i === index ? { ...did, [field]: value } : did
        )
      }
    }));
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <Loader className="animate-spin" size={32} />
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '960px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <PhoneIncoming size={28} color="#3b82f6" />
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>Recepcion de Llamadas</h1>
        </div>
        <p style={{ color: '#6b7280', margin: 0 }}>
          Configura como tu sistema recibe llamadas: Gateway FXO (lineas existentes) o Carrier Grade (SIP Trunk).
        </p>
      </div>

      {/* Status Banner */}
      {config.method && (
        <div style={{
          padding: '1rem 1.25rem',
          borderRadius: '12px',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          background: testResult?.reachable ? '#ecfdf5' : config.method ? '#eff6ff' : '#f9fafb',
          border: `1px solid ${testResult?.reachable ? '#a7f3d0' : '#dbeafe'}`
        }}>
          <Activity size={20} color={testResult?.reachable ? '#10b981' : '#3b82f6'} />
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
              {config.method === 'fxo_gateway' ? 'Gateway FXO' : 'Carrier Grade / SIP Trunk'}
              {testResult?.reachable && ' - Conectado'}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
              {config.method === 'fxo_gateway'
                ? `IP: ${config.fxo_gateway.ip || 'No configurada'} | Puertos FXO: ${config.fxo_gateway.fxo_ports}`
                : `Host: ${config.carrier_grade.host || 'No configurado'} | Auth: ${config.carrier_grade.auth_type}`
              }
            </div>
          </div>
        </div>
      )}

      {/* Method Selector */}
      <div style={{ marginBottom: '2rem' }}>
        <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.75rem', fontSize: '0.95rem' }}>
          Metodo de Recepcion
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          {/* FXO Gateway Card */}
          <button
            onClick={() => setConfig(prev => ({ ...prev, method: 'fxo_gateway' }))}
            style={{
              padding: '1.5rem',
              border: `2px solid ${config.method === 'fxo_gateway' ? '#3b82f6' : '#e5e7eb'}`,
              borderRadius: '12px',
              background: config.method === 'fxo_gateway' ? '#eff6ff' : '#fff',
              cursor: 'pointer',
              textAlign: 'center',
              transition: 'all 0.2s'
            }}
          >
            <Server size={32} color={config.method === 'fxo_gateway' ? '#3b82f6' : '#9ca3af'} style={{ margin: '0 auto 0.75rem' }} />
            <div style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.25rem' }}>Gateway FXO</div>
            <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
              El cliente conserva sus lineas analogicas. El gateway convierte a SIP.
            </div>
          </button>

          {/* Carrier Grade Card */}
          <button
            onClick={() => setConfig(prev => ({ ...prev, method: 'carrier_grade' }))}
            style={{
              padding: '1.5rem',
              border: `2px solid ${config.method === 'carrier_grade' ? '#3b82f6' : '#e5e7eb'}`,
              borderRadius: '12px',
              background: config.method === 'carrier_grade' ? '#eff6ff' : '#fff',
              cursor: 'pointer',
              textAlign: 'center',
              transition: 'all 0.2s'
            }}
          >
            <Globe size={32} color={config.method === 'carrier_grade' ? '#3b82f6' : '#9ca3af'} style={{ margin: '0 auto 0.75rem' }} />
            <div style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.25rem' }}>Carrier Grade / SIP Trunk</div>
            <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
              Desvio de llamadas desde el operador al servidor SIP.
            </div>
          </button>
        </div>
        {errors.method && <p style={{ color: '#dc2626', fontSize: '0.85rem', marginTop: '0.5rem' }}>{errors.method}</p>}
      </div>

      {/* FXO Gateway Form */}
      {config.method === 'fxo_gateway' && (
        <div style={{ background: '#f9fafb', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem', border: '1px solid #e5e7eb' }}>
          <h3 style={{ fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Server size={20} color="#3b82f6" /> Configuracion del Gateway FXO
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={labelStyle}>IP del Gateway</label>
              <input
                type="text"
                placeholder="192.168.1.100"
                value={config.fxo_gateway.ip}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  fxo_gateway: { ...prev.fxo_gateway, ip: e.target.value }
                }))}
                style={inputStyle}
              />
              {errors.gateway_ip && <p style={errorStyle}>{errors.gateway_ip}</p>}
            </div>
            <div>
              <label style={labelStyle}>Puerto SIP</label>
              <input
                type="number"
                value={config.fxo_gateway.sip_port}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  fxo_gateway: { ...prev.fxo_gateway, sip_port: parseInt(e.target.value) || 5060 }
                }))}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={labelStyle}>Usuario SIP</label>
              <input
                type="text"
                placeholder="gateway"
                value={config.fxo_gateway.user}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  fxo_gateway: { ...prev.fxo_gateway, user: e.target.value }
                }))}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Contrasena</label>
              <input
                type="password"
                placeholder="********"
                value={config.fxo_gateway.password}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  fxo_gateway: { ...prev.fxo_gateway, password: e.target.value }
                }))}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={labelStyle}>Puertos FXO</label>
              <input
                type="number"
                min="1"
                max="24"
                value={config.fxo_gateway.fxo_ports}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  fxo_gateway: { ...prev.fxo_gateway, fxo_ports: parseInt(e.target.value) || 4 }
                }))}
                style={inputStyle}
              />
              <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Lineas analogicas conectadas al gateway</span>
            </div>
            <div>
              <label style={labelStyle}>Codec</label>
              <select
                value={config.fxo_gateway.codec}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  fxo_gateway: { ...prev.fxo_gateway, codec: e.target.value }
                }))}
                style={inputStyle}
              >
                <option value="ulaw">G.711 ulaw (Norteamerica)</option>
                <option value="alaw">G.711 alaw (Europa/Latam)</option>
                <option value="g729">G.729 (Bajo ancho de banda)</option>
              </select>
            </div>
          </div>

          {/* DIDs para FXO */}
          <DIDList
            dids={config.fxo_gateway.dids}
            method="fxo_gateway"
            addDID={addDID}
            removeDID={removeDID}
            updateDID={updateDID}
          />
        </div>
      )}

      {/* Carrier Grade Form */}
      {config.method === 'carrier_grade' && (
        <div style={{ background: '#f9fafb', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem', border: '1px solid #e5e7eb' }}>
          <h3 style={{ fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Globe size={20} color="#3b82f6" /> Configuracion Carrier Grade / SIP Trunk
          </h3>

          <div style={{ marginBottom: '1rem' }}>
            <label style={labelStyle}>Host del Proveedor SIP</label>
            <input
              type="text"
              placeholder="sip.proveedor.com"
              value={config.carrier_grade.host}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                carrier_grade: { ...prev.carrier_grade, host: e.target.value }
              }))}
              style={inputStyle}
            />
            {errors.carrier_host && <p style={errorStyle}>{errors.carrier_host}</p>}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={labelStyle}>Usuario SIP</label>
              <input
                type="text"
                placeholder="usuario_sip"
                value={config.carrier_grade.user}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  carrier_grade: { ...prev.carrier_grade, user: e.target.value }
                }))}
                style={inputStyle}
              />
              {errors.carrier_user && <p style={errorStyle}>{errors.carrier_user}</p>}
            </div>
            <div>
              <label style={labelStyle}>Contrasena</label>
              <input
                type="password"
                placeholder="********"
                value={config.carrier_grade.password}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  carrier_grade: { ...prev.carrier_grade, password: e.target.value }
                }))}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={labelStyle}>Caller ID Saliente</label>
              <input
                type="text"
                placeholder="+5215512345678"
                value={config.carrier_grade.outbound_caller_id}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  carrier_grade: { ...prev.carrier_grade, outbound_caller_id: e.target.value }
                }))}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Tipo de Autenticacion</label>
              <select
                value={config.carrier_grade.auth_type}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  carrier_grade: { ...prev.carrier_grade, auth_type: e.target.value }
                }))}
                style={inputStyle}
              >
                <option value="register">Register (usuario + contrasena)</option>
                <option value="ip_auth">IP Auth (sin credenciales)</option>
              </select>
            </div>
          </div>

          {/* DIDs para Carrier Grade */}
          <DIDList
            dids={config.carrier_grade.dids}
            method="carrier_grade"
            addDID={addDID}
            removeDID={removeDID}
            updateDID={updateDID}
          />
        </div>
      )}

      {/* Test Result */}
      {testResult && (
        <div style={{
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1rem',
          background: testResult.reachable ? '#ecfdf5' : '#fef2f2',
          border: `1px solid ${testResult.reachable ? '#a7f3d0' : '#fecaca'}`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          {testResult.reachable
            ? <CheckCircle size={20} color="#10b981" />
            : <XCircle size={20} color="#ef4444" />
          }
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{testResult.message}</div>
            {testResult.target && (
              <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{testResult.target}</div>
            )}
          </div>
        </div>
      )}

      {/* Save Result */}
      {saveResult && (
        <div style={{
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1rem',
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
          <span style={{ fontSize: '0.9rem' }}>{saveResult.message}</span>
        </div>
      )}

      {/* Action Buttons */}
      {config.method && (
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={testConnection}
            disabled={testing}
            style={{
              ...btnStyle,
              background: '#f3f4f6',
              color: '#374151',
              border: '1px solid #d1d5db'
            }}
          >
            {testing
              ? <Loader size={16} className="animate-spin" />
              : <Zap size={16} />
            }
            {testing ? 'Probando...' : 'Probar Conexion'}
          </button>

          <button
            onClick={saveConfig}
            disabled={saving}
            style={{
              ...btnStyle,
              background: '#3b82f6',
              color: '#fff',
              border: '1px solid #3b82f6'
            }}
          >
            {saving
              ? <Loader size={16} className="animate-spin" />
              : <Save size={16} />
            }
            {saving ? 'Guardando...' : 'Guardar Configuracion'}
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================
// Sub-componente: Lista de DIDs
// ============================================
function DIDList({ dids, method, addDID, removeDID, updateDID }) {
  return (
    <div style={{ marginTop: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <label style={{ ...labelStyle, marginBottom: 0 }}>Numeros / DIDs Asignados</label>
        <button
          onClick={() => addDID(method)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem',
            background: 'none',
            border: '1px solid #3b82f6',
            color: '#3b82f6',
            borderRadius: '6px',
            padding: '0.25rem 0.75rem',
            cursor: 'pointer',
            fontSize: '0.8rem'
          }}
        >
          <Plus size={14} /> Agregar DID
        </button>
      </div>

      {dids.length === 0 ? (
        <div style={{ color: '#9ca3af', fontSize: '0.85rem', padding: '0.5rem 0' }}>
          No hay DIDs configurados. Agrega numeros para identificar las lineas entrantes.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {dids.map((did, index) => (
            <div key={index} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="+5215512345678"
                value={did.number}
                onChange={(e) => updateDID(method, index, 'number', e.target.value)}
                style={{ ...inputStyle, flex: 2 }}
              />
              <input
                type="text"
                placeholder="Etiqueta (ej: Linea Principal)"
                value={did.label}
                onChange={(e) => updateDID(method, index, 'label', e.target.value)}
                style={{ ...inputStyle, flex: 2 }}
              />
              <button
                onClick={() => removeDID(method, index)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#ef4444',
                  padding: '0.5rem'
                }}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================
// Estilos compartidos
// ============================================
const labelStyle = {
  display: 'block',
  fontSize: '0.85rem',
  fontWeight: 500,
  color: '#374151',
  marginBottom: '0.25rem'
};

const inputStyle = {
  width: '100%',
  padding: '0.5rem 0.75rem',
  border: '1px solid #d1d5db',
  borderRadius: '8px',
  fontSize: '0.9rem',
  background: '#fff',
  boxSizing: 'border-box'
};

const errorStyle = {
  color: '#dc2626',
  fontSize: '0.8rem',
  marginTop: '0.25rem'
};

const btnStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
  padding: '0.625rem 1.25rem',
  borderRadius: '8px',
  fontWeight: 600,
  fontSize: '0.9rem',
  cursor: 'pointer',
  transition: 'all 0.2s'
};
