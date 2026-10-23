import React, { useState } from 'react';

const WalletSearch = ({ onSearch }) => {
  const [address, setAddress] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (address && address.length === 42 && address.startsWith('0x')) {
      onSearch(address);
    } else {
      alert('Please enter a valid Ethereum address (0x...)');
    }
  };

  return (
    <div className="mb-6 bg-white p-6 rounded-lg shadow">
      <form onSubmit={handleSubmit} className="flex gap-4">
        <input
          type="text"
          placeholder="Enter wallet address (0x...)"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Analyze
        </button>
      </form>
    </div>
  );
};

export default WalletSearch;
