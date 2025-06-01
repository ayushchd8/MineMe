// Lead interface - Used by LeadsTable
export interface Lead {
  Id: string;
  Name: string;
  Title?: string;
  Email?: string;
  Phone?: string;
  Company?: string;
  Status?: string;
  LeadSource?: string;
  LastActivityDate?: string;
  last_sync?: string;
}

// Salesforce Status Response - Used by SalesforceConnector
export interface SalesforceStatusResponse {
  status: 'connected' | 'error' | 'unauthenticated';
  organization?: string;
  sample_objects?: string[];
  message?: string;
}

// Salesforce Objects Response - Used by SalesforceConnector  
export interface SalesforceObjectsResponse {
  objects: Array<{
    name: string;
    label: string;
    custom: boolean;
  }>;
}

export interface SyncLog {
  id: number;
  sync_type: string;
  status: string;
  start_time: string;
  end_time?: string;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_deleted: number;
  error_message?: string;
}

export interface SyncStatus {
  object_type: string;
  latest_sync?: SyncLog;
  recent_logs: SyncLog[];
  total_leads: number;
} 