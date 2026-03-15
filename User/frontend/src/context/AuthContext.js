import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiPost, apiGet } from '../api/client';

const AuthContext = createContext(null);

const TOKEN_KEY = 'chatbot_access_token';
const USER_KEY = 'chatbot_user';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  const isAdmin = user?.role === 'admin';

  const persistAuth = useCallback((newToken, newUser) => {
    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken);
      setToken(newToken);
    } else {
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
    }
    if (newUser) {
      localStorage.setItem(USER_KEY, JSON.stringify(newUser));
      setUser(newUser);
    } else {
      localStorage.removeItem(USER_KEY);
      setUser(null);
    }
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await apiPost('/auth/login', { email, password });
    if (!data.success) {
      throw new Error(data.error || 'Login failed');
    }
    persistAuth(data.access_token, data.user);
    return data.user;
  }, [persistAuth]);

  const register = useCallback(async (email, password, fullName = '') => {
    const data = await apiPost('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    if (!data.success) {
      throw new Error(data.error || 'Registration failed');
    }
    persistAuth(data.access_token, data.user);
    return data.user;
  }, [persistAuth]);

  const logout = useCallback(async () => {
    const t = token || localStorage.getItem(TOKEN_KEY);
    if (t) {
      try {
        await apiPost('/auth/logout', {}, t);
      } catch (_) {}
    }
    persistAuth(null, null);
  }, [persistAuth, token]);

  const refreshUser = useCallback(async () => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) {
      setUser(null);
      setToken(null);
      setLoading(false);
      return;
    }
    try {
      const data = await apiGet('/me', t);
      if (data.success && data.user) {
        setToken(t);
        setUser(data.user);
        localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      } else {
        persistAuth(null, null);
      }
    } catch (_) {
      persistAuth(null, null);
    } finally {
      setLoading(false);
    }
  }, [persistAuth]);

  useEffect(() => {
    const savedUser = localStorage.getItem(USER_KEY);
    const savedToken = localStorage.getItem(TOKEN_KEY);
    if (savedToken && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
        setToken(savedToken);
        refreshUser();
        return;
      } catch (_) {}
    }
    setLoading(false);
  }, [refreshUser]);

  const value = {
    user,
    token,
    loading,
    isAdmin,
    login,
    register,
    logout,
    refreshUser,
    isAuthenticated: !!token && !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
