import React, { useState, useEffect, useCallback } from 'react';
import { getLeads, syncLeads, getSyncStatus } from '../api';

interface Lead {
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

interface SyncStatus {
  object_type: string;
  latest_sync?: {
    id: number;
    sync_type: string;
    status: string;
    start_time: string;
    end_time?: string;
    records_processed: number;
    records_created: number;
    records_updated: number;
    records_deleted: number;
  };
  recent_logs: Array<{
    id: number;
    sync_type: string;
    status: string;
    start_time: string;
    end_time?: string;
    records_processed: number;
    error_message?: string;
  }>;
  total_leads: number;
}

const LeadsTable: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<string>('');

  const fetchLeads = async () => {
    try {
      setLoading(true);
      const response = await getLeads();
      setLeads(response.records);
      setDataSource(response.source);
      setError(null);
    } catch (err) {
      setError('Failed to fetch leads');
      console.error('Error fetching leads:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSyncStatus = async () => {
    try {
      const status = await getSyncStatus();
      setSyncStatus(status);
    } catch (err) {
      console.error('Error fetching sync status:', err);
    }
  };

  const handleSync = useCallback(async (syncType: 'full' | 'incremental') => {
    try {
      setSyncing(true);
      setError(null);
      
      const result = await syncLeads(syncType);
      console.log('Sync result:', result);
      
      // Refresh data after sync
      await Promise.all([fetchLeads(), fetchSyncStatus()]);
      
    } catch (err) {
      setError(`Sync failed: ${err}`);
      console.error('Error during sync:', err);
    } finally {
      setSyncing(false);
    }
  }, []);

  useEffect(() => {
    const initializeData = async () => {
      // First, fetch current leads and sync status
      await Promise.all([fetchLeads(), fetchSyncStatus()]);
    };
    
    initializeData();
  }, []);

  // Effect to trigger automatic full sync on first visit
  useEffect(() => {
    const shouldAutoSync = () => {
      // Auto sync if: no leads AND no previous sync history
      return leads.length === 0 && 
             syncStatus && 
             !syncStatus.latest_sync && 
             syncStatus.recent_logs.length === 0;
    };

    if (!loading && !syncing && shouldAutoSync()) {
      console.log('First time visit detected - performing automatic full sync');
      handleSync('full');
    }
  }, [loading, leads, syncStatus, syncing, handleSync]);

  // Effect for automatic incremental sync every 60 seconds
  useEffect(() => {
    // Only start auto-sync if we have data (after initial sync)
    if (leads.length === 0) return;

    console.log('Setting up automatic incremental sync every 60 seconds');
    
    const interval = setInterval(() => {
      if (!syncing) {
        console.log('Performing automatic incremental sync');
        handleSync('incremental');
      }
    }, 60000); // 60 seconds

    return () => {
      console.log('Cleaning up automatic sync interval');
      clearInterval(interval);
    };
  }, [leads.length, syncing, handleSync]);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
        <div className="ml-4 text-gray-600">
          {syncing ? 'Syncing leads from Salesforce...' : 'Loading...'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Sync Status and Controls */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Lead Data Management</h3>
          <div className="flex space-x-2">
            <button
              onClick={() => handleSync('incremental')}
              disabled={syncing}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {syncing ? 'Syncing...' : 'Incremental Sync'}
            </button>
            <button
              onClick={() => handleSync('full')}
              disabled={syncing}
              className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {syncing ? 'Syncing...' : 'Full Sync'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Data Source:</span> {dataSource}
          </div>
          <div>
            <span className="font-medium">Total Leads:</span> {syncStatus?.total_leads || leads.length}
          </div>
          <div>
            <span className="font-medium">Last Sync:</span>{' '}
            {syncStatus?.latest_sync ? formatDate(syncStatus.latest_sync.end_time || syncStatus.latest_sync.start_time) : 'Never'}
          </div>
        </div>

        {leads.length > 0 && (
          <div className="mt-4 p-3 bg-blue-50 rounded-md">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></div>
              <p className="text-sm text-blue-700">
                <span className="font-medium">Auto-sync active:</span> Checking for updates every 60 seconds
              </p>
            </div>
          </div>
        )}

        {syncStatus?.latest_sync && (
          <div className="mt-4 p-3 bg-gray-50 rounded-md">
            <p className="text-sm text-gray-700">
              <span className="font-medium">Last sync details:</span>{' '}
              {syncStatus.latest_sync.sync_type} sync, {syncStatus.latest_sync.records_processed} processed, {syncStatus.latest_sync.records_created} created, {syncStatus.latest_sync.records_updated} updated
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Leads Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Leads ({leads.length})</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Salesforce Lead records
          </p>
        </div>
        
        {leads.length === 0 ? (
          <div className="text-center py-12">
            {syncing ? (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-4"></div>
                <p className="text-gray-600 font-medium">First time setup - syncing leads from Salesforce...</p>
                <p className="text-gray-500 text-sm mt-2">This may take a moment depending on the number of leads.</p>
              </div>
            ) : (
              <div>
                <p className="text-gray-500">No leads found.</p>
                <p className="text-gray-400 text-sm mt-2">
                  Click "Full Sync" to fetch leads from Salesforce.
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Company
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Lead Source
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {leads.map((lead) => (
                  <tr key={lead.Id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {lead.Name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.Title || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.Company || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.Status || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.LeadSource || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default LeadsTable; 