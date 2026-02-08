import { useState, useEffect } from 'react';
import {
  Activity,
  Server,
  Cpu,
  HardDrive,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Users,
  Phone
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function SystemStatus() {
  const [services, setServices] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const serviceList = [
    { name: 'Backend API', port: 8000, healthUrl: `${API_URL}/health` },
    { name: 'TTS (F5/Kokoro)', port: 8001, healthUrl: 'http://localhost:8001/health' },
    { name: 'STT (Whisper)', port: 8002, healthUrl: 'http://localhost:8002/health' },
    { name: 'LLM (LangChain)', port: 8003, healthUrl: 'http://localhost:8003/health' },
    { name: 'Audio Preprocess', port: 8004, healthUrl: 'http://localhost:8004/health' },
    { name: 'Asterisk PBX', port: 5060, healthUrl: null },
    { name: 'FreePBX UI', port: 8080, healthUrl: null },
    { name: 'PostgreSQL', port: 5432, healthUrl: null },
    { name: 'MariaDB', port: 3306, healthUrl: null },
  ];

  useEffect(() => {
    checkAllServices();
    const interval = setInterval(checkAllServices, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkAllServices = async () => {
    setLoading(true);

    const results = await Promise.all(
      serviceList.map(async (service) => {
        try {
          if (service.healthUrl) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            const res = await fetch(service.healthUrl, {
              method: 'GET',
              signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (res.ok) {
              const data = await res.json();
              return { ...service, status: 'online', details: data };
            }
            return { ...service, status: 'error', details: null };
          }
          // For services without health endpoint, assume unknown
          return { ...service, status: 'unknown', details: null };
        } catch (err) {
          return { ...service, status: 'offline', details: null };
        }
      })
    );

    setServices(results);
    setLastUpdate(new Date());

    // Get main backend health
    try {
      const res = await fetch(`${API_URL}/health`);
      if (res.ok) {
        setHealth(await res.json());
      }
    } catch {
      setHealth(null);
    }

    setLoading(false);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online': return <CheckCircle size={18} color="#10b981" />;
      case 'offline': return <XCircle size={18} color="#ef4444" />;
      case 'error': return <AlertTriangle size={18} color="#f59e0b" />;
      default: return <Clock size={18} color="#6b7280" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return '#10b981';
      case 'offline': return '#ef4444';
      case 'error': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const onlineCount = services.filter(s => s.status === 'online').length;
  const totalCount = services.length;

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <Activity size={28} color="#f59e0b" />
              <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Estado del Sistema</h1>
            </div>
            <p style={{ color: 'var(--text-secondary)' }}>
              Monitorea servicios, recursos y estado general del deployment.
            </p>
          </div>
          <button className="btn btn-secondary" onClick={checkAllServices} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Actualizando...' : 'Actualizar'}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '48px', height: '48px', borderRadius: '12px',
              background: 'rgba(16, 185, 129, 0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Server size={24} color="#10b981" />
            </div>
            <div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{onlineCount}/{totalCount}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Servicios Online</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '48px', height: '48px', borderRadius: '12px',
              background: 'rgba(59, 130, 246, 0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Phone size={24} color="#3b82f6" />
            </div>
            <div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>
                {health?.license?.active_calls || 0}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Llamadas Activas</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '48px', height: '48px', borderRadius: '12px',
              background: 'rgba(139, 92, 246, 0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Users size={24} color="#8b5cf6" />
            </div>
            <div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>
                {health?.license?.max_calls || 'N/A'}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Max Concurrentes</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '48px', height: '48px', borderRadius: '12px',
              background: health?.license?.valid ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              {health?.license?.valid ? <CheckCircle size={24} color="#10b981" /> : <AlertTriangle size={24} color="#ef4444" />}
            </div>
            <div>
              <div style={{ fontSize: '1rem', fontWeight: 700 }}>
                {health?.license?.valid ? 'Valida' : 'Sin Licencia'}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Licencia</div>
            </div>
          </div>
        </div>
      </div>

      {/* Services Grid */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">Servicios</h3>
          {lastUpdate && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Actualizado: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>

        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {services.map((service) => (
            <div
              key={service.name}
              style={{
                padding: '1rem',
                background: 'var(--bg-primary)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderLeft: `3px solid ${getStatusColor(service.status)}`
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {getStatusIcon(service.status)}
                <div>
                  <div style={{ fontWeight: 500 }}>{service.name}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Puerto {service.port}
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '0.8rem',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '12px',
                  background: `${getStatusColor(service.status)}22`,
                  color: getStatusColor(service.status),
                  textTransform: 'capitalize'
                }}>
                  {service.status}
                </div>
                {service.details?.version && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    v{service.details.version}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Backend Health Details */}
      {health && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Backend Health</h3>
          </div>
          <pre style={{
            background: 'var(--bg-primary)',
            padding: '1rem',
            borderRadius: '8px',
            fontSize: '0.85rem',
            overflow: 'auto',
            color: 'var(--text-secondary)'
          }}>
            {JSON.stringify(health, null, 2)}
          </pre>
        </div>
      )}

      {/* Quick Links */}
      <div className="grid-3" style={{ marginTop: '1.5rem' }}>
        <a
          href="http://localhost:8080"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: '1rem',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            textDecoration: 'none',
            color: 'inherit',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}
        >
          <Server size={20} color="#3b82f6" />
          <div>
            <div style={{ fontWeight: 500 }}>FreePBX</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>:8080</div>
          </div>
        </a>

        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: '1rem',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            textDecoration: 'none',
            color: 'inherit',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}
        >
          <Activity size={20} color="#10b981" />
          <div>
            <div style={{ fontWeight: 500 }}>API Docs</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>:8000/docs</div>
          </div>
        </a>

        <a
          href="http://localhost:3001"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: '1rem',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            textDecoration: 'none',
            color: 'inherit',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}
        >
          <Cpu size={20} color="#f59e0b" />
          <div>
            <div style={{ fontWeight: 500 }}>Dashboard Cliente</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>:3001</div>
          </div>
        </a>
      </div>
    </div>
  );
}
