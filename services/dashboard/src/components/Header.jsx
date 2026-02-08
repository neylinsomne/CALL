import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Search, Bell, ChevronDown, LogOut } from 'lucide-react';

export default function Header() {
    const { user, logout } = useAuth();
    const [showMenu, setShowMenu] = useState(false);

    // Get initials from org name
    const getInitials = (name) => {
        if (!name) return '??';
        const words = name.split(' ');
        return words.slice(0, 2).map(w => w[0]).join('').toUpperCase();
    };

    return (
        <header className="header">
            <div className="header-search">
                <Search size={18} color="var(--text-muted)" />
                <input type="text" placeholder="Buscar llamadas, agentes, clientes..." />
            </div>

            <div className="header-actions">
                <button className="btn-icon" style={{ position: 'relative' }}>
                    <Bell size={20} />
                    <span style={{
                        position: 'absolute',
                        top: '6px',
                        right: '6px',
                        width: '8px',
                        height: '8px',
                        background: 'var(--accent-red)',
                        borderRadius: '50%'
                    }} />
                </button>

                <div
                    className="header-user"
                    onClick={() => setShowMenu(!showMenu)}
                    style={{ position: 'relative' }}
                >
                    <div className="avatar" style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' }}>
                        {getInitials(user?.org_name)}
                    </div>
                    <div>
                        <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>{user?.org_name || 'Organizacion'}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                            {user?.plan_type || 'Plan'}
                        </div>
                    </div>
                    <ChevronDown size={16} color="var(--text-muted)" />

                    {showMenu && (
                        <div style={{
                            position: 'absolute',
                            top: '100%',
                            right: 0,
                            marginTop: '0.5rem',
                            background: 'var(--bg-card)',
                            border: '1px solid var(--border)',
                            borderRadius: '8px',
                            padding: '0.5rem',
                            minWidth: '150px',
                            boxShadow: 'var(--shadow-lg)',
                            zIndex: 100
                        }}>
                            <div
                                onClick={logout}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    padding: '0.5rem',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    color: 'var(--accent-red)'
                                }}
                            >
                                <LogOut size={16} />
                                Cerrar Sesión
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
