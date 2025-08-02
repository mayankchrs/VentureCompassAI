import React, { useState } from 'react';
import CompanySearch from './components/CompanySearch';
import AgentDashboard from './components/AgentDashboard';
import ResultsView from './components/ResultsView';
import BudgetTracker from './components/BudgetTracker';
import './App.css';

interface AppState {
  currentView: 'search' | 'analysis' | 'results';
  runId: string | null;
  companyName: string | null;
}

function App() {
  const [appState, setAppState] = useState<AppState>({
    currentView: 'search',
    runId: null,
    companyName: null,
  });

  const handleAnalysisStart = (runId: string, companyName: string) => {
    setAppState({
      currentView: 'analysis',
      runId,
      companyName,
    });
  };

  const handleAnalysisComplete = () => {
    setAppState(prev => ({
      ...prev,
      currentView: 'results',
    }));
  };

  const handleNewSearch = () => {
    setAppState({
      currentView: 'search',
      runId: null,
      companyName: null,
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8 text-center max-w-4xl mx-auto">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-white">VentureCompass AI</h1>
            <span className="text-xs bg-purple-600 text-white px-2 py-1 rounded-full flex-shrink-0">v2.0</span>
          </div>
          <p className="text-gray-300 text-base md:text-lg mb-4">
            Advanced 6-Agent Intelligence System for Startup Due Diligence
          </p>
          <div className="flex flex-wrap justify-center items-center gap-4 text-sm text-gray-400">
            <span className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2 flex-shrink-0"></div>
              <span className="whitespace-nowrap">Tavily APIs</span>
            </span>
            <span className="flex items-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-2 flex-shrink-0"></div>
              <span className="whitespace-nowrap">LangGraph Coordination</span>
            </span>
            <span className="flex items-center">
              <div className="w-2 h-2 bg-purple-500 rounded-full mr-2 flex-shrink-0"></div>
              <span className="whitespace-nowrap">GPT-4o-mini</span>
            </span>
          </div>
        </header>

        {/* Budget Tracker - Always visible */}
        <div className="mb-6">
          <BudgetTracker />
        </div>

        {/* Main Content */}
        {appState.currentView === 'search' && (
          <CompanySearch onAnalysisStart={handleAnalysisStart} />
        )}

        {appState.currentView === 'analysis' && appState.runId && (
          <AgentDashboard 
            runId={appState.runId} 
            companyName={appState.companyName || 'Unknown Company'}
            onAnalysisComplete={handleAnalysisComplete}
            onNewSearch={handleNewSearch}
          />
        )}

        {appState.currentView === 'results' && appState.runId && (
          <ResultsView 
            runId={appState.runId} 
            companyName={appState.companyName || 'Unknown Company'}
            onNewSearch={handleNewSearch}
          />
        )}

        {/* Footer */}
        <footer className="mt-16 text-center text-gray-500 text-sm">
          <div className="border-t border-gray-700 pt-8">
            <p>🚀 Tavily Interview Assignment • Lead GenAI Engineer Role</p>
            <p className="mt-2">
              Showcasing advanced multi-agent coordination with complete Tavily API integration
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;