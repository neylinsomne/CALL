import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import {
  Settings,
  Server,
  Users,
  Network,
  Activity,
  Shield,
  Terminal,
  Cpu,
  LogOut,
  Mail,
  Phone
} from 'lucide-react';

import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import SystemSetup from './pages/SystemSetup';
import ClientProvisioning from './pages/ClientProvisioning';
import SystemStatus from './pages/SystemStatus';
import NetworkConfig from './pages/NetworkConfig';

const navItems = [
  {
    section: 'Instalacion',
    items: [
      { path: '/', icon: Cpu, label: 'Setup del Sistema' },
      { path: '/network', icon: Network, label: 'Red / NAT' },
      { path: '/clients', icon: Users, label: 'Provisionar Cliente' },
    ]
  },
  {
    section: 'Monitoreo',
    items: [
      { path: '/status', icon: Activity, label: 'Estado del Sistema' },
    ]
  }
];

function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Settings size={28} color="#8b5cf6" />
        <div>
          <h1>AI Call Center</h1>
          <span>ADMIN</span>
        </div>
      </div>

      <nav>
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

      <div style={{ marginTop: 'auto' }}>
        {/* Soporte Tecnico */}
        <div style={{
          padding: '0.75rem',
          background: 'rgba(59, 130, 246, 0.1)',
          borderRadius: '8px',
          marginBottom: '0.75rem'
        }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            Soporte Tecnico
          </div>
          <a
            href="mailto:soporte@callcenter-ai.com"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.75rem',
              color: '#3b82f6',
              textDecoration: 'none',
              marginBottom: '0.25rem'
            }}
          >
            <Mail size={12} />
            soporte@callcenter-ai.com
          </a>
          <a
            href="tel:+573001234567"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              textDecoration: 'none'
            }}
          >
            <Phone size={12} />
            +57 300 123 4567
          </a>
        </div>

        {/* Panel Info + Logout */}
        <div style={{
          padding: '1rem',
          background: 'rgba(139, 92, 246, 0.1)',
          borderRadius: '12px'
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            Panel de Administracion
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            Solo para uso interno del equipo tecnico
          </div>
          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 0.75rem',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              color: '#ef4444',
              cursor: 'pointer',
              fontSize: '0.8rem',
              width: '100%',
              justifyContent: 'center'
            }}
          >
            <LogOut size={14} />
            Cerrar Sesion
          </button>
        </div>
      </div>
    </aside>
  );
}

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-primary)'
      }}>
        <div className="animate-spin" style={{
          width: '40px',
          height: '40px',
          border: '3px solid var(--border-color)',
          borderTopColor: '#8b5cf6',
          borderRadius: '50%'
        }} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return children;
}

function AppContent() {
  return (
    <ProtectedRoute>
      <div className="app">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<SystemSetup />} />
            <Route path="/network" element={<NetworkConfig />} />
            <Route path="/clients" element={<ClientProvisioning />} />
            <Route path="/status" element={<SystemStatus />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </ProtectedRoute>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
