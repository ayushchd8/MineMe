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
      // You can emit an event or dispatch an action here to trigger login
      window.dispatchEvent(new CustomEvent('auth-required'));
    }
    return Promise.reject(error);
  }
);

// Export the api instance for use in components
export { api };

// Salesforce Objects API
export const getObjects = async () => {
  const response = await api.get('/objects');
  return response.data;
};

export const getObject = async (id: number) => {
  const response = await api.get(`/objects/${id}`);
  return response.data;
};

export const registerObject = async (apiName: string) => {
  const response = await api.post('/objects', { api_name: apiName });
  return response.data;
};

export const updateObject = async (id: number, data: any) => {
  const response = await api.put(`/objects/${id}`, data);
  return response.data;
};

export const deleteObject = async (id: number) => {
  const response = await api.delete(`/objects/${id}`);
  return response.data;
};

// Salesforce Records API
export const getRecordsByObject = async (objectId: number, params = {}) => {
  const response = await api.get(`/records/object/${objectId}`, { params });
  return response.data;
};

export const getRecordBySfId = async (sfId: string) => {
  const response = await api.get(`/records/${sfId}`);
  return response.data;
};

export const searchRecords = async (query: string, objectId?: number) => {
  const params = { q: query, ...(objectId ? { object_id: objectId } : {}) };
  const response = await api.get('/records/search', { params });
  return response.data;
};

// Synchronization API
export const getSyncStatus = async () => {
  const response = await api.get('/sync/status');
  return response.data;
};

export const getSyncLogs = async (params = {}) => {
  const response = await api.get('/sync/logs', { params });
  return response.data;
};

export const syncObject = async (objectId: number, syncType = 'incremental') => {
  const response = await api.post(`/sync/object/${objectId}`, { type: syncType });
  return response.data;
};

export const syncAllObjects = async (syncType = 'incremental') => {
  const response = await api.post('/sync/all', { type: syncType });
  return response.data;
};

// Salesforce Status and Objects
export const getSalesforceStatus = async () => {
  const response = await api.get('/salesforce/status');
  return response.data;
};

export const getSalesforceObjects = async () => {
  const response = await api.get('/salesforce/objects');
  return response.data;
};

export const getLeads = async () => {
  const response = await api.get('/leads');
  return response.data;
};

const apiExports = {
  getObjects,
  getObject,
  registerObject,
  updateObject,
  deleteObject,
  getRecordsByObject,
  getRecordBySfId,
  searchRecords,
  getSyncStatus,
  getSyncLogs,
  syncObject,
  syncAllObjects,
  getSalesforceStatus,
  getSalesforceObjects,
  getLeads,
}; 

export default apiExports; 