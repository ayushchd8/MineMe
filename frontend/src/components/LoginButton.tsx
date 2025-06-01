import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const LoginButton: React.FC = () => {
  const { isAuthenticated, user, isLoading, login, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Checking authentication...</span>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="flex items-center space-x-4 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex-1">
          <p className="text-sm font-medium text-green-800">
            Authenticated as: {user?.Name || user?.Username}
          </p>
          <p className="text-xs text-green-600">
            Email: {user?.Email}
          </p>
        </div>
        <button
          onClick={logout}
          className="px-4 py-2 text-sm font-medium text-red-700 bg-red-100 border border-red-300 rounded-md hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          Logout
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <h3 className="text-lg font-medium text-yellow-800 mb-2">
        Salesforce Authentication Required
      </h3>
      <p className="text-sm text-yellow-700 mb-4">
        Please authenticate with Salesforce to access your data.
      </p>
      <button
        onClick={login}
        disabled={isLoading}
        className="w-full flex justify-center items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            Redirecting...
          </>
        ) : (
          'Connect to Salesforce'
        )}
      </button>
    </div>
  );
};

export default LoginButton; 