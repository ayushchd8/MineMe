// Salesforce Object
export interface SalesforceObject {
  id: number;
  name: string;
  api_name: string;
  description?: string;
  is_active: boolean;
  last_sync_time?: string;
}

// Salesforce Record
export interface SalesforceRecord {
  id: number;
  sf_id: string;
  data: any;
  last_modified_date?: string;
  is_deleted: boolean;
}

// Sync Log
export interface SyncLog {
  id: number;
  object_id?: number;
  object_name?: string;
  type: 'full' | 'incremental';
  status: 'started' | 'completed' | 'failed';
  start_time: string;
  end_time?: string;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_deleted: number;
  error_message?: string;
}

// Sync Status
export interface SyncStatus {
  object: {
    id: number;
    name: string;
    api_name: string;
  };
  last_sync_time?: string;
  latest_sync?: SyncLog;
}

// API Response Types
export interface ObjectsResponse {
  objects: SalesforceObject[];
}

export interface RecordsResponse {
  object: {
    id: number;
    name: string;
    api_name: string;
  };
  records: SalesforceRecord[];
  total: number;
  offset: number;
  limit?: number;
}

export interface SearchResponse {
  query: string;
  results: Array<{
    id: number;
    sf_id: string;
    object: {
      id: number;
      name: string;
      api_name: string;
    };
    data: any;
  }>;
  count: number;
}

export interface SyncStatusResponse {
  objects: SyncStatus[];
}

export interface SyncLogsResponse {
  logs: SyncLog[];
  total: number;
  offset: number;
  limit: number;
}

export interface SyncResult {
  processed: number;
  created: number;
  updated: number;
  deleted: number;
}

export interface SyncObjectResponse {
  success: boolean;
  object_id: number;
  sync_type: 'full' | 'incremental';
  result: SyncResult;
}

export interface SyncAllResponse {
  success: boolean;
  sync_type: 'full' | 'incremental';
  results: Array<{
    object_id: number;
    object_name: string;
    success: boolean;
    result: SyncResult;
  }>;
} 