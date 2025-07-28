import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiFetch } from '../utils/api';

interface User {
  sub: string;
  email: string;
  name?: string;
  picture?: string;
  role: 'admin' | 'developer' | 'student' | 'user';
}

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);

  const checkAuth = async () => {
    console.log('Checking auth status...');
    try {
      // Get token from localStorage
      const token = localStorage.getItem('auth_token');

      // Check auth status with backend
      const response = await apiFetch('/auth/status', {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });

      console.log('Auth response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Auth data:', data);
        if (data.authenticated) {
          setUser(data.user);
          setIsAuthenticated(true);
          // Save last authenticated user
          if (data.user?.email) {
            localStorage.setItem('lastAuthenticatedUser', data.user.email);
          }
        } else {
          setIsAuthenticated(false);
          setUser(null);
        }
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, user, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop()?.split(';').shift() || null;
  }
  return null;
}
