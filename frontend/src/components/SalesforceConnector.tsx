import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getSalesforceStatus, getSalesforceObjects } from '../api';

const SalesforceConnector: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [status, setStatus] = useState<'loading' | 'connected' | 'error'>('loading');
  const [message, setMessage] = useState<string>('Connecting to Salesforce...');
  const [organizationName, setOrganizationName] = useState<string>('');
  const [objects, setObjects] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setStatus('error');
      setMessage('Please authenticate with Salesforce first');
      return;
    }

    // Check the connection to Salesforce
    const checkConnection = async () => {
      try {
        setStatus('loading');
        setMessage('Checking Salesforce connection...');
        setError(null);
        
        const data = await getSalesforceStatus();
        
        if (data.status === 'connected') {
          setStatus('connected');
          setOrganizationName(data.organization || 'Unknown Organization');
          setMessage('Successfully connected to Salesforce!');
          
          // Fetch available objects
          fetchObjects();
        } else if (data.status === 'unauthenticated') {
          setStatus('error');
          setMessage('Please authenticate with Salesforce first');
        } else {
          setStatus('error');
          setMessage(`Connection error: ${data.message || 'Unknown error'}`);
        }
      } catch (err: any) {
        setStatus('error');
        setError(err.message || 'Failed to connect to Salesforce');
        setMessage(`Error: ${err.response?.data?.message || err.message || 'Please authenticate with Salesforce first'}`);
      }
    };
    
    const fetchObjects = async () => {
      try {
        setMessage('Fetching Salesforce objects...');
        
        const data = await getSalesforceObjects();
        setObjects(data.objects || []);
        setMessage('Successfully fetched Salesforce objects!');
      } catch (err: any) {
        setError(err.message || 'Failed to fetch Salesforce objects');
        setMessage(`Error fetching objects: ${err.response?.data?.message || err.message || 'Authentication required'}`);
      }
    };
    
    checkConnection();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="bg-white shadow-md rounded-lg p-6 max-w-4xl mx-auto mt-8">
        <h2 className="text-2xl font-semibold mb-4">Salesforce Connection Status</h2>
        <div className="p-4 mb-6 rounded-md bg-yellow-100 text-yellow-800">
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full mr-2 bg-yellow-500"></div>
            <span className="font-medium">Authentication required</span>
          </div>
          <div className="mt-2 text-sm">
            Please authenticate with Salesforce using the button above to view connection status and available objects.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow-md rounded-lg p-6 max-w-4xl mx-auto mt-8">
      <h2 className="text-2xl font-semibold mb-4">Salesforce Connection Status</h2>
      
      <div className={`p-4 mb-6 rounded-md ${
        status === 'connected' ? 'bg-green-100 text-green-800' :
        status === 'error' ? 'bg-red-100 text-red-800' :
        'bg-blue-100 text-blue-800'
      }`}>
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-2 ${
            status === 'connected' ? 'bg-green-500' :
            status === 'error' ? 'bg-red-500' :
            'bg-blue-500 animate-pulse'
          }`}></div>
          <span className="font-medium">{message}</span>
        </div>
        
        {error && (
          <div className="mt-2 text-sm">
            {error}
          </div>
        )}
      </div>
      
      {status === 'connected' && (
        <div>
          <div className="mb-4">
            <h3 className="text-lg font-medium mb-2">Organization</h3>
            <p className="bg-gray-100 p-3 rounded">{organizationName}</p>
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Available Objects</h3>
            {objects.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="py-2 px-4 border-b text-left">Name</th>
                      <th className="py-2 px-4 border-b text-left">API Name</th>
                      <th className="py-2 px-4 border-b text-left">Capabilities</th>
                    </tr>
                  </thead>
                  <tbody>
                    {objects.map((obj, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="py-2 px-4 border-b">{obj.name}</td>
                        <td className="py-2 px-4 border-b">{obj.api_name}</td>
                        <td className="py-2 px-4 border-b">
                          <div className="flex flex-wrap gap-1">
                            {obj.is_queryable && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                Queryable
                              </span>
                            )}
                            {obj.is_createable && (
                              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                Createable
                              </span>
                            )}
                            {obj.is_updateable && (
                              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                                Updateable
                              </span>
                            )}
                            {obj.is_deletable && (
                              <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                                Deletable
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500">No objects found or still loading...</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesforceConnector; 