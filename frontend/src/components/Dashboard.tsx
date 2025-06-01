import React from 'react';
import LeadsTable from './LeadsTable';

const Dashboard: React.FC = () => {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Leads Dashboard</h1>
      <LeadsTable />
    </div>
  );
};

export default Dashboard; 