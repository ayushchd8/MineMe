import axios from 'axios';

// Create axios instance with base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
};

export default apiExports; 