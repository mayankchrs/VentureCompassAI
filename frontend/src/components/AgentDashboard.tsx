import React, { useEffect, useState } from 'react';
import useSWR from 'swr';
import axios from 'axios';

interface AgentDashboardProps {
  runId: string;
  companyName: string;
  onAnalysisComplete: () => void;
  onNewSearch: () => void;
}

interface RunState {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial';
  company: { name: string; domain?: string };
  insights: any;
  patents: any[];
  risks: any[];
  sources: any[];
  cost: { tavily_credits: number; llm_tokens: number; openai_usd: number };
  errors: any[];
}

const fetcher = (url: string) => axios.get(url).then(res => res.data);

const AgentDashboard: React.FC<AgentDashboardProps> = ({ 
  runId, 
  companyName, 
  onAnalysisComplete, 
  onNewSearch 
}) => {
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [startTime] = useState(Date.now());

  const { data: runData, error } = useSWR<RunState>(
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/run/${runId}`,
    fetcher,
    { 
      refreshInterval: 2000, // Poll every 2 seconds
      errorRetryCount: 3,
      errorRetryInterval: 1000
    }
  );

  // Timer effect
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  // Auto-navigate to results when complete
  useEffect(() => {
    if (runData?.status === 'completed' || runData?.status === 'partial') {
      setTimeout(() => {
        onAnalysisComplete();
      }, 2000); // 2 second delay to show completion
    }
  }, [runData?.status, onAnalysisComplete]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getAgentStatus = (agentName: string) => {
    if (!runData) return 'pending';
    
    // Simple status logic based on available data
    if (runData.status === 'completed' || runData.status === 'partial') return 'completed';
    if (runData.status === 'failed') return 'failed';
    
    // Progressive status based on data availability
    switch (agentName) {
      case 'Discovery':
        return runData.sources?.length > 0 ? 'completed' : runData.status === 'running' ? 'running' : 'pending';
      case 'News':
        return runData.sources?.some(s => s.type === 'news') ? 'completed' : runData.status === 'running' ? 'running' : 'pending';
      case 'Patents':
        return runData.patents?.length > 0 ? 'completed' : runData.status === 'running' ? 'running' : 'pending';
      case 'DeepDive':
        return runData.sources?.some(s => s.type === 'extract') ? 'completed' : runData.status === 'running' ? 'running' : 'pending';
      case 'Verification':
        return runData.sources?.length > 3 ? 'completed' : runData.status === 'running' ? 'running' : 'pending';
      case 'Synthesis':
        return runData.insights ? 'completed' : runData.status === 'running' ? 'running' : 'pending';
      default:
        return 'pending';
    }
  };

  const agents = [
    {
      name: 'Discovery',
      description: 'Mapping digital footprint',
      icon: '🗺️',
      api: 'Tavily Map',
      color: 'blue'
    },
    {
      name: 'News',
      description: 'Gathering recent news',
      icon: '📰',
      api: 'Tavily Search',
      color: 'green'
    },
    {
      name: 'Patents',
      description: 'Hunting IP portfolio',
      icon: '⚖️',
      api: 'Tavily Search',
      color: 'purple'
    },
    {
      name: 'DeepDive',
      description: 'Extracting deep content',
      icon: '🔍',
      api: 'Crawl + Extract',
      color: 'yellow'
    },
    {
      name: 'Verification',
      description: 'Cross-validating facts',
      icon: '✅',
      api: 'Multi-source',
      color: 'red'
    },
    {
      name: 'Synthesis',
      description: 'Generating insights',
      icon: '🧠',
      api: 'GPT-4o-mini',
      color: 'indigo'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'running': return 'bg-blue-500 animate-pulse';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✓';
      case 'running': return '⟳';
      case 'failed': return '✗';
      default: return '○';
    }
  };

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-500/20 border border-red-500/50 rounded-2xl p-8 text-center">
          <h2 className="text-2xl font-bold text-red-200 mb-4">Analysis Error</h2>
          <p className="text-red-300 mb-6">Failed to fetch analysis status. Please try again.</p>
          <button
            onClick={onNewSearch}
            className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Start New Analysis
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 mb-6 border border-white/20">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Analyzing {companyName}
            </h2>
            <p className="text-gray-300">
              Run ID: {runId} • Status: <span className="capitalize text-blue-300">{runData?.status || 'loading'}</span>
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-mono text-white">{formatTime(timeElapsed)}</div>
            <div className="text-gray-400 text-sm">Elapsed Time</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="flex justify-between mb-2">
            <span className="text-gray-300 text-sm">Overall Progress</span>
            <span className="text-gray-300 text-sm">
              {agents.filter(agent => getAgentStatus(agent.name) === 'completed').length} / {agents.length} agents
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-1000"
              style={{ 
                width: `${(agents.filter(agent => getAgentStatus(agent.name) === 'completed').length / agents.length) * 100}%` 
              }}
            />
          </div>
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        {agents.map((agent, index) => {
          const status = getAgentStatus(agent.name);
          return (
            <div 
              key={agent.name}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:border-white/30 transition-all duration-300"
            >
              <div className="flex items-center mb-4">
                <div className={`h-10 w-10 bg-${agent.color}-500/20 rounded-lg flex items-center justify-center mr-3`}>
                  <span className="text-2xl">{agent.icon}</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-white">{agent.name} Agent</h3>
                  <p className="text-xs text-gray-400">{agent.api}</p>
                </div>
                <div className={`h-3 w-3 rounded-full ${getStatusColor(status)}`} />
              </div>
              
              <p className="text-gray-300 text-sm mb-3">{agent.description}</p>
              
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400 capitalize">{status}</span>
                <span className="text-lg">{getStatusIcon(status)}</span>
              </div>

              {/* Progress details */}
              {status === 'completed' && (
                <div className="mt-3 pt-3 border-t border-white/10">
                  <div className="text-xs text-gray-400">
                    {agent.name === 'News' && `${runData?.sources?.filter(s => s.type === 'news')?.length || 0} articles`}
                    {agent.name === 'Patents' && `${runData?.patents?.length || 0} patents`}
                    {agent.name === 'Discovery' && `${runData?.sources?.filter(s => s.type === 'map')?.length || 0} pages mapped`}
                    {agent.name === 'DeepDive' && `${runData?.sources?.filter(s => s.type === 'extract')?.length || 0} pages analyzed`}
                    {agent.name === 'Verification' && `${runData?.sources?.length || 0} sources verified`}
                    {agent.name === 'Synthesis' && runData?.insights && 'Report generated'}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Cost Tracking */}
      {runData?.cost && (
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 mb-6">
          <h3 className="font-semibold text-white mb-4">Real-time Cost Tracking</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-300">
                {runData.cost.tavily_credits || 0}
              </div>
              <div className="text-gray-400 text-sm">Tavily Credits</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-300">
                {runData.cost.llm_tokens || 0}
              </div>
              <div className="text-gray-400 text-sm">LLM Tokens</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-300">
                ${(runData.cost.openai_usd || 0).toFixed(4)}
              </div>
              <div className="text-gray-400 text-sm">OpenAI Cost</div>
            </div>
          </div>
        </div>
      )}

      {/* Errors */}
      {runData?.errors && runData.errors.length > 0 && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-6 mb-6">
          <h3 className="font-semibold text-red-200 mb-4">Warnings & Errors</h3>
          <div className="space-y-2">
            {runData.errors.map((error: any, index: number) => (
              <div key={index} className="text-red-300 text-sm">
                <strong>{error.agent}:</strong> {error.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="text-center">
        <button
          onClick={onNewSearch}
          className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
        >
          Cancel & Start New Analysis
        </button>
      </div>
    </div>
  );
};

export default AgentDashboard;