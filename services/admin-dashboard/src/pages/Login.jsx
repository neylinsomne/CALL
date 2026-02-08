import { useState } from 'react';
import { Shield, Key, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const [apiKey, setApiKey] = useState('');
  const { login, loading, error } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (apiKey.trim()) {
      await login(apiKey.trim());
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%)'
    }}>
      <div style={{
        background: 'var(--bg-card)',
        borderRadius: '16px',
        padding: '2.5rem',
        width: '100%',
        maxWidth: '420px',
        border: '1px solid var(--border-color)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '16px',
            background: 'rgba(139, 92, 246, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem'
          }}>
            <Shield size={32} color="#8b5cf6" />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            Admin Dashboard
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Acceso restringido al equipo tecnico
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.85rem',
              fontWeight: 500,
              marginBottom: '0.5rem',
              color: 'var(--text-secondary)'
            }}>
              Clave API de Administrador
            </label>
            <div style={{ position: 'relative' }}>
              <Key size={18} style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)'
              }} />
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Ingresa la clave API..."
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem 0.875rem 2.75rem',
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontSize: '0.95rem'
                }}
                autoFocus
              />
            </div>
          </div>

          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1rem',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              marginBottom: '1.5rem',
              color: '#ef4444',
              fontSize: '0.875rem'
            }}>
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !apiKey.trim()}
            className="btn btn-primary"
            style={{
              width: '100%',
              padding: '0.875rem',
              fontSize: '1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem'
            }}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Verificando...
              </>
            ) : (
              <>
                <Shield size={18} />
                Acceder
              </>
            )}
          </button>
        </form>

        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          background: 'rgba(245, 158, 11, 0.1)',
          borderRadius: '8px',
          border: '1px solid rgba(245, 158, 11, 0.2)'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 500, marginBottom: '0.25rem' }}>
            Nota de Seguridad
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            La clave API se configura en ADMIN_API_KEY del archivo .env del backend.
            Este dashboard solo debe ser accesible desde la red interna.
          </div>
        </div>
      </div>
    </div>
  );
}
