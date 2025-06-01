import axios from 'axios';

// Create axios instance with base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// Function to get session ID from various sources
const getSessionId = (): string | null => {
  // First check URL parameters (for OAuth callback)
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
  timeout: 10000, // 10 second timeout
});

// Add request interceptor to log requests and include session ID
api.interceptors.request.use(
  (config) => {
    // Add session ID to headers if available
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

// Salesforce Status and Objects - Used by SalesforceConnector
export const getSalesforceStatus = async () => {
  const response = await api.get('/salesforce/status');
  return response.data;
};

export const getSalesforceObjects = async () => {
  const response = await api.get('/salesforce/objects');
  return response.data;
};

// Leads API - Used by LeadsTable
export const getLeads = async () => {
  const response = await api.get('/leads');
  return response.data;
};

const apiExports = {
  getSalesforceStatus,
  getSalesforceObjects,
  getLeads,
};

export default apiExports; 