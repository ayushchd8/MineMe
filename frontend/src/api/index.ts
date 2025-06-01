import axios from 'axios';
import { Lead, SalesforceStatusResponse, SalesforceObjectsResponse, SyncStatus } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// Function to get session ID from various sources
const getSessionId = (): string | null => {
  // Check URL parameters (for OAuth callback)
  const urlParams = new URLSearchParams(window.location.search);
  const urlSessionId = urlParams.get('session_id');
  if (urlSessionId) {
    return urlSessionId;
  }
  
  // Then check localStorage (if we stored it there)
  const storedSessionId = localStorage.getItem('sf_session_id');
  if (storedSessionId) {
    return storedSessionId;
  }
  
  return null;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for session cookies
  timeout: 10000,
});

// Request interceptor to log requests and include session ID
api.interceptors.request.use(
  (config) => {
    // Session ID to headers if available
    const sessionId = getSessionId();
    if (sessionId) {
      config.headers['X-Session-ID'] = sessionId;
    }
    
    console.log('API Request:', config.method?.toUpperCase(), config.url, {
      headers: config.headers,
      withCredentials: config.withCredentials,
      sessionId: sessionId
    });
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor to handle authentication errors
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.config?.url, error.response?.data);
    if (error.response?.status === 401) {
      // Handle 401 errors - redirect to login
      console.log('Authentication required');
      window.dispatchEvent(new CustomEvent('auth-required'));
    }
    return Promise.reject(error);
  }
);

// Export the api instance for use in components
export { api };

export const getSalesforceStatus = async (): Promise<SalesforceStatusResponse> => {
  const response = await api.get('/salesforce/status');
  return response.data;
};

export const getSalesforceObjects = async (): Promise<SalesforceObjectsResponse> => {
  const response = await api.get('/salesforce/objects');
  return response.data;
};

export const getLeads = async (): Promise<{ records: Lead[]; count: number; source: string }> => {
  const response = await api.get('/leads');
  return response.data;
};

export const syncLeads = async (syncType: 'full' | 'incremental' = 'incremental') => {
  const response = await api.post('/sync/leads', { sync_type: syncType });
  return response.data;
};

export const getSyncStatus = async (): Promise<SyncStatus> => {
  const response = await api.get('/sync/status');
  return response.data;
};

const apiExports = {
  getSalesforceStatus,
  getSalesforceObjects,
  getLeads,
  syncLeads,
  getSyncStatus,
};

export default apiExports; 