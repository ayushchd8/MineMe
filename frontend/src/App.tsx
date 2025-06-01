import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import ObjectsList from './components/ObjectsList';
import RegisterObject from './components/RegisterObject';
import RecordsList from './components/RecordsList';
import SalesforceConnector from './components/SalesforceConnector';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<SalesforceConnector />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/objects" element={<ObjectsList />} />
            <Route path="/objects/register" element={<RegisterObject />} />
            <Route path="/records/object/:objectId" element={<RecordsList />} />
          </Routes>
        </main>
    </div>
    </Router>
  );
}

export default App;
