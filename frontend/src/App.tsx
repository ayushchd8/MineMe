import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import ObjectsList from './components/ObjectsList';
import RegisterObject from './components/RegisterObject';
import RecordsList from './components/RecordsList';
import SalesforceConnector from './components/SalesforceConnector';
import LoginButton from './components/LoginButton';

// Protected wrapper component
const ProtectedApp: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        {/* Always show login status */}
        <div className="mb-6">
          <LoginButton />
        </div>
        
        {/* Show content only if authenticated */}
        {isAuthenticated ? (
          <Routes>
            <Route path="/" element={<SalesforceConnector />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/objects" element={<ObjectsList />} />
            <Route path="/objects/register" element={<RegisterObject />} />
            <Route path="/records/object/:objectId" element={<RecordsList />} />
          </Routes>
        ) : (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              Welcome to MineMe
            </h2>
            <p className="text-gray-600">
              Please authenticate with Salesforce to access your data and start syncing.
            </p>
          </div>
        )}
      </main>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <ProtectedApp />
      </Router>
    </AuthProvider>
  );
}

export default App;
