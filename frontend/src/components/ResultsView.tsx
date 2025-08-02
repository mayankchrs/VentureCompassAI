import React, { useState } from 'react';
import useSWR from 'swr';
import axios from 'axios';

interface ResultsViewProps {
  runId: string;
  companyName: string;
  onNewSearch: () => void;
}

interface RunResults {
  run_id: string;
  status: string;
  company: { name: string; domain?: string };
  insights: {
    executive_summary: string;
    investment_signals: string[];
    risk_assessment: string[];
    confidence_score: number;
    llm_enhanced: boolean;
    data_sources: {
      news_articles: number;
      patents_found: number;
      pages_analyzed: number;
      verified_facts: number;
      team_members: number;
    };
    funding_events: Array<{
      summary: string;
      url: string;
      published_date?: string;
    }>;
    partnerships: Array<{
      summary: string;
      url: string;
      published_date?: string;
    }>;
  };
  patents: Array<{
    title: string;
    assignee: string;
    filing_date: string;
    url: string;
  }>;
  sources: Array<{
    id: string;
    type: string;
    title: string;
    url: string;
    confidence_score?: number;
  }>;
  cost: {
    tavily_credits: number;
    llm_tokens: number;
    openai_usd: number;
  };
}

const fetcher = (url: string) => axios.get(url).then(res => res.data);

const ResultsView: React.FC<ResultsViewProps> = ({ runId, companyName, onNewSearch }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'sources' | 'patents' | 'export'>('overview');

  const { data: results, error } = useSWR<RunResults>(
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/run/${runId}`,
    fetcher,
    { errorRetryCount: 3 }
  );

  const getConfidenceColor = (score: number) => {
    if (score >= 80) return 'text-green-400 bg-green-500/20 border-green-500/50';
    if (score >= 60) return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
    return 'text-red-400 bg-red-500/20 border-red-500/50';
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 80) return 'High Confidence';
    if (score >= 60) return 'Medium Confidence';
    return 'Low Confidence';
  };

  const handleExportJSON = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/run/${runId}/export.json`
      );
      
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `venture-compass-${companyName.toLowerCase().replace(/\s+/g, '-')}-${runId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-500/20 border border-red-500/50 rounded-2xl p-8 text-center">
          <h2 className="text-2xl font-bold text-red-200 mb-4">Failed to Load Results</h2>
          <p className="text-red-300 mb-6">Unable to fetch analysis results.</p>
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

  if (!results) {
    return (
      <div className="max-w-4xl mx-auto text-center">
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
          <div className="animate-spin h-8 w-8 border-b-2 border-white rounded-full mx-auto mb-4"></div>
          <p className="text-gray-300">Loading results...</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Executive Summary', icon: '📊' },
    { id: 'sources', label: 'Sources & Verification', icon: '🔗' },
    { id: 'patents', label: 'IP Portfolio', icon: '⚖️' },
    { id: 'export', label: 'Export & API', icon: '💾' }
  ];

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 mb-6 border border-white/20">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              {companyName} Intelligence Report
            </h1>
            <p className="text-gray-300">
              Analysis completed • Run ID: {runId} • 
              <span className="capitalize ml-1">{results.status}</span>
            </p>
          </div>
          <button
            onClick={onNewSearch}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            New Analysis
          </button>
        </div>

        {/* Confidence Score */}
        {results.insights && (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className={`px-3 py-1 rounded-lg border ${getConfidenceColor(results.insights.confidence_score)}`}>
                <span className="font-medium">
                  {getConfidenceLabel(results.insights.confidence_score)} ({results.insights.confidence_score}%)
                </span>
              </div>
              {results.insights.llm_enhanced && (
                <div className="flex items-center text-purple-300">
                  <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  LLM Enhanced
                </div>
              )}
            </div>
            <div className="text-right text-sm text-gray-400">
              {results.insights.data_sources.news_articles} articles • 
              {results.insights.data_sources.patents_found} patents • 
              {results.insights.data_sources.pages_analyzed} pages
            </div>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl border border-white/20 mb-6">
        <div className="flex border-b border-white/20">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex-1 px-6 py-4 text-center font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-white bg-white/10 border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'overview' && results.insights && (
            <div className="space-y-6">
              {/* Executive Summary */}
              <div>
                <h3 className="text-xl font-semibold text-white mb-3">Executive Summary</h3>
                <p className="text-gray-300 leading-relaxed">
                  {results.insights.executive_summary}
                </p>
              </div>

              {/* Investment Signals */}
              {results.insights.investment_signals.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold text-white mb-3">Investment Signals</h3>
                  <div className="space-y-2">
                    {results.insights.investment_signals.map((signal, index) => (
                      <div key={index} className="flex items-start">
                        <div className="h-2 w-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                        <p className="text-gray-300">{signal}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Risk Assessment */}
              {results.insights.risk_assessment.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold text-white mb-3">Risk Assessment</h3>
                  <div className="space-y-2">
                    {results.insights.risk_assessment.map((risk, index) => (
                      <div key={index} className="flex items-start">
                        <div className="h-2 w-2 bg-red-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                        <p className="text-gray-300">{risk}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Funding Events & Partnerships */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {results.insights.funding_events.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-3">Recent Funding</h3>
                    <div className="space-y-3">
                      {results.insights.funding_events.slice(0, 3).map((event, index) => (
                        <div key={index} className="p-3 bg-white/5 rounded-lg">
                          <a 
                            href={event.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-300 hover:text-blue-200 text-sm font-medium"
                          >
                            {event.summary}
                          </a>
                          {event.published_date && (
                            <p className="text-gray-400 text-xs mt-1">{event.published_date}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {results.insights.partnerships.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-3">Key Partnerships</h3>
                    <div className="space-y-3">
                      {results.insights.partnerships.slice(0, 3).map((partnership, index) => (
                        <div key={index} className="p-3 bg-white/5 rounded-lg">
                          <a 
                            href={partnership.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-purple-300 hover:text-purple-200 text-sm font-medium"
                          >
                            {partnership.summary}
                          </a>
                          {partnership.published_date && (
                            <p className="text-gray-400 text-xs mt-1">{partnership.published_date}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'sources' && (
            <div>
              <h3 className="text-xl font-semibold text-white mb-4">
                Source Verification ({results.sources.length} sources)
              </h3>
              <div className="space-y-3">
                {results.sources.map((source, index) => (
                  <div key={index} className="p-4 bg-white/5 rounded-lg border border-white/10">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <a 
                          href={source.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-300 hover:text-blue-200 font-medium"
                        >
                          {source.title || 'Untitled Source'}
                        </a>
                        <p className="text-gray-400 text-sm mt-1">
                          Type: {source.type} • ID: {source.id}
                        </p>
                      </div>
                      {source.confidence_score && (
                        <div className={`px-2 py-1 rounded text-xs ${getConfidenceColor(source.confidence_score)}`}>
                          {source.confidence_score}%
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'patents' && (
            <div>
              <h3 className="text-xl font-semibold text-white mb-4">
                Patent Portfolio ({results.patents.length} patents)
              </h3>
              {results.patents.length > 0 ? (
                <div className="space-y-4">
                  {results.patents.map((patent, index) => (
                    <div key={index} className="p-4 bg-white/5 rounded-lg border border-white/10">
                      <h4 className="text-white font-medium mb-2">{patent.title}</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-400">
                        <p><strong>Assignee:</strong> {patent.assignee}</p>
                        <p><strong>Filing Date:</strong> {patent.filing_date}</p>
                      </div>
                      <a 
                        href={patent.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-300 hover:text-blue-200 text-sm mt-2 inline-block"
                      >
                        View Patent →
                      </a>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400">No patents found for this company.</p>
              )}
            </div>
          )}

          {activeTab === 'export' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-semibold text-white mb-4">Export Options</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={handleExportJSON}
                    className="p-4 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 rounded-lg transition-colors text-left"
                  >
                    <div className="text-blue-300 font-medium mb-1">📄 JSON Export</div>
                    <div className="text-gray-400 text-sm">Complete analysis data in JSON format</div>
                  </button>
                  <div className="p-4 bg-gray-600/20 border border-gray-500/50 rounded-lg opacity-50">
                    <div className="text-gray-400 font-medium mb-1">📊 PDF Report</div>
                    <div className="text-gray-500 text-sm">Coming soon</div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Analysis Cost Breakdown</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-white/5 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-300">{results.cost.tavily_credits}</div>
                    <div className="text-gray-400 text-sm">Tavily Credits</div>
                  </div>
                  <div className="p-3 bg-white/5 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-300">{results.cost.llm_tokens}</div>
                    <div className="text-gray-400 text-sm">LLM Tokens</div>
                  </div>
                  <div className="p-3 bg-white/5 rounded-lg text-center">
                    <div className="text-2xl font-bold text-purple-300">${results.cost.openai_usd.toFixed(4)}</div>
                    <div className="text-gray-400 text-sm">OpenAI Cost</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultsView;