import React, { useState } from 'react';
import WalletAnalysis from '../components/WalletAnalysis';
import WalletSearch from '../components/WalletSearch';

const Dashboard = () => {
  const [selectedWallet, setSelectedWallet] = useState(null);

  const handleSearch = (address) => {
    setSelectedWallet(address);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-blue-600">AI Blockchain Analytics</h1>
          <p className="text-gray-600">Risk Assessment & Portfolio Insights</p>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <WalletSearch onSearch={handleSearch} />
        {selectedWallet && <WalletAnalysis walletAddress={selectedWallet} />}
        
        {!selectedWallet && (
          <div className="bg-white p-12 rounded-lg shadow text-center">
            <h2 className="text-3xl font-bold mb-4">Welcome to AI Blockchain Analytics</h2>
            <p className="text-gray-600 mb-6">
              Enter a wallet address above to get started with AI-powered risk analysis
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
              <div className="p-6 border rounded-lg">
                <div className="text-4xl mb-4">🔍</div>
                <h3 className="font-bold mb-2">Risk Scoring</h3>
                <p className="text-sm text-gray-600">AI-powered wallet risk assessment</p>
              </div>
              <div className="p-6 border rounded-lg">
                <div className="text-4xl mb-4">⚠️</div>
                <h3 className="font-bold mb-2">Anomaly Detection</h3>
                <p className="text-sm text-gray-600">Detect suspicious transactions</p>
              </div>
              <div className="p-6 border rounded-lg">
                <div className="text-4xl mb-4">📊</div>
                <h3 className="font-bold mb-2">Portfolio Insights</h3>
                <p className="text-sm text-gray-600">Comprehensive analytics</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
