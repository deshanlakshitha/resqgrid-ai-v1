'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { authAPI } from './api';

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: string;
  organization?: string | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  ready: false,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  // Restore session on mount
  useEffect(() => {
    const restore = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const { data } = await authAPI.getProfile();
          setUser(data);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
      setReady(true);
    };
    restore();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data: tokens } = await authAPI.login(email, password);
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    const { data: profile } = await authAPI.getProfile();
    setUser(profile);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, ready, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
