import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { walletAPI, transactionAPI } from '../services/api';

const WalletAnalysis = ({ walletAddress }) => {
  const [walletData, setWalletData] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [defiData, setDefiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timePeriod, setTimePeriod] = useState('1week');

  useEffect(() => {
    if (walletAddress) {
      fetchWalletData();
    }
  }, [walletAddress]);

  const fetchWalletData = async () => {
    try {
      setLoading(true);
      
      // Fetch wallet data
      const wallet = await walletAPI.getWallet(walletAddress);
      setWalletData(wallet);
      
      // Fetch transactions
      try {
        const txs = await transactionAPI.getWalletTransactions(walletAddress, 1000);
        setTransactions(txs);
        console.log(`Fetched ${txs.length} transactions for ${walletAddress}`);
      } catch (txError) {
        console.warn('Could not fetch transactions:', txError.message);
        setTransactions([]);
      }
      
      // Fetch DeFi analytics
      try {
        const defi = await walletAPI.getDeFiAnalytics(walletAddress);
        setDefiData(defi);
      } catch (defiError) {
        console.warn('Could not fetch DeFi data:', defiError.message);
        setDefiData(null);
      }
      
      setError(null);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching wallet data:', err);
      setError(err.response?.data?.detail || err.message);
      setLoading(false);
    }
  };

  // Get date range based on selected time period
  const getDateRange = (period) => {
    const now = new Date();
    let startDate = new Date();
    
    switch (period) {
      case '1day':
        startDate.setDate(now.getDate() - 1);
        return { startDate, days: 1, groupBy: 'hour' };
      case '1week':
        startDate.setDate(now.getDate() - 7);
        return { startDate, days: 7, groupBy: 'day' };
      case '1month':
        startDate.setMonth(now.getMonth() - 1);
        return { startDate, days: 30, groupBy: 'day' };
      case '3months':
        startDate.setMonth(now.getMonth() - 3);
        return { startDate, days: 90, groupBy: 'week' };
      case '1year':
        startDate.setFullYear(now.getFullYear() - 1);
        return { startDate, days: 365, groupBy: 'month' };
      case 'all':
        return { startDate: null, days: null, groupBy: 'month' };
      default:
        startDate.setDate(now.getDate() - 7);
        return { startDate, days: 7, groupBy: 'day' };
    }
  };

  // Generate chart data from real transaction data with time period filtering
  const generateChartData = (walletData, transactions, selectedPeriod = '1week') => {
    const { startDate, groupBy } = getDateRange(selectedPeriod);
    
    // Filter transactions by time period
    let filteredTransactions = transactions || [];
    if (startDate) {
      filteredTransactions = transactions.filter(tx => {
        const txDate = new Date(tx.timestamp * 1000);
        return txDate >= startDate;
      });
    }
    
    if (filteredTransactions.length > 0) {
      const groupedData = {};
      
      // Group transactions by time period
      filteredTransactions.forEach(tx => {
        const txDate = new Date(tx.timestamp * 1000);
        let groupKey;
        
        switch (groupBy) {
          case 'hour':
            groupKey = txDate.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric', 
              hour: '2-digit' 
            });
            break;
          case 'day':
            groupKey = txDate.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric' 
            });
            break;
          case 'week':
            const weekStart = new Date(txDate);
            weekStart.setDate(txDate.getDate() - txDate.getDay());
            groupKey = weekStart.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric' 
            });
            break;
          case 'month':
            groupKey = txDate.toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'short' 
            });
            break;
          default:
            groupKey = txDate.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric' 
            });
        }
        
        if (!groupedData[groupKey]) {
          groupedData[groupKey] = { 
            transactions: 0, 
            value: 0, 
            fees: 0,
            incoming: 0,
            outgoing: 0,
            date: groupKey
          };
        }
        
        groupedData[groupKey].transactions += 1;
        const txValue = parseFloat(tx.value || 0);
        const txFee = parseFloat(tx.transaction_fee || 0);
        
        groupedData[groupKey].value += txValue;
        groupedData[groupKey].fees += txFee;
        
        // Determine if incoming or outgoing
        if (tx.from_address?.toLowerCase() === walletAddress?.toLowerCase()) {
          groupedData[groupKey].outgoing += txValue;
        } else {
          groupedData[groupKey].incoming += txValue;
        }
      });
      
      // Convert to array and sort by date
      return Object.values(groupedData)
        .sort((a, b) => new Date(a.date) - new Date(b.date));
    }
    
    // Fallback: generate empty periods for the selected time range
    if (startDate) {
      const emptyData = [];
      const current = new Date(startDate);
      const now = new Date();
      
      while (current <= now) {
        let dateLabel;
        switch (groupBy) {
          case 'hour':
            dateLabel = current.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric', 
              hour: '2-digit' 
            });
            current.setHours(current.getHours() + 1);
            break;
          case 'day':
            dateLabel = current.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric' 
            });
            current.setDate(current.getDate() + 1);
            break;
          case 'week':
            dateLabel = current.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric' 
            });
            current.setDate(current.getDate() + 7);
            break;
          case 'month':
            dateLabel = current.toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'short' 
            });
            current.setMonth(current.getMonth() + 1);
            break;
        }
        
        emptyData.push({
          date: dateLabel,
          transactions: 0,
          value: 0,
          fees: 0,
          incoming: 0,
          outgoing: 0
        });
      }
      
      return emptyData.slice(-50); // Limit to 50 data points
    }
    
    // Fallback to summary data if no transaction details
    const days = Math.min(walletData.days_active || 7, 30);
    const data = [];
    
    for (let i = 0; i < Math.max(days, 7); i++) {
      const date = new Date();
      date.setDate(date.getDate() - (Math.max(days, 7) - i - 1));
      
      // Use actual wallet statistics
      const avgDaily = (walletData.transaction_count || 0) / Math.max(days, 7);
      const totalValue = (walletData.total_value_in || 0) + (walletData.total_value_out || 0);
      const avgDailyValue = totalValue / Math.max(days, 7);
      
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        transactions: Math.round(avgDaily),
        value: avgDailyValue
      });
    }
    
    return data;
  };

  const chartData = walletData ? generateChartData(walletData, transactions, timePeriod) : [];

  if (loading) return (
    <div className="p-4 flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <span className="ml-2">Analyzing wallet on blockchain...</span>
    </div>
  );
  
  if (error) return (
    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
      <div className="text-red-800 font-semibold">Error analyzing wallet:</div>
      <div className="text-red-600 text-sm mt-1">{error}</div>
      <button 
        onClick={fetchWalletData}
        className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
      >
        Retry Analysis
      </button>
    </div>
  );
  
  if (!walletData) return <div className="p-4">No data available</div>;

  const getRiskColor = (level) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return colors[level] || 'bg-gray-100';
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold">
            {walletAddress.substring(0, 10)}...{walletAddress.substring(walletAddress.length - 8)}
          </h1>
          {walletData.blockchain_fetched && (
            <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
              🔴 Live Data
            </div>
          )}
        </div>
        <div className="flex gap-4">
          <div className={`px-4 py-2 rounded-lg ${getRiskColor(walletData.risk_level)}`}>
            Risk Level: {walletData.risk_level.toUpperCase()}
          </div>
          <div className="px-4 py-2 bg-blue-100 text-blue-800 rounded-lg">
            Risk Score: {(walletData.risk_score * 100).toFixed(2)}%
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded">
          <p className="text-gray-600 text-sm">Transactions</p>
          <p className="text-2xl font-bold">{walletData.transaction_count?.toLocaleString() || '0'}</p>
        </div>
        <div className="bg-green-50 p-4 rounded">
          <p className="text-green-600 text-sm">Total In</p>
          <p className="text-2xl font-bold text-green-700">{(walletData.total_value_in || 0).toFixed(4)} ETH</p>
        </div>
        <div className="bg-red-50 p-4 rounded">
          <p className="text-red-600 text-sm">Total Out</p>
          <p className="text-2xl font-bold text-red-700">{(walletData.total_value_out || 0).toFixed(4)} ETH</p>
        </div>
        <div className="bg-orange-50 p-4 rounded">
          <p className="text-orange-600 text-sm">Fees Paid</p>
          <p className="text-2xl font-bold text-orange-700">{(walletData.total_fees_paid || 0).toFixed(4)} ETH</p>
        </div>
        <div className="bg-gray-50 p-4 rounded">
          <p className="text-gray-600 text-sm">Days Active</p>
          <p className="text-2xl font-bold">{walletData.days_active || 0}</p>
        </div>
      </div>

      {walletData.current_balance !== undefined && (
        <div className="mb-4 bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <p className="text-blue-800 font-semibold mb-2">Balance Analysis</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-2xl font-bold text-blue-900 mb-2">{walletData.current_balance.toFixed(6)} ETH</p>
                  <p className="text-blue-700 text-sm font-medium">Current Live Balance</p>
                </div>
              </div>
            </div>
            {walletData.blockchain_fetched && (
              <div className="text-blue-600 text-sm ml-4">
                ✅ Live Data
              </div>
            )}
          </div>
        </div>
      )}

      {transactions.length > 0 && (
        <div className="mb-6 bg-white p-4 rounded-lg border">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-semibold text-gray-800">Recent Transactions</h3>
            <span className="text-sm text-gray-500">
              Showing {Math.min(10, transactions.length)} of {transactions.length} transactions
            </span>
          </div>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {transactions.slice(0, 10).map((tx, index) => (
              <div key={index} className="bg-gray-50 p-3 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-gray-600 font-mono text-sm">{tx.hash?.slice(0, 12)}...</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        tx.from_address?.toLowerCase() === walletAddress?.toLowerCase() 
                          ? 'bg-red-100 text-red-700' 
                          : 'bg-green-100 text-green-700'
                      }`}>
                        {tx.from_address?.toLowerCase() === walletAddress?.toLowerCase() ? 'SENT' : 'RECEIVED'}
                      </span>
                      {tx.timestamp && (
                        <span className="text-xs text-gray-400">
                          {new Date(tx.timestamp * 1000).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mb-1">
                      {tx.from_address?.toLowerCase() === walletAddress?.toLowerCase() 
                        ? `To: ${tx.to_address?.slice(0, 10)}...${tx.to_address?.slice(-8)}` 
                        : `From: ${tx.from_address?.slice(0, 10)}...${tx.from_address?.slice(-8)}`
                      }
                    </div>
                    {tx.block_number && (
                      <div className="text-xs text-gray-400">
                        Block #{tx.block_number}
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <div className={`font-bold text-sm ${
                      tx.from_address?.toLowerCase() === walletAddress?.toLowerCase() 
                        ? 'text-red-600' 
                        : 'text-green-600'
                    }`}>
                      {tx.from_address?.toLowerCase() === walletAddress?.toLowerCase() ? '-' : '+'}
                      {tx.value?.toFixed(4)} ETH
                    </div>
                    {tx.transaction_fee && tx.transaction_fee > 0 && (
                      <div className="text-xs text-orange-600 mt-1">
                        Gas: {tx.transaction_fee.toFixed(6)} ETH
                      </div>
                    )}
                    {tx.gas_used && (
                      <div className="text-xs text-gray-400">
                        {tx.gas_used.toLocaleString()} gas
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Time Period Selector */}
      <div className="mb-6 bg-white p-4 rounded-lg border">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <h3 className="text-lg font-semibold text-gray-800">📊 Analytics Timeline</h3>
          <div className="flex flex-wrap gap-2">
            {[
              { value: '1day', label: '1 Day' },
              { value: '1week', label: '1 Week' },
              { value: '1month', label: '1 Month' },
              { value: '3months', label: '3 Months' },
              { value: '1year', label: '1 Year' },
              { value: 'all', label: 'All Time' }
            ].map((period) => (
              <button
                key={period.value}
                onClick={() => setTimePeriod(period.value)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  timePeriod === period.value
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {period.label}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-2 text-sm text-gray-500">
          Showing {chartData.length} data points • 
          {chartData.reduce((sum, d) => sum + (d.transactions || 0), 0)} transactions • 
          {chartData.reduce((sum, d) => sum + (d.value || 0), 0).toFixed(4)} ETH total value
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Transaction Activity</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                angle={-45}
                textAnchor="end"
                height={60}
                fontSize={12}
              />
              <YAxis fontSize={12} />
              <Tooltip 
                formatter={(value, name) => [value, name]}
                labelStyle={{ fontSize: '12px' }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="transactions" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Transactions"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Value Flow</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                angle={-45}
                textAnchor="end"
                height={60}
                fontSize={12}
              />
              <YAxis fontSize={12} />
              <Tooltip 
                formatter={(value, name) => [value.toFixed(4) + ' ETH', name]}
                labelStyle={{ fontSize: '12px' }}
              />
              <Legend />
              <Bar dataKey="incoming" fill="#10b981" name="Incoming (ETH)" />
              <Bar dataKey="outgoing" fill="#ef4444" name="Outgoing (ETH)" />
              <Bar dataKey="fees" fill="#f59e0b" name="Fees (ETH)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Transaction Volume</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                angle={-45}
                textAnchor="end"
                height={60}
                fontSize={12}
              />
              <YAxis fontSize={12} />
              <Tooltip 
                formatter={(value, name) => [value.toFixed(4) + ' ETH', name]}
                labelStyle={{ fontSize: '12px' }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#06b6d4" 
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Total Volume (ETH)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* DeFi Analytics Section */}
      {defiData && defiData.total_positions > 0 && (
        <div className="mt-6 bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-lg border border-purple-200">
          <h2 className="text-2xl font-bold mb-4 text-purple-800 flex items-center">
            🏦 DeFi Portfolio Analytics
            <span className="ml-2 text-sm bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
              Powered by The Graph
            </span>
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
            <div className="bg-white p-4 rounded border">
              <p className="text-purple-600 text-sm">Active Positions</p>
              <p className="text-2xl font-bold text-purple-700">{defiData.total_positions}</p>
            </div>
            <div className="bg-white p-4 rounded border">
              <p className="text-green-600 text-sm">Total Supplied</p>
              <p className="text-2xl font-bold text-green-700">{defiData.total_supplied.toFixed(4)}</p>
              <p className="text-xs text-gray-500">ETH</p>
            </div>
            <div className="bg-white p-4 rounded border">
              <p className="text-red-600 text-sm">Total Borrowed</p>
              <p className="text-2xl font-bold text-red-700">{defiData.total_borrowed.toFixed(4)}</p>
              <p className="text-xs text-gray-500">ETH</p>
            </div>
            <div className="bg-white p-4 rounded border">
              <p className="text-blue-600 text-sm">Health Factor</p>
              <p className={`text-2xl font-bold ${
                defiData.health_factor === Infinity || defiData.health_factor > 999 
                  ? 'text-green-700' 
                  : defiData.health_factor > 2 
                  ? 'text-green-700' 
                  : defiData.health_factor > 1.5 
                  ? 'text-yellow-600' 
                  : 'text-red-700'
              }`}>
                {defiData.health_factor === Infinity || defiData.health_factor > 999 ? '∞' : defiData.health_factor.toFixed(2)}
              </p>
            </div>
            <div className="bg-white p-4 rounded border">
              <p className="text-orange-600 text-sm">Leverage</p>
              <p className="text-2xl font-bold text-orange-700">{defiData.leverage_ratio ? defiData.leverage_ratio.toFixed(2) : '0.00'}x</p>
            </div>
            <div className="bg-white p-4 rounded border">
              <p className="text-indigo-600 text-sm">Protocols</p>
              <p className="text-2xl font-bold text-indigo-700">{defiData.protocol_diversification || 0}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Protocols Used */}
            <div className="bg-white p-4 rounded border">
              <h3 className="text-lg font-semibold mb-3 text-gray-800">Protocols Used</h3>
              <div className="space-y-2">
                {defiData.protocols_used.map((protocol, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                    <span className="text-gray-700">{protocol}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Factors */}
            <div className="bg-white p-4 rounded border">
              <h3 className="text-lg font-semibold mb-3 text-gray-800">Risk Analysis</h3>
              {defiData.defi_risk_factors.length > 0 ? (
                <div className="space-y-2">
                  {defiData.defi_risk_factors.map((risk, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <span className="text-red-500">⚠️</span>
                      <span className="text-red-700 font-medium">
                        {risk.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-green-500">✅</span>
                  <span className="text-green-700">No major risk factors detected</span>
                </div>
              )}
            </div>
          </div>

          {/* Position Details */}
          {defiData.positions && defiData.positions.length > 0 && (
            <div className="mt-6 bg-white p-4 rounded border">
              <h3 className="text-lg font-semibold mb-3 text-gray-800">Position Details</h3>
              <div className="space-y-3">
                {defiData.positions.slice(0, 5).map((position, index) => (
                  <div key={index} className="border-l-4 border-purple-300 pl-4 py-2">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-gray-800">{position.protocol}</span>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            position.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                          }`}>
                            {position.active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 capitalize mb-1">
                          {position.type.replace(/_/g, ' ')} 
                          {position.position_id && ` #${position.position_id}`}
                        </div>
                        {position.tokens && (
                          <div className="text-sm font-medium text-blue-700 mb-2">
                            {position.tokens.join(' / ')} Pool
                            {position.fee_tier && (
                              <span className="text-gray-500 ml-1">({(position.fee_tier / 10000).toFixed(2)}%)</span>
                            )}
                          </div>
                        )}
                      </div>
                      
                      <div className="text-right flex-shrink-0 ml-4">
                        {position.type === 'liquidity_pool' && (
                          <div className="space-y-1">
                            {position.deposited_token0 > 0 && (
                              <div className="text-xs">
                                <span className="text-gray-600">{position.tokens[0]}:</span>
                                <span className="font-medium text-green-600 ml-1">
                                  {position.deposited_token0.toFixed(4)}
                                </span>
                              </div>
                            )}
                            {position.deposited_token1 > 0 && (
                              <div className="text-xs">
                                <span className="text-gray-600">{position.tokens[1]}:</span>
                                <span className="font-medium text-green-600 ml-1">
                                  {position.deposited_token1.toFixed(4)}
                                </span>
                              </div>
                            )}
                            {(position.fees_token0 > 0 || position.fees_token1 > 0) && (
                              <div className="text-xs text-purple-600 border-t pt-1 mt-1">
                                Fees: {position.fees_token0?.toFixed(6) || '0'} / {position.fees_token1?.toFixed(6) || '0'}
                              </div>
                            )}
                            {position.pool_tvl_usd && (
                              <div className="text-xs text-gray-500 mt-1">
                                Pool TVL: ${position.pool_tvl_usd.toLocaleString()}
                              </div>
                            )}
                          </div>
                        )}
                        
                        {position.type === 'lending' && (
                          <div className="space-y-1">
                            {position.supplied && position.supplied > 0 && (
                              <div className="text-sm font-medium text-green-600">
                                Supplied: {position.supplied.toFixed(4)} {position.token}
                              </div>
                            )}
                            {((position.borrowed_stable || 0) + (position.borrowed_variable || 0) + (position.borrowed || 0)) > 0 && (
                              <div className="text-sm font-medium text-red-600">
                                Borrowed: {((position.borrowed_stable || 0) + (position.borrowed_variable || 0) + (position.borrowed || 0)).toFixed(4)} {position.token}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {defiData.positions.length > 5 && (
                  <div className="text-center text-sm text-gray-500 pt-2 border-t">
                    ... and {defiData.positions.length - 5} more positions
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      <button
        onClick={fetchWalletData}
        className="mt-6 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Refresh Data
      </button>
    </div>
  );
};

export default WalletAnalysis;
