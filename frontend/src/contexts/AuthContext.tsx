import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for session cookies
});

interface User {
  Id: string;
  Name: string;
  Email: string;
  Username: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const checkAuthStatus = async () => {
    try {
      const response = await api.get('/auth/status');
      if (response.data.status === 'authenticated') {
        setIsAuthenticated(true);
        setUser(response.data.user);
        const newSessionId = response.data.session_id;
        setSessionId(newSessionId);
        // Store in localStorage for persistence
        if (newSessionId) {
          localStorage.setItem('sf_session_id', newSessionId);
        }
      } else {
        setIsAuthenticated(false);
        setUser(null);
        setSessionId(null);
        localStorage.removeItem('sf_session_id');
      }
    } catch (error) {
      console.log('Not authenticated');
      setIsAuthenticated(false);
      setUser(null);
      setSessionId(null);
      localStorage.removeItem('sf_session_id');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/auth/login');
      if (response.data.status === 'success') {
        // Redirect to Salesforce OAuth page
        window.location.href = response.data.auth_url;
      }
    } catch (error) {
      console.error('Login failed:', error);
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      setSessionId(null);
      localStorage.removeItem('sf_session_id');
    }
  };

  // Check authentication status on mount and load session from localStorage
  useEffect(() => {
    // Check if we have a stored session ID
    const storedSessionId = localStorage.getItem('sf_session_id');
    if (storedSessionId) {
      setSessionId(storedSessionId);
    }
    checkAuthStatus();
  }, []);

  // Handle OAuth callback
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const authSuccess = urlParams.get('auth');
    const callbackSessionId = urlParams.get('session_id');
    
    if (authSuccess === 'success') {
      // Store session_id if provided
      if (callbackSessionId) {
        setSessionId(callbackSessionId);
        localStorage.setItem('sf_session_id', callbackSessionId);
        console.log('Session ID captured from callback:', callbackSessionId);
      }
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
      // Check auth status after successful OAuth
      checkAuthStatus();
    } else if (authSuccess === 'error') {
      const errorMessage = urlParams.get('message');
      console.error('OAuth error:', errorMessage);
      alert(`Authentication failed: ${errorMessage}`);
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
      setIsLoading(false);
    }
  }, []);

  // Update API interceptor to include session_id
  useEffect(() => {
    const requestInterceptor = api.interceptors.request.use((config) => {
      if (sessionId) {
        config.headers['X-Session-ID'] = sessionId;
      }
      return config;
    });

    return () => {
      api.interceptors.request.eject(requestInterceptor);
    };
  }, [sessionId]);

  const value: AuthContextType = {
    isAuthenticated,
    user,
    isLoading,
    login,
    logout,
    checkAuthStatus,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 