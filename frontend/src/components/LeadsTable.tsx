import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

interface Lead {
  Name: string;
  Title?: string;
  Company?: string;
  Status?: string;
  LeadSource?: string;
  LastActivityDate?: string;
}

const LeadsTable: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [secondsSinceUpdate, setSecondsSinceUpdate] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  const fetchLeads = async (manual = false) => {
    if (manual) setRefreshing(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/leads`);
      setLeads(response.data.leads || []);
      const now = new Date();
      setLastUpdated(now);
      setSecondsSinceUpdate(0);
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || 'Failed to fetch leads');
    } finally {
      setLoading(false);
      if (manual) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLeads();
    const interval = setInterval(() => fetchLeads(), 60000); // 1 minute
    return () => clearInterval(interval);
  }, []);

  // Timer to update seconds since last update
  useEffect(() => {
    if (!lastUpdated) return;
    const timer = setInterval(() => {
      setSecondsSinceUpdate(Math.floor((Date.now() - lastUpdated.getTime()) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [lastUpdated]);

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 gap-2">
        <h2 className="text-xl font-semibold">Salesforce Leads</h2>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString()} ({secondsSinceUpdate} sec ago)
            </span>
          )}
          <button
            onClick={() => fetchLeads(true)}
            disabled={refreshing}
            className={`ml-2 px-3 py-1 rounded bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed`}
            title="Refresh now"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>
      {loading ? (
        <div className="py-8 text-center">Loading leads...</div>
      ) : error ? (
        <div className="bg-red-100 text-red-800 p-4 rounded mb-4">{error}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-200">
            <thead className="bg-gray-100">
              <tr>
                <th className="py-2 px-4 border-b text-left">Name</th>
                <th className="py-2 px-4 border-b text-left">Title</th>
                <th className="py-2 px-4 border-b text-left">Company</th>
                <th className="py-2 px-4 border-b text-left">Lead Status</th>
                <th className="py-2 px-4 border-b text-left">Lead Source</th>
                <th className="py-2 px-4 border-b text-left">Last Activity</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="py-2 px-4 border-b">{lead.Name}</td>
                  <td className="py-2 px-4 border-b">{lead.Title || '-'}</td>
                  <td className="py-2 px-4 border-b">{lead.Company || '-'}</td>
                  <td className="py-2 px-4 border-b">{lead.Status || '-'}</td>
                  <td className="py-2 px-4 border-b">{lead.LeadSource || '-'}</td>
                  <td className="py-2 px-4 border-b">{lead.LastActivityDate ? new Date(lead.LastActivityDate).toLocaleDateString() : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default LeadsTable; 