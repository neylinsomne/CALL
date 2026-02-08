import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check for stored token on mount
    const storedToken = localStorage.getItem('api_token');
    const storedUser = localStorage.getItem('user_info');

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      validateToken(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const validateToken = async (apiToken) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/me`, {
        headers: {
          'Authorization': `Bearer ${apiToken}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setUser(data);
        setToken(apiToken);
        localStorage.setItem('api_token', apiToken);
        localStorage.setItem('user_info', JSON.stringify(data));
        setError(null);
        return true;
      } else {
        // Token invalid or expired
        logout();
        setError('Token invalido o expirado');
        return false;
      }
    } catch (err) {
      console.error('Error validating token:', err);
      // If backend is unreachable, keep the stored session
      setError(null);
      return true;
    } finally {
      setLoading(false);
    }
  };

  const login = async (apiToken) => {
    setLoading(true);
    setError(null);
    const result = await validateToken(apiToken);
    return result;
  };

  const logout = () => {
    localStorage.removeItem('api_token');
    localStorage.removeItem('user_info');
    setUser(null);
    setToken(null);
  };

  const getAuthHeaders = () => {
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  };

  // Helper for authenticated API calls
  const fetchWithAuth = async (url, options = {}) => {
    const headers = {
      ...options.headers,
      ...getAuthHeaders()
    };
    return fetch(url.startsWith('http') ? url : `${API_URL}${url}`, {
      ...options,
      headers
    });
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      error,
      isAuthenticated: !!user,
      login,
      logout,
      getAuthHeaders,
      fetchWithAuth
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
