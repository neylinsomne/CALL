import { useState, useEffect } from 'react';
import {
  Cpu,
  HardDrive,
  Wifi,
  Server,
  CheckCircle,
  XCircle,
  Loader,
  RefreshCw,
  AlertTriangle,
  Play,
  Monitor
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function SystemSetup() {
  const [detecting, setDetecting] = useState(false);
  const [hardware, setHardware] = useState(null);
  const [services, setServices] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkServices();
  }, []);

  const detectHardware = async () => {
    setDetecting(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/config/detect-hardware`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setHardware(data);
      } else {
        setError('Error detectando hardware');
      }
    } catch (err) {
      setError('No se pudo conectar al backend. Verifica que este corriendo.');
    } finally {
      setDetecting(false);
    }
  };

  const checkServices = async () => {
    const serviceList = [
      { name: 'Backend API', port: 8000, url: `${API_URL}/health` },
      { name: 'TTS Service', port: 8001, url: 'http://localhost:8001/health' },
      { name: 'STT Service', port: 8002, url: 'http://localhost:8002/health' },
      { name: 'LLM Service', port: 8003, url: 'http://localhost:8003/health' },
      { name: 'Asterisk', port: 5060, url: null },
      { name: 'FreePBX', port: 8080, url: null },
    ];

    const results = await Promise.all(
      serviceList.map(async (service) => {
        if (service.url) {
          try {
            const res = await fetch(service.url, { method: 'GET', mode: 'no-cors' });
            return { ...service, status: 'online' };
          } catch {
            return { ...service, status: 'offline' };
          }
        }
        return { ...service, status: 'unknown' };
      })
    );

    setServices(results);
  };

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <Cpu size={28} color="#8b5cf6" />
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Setup del Sistema</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)' }}>
          Detecta hardware, verifica servicios y configura el sistema para un nuevo deployment.
        </p>
      </div>

      {/* Services Status */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Server size={20} /> Estado de Servicios
          </h3>
          <button className="btn btn-secondary" onClick={checkServices}>
            <RefreshCw size={16} /> Actualizar
          </button>
        </div>

        <div className="grid-3">
          {services.map((service) => (
            <div
              key={service.name}
              style={{
                padding: '1rem',
                background: 'var(--bg-primary)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem'
              }}
            >
              <div
                className={`status-dot ${service.status}`}
                style={{ width: '10px', height: '10px' }}
              />
              <div>
                <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{service.name}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Puerto {service.port}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Hardware Detection */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <HardDrive size={20} /> Deteccion de Hardware
          </h3>
          <button
            className="btn btn-primary"
            onClick={detectHardware}
            disabled={detecting}
          >
            {detecting ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
            {detecting ? 'Detectando...' : 'Detectar Hardware'}
          </button>
        </div>

        {error && (
          <div style={{
            padding: '1rem',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            color: '#ef4444',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            marginBottom: '1rem'
          }}>
            <AlertTriangle size={20} />
            {error}
          </div>
        )}

        {hardware && (
          <div className="grid-2" style={{ marginTop: '1rem' }}>
            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Tipo de Hardware
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600, textTransform: 'capitalize' }}>
                {hardware.hardware_type || 'No detectado'}
              </div>
            </div>

            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Canales PSTN Disponibles
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                {hardware.pstn_channels || 0}
              </div>
            </div>

            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Gateway Detectado
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {hardware.gateway_detected ? (
                  <>
                    <CheckCircle size={20} color="#10b981" />
                    <span style={{ color: '#10b981' }}>Si - {hardware.gateway_ip}</span>
                  </>
                ) : (
                  <>
                    <XCircle size={20} color="#6b7280" />
                    <span style={{ color: '#6b7280' }}>No</span>
                  </>
                )}
              </div>
            </div>

            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                DAHDI Detectado
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {hardware.dahdi_detected ? (
                  <>
                    <CheckCircle size={20} color="#10b981" />
                    <span style={{ color: '#10b981' }}>Si - {hardware.dahdi_channels?.length || 0} canales</span>
                  </>
                ) : (
                  <>
                    <XCircle size={20} color="#6b7280" />
                    <span style={{ color: '#6b7280' }}>No</span>
                  </>
                )}
              </div>
            </div>

            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: '8px', gridColumn: 'span 2' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Llamadas Concurrentes Maximas
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-blue)' }}>
                {hardware.max_concurrent_calls || 'N/A'}
              </div>
            </div>
          </div>
        )}

        {!hardware && !detecting && (
          <div style={{
            padding: '2rem',
            textAlign: 'center',
            color: 'var(--text-muted)'
          }}>
            <Monitor size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
            <p>Haz clic en "Detectar Hardware" para escanear el sistema</p>
          </div>
        )}
      </div>

      {/* Quick Links */}
      <div className="grid-3">
        <a
          href="/network"
          style={{
            padding: '1.5rem',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            textDecoration: 'none',
            color: 'inherit',
            display: 'block'
          }}
        >
          <Wifi size={24} color="#3b82f6" style={{ marginBottom: '0.75rem' }} />
          <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Configurar Red / NAT</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            IP publica, puertos RTP, DDNS
          </div>
        </a>

        <a
          href="/clients"
          style={{
            padding: '1.5rem',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            textDecoration: 'none',
            color: 'inherit',
            display: 'block'
          }}
        >
          <Server size={24} color="#10b981" style={{ marginBottom: '0.75rem' }} />
          <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Provisionar Cliente</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Crear extensiones y configuracion
          </div>
        </a>

        <a
          href="/status"
          style={{
            padding: '1.5rem',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            textDecoration: 'none',
            color: 'inherit',
            display: 'block'
          }}
        >
          <Monitor size={24} color="#f59e0b" style={{ marginBottom: '0.75rem' }} />
          <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Ver Estado</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Logs, servicios, metricas
          </div>
        </a>
      </div>
    </div>
  );
}
