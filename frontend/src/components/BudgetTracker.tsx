import React from 'react';
import useSWR from 'swr';
import axios from 'axios';

interface BudgetStatus {
  max_budget: number;
  current_spend: number;
  remaining: number;
  percentage_used: number;
  status: 'healthy' | 'warning' | 'critical';
  recent_operations: Array<{
    operation: string;
    cost: number;
    timestamp: string;
    tokens_used: number;
  }>;
}

const fetcher = (url: string) => axios.get(url).then(res => res.data);

const BudgetTracker: React.FC = () => {
  const { data: budgetData, error } = useSWR<BudgetStatus>(
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/run/budget/status`,
    fetcher,
    { 
      refreshInterval: 5000, // Poll every 5 seconds
      errorRetryCount: 2
    }
  );

  if (error || !budgetData) {
    return (
      <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
        <div className="flex items-center justify-center text-gray-400">
          <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
          </svg>
          Budget Tracker Unavailable
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'critical': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage < 50) return 'from-green-500 to-green-600';
    if (percentage < 80) return 'from-yellow-500 to-yellow-600';
    return 'from-red-500 to-red-600';
  };

  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <svg className="h-5 w-5 text-green-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
          </svg>
          <span className="text-white font-medium">Budget Status</span>
          <span className={`ml-2 text-sm capitalize ${getStatusColor(budgetData.status)}`}>
            {budgetData.status}
          </span>
        </div>
        <div className="text-right">
          <div className="text-white font-mono text-sm">
            ${budgetData.current_spend.toFixed(4)} / ${budgetData.max_budget.toFixed(2)}
          </div>
          <div className="text-gray-400 text-xs">
            ${budgetData.remaining.toFixed(4)} remaining
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className={`bg-gradient-to-r ${getProgressColor(budgetData.percentage_used)} h-2 rounded-full transition-all duration-1000`}
            style={{ width: `${Math.min(budgetData.percentage_used, 100)}%` }}
          />
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-400">
          <span>0%</span>
          <span>{budgetData.percentage_used.toFixed(1)}% used</span>
          <span>100%</span>
        </div>
      </div>

      {/* Recent Operations */}
      {budgetData.recent_operations && budgetData.recent_operations.length > 0 && (
        <div className="pt-3 border-t border-white/10">
          <div className="text-xs text-gray-400 mb-2">Recent API Calls:</div>
          <div className="space-y-1">
            {budgetData.recent_operations.slice(0, 3).map((op, index) => (
              <div key={index} className="flex justify-between text-xs">
                <span className="text-gray-300 capitalize">{op.operation}</span>
                <span className="text-gray-400">${op.cost.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warning Messages */}
      {budgetData.status === 'warning' && (
        <div className="mt-3 p-2 bg-yellow-500/20 border border-yellow-500/50 rounded text-xs text-yellow-200">
          ⚠️ Approaching budget limit. Consider optimizing API usage.
        </div>
      )}

      {budgetData.status === 'critical' && (
        <div className="mt-3 p-2 bg-red-500/20 border border-red-500/50 rounded text-xs text-red-200">
          🚨 Critical budget level! API calls may be limited.
        </div>
      )}
    </div>
  );
};

export default BudgetTracker;