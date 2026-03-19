import { createContext, useState, useEffect } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [admin, setAdmin] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('adminToken');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setAdmin({ token });
    }
    setLoading(false);

    // Add interceptor to handle 401 Unauthorized errors (expired session)
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          logout();
        }
        return Promise.reject(error);
      }
    );

    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  const login = async (username, password) => {
    try {
      const res = await axios.post('/api/auth/login', { username, password });
      const { token } = res.data;
      localStorage.setItem('adminToken', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setAdmin({ token, username });
      return true;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Login failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('adminToken');
    delete axios.defaults.headers.common['Authorization'];
    setAdmin(null);
  };

  return (
    <AuthContext.Provider value={{ admin, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
