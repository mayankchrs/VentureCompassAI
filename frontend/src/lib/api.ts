import axios from 'axios';
import { RunCreateRequest, RunCreateResponse, RunState, BudgetStatus, RunsHistoryResponse } from '@/types/api';

// Environment configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api';
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000');
const DEBUG_API = process.env.NEXT_PUBLIC_DEBUG_API === 'true';

// Log configuration in development
if (process.env.NODE_ENV === 'development') {
  console.log('🔧 API Configuration:', {
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    debug: DEBUG_API,
    envVariable: process.env.NEXT_PUBLIC_API_BASE_URL ? '✅ Set' : '❌ Using fallback'
  });
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for debugging
if (DEBUG_API) {
  api.interceptors.request.use((config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
    return config;
  });

  api.interceptors.response.use(
    (response) => {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`, response.data);
      return response;
    },
    (error) => {
      console.error(`❌ API Error: ${error.config?.url}`, {
        status: error.response?.status,
        message: error.response?.data?.message || error.message,
        data: error.response?.data
      });
      return Promise.reject(error);
    }
  );
}

export const apiClient = {
  // Create a new analysis run
  createRun: async (data: RunCreateRequest): Promise<RunCreateResponse> => {
    const response = await api.post('/run/', data);
    return response.data;
  },

  // Get run status and results
  getRun: async (runId: string): Promise<RunState> => {
    const response = await api.get(`/run/${runId}`);
    return response.data;
  },

  // Export run data
  exportRun: async (runId: string): Promise<RunState> => {
    const response = await api.get(`/run/${runId}/export.json`);
    return response.data;
  },

  // Get budget status
  getBudgetStatus: async (): Promise<BudgetStatus> => {
    const response = await api.get('/run/budget/status');
    return response.data;
  },

  // Get budget history
  getBudgetHistory: async (): Promise<any> => {
    const response = await api.get('/run/budget/history');
    return response.data;
  },

  // Get runs history
  getRunsHistory: async (): Promise<RunsHistoryResponse> => {
    const response = await api.get('/run/history');
    return response.data;
  },
};

export default api;