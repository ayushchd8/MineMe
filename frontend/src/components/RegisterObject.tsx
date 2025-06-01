import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerObject } from '../api';

const RegisterObject: React.FC = () => {
  const navigate = useNavigate();
  const [apiName, setApiName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!apiName.trim()) {
      setError('API name is required');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      await registerObject(apiName);
      navigate('/objects');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to register object');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-xl font-semibold mb-4">Register Salesforce Object</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <p>{error}</p>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="apiName">
            API Name
          </label>
          <input
            id="apiName"
            type="text"
            placeholder="e.g. Account, Contact, Lead"
            value={apiName}
            onChange={(e) => setApiName(e.target.value)}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            disabled={loading}
          />
          <p className="text-gray-600 text-xs mt-1">
            Enter the API name of the Salesforce object you want to sync.
          </p>
        </div>
        
        <div className="flex items-center justify-between">
          <button
            type="submit"
            className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            disabled={loading}
          >
            {loading ? 'Registering...' : 'Register Object'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/objects')}
            className="text-blue-500 hover:text-blue-800"
            disabled={loading}
          >
            Cancel
          </button>
        </div>
      </form>
      
      <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mt-4">
        <h3 className="font-bold">Common Salesforce Object API Names:</h3>
        <ul className="list-disc pl-5 mt-2">
          <li>Account</li>
          <li>Contact</li>
          <li>Lead</li>
          <li>Opportunity</li>
          <li>Case</li>
          <li>Campaign</li>
          <li>Task</li>
          <li>Event</li>
        </ul>
      </div>
    </div>
  );
};

export default RegisterObject; 