import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Calls from './pages/Calls';
import CallDetail from './pages/CallDetail';
import Agents from './pages/Agents';
import AgentProfile from './pages/AgentProfile';
import Analytics from './pages/Analytics';
import SentimentAnalytics from './pages/SentimentAnalytics';
import Vocabulary from './pages/Vocabulary';
import KnowledgeBase from './pages/KnowledgeBase';
import ConfigurationWizard from './pages/ConfigurationWizard';
import Telephony from './pages/Telephony';
import VoiceLab from './pages/VoiceLab';

// Loading spinner component
function LoadingScreen() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-primary)'
    }}>
      <div style={{
        width: '48px',
        height: '48px',
        border: '3px solid var(--border-color)',
        borderTopColor: '#3b82f6',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }} />
    </div>
  );
}

// Protected route wrapper
function ProtectedContent() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="app">
      <Sidebar />
      <Header />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/setup" element={<ConfigurationWizard />} />
          <Route path="/calls" element={<Calls />} />
          <Route path="/calls/:id" element={<CallDetail />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/agents/:id" element={<AgentProfile />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/emotions" element={<SentimentAnalytics />} />
          <Route path="/vocabulary" element={<Vocabulary />} />
          <Route path="/knowledge" element={<KnowledgeBase />} />
          <Route path="/telephony" element={<Telephony />} />
          <Route path="/voice-lab" element={<VoiceLab />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ProtectedContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
