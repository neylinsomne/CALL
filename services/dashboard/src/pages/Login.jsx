import { useState } from 'react';
import { useAuth } from '../App';
import { Headphones, Mail, Lock, AlertCircle } from 'lucide-react';

export default function Login() {
    const { login } = useAuth();
    const [email, setEmail] = useState('admin@callcenter.com');
    const [password, setPassword] = useState('admin123');
    const [error, setError] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!login(email, password)) {
            setError('Credenciales incorrectas');
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'var(--bg-primary)'
        }}>
            <div style={{
                width: '100%',
                maxWidth: '400px',
                padding: '2rem'
            }}>
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div style={{
                        width: '64px',
                        height: '64px',
                        borderRadius: '16px',
                        background: 'var(--gradient-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 1rem'
                    }}>
                        <Headphones size={32} color="white" />
                    </div>
                    <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>AI Call Center</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Inicia sesión para continuar</p>
                </div>

                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                            Correo electrónico
                        </label>
                        <div style={{ position: 'relative' }}>
                            <Mail size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                            <input
                                type="email"
                                className="input"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                style={{ paddingLeft: '40px' }}
                            />
                        </div>
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                            Contraseña
                        </label>
                        <div style={{ position: 'relative' }}>
                            <Lock size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                            <input
                                type="password"
                                className="input"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                style={{ paddingLeft: '40px' }}
                            />
                        </div>
                    </div>

                    {error && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.75rem',
                            background: 'rgba(239, 68, 68, 0.1)',
                            borderRadius: '8px',
                            marginBottom: '1rem',
                            color: 'var(--accent-red)',
                            fontSize: '0.9rem'
                        }}>
                            <AlertCircle size={18} />
                            {error}
                        </div>
                    )}

                    <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                        Iniciar Sesión
                    </button>
                </form>

                <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Usuarios de prueba:</div>
                    <div style={{ fontSize: '0.85rem' }}>
                        <div>admin@callcenter.com / admin123</div>
                        <div>supervisor@callcenter.com / super123</div>
                        <div>agent@callcenter.com / agent123</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
