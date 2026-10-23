import axios from 'axios';

// Configure API base URL based on environment
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
apiClient.interceptors.request.use(
  (config) => {
    console.log('Making API request to:', config.baseURL + config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response || error.message);
    return Promise.reject(error);
  }
);

// API functions
export const walletAPI = {
  // Get wallet analysis
  getWallet: async (address) => {
    const response = await apiClient.get(`/api/wallets/${address}`);
    return response.data;
  },

  // Get DeFi analytics for wallet
  getDeFiAnalytics: async (address) => {
    const response = await apiClient.get(`/api/wallets/${address}/defi`);
    return response.data;
  },

  // Get all wallets
  getAllWallets: async (limit = 10, offset = 0) => {
    const response = await apiClient.get(`/api/wallets/`, {
      params: { limit, offset }
    });
    return response.data;
  },

  // Search wallets
  searchWallets: async (query) => {
    const response = await apiClient.get(`/api/wallets/search`, {
      params: { q: query }
    });
    return response.data;
  }
};

export const transactionAPI = {
  // Get wallet transactions
  getWalletTransactions: async (address, limit = 50) => {
    const response = await apiClient.get(`/api/transactions/wallet/${address}`, {
      params: { limit }
    });
    return response.data;
  },

  // Get transaction details
  getTransaction: async (txHash) => {
    const response = await apiClient.get(`/api/transactions/${txHash}`);
    return response.data;
  }
};

export const analyticsAPI = {
  // Get analytics overview
  getOverview: async () => {
    const response = await apiClient.get('/api/analytics/overview');
    return response.data;
  },

  // Get risk distribution
  getRiskDistribution: async () => {
    const response = await apiClient.get('/api/analytics/risk-distribution');
    return response.data;
  },

  // Get activity trends
  getActivityTrends: async (period = '7d') => {
    const response = await apiClient.get('/api/analytics/trends', {
      params: { period }
    });
    return response.data;
  }
};

export default apiClient;