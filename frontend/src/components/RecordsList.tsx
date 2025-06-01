import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getRecordsByObject } from '../api';
import { SalesforceRecord } from '../types';

const RecordsList: React.FC = () => {
  const { objectId } = useParams<{ objectId: string }>();
  const navigate = useNavigate();
  
  const [records, setRecords] = useState<SalesforceRecord[]>([]);
  const [objectName, setObjectName] = useState<string>('');
  const [objectApiName, setObjectApiName] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [includeDeleted, setIncludeDeleted] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(10);
  const [total, setTotal] = useState<number>(0);
  
  useEffect(() => {
    const fetchRecords = async () => {
      if (!objectId) return;
      
      try {
        setLoading(true);
        const response = await getRecordsByObject(parseInt(objectId, 10), {
          include_deleted: includeDeleted,
          limit,
          offset: (page - 1) * limit
        });
        
        setRecords(response.records);
        setObjectName(response.object.name);
        setObjectApiName(response.object.api_name);
        setTotal(response.total);
        setError(null);
      } catch (err) {
        setError('Failed to fetch records');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchRecords();
  }, [objectId, includeDeleted, page, limit]);
  
  // Extract common fields from records
  const getCommonFields = () => {
    if (records.length === 0) return [];
    
    // Get all fields from the first record
    const firstRecord = records[0].data;
    const fields = Object.keys(firstRecord).filter(field => 
      !field.startsWith('attributes') && 
      field !== 'Id'
    );
    
    // Limit to first 5 fields for display
    return fields.slice(0, 5);
  };
  
  const commonFields = getCommonFields();
  
  const totalPages = Math.ceil(total / limit);
  
  if (loading && records.length === 0) {
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
  
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-semibold">{objectName} Records</h2>
          <p className="text-gray-600">API Name: {objectApiName}</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="includeDeleted"
              checked={includeDeleted}
              onChange={() => setIncludeDeleted(!includeDeleted)}
              className="mr-2"
            />
            <label htmlFor="includeDeleted">Include Deleted</label>
          </div>
          <button
            onClick={() => navigate('/objects')}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded"
          >
            Back to Objects
          </button>
        </div>
      </div>
      
      {records.length === 0 ? (
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-4">
          <p>No records found for this object. Try syncing the object first.</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-200">
              <thead>
                <tr className="bg-gray-100">
                  <th className="py-2 px-4 border-b text-left">ID</th>
                  {commonFields.map(field => (
                    <th key={field} className="py-2 px-4 border-b text-left">{field}</th>
                  ))}
                  <th className="py-2 px-4 border-b text-left">Status</th>
                  <th className="py-2 px-4 border-b text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map(record => (
                  <tr key={record.sf_id} className={`hover:bg-gray-50 ${record.is_deleted ? 'bg-red-50' : ''}`}>
                    <td className="py-2 px-4 border-b">{record.sf_id}</td>
                    {commonFields.map(field => (
                      <td key={`${record.sf_id}-${field}`} className="py-2 px-4 border-b">
                        {record.data[field] ? 
                          (typeof record.data[field] === 'object' ? 
                            JSON.stringify(record.data[field]) : 
                            String(record.data[field])
                          ) : 
                          '-'
                        }
                      </td>
                    ))}
                    <td className="py-2 px-4 border-b">
                      {record.is_deleted ? (
                        <span className="px-2 py-1 rounded-full text-xs bg-red-100 text-red-800">
                          Deleted
                        </span>
                      ) : (
                        <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                          Active
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-4 border-b">
                      <button
                        onClick={() => navigate(`/records/${record.sf_id}`)}
                        className="text-blue-500 hover:text-blue-700"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {totalPages > 1 && (
            <div className="flex justify-between items-center mt-4">
              <div>
                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total} records
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className={`px-3 py-1 rounded ${
                    page === 1 ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'
                  }`}
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className={`px-3 py-1 rounded ${
                    page === totalPages ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'
                  }`}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RecordsList; 