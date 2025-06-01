import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getObjects, syncObject } from '../api';
import { SalesforceObject } from '../types';

const ObjectsList: React.FC = () => {
  const [objects, setObjects] = useState<SalesforceObject[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [syncingObjectId, setSyncingObjectId] = useState<number | null>(null);

  const fetchObjects = async () => {
    try {
      setLoading(true);
      const response = await getObjects();
      setObjects(response.objects);
      setError(null);
    } catch (err) {
      setError('Failed to fetch Salesforce objects');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObjects();
  }, []);

  const handleSync = async (objectId: number) => {
    try {
      setSyncingObjectId(objectId);
      await syncObject(objectId);
      fetchObjects(); // Refresh the list
    } catch (err) {
      setError('Failed to sync object');
      console.error(err);
    } finally {
      setSyncingObjectId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        <p>{error}</p>
      </div>
    );
  }

  if (objects.length === 0) {
    return (
      <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-4">
        <p>No Salesforce objects found. Register an object to get started.</p>
        <Link to="/objects/register" className="mt-2 inline-block bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded">
          Register Object
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Salesforce Objects</h2>
        <Link to="/objects/register" className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded">
          Register New Object
        </Link>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200">
          <thead>
            <tr className="bg-gray-100">
              <th className="py-2 px-4 border-b text-left">Name</th>
              <th className="py-2 px-4 border-b text-left">API Name</th>
              <th className="py-2 px-4 border-b text-left">Status</th>
              <th className="py-2 px-4 border-b text-left">Last Sync</th>
              <th className="py-2 px-4 border-b text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {objects.map((obj) => (
              <tr key={obj.id} className="hover:bg-gray-50">
                <td className="py-2 px-4 border-b">
                  <Link to={`/objects/${obj.id}`} className="text-blue-500 hover:underline">
                    {obj.name}
                  </Link>
                </td>
                <td className="py-2 px-4 border-b">{obj.api_name}</td>
                <td className="py-2 px-4 border-b">
                  <span className={`px-2 py-1 rounded-full text-xs ${obj.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {obj.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="py-2 px-4 border-b">
                  {obj.last_sync_time ? new Date(obj.last_sync_time).toLocaleString() : 'Never'}
                </td>
                <td className="py-2 px-4 border-b">
                  <div className="flex space-x-2">
                    <Link 
                      to={`/records/object/${obj.id}`} 
                      className="text-blue-500 hover:text-blue-700"
                    >
                      View Records
                    </Link>
                    <button
                      onClick={() => handleSync(obj.id)}
                      disabled={syncingObjectId === obj.id}
                      className={`text-green-500 hover:text-green-700 ${syncingObjectId === obj.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {syncingObjectId === obj.id ? 'Syncing...' : 'Sync Now'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ObjectsList; 