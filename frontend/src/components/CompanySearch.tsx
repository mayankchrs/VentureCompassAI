import React, { useState } from 'react';
import axios from 'axios';

interface CompanySearchProps {
  onAnalysisStart: (runId: string, companyName: string) => void;
}

const CompanySearch: React.FC<CompanySearchProps> = ({ onAnalysisStart }) => {
  const [companyName, setCompanyName] = useState('');
  const [domain, setDomain] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const demoCompanies = [
    { name: 'Notion', domain: 'notion.so', description: 'All-in-one workspace for notes, docs, and collaboration' },
    { name: 'Stripe', domain: 'stripe.com', description: 'Online payment processing for businesses' },
    { name: 'Anthropic', domain: 'anthropic.com', description: 'AI safety research company' },
    { name: 'OpenAI', domain: 'openai.com', description: 'Artificial intelligence research lab' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/run`, {
        company: companyName.trim(),
        domain: domain.trim() || undefined,
      });

      onAnalysisStart(response.data.run_id, companyName.trim());
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start analysis');
      setIsLoading(false);
    }
  };

  const handleDemoSelect = (demo: typeof demoCompanies[0]) => {
    setCompanyName(demo.name);
    setDomain(demo.domain);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-white mb-2">
            Start Startup Intelligence Analysis
          </h2>
          <p className="text-gray-300">
            6 AI agents will analyze your target company using advanced web research and cross-validation
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="company" className="block text-sm font-medium text-gray-200 mb-2">
              Company Name *
            </label>
            <input
              type="text"
              id="company"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g., Notion, Stripe, Anthropic..."
              className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
              required
            />
          </div>

          <div>
            <label htmlFor="domain" className="block text-sm font-medium text-gray-200 mb-2">
              Company Domain (Optional)
            </label>
            <input
              type="text"
              id="domain"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="e.g., notion.so, stripe.com..."
              className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
            />
            <p className="text-gray-400 text-sm mt-1">
              Optional: Helps agents discover more targeted information
            </p>
          </div>

          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !companyName.trim()}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Starting Agent Analysis...
              </div>
            ) : (
              'Launch Multi-Agent Analysis'
            )}
          </button>
        </form>

        {/* Demo Companies */}
        <div className="mt-8 pt-6 border-t border-white/20">
          <p className="text-gray-300 text-sm mb-4 text-center">Quick Demo Companies:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {demoCompanies.map((demo, index) => (
              <button
                key={index}
                onClick={() => handleDemoSelect(demo)}
                className="text-left p-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-lg transition-all duration-200"
              >
                <div className="font-medium text-white">{demo.name}</div>
                <div className="text-xs text-gray-400 mt-1">{demo.domain}</div>
                <div className="text-xs text-gray-500 mt-1">{demo.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Agent Preview */}
        <div className="mt-8 pt-6 border-t border-white/20">
          <p className="text-gray-300 text-sm mb-4 text-center font-medium">6-Agent Analysis Pipeline:</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-xs">
            <div className="text-center">
              <div className="h-8 w-8 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <svg className="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
              </div>
              <div className="text-blue-300 font-medium">Discovery</div>
              <div className="text-gray-400">Map API</div>
            </div>
            <div className="text-center">
              <div className="h-8 w-8 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <svg className="h-4 w-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
              </div>
              <div className="text-green-300 font-medium">News</div>
              <div className="text-gray-400">Search API</div>
            </div>
            <div className="text-center">
              <div className="h-8 w-8 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <svg className="h-4 w-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div className="text-purple-300 font-medium">Patents</div>
              <div className="text-gray-400">Search API</div>
            </div>
            <div className="text-center">
              <div className="h-8 w-8 bg-yellow-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <svg className="h-4 w-4 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <div className="text-yellow-300 font-medium">DeepDive</div>
              <div className="text-gray-400">Crawl+Extract</div>
            </div>
            <div className="text-center">
              <div className="h-8 w-8 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <svg className="h-4 w-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="text-red-300 font-medium">Verification</div>
              <div className="text-gray-400">Cross-check</div>
            </div>
            <div className="text-center">
              <div className="h-8 w-8 bg-indigo-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <svg className="h-4 w-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 011-1h1a2 2 0 100-4H7a1 1 0 01-1-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
                </svg>
              </div>
              <div className="text-indigo-300 font-medium">Synthesis</div>
              <div className="text-gray-400">GPT-4o-mini</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanySearch;