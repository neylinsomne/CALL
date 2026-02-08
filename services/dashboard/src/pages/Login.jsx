import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Headphones, Key, AlertCircle, Loader2, Mail, HelpCircle } from 'lucide-react';

export default function Login() {
  const { login, loading, error } = useAuth();
  const [token, setToken] = useState('');
  const [localError, setLocalError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');

    if (!token.trim()) {
      setLocalError('Ingresa tu token de acceso');
      return;
    }

    if (!token.startsWith('cc_')) {
      setLocalError('El token debe comenzar con "cc_"');
      return;
    }

    const success = await login(token.trim());
    if (!success) {
      setLocalError('Token invalido o expirado. Contacta al administrador.');
    }
  };

  const displayError = localError || error;

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        padding: '2rem'
      }}>
        {/* Logo and Title */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            width: '72px',
            height: '72px',
            borderRadius: '18px',
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem',
            boxShadow: '0 10px 30px rgba(59, 130, 246, 0.3)'
          }}>
            <Headphones size={36} color="white" />
          </div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem', fontWeight: 700 }}>
            AI Call Center
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Ingresa tu token de acceso para continuar
          </p>
        </div>

        {/* Login Form */}
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: '16px',
          padding: '2rem',
          border: '1px solid var(--border-color)',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)'
        }}>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontSize: '0.9rem',
                color: 'var(--text-secondary)',
                fontWeight: 500
              }}>
                Token de Acceso
              </label>
              <div style={{ position: 'relative' }}>
                <Key size={18} style={{
                  position: 'absolute',
                  left: '14px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)'
                }} />
                <input
                  type="password"
                  className="input"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="cc_xxxxxxxx_xxxxxxxxxxxxxxxx"
                  style={{
                    paddingLeft: '44px',
                    fontSize: '0.95rem',
                    height: '48px'
                  }}
                  autoFocus
                />
              </div>
            </div>

            {displayError && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.875rem',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '10px',
                marginBottom: '1.5rem',
                color: '#ef4444',
                fontSize: '0.9rem'
              }}>
                <AlertCircle size={18} />
                {displayError}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{
                width: '100%',
                height: '48px',
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
                'Iniciar Sesion'
              )}
            </button>
          </form>
        </div>

        {/* Help Section */}
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          background: 'rgba(59, 130, 246, 0.1)',
          borderRadius: '12px',
          border: '1px solid rgba(59, 130, 246, 0.2)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85rem',
            color: '#3b82f6',
            marginBottom: '0.5rem',
            fontWeight: 500
          }}>
            <HelpCircle size={16} />
            ¿No tienes un token?
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            Contacta al administrador de tu organizacion para obtener tu token de acceso.
          </p>
          <a
            href="mailto:soporte@callcenter-ai.com"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.8rem',
              color: '#3b82f6',
              textDecoration: 'none'
            }}
          >
            <Mail size={14} />
            soporte@callcenter-ai.com
          </a>
        </div>
      </div>
    </div>
  );
}
