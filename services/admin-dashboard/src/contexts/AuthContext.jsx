import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const API_URL = 'http://localhost:8000';

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check if we have a valid API key stored
    const storedKey = localStorage.getItem('admin_api_key');
    if (storedKey) {
      validateApiKey(storedKey);
    } else {
      setLoading(false);
    }
  }, []);

  const validateApiKey = async (apiKey) => {
    try {
      const res = await fetch(`${API_URL}/api/admin/validate`, {
        headers: {
          'X-API-Key': apiKey
        }
      });

      if (res.ok) {
        localStorage.setItem('admin_api_key', apiKey);
        setIsAuthenticated(true);
        setError(null);
      } else {
        localStorage.removeItem('admin_api_key');
        setIsAuthenticated(false);
        setError('Clave API inválida');
      }
    } catch (err) {
      // If backend is not reachable, allow access with stored key
      // This is for offline installations
      if (localStorage.getItem('admin_api_key')) {
        setIsAuthenticated(true);
      }
      setError(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (apiKey) => {
    setLoading(true);
    setError(null);
    await validateApiKey(apiKey);
  };

  const logout = () => {
    localStorage.removeItem('admin_api_key');
    setIsAuthenticated(false);
  };

  const getAuthHeaders = () => {
    const apiKey = localStorage.getItem('admin_api_key');
    return apiKey ? { 'X-API-Key': apiKey } : {};
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      loading,
      error,
      login,
      logout,
      getAuthHeaders
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
