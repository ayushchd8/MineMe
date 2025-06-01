// Lead interface - Used by LeadsTable
export interface Lead {
  Id?: string;
  Name?: string;
  Title?: string;
  Email?: string;
  Phone?: string;
  Company?: string;
  Status?: string;
  LeadSource?: string;
  LastActivityDate?: string;
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
    api_name: string;
    is_queryable: boolean;
    is_searchable: boolean;
    is_createable: boolean;
    is_updateable: boolean;
    is_deletable: boolean;
  }>;
} 