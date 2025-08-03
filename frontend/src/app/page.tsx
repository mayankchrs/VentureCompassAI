'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { CompanySearchForm } from '@/components/CompanySearchForm';
import { RunsHistory } from '@/components/RunsHistory';
import { RunResults } from '@/components/RunResults';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Zap, Search, History, Users, FileText, Shield, TrendingUp, Lightbulb, Globe, Brain, CheckCircle } from 'lucide-react';

type ViewMode = 'search' | 'history' | 'results';

export default function HomePage() {
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('search');
  const [viewMode, setViewMode] = useState<ViewMode>('search');

  const handleRunCreated = (runId: string) => {
    setCurrentRunId(runId);
    setViewMode('results');
    setActiveTab('results');
  };

  const handleSelectRun = (runId: string) => {
    setCurrentRunId(runId);
    setViewMode('results');
    setActiveTab('results');
  };

  const handleBackToHistory = () => {
    setCurrentRunId(null);
    setViewMode('history');
    setActiveTab('history');
  };

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    if (value === 'search') {
      setViewMode('search');
      setCurrentRunId(null);
    } else if (value === 'history') {
      setViewMode('history');
      setCurrentRunId(null);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="text-center pt-8 pb-4"
      >
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent mb-2">
          VentureCompass AI
        </h1>
        <p className="text-muted-foreground">
          8-Agent Multi-Phase Intelligence System
        </p>
      </motion.header>

      {/* Main Content */}
      <motion.main
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="max-w-6xl mx-auto px-4"
      >
        {viewMode === 'results' && currentRunId ? (
          <RunResults runId={currentRunId} onBack={handleBackToHistory} />
        ) : (
          <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
            <TabsList className="grid w-full grid-cols-2 max-w-md mx-auto mb-8">
              <TabsTrigger value="search" className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                New Analysis
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2">
                <History className="h-4 w-4" />
                History
              </TabsTrigger>
            </TabsList>

            <TabsContent value="search" className="space-y-6">
              <div className="flex items-center justify-center">
                <CompanySearchForm onRunCreated={handleRunCreated} />
              </div>
              
              {/* Agents Showcase Section */}
              <motion.section
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="mt-16"
              >
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold mb-2">8-Agent Intelligence System</h2>
                  <p className="text-muted-foreground">
                    Comprehensive startup analysis powered by specialized AI agents working in coordinated phases
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {/* Phase 1: Discovery */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="bg-card border rounded-lg p-4 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <Globe className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm">Discovery Agent</h3>
                        <Badge variant="outline" className="text-xs">Phase 1</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Maps company digital presence using Tavily Map API. Discovers websites, key pages, and aliases to build strategic research foundation.
                    </p>
                  </motion.div>

                  {/* Phase 2: Parallel Research - News */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="bg-card border rounded-lg p-4 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                        <FileText className="h-5 w-5 text-green-600 dark:text-green-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm">News Agent</h3>
                        <Badge variant="outline" className="text-xs">Phase 2</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Researches funding, partnerships, and market coverage using Tavily Search API with news focus. Analyzes investment signals and market momentum.
                    </p>
                  </motion.div>

                  {/* Phase 2: Parallel Research - Patents */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                    className="bg-card border rounded-lg p-4 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                        <Shield className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm">Patent Agent</h3>
                        <Badge variant="outline" className="text-xs">Phase 2</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Analyzes IP portfolios, patent filings, and innovation landscapes. Assesses competitive moats and technology differentiation.
                    </p>
                  </motion.div>

                  {/* Phase 2: Parallel Research - Founder */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7 }}
                    className="bg-card border rounded-lg p-4 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                        <Users className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm">Founder Agent</h3>
                        <Badge variant="outline" className="text-xs">Phase 2</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Researches leadership team backgrounds, track records, and execution capability. Analyzes founder credibility and market standing.
                    </p>
                  </motion.div>

                  {/* Phase 2: Parallel Research - Competitive */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 }}
                    className="bg-card border rounded-lg p-4 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                        <TrendingUp className="h-5 w-5 text-red-600 dark:text-red-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm">Competitive Agent</h3>
                        <Badge variant="outline" className="text-xs">Phase 2</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Maps competitive landscape, market positioning, and threats. Identifies opportunities and strategic advantages in the market.
                    </p>
                  </motion.div>

                  {/* Phase 2: Deep Content Analysis */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.9 }}
                    className="bg-card border rounded-lg p-4 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-indigo-100 dark:bg-indigo-900 rounded-lg">
                        <Lightbulb className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm">DeepDive Agent</h3>
                        <Badge variant="outline" className="text-xs">Phase 2</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Extracts detailed insights using Tavily Crawl and Extract APIs. Analyzes company profile, business model, and strategic positioning.
                    </p>
                  </motion.div>

                  {/* Phase 3: Verification */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1.0 }}
                    className="bg-card border rounded-lg p-4 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
                        <CheckCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm">Verification Agent</h3>
                        <Badge variant="outline" className="text-xs">Phase 3</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Cross-validates information across sources with confidence scoring. Identifies red flags, gaps, and provides reliability assessment.
                    </p>
                  </motion.div>

                  {/* Phase 3: Synthesis */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1.1 }}
                    className="bg-card border rounded-lg p-4 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-teal-100 dark:bg-teal-900 rounded-lg">
                        <Brain className="h-5 w-5 text-teal-600 dark:text-teal-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm">Synthesis Agent</h3>
                        <Badge variant="outline" className="text-xs">Phase 3</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Synthesizes comprehensive investment intelligence from all agents. Generates executive summary, signals, risks, and recommendations.
                    </p>
                  </motion.div>
                </div>

                {/* Workflow Overview */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.2 }}
                  className="mt-8 bg-muted/50 rounded-lg p-6"
                >
                  <h3 className="font-semibold mb-4 text-center">Multi-Phase Coordination</h3>
                  <div className="flex items-center justify-center gap-4 text-sm">
                    <div className="text-center">
                      <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-2 mx-auto">
                        <span className="text-blue-600 dark:text-blue-400 font-semibold">1</span>
                      </div>
                      <span className="text-muted-foreground">Discovery</span>
                    </div>
                    <div className="text-muted-foreground">→</div>
                    <div className="text-center">
                      <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mb-2 mx-auto">
                        <span className="text-green-600 dark:text-green-400 font-semibold">2</span>
                      </div>
                      <span className="text-muted-foreground">Parallel Research</span>
                    </div>
                    <div className="text-muted-foreground">→</div>
                    <div className="text-center">
                      <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mb-2 mx-auto">
                        <span className="text-purple-600 dark:text-purple-400 font-semibold">3</span>
                      </div>
                      <span className="text-muted-foreground">Synthesis</span>
                    </div>
                  </div>
                </motion.div>
              </motion.section>
            </TabsContent>

            <TabsContent value="history" className="space-y-6">
              <RunsHistory onSelectRun={handleSelectRun} />
            </TabsContent>
          </Tabs>
        )}
      </motion.main>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="mt-16 text-center text-sm text-muted-foreground pb-8"
      >
        <div className="flex items-center justify-center gap-2 mb-2">
          <Zap className="h-4 w-4 text-primary" />
          <span>Powered by</span>
          <Badge variant="outline">Tavily APIs</Badge>
          <span>+</span>
          <Badge variant="outline">LangGraph</Badge>
          <span>+</span>
          <Badge variant="outline">GPT-4o-mini</Badge>
        </div>
        <p>
          VentureCompass AI v2.0 • Complete Tavily API Integration Showcase
        </p>
      </motion.footer>
    </div>
  );
}