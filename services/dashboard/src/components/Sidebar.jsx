import { useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Phone,
    PhoneIncoming,
    Users,
    BarChart3,
    Settings,
    Headphones,
    MessageSquare,
    TrendingUp,
    Mic,
    BookOpen
} from 'lucide-react';

const navItems = [
    {
        section: 'Principal',
        items: [
            { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
            { path: '/calls', icon: Phone, label: 'Llamadas' },
            { path: '/agents', icon: Users, label: 'Agentes' },
        ]
    },
    {
        section: 'Análisis',
        items: [
            { path: '/analytics', icon: BarChart3, label: 'Analytics' },
            { path: '/emotions', icon: MessageSquare, label: 'Emociones' },
            { path: '/performance', icon: TrendingUp, label: 'Rendimiento' },
        ]
    },
    {
        section: 'Herramientas',
        items: [
            { path: '/telephony', icon: PhoneIncoming, label: 'Telefonía' },
            { path: '/vocabulary', icon: Mic, label: 'Vocabulario' },
            { path: '/knowledge', icon: BookOpen, label: 'Base Conocimiento' },
            { path: '/settings', icon: Settings, label: 'Configuración' },
        ]
    }
];

export default function Sidebar() {
    const location = useLocation();
    const navigate = useNavigate();

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <Headphones size={28} color="#3b82f6" />
                <h1>AI Call Center</h1>
            </div>

            <nav className="sidebar-nav">
                {navItems.map((section) => (
                    <div key={section.section} className="nav-section">
                        <div className="nav-section-title">{section.section}</div>
                        {section.items.map((item) => (
                            <div
                                key={item.path}
                                className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
                                onClick={() => navigate(item.path)}
                            >
                                <item.icon size={20} />
                                <span>{item.label}</span>
                            </div>
                        ))}
                    </div>
                ))}
            </nav>

            <div style={{
                padding: '1rem',
                background: 'rgba(59, 130, 246, 0.1)',
                borderRadius: '12px',
                marginTop: 'auto'
            }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                    🤖 AI Status
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{
                        width: '8px',
                        height: '8px',
                        background: '#10b981',
                        borderRadius: '50%'
                    }} />
                    <span style={{ fontSize: '0.85rem' }}>Operativo</span>
                </div>
            </div>
        </aside>
    );
}
