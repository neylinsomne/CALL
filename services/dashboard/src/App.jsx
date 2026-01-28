import { useState, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { authenticateUser, MOCK_USERS } from './data/mockData';
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

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

function App() {
    const [user, setUser] = useState(() => {
        // Auto-login for demo
        const saved = localStorage.getItem('user');
        return saved ? JSON.parse(saved) : MOCK_USERS[0]; // Default to admin
    });

    const login = (email, password) => {
        const user = authenticateUser(email, password);
        if (user) {
            setUser(user);
            localStorage.setItem('user', JSON.stringify(user));
            return true;
        }
        return false;
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('user');
    };

    if (!user) {
        return (
            <AuthContext.Provider value={{ user, login, logout }}>
                <Login />
            </AuthContext.Provider>
        );
    }

    return (
        <AuthContext.Provider value={{ user, login, logout }}>
            <BrowserRouter>
                <div className="app">
                    <Sidebar />
                    <Header />
                    <main className="main-content">
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/calls" element={<Calls />} />
                            <Route path="/calls/:id" element={<CallDetail />} />
                            <Route path="/agents" element={<Agents />} />
                            <Route path="/agents/:id" element={<AgentProfile />} />
                            <Route path="/analytics" element={<Analytics />} />
                            <Route path="/emotions" element={<SentimentAnalytics />} />
                            <Route path="/vocabulary" element={<Vocabulary />} />
                            <Route path="/knowledge" element={<KnowledgeBase />} />
                            <Route path="*" element={<Navigate to="/" />} />
                        </Routes>
                    </main>
                </div>
            </BrowserRouter>
        </AuthContext.Provider>
    );
}

export default App;

