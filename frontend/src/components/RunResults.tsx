'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { 
  ArrowLeft,
  Building2,
  Clock,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Loader2,
  XCircle,
  ExternalLink,
  FileText,
  Users,
  Lightbulb,
  Shield,
  TrendingUp,
  Calendar,
  Download,
  ChevronDown,
  Globe,
  Table
} from 'lucide-react';
import { useRunStatus } from '@/hooks/useRunAnalysis';
import { RunState, RunStatus } from '@/types/api';
import { apiClient } from '@/lib/api';

const statusConfig: Record<RunStatus, { icon: React.ReactNode; color: string; label: string }> = {
  pending: { icon: <Clock className="h-4 w-4" />, color: 'text-yellow-600', label: 'Pending' },
  running: { icon: <Loader2 className="h-4 w-4 animate-spin" />, color: 'text-blue-600', label: 'Running' },
  partial: { icon: <AlertTriangle className="h-4 w-4" />, color: 'text-orange-600', label: 'Partial Results' },
  complete: { icon: <CheckCircle className="h-4 w-4" />, color: 'text-green-600', label: 'Complete' },
  completed: { icon: <CheckCircle className="h-4 w-4" />, color: 'text-green-600', label: 'Complete' },
  error: { icon: <XCircle className="h-4 w-4" />, color: 'text-red-600', label: 'Error' },
};

interface RunResultsProps {
  runId: string;
  onBack: () => void;
}

export function RunResults({ runId, onBack }: RunResultsProps) {
  const { data: runData, isLoading, error } = useRunStatus(runId, true);
  const [showExportDropdown, setShowExportDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowExportDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleExport = async (format: 'json' | 'html' | 'csv' = 'json') => {
    try {
      if (format === 'html') {
        // Open HTML report in new tab
        const url = `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'}/run/${runId}/export.html`;
        window.open(url, '_blank');
        return;
      }
      
      if (format === 'csv') {
        // Download CSV file
        const url = `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'}/run/${runId}/export.csv`;
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis_${runId}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        return;
      }
      
      // JSON export
      const data = await apiClient.exportRun(runId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analysis_${runId}_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4 mb-6">
          <Button onClick={onBack} variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to History
          </Button>
        </div>
        
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mr-3" />
            <span className="text-lg text-muted-foreground">Loading analysis results...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4 mb-6">
          <Button onClick={onBack} variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to History
          </Button>
        </div>
        
        <Card>
          <CardContent className="text-center py-12">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Failed to Load Results</h3>
            <p className="text-muted-foreground">Could not retrieve analysis data for run {runId}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!runData) return null;

  const status = statusConfig[runData.status];

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <Button onClick={onBack} variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to History
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{runData.company.name}</h1>
            <p className="text-muted-foreground">Analysis Results • {runId}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Badge variant="outline" className={`${status.color} border-current`}>
            {status.icon}
            <span className="ml-1">{status.label}</span>
          </Badge>
          
          {/* Export Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <Button 
              onClick={() => setShowExportDropdown(!showExportDropdown)} 
              variant="outline" 
              size="sm"
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export
              <ChevronDown className="h-4 w-4" />
            </Button>
            
            {showExportDropdown && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-50">
                <div className="py-1">
                  <button
                    onClick={() => {
                      handleExport('html');
                      setShowExportDropdown(false);
                    }}
                    className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <Globe className="h-4 w-4" />
                    Interactive HTML Report
                  </button>
                  <button
                    onClick={() => {
                      handleExport('csv');
                      setShowExportDropdown(false);
                    }}
                    className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <Table className="h-4 w-4" />
                    CSV Spreadsheet
                  </button>
                  <button
                    onClick={() => {
                      handleExport('json');
                      setShowExportDropdown(false);
                    }}
                    className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FileText className="h-4 w-4" />
                    Raw JSON Data
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Company Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Company Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Company</h4>
                <p className="text-lg">{runData.company.name}</p>
                {runData.company.domain && (
                  <a 
                    href={runData.company.domain} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-primary hover:underline flex items-center gap-1 mt-1"
                  >
                    {runData.company.domain}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
              <div>
                <h4 className="font-semibold mb-2">Analysis Cost</h4>
                <div className="space-y-1">
                  <p className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    <span>OpenAI: ${runData.cost.openai_usd.toFixed(4)}</span>
                  </p>
                  <p className="flex items-center gap-2">
                    <span className="w-4 h-4 text-center text-xs">T</span>
                    <span>Tavily: {runData.cost.tavily_credits} credits</span>
                  </p>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Status</h4>
                <div className="space-y-1">
                  <p>Status: {status.label}</p>
                  {runData.errors && runData.errors.length > 0 && (
                    <p className="text-orange-600">
                      Errors: {runData.errors.length}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Founders */}
      {runData.founders && runData.founders.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Leadership Team
                <Badge variant="secondary">{runData.founders.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {runData.founders.map((founder, index) => (
                  <div key={founder._id || founder.id || index} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-lg">{founder.name}</h4>
                        <p className="text-primary font-medium">{founder.role}</p>
                      </div>
                      <div className="text-right">
                        <Badge variant={founder.source_confidence === 'high' ? 'default' : founder.source_confidence === 'medium' ? 'secondary' : 'outline'}>
                          {founder.source_confidence || 'unknown'} confidence
                        </Badge>
                      </div>
                    </div>
                    
                    {founder.background_summary && (
                      <p className="text-muted-foreground mb-3">{founder.background_summary}</p>
                    )}
                    
                    {founder.key_achievements && founder.key_achievements.length > 0 && (
                      <div className="mb-3">
                        <h5 className="font-medium mb-2">Key Achievements</h5>
                        <ul className="space-y-1">
                          {founder.key_achievements.map((achievement, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm">
                              <CheckCircle className="h-3 w-3 text-green-600 mt-1 flex-shrink-0" />
                              <span>{achievement}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {founder.previous_experience && founder.previous_experience.length > 0 && (
                      <div className="mb-3">
                        <h5 className="font-medium mb-2">Previous Experience</h5>
                        <ul className="space-y-1">
                          {founder.previous_experience.map((exp, idx) => (
                            <li key={idx} className="text-sm text-muted-foreground">• {exp}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {founder.investment_assessment && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <h5 className="font-medium text-blue-800 mb-1">Investment Assessment</h5>
                        <p className="text-sm text-blue-700">{founder.investment_assessment}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Insights */}
      {runData.insights && runData.insights.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5" />
                Analysis Summary
                <Badge variant="secondary">{runData.insights.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {runData.insights.map((insight, index) => (
                  <div key={insight._id || index} className="space-y-4">
                    {/* Executive Summary */}
                    {insight.executive_summary && (
                      <div className="border-l-4 border-primary pl-4">
                        <h4 className="font-semibold text-lg mb-2">Executive Summary</h4>
                        <p className="text-muted-foreground">{insight.executive_summary}</p>
                        <div className="flex items-center gap-2 mt-3">
                          <Badge 
                            variant={insight.confidence_score > 0.7 ? "default" : insight.confidence_score > 0.4 ? "secondary" : "destructive"}
                          >
                            {Math.round(insight.confidence_score * 100)}% confidence
                          </Badge>
                          {insight.llm_enhanced && (
                            <Badge variant="outline">AI Enhanced</Badge>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Investment Signals */}
                    {insight.investment_signals && insight.investment_signals.length > 0 && (
                      <div className="border-l-4 border-green-500 pl-4">
                        <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                          <TrendingUp className="h-5 w-5 text-green-600" />
                          Investment Signals
                        </h4>
                        <ul className="space-y-2">
                          {insight.investment_signals.map((signal, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                              <span className="text-sm">{signal}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Risk Assessment */}
                    {insight.risk_assessment && insight.risk_assessment.length > 0 && (
                      <div className="border-l-4 border-orange-500 pl-4">
                        <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                          <AlertTriangle className="h-5 w-5 text-orange-600" />
                          Risk Assessment
                        </h4>
                        <ul className="space-y-2">
                          {insight.risk_assessment.map((risk, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                              <span className="text-sm">{risk}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Data Sources */}
                    {insight.data_sources && (
                      <div className="bg-muted rounded-lg p-4">
                        <h5 className="font-medium mb-2">Analysis Coverage</h5>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div className="text-center">
                            <div className="font-semibold">{insight.data_sources.news_articles || 0}</div>
                            <div className="text-muted-foreground">News Articles</div>
                          </div>
                          <div className="text-center">
                            <div className="font-semibold">{insight.data_sources.patents_found || 0}</div>
                            <div className="text-muted-foreground">Patents</div>
                          </div>
                          <div className="text-center">
                            <div className="font-semibold">{insight.data_sources.pages_analyzed || 0}</div>
                            <div className="text-muted-foreground">Pages Analyzed</div>
                          </div>
                          <div className="text-center">
                            <div className="font-semibold">{insight.data_sources.verified_facts || 0}</div>
                            <div className="text-muted-foreground">Verified Facts</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Competitive Analysis */}
      {runData.competitive && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Competitive Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Market Positioning */}
                {runData.competitive.market_positioning && (
                  <div className="border-l-4 border-blue-500 pl-4">
                    <h4 className="font-semibold text-lg mb-2">Market Positioning</h4>
                    <p className="text-muted-foreground">{runData.competitive.market_positioning}</p>
                  </div>
                )}

                {/* Competitive Advantages */}
                {runData.competitive.competitive_advantages && runData.competitive.competitive_advantages.length > 0 && (
                  <div className="border-l-4 border-green-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      Competitive Advantages
                    </h4>
                    <ul className="space-y-2">
                      {runData.competitive.competitive_advantages.map((advantage, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{advantage}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Market Threats */}
                {runData.competitive.market_threats && runData.competitive.market_threats.length > 0 && (
                  <div className="border-l-4 border-red-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                      Market Threats
                    </h4>
                    <ul className="space-y-2">
                      {runData.competitive.market_threats.map((threat, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{threat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Market Opportunities */}
                {runData.competitive.market_opportunities && runData.competitive.market_opportunities.length > 0 && (
                  <div className="border-l-4 border-purple-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-purple-600" />
                      Market Opportunities
                    </h4>
                    <ul className="space-y-2">
                      {runData.competitive.market_opportunities.map((opportunity, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <Lightbulb className="h-4 w-4 text-purple-600 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{opportunity}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Key Competitors */}
                {runData.competitive.competitors && runData.competitive.competitors.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-lg mb-4">Key Competitors</h4>
                    <div className="grid gap-4">
                      {runData.competitive.competitors.slice(0, 5).map((competitor, idx) => (
                        <div key={idx} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-2">
                            <h5 className="font-semibold">{competitor.name}</h5>
                            <Badge variant={
                              competitor.category === 'Direct' ? 'destructive' : 
                              competitor.category === 'Indirect' ? 'secondary' : 'outline'
                            }>
                              {competitor.category} Competitor
                            </Badge>
                          </div>
                          {competitor.description && (
                            <p className="text-muted-foreground text-sm mb-2">{competitor.description}</p>
                          )}
                          {competitor.strengths && competitor.strengths.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-muted-foreground mb-1">Strengths:</p>
                              <div className="flex flex-wrap gap-1">
                                {competitor.strengths.map((strength, sidx) => (
                                  <Badge key={sidx} variant="outline" className="text-xs">
                                    {strength}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Investment Implications */}
                {runData.competitive.investment_implications && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h5 className="font-medium text-blue-800 mb-2">Investment Implications</h5>
                    <p className="text-sm text-blue-700">{runData.competitive.investment_implications}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Deep Dive Analysis */}
      {runData.deepdive && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Deep Dive Analysis
                {runData.deepdive.confidence_score && (
                  <Badge variant="default">
                    {Math.round(runData.deepdive.confidence_score * 100)}% confidence
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Company Profile */}
                {runData.deepdive.company_profile && (
                  <div className="border-l-4 border-blue-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3">Company Profile</h4>
                    <div className="grid md:grid-cols-2 gap-4">
                      {runData.deepdive.company_profile.mission_vision && (
                        <div>
                          <h5 className="font-medium mb-1">Mission & Vision</h5>
                          <p className="text-sm text-muted-foreground">{runData.deepdive.company_profile.mission_vision}</p>
                        </div>
                      )}
                      {runData.deepdive.company_profile.business_model && (
                        <div>
                          <h5 className="font-medium mb-1">Business Model</h5>
                          <p className="text-sm text-muted-foreground">{runData.deepdive.company_profile.business_model}</p>
                        </div>
                      )}
                      {runData.deepdive.company_profile.target_market && (
                        <div>
                          <h5 className="font-medium mb-1">Target Market</h5>
                          <p className="text-sm text-muted-foreground">{runData.deepdive.company_profile.target_market}</p>
                        </div>
                      )}
                      {runData.deepdive.company_profile.value_proposition && (
                        <div>
                          <h5 className="font-medium mb-1">Value Proposition</h5>
                          <p className="text-sm text-muted-foreground">{runData.deepdive.company_profile.value_proposition}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Team Analysis */}
                {runData.deepdive.team_analysis && (
                  <div className="border-l-4 border-green-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3">Team Analysis</h4>
                    <div className="grid md:grid-cols-2 gap-4">
                      {Object.entries(runData.deepdive.team_analysis).map(([key, value]) => (
                        <div key={key}>
                          <h5 className="font-medium mb-1 capitalize">{key.replace(/[_-]/g, ' ')}</h5>
                          <p className="text-sm text-muted-foreground">
                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Product Analysis */}
                {runData.deepdive.product_analysis && (
                  <div className="border-l-4 border-purple-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3">Product Analysis</h4>
                    <div className="grid md:grid-cols-2 gap-4">
                      {Object.entries(runData.deepdive.product_analysis).map(([key, value]) => (
                        <div key={key}>
                          <h5 className="font-medium mb-1 capitalize">{key.replace(/[_-]/g, ' ')}</h5>
                          <p className="text-sm text-muted-foreground">
                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Business Traction */}
                {runData.deepdive.business_traction && (
                  <div className="border-l-4 border-orange-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3">Business Traction</h4>
                    <div className="grid md:grid-cols-2 gap-4">
                      {Object.entries(runData.deepdive.business_traction).map(([key, value]) => (
                        <div key={key}>
                          <h5 className="font-medium mb-1 capitalize">{key.replace(/[_-]/g, ' ')}</h5>
                          <p className="text-sm text-muted-foreground">
                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Investment Insights */}
                {runData.deepdive.investment_insights && runData.deepdive.investment_insights.length > 0 && (
                  <div className="border-l-4 border-yellow-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-600" />
                      Investment Insights
                    </h4>
                    <ul className="space-y-2">
                      {runData.deepdive.investment_insights.map((insight, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <Lightbulb className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Content Sources */}
                {runData.deepdive.content_sources && runData.deepdive.content_sources.length > 0 && (
                  <div className="bg-muted rounded-lg p-4">
                    <h5 className="font-medium mb-2">Content Sources Analyzed</h5>
                    <div className="flex flex-wrap gap-2">
                      {runData.deepdive.content_sources.map((source, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {typeof source === 'object' ? (source.url || source.title || 'Source') : String(source)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Comprehensive Assessment */}
                {runData.deepdive.comprehensive_assessment && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h5 className="font-medium text-blue-800 mb-2">Comprehensive Assessment</h5>
                    <p className="text-sm text-blue-700">{runData.deepdive.comprehensive_assessment}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Sources */}
      {runData.sources && runData.sources.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                News & Sources
                <Badge variant="secondary">{runData.sources.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {runData.sources.slice(0, 6).map((source, index) => (
                  <div key={source.id || index} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold line-clamp-2">{source.title}</h4>
                        {source.snippet && (
                          <p className="text-muted-foreground mt-1 line-clamp-3">{source.snippet}</p>
                        )}
                        <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                          {source.domain && <span>{source.domain}</span>}
                          {source.published_at && (
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {new Date(source.published_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-4 p-2 hover:bg-muted rounded"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </div>
                ))}
                {runData.sources.length > 6 && (
                  <p className="text-center text-muted-foreground">
                    And {runData.sources.length - 6} more sources...
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Patents */}
      {runData.patents && runData.patents.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Patents & IP Analysis
                <Badge variant="secondary">{runData.patents.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {runData.patents.slice(0, 5).map((patent, index) => (
                  <div key={patent._id || patent.id || index} className="border rounded-lg p-4">
                    <h4 className="font-semibold line-clamp-2">{patent.title}</h4>
                    {patent.abstract && (
                      <p className="text-muted-foreground mt-2 line-clamp-3">{patent.abstract}</p>
                    )}
                    <div className="flex items-center gap-4 mt-3 text-sm">
                      {patent.assignee && (
                        <Badge variant="outline">{patent.assignee}</Badge>
                      )}
                      {patent.agent_type && (
                        <Badge variant="outline" className="text-xs">
                          {patent.agent_type.replace('_', ' ').toUpperCase()}
                        </Badge>
                      )}
                      {patent.filing_date && (
                        <span className="text-muted-foreground">
                          Filed: {new Date(patent.filing_date).toLocaleDateString()}
                        </span>
                      )}
                      {patent.created_at && !patent.filing_date && (
                        <span className="text-muted-foreground">
                          Analyzed: {new Date(patent.created_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {runData.patents.length > 5 && (
                  <p className="text-center text-muted-foreground">
                    And {runData.patents.length - 5} more items...
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Risks */}
      {runData.risks && runData.risks.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Risk Assessment
                <Badge variant="secondary">{runData.risks.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {runData.risks.map((risk, index) => (
                  <div key={index} className="border-l-4 border-orange-500 pl-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold">{risk.category}</h4>
                        <p className="text-muted-foreground mt-1">{risk.summary}</p>
                      </div>
                      <Badge 
                        variant={risk.severity === 'high' ? 'destructive' : risk.severity === 'medium' ? 'default' : 'secondary'}
                      >
                        {risk.severity} risk
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Verification Analysis */}
      {runData.verification && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Verification & Fact-Checking
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Verified Facts */}
                {runData.verification.verified_facts && runData.verification.verified_facts.length > 0 && (
                  <div className="border-l-4 border-green-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      Verified Facts
                    </h4>
                    <div className="space-y-3">
                      {runData.verification.verified_facts.map((fact, idx) => (
                        <div key={idx} className="border rounded-lg p-3">
                          <div className="flex items-start justify-between mb-2">
                            <p className="font-medium">{fact.claim}</p>
                            <div className="flex items-center gap-2">
                              <Badge variant={
                                fact.status === 'verified' ? 'default' : 
                                fact.status === 'unverified' ? 'destructive' : 'secondary'
                              }>
                                {fact.status}
                              </Badge>
                              <Badge variant="outline">
                                {Math.round(fact.confidence * 100)}%
                              </Badge>
                            </div>
                          </div>
                          {fact.notes && (
                            <p className="text-sm text-muted-foreground">{fact.notes}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Red Flags */}
                {runData.verification.red_flags && runData.verification.red_flags.length > 0 && (
                  <div className="border-l-4 border-red-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <XCircle className="h-5 w-5 text-red-600" />
                      Red Flags
                    </h4>
                    <ul className="space-y-2">
                      {runData.verification.red_flags.map((flag, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <XCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{flag}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Information Gaps */}
                {runData.verification.information_gaps && runData.verification.information_gaps.length > 0 && (
                  <div className="border-l-4 border-yellow-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      Information Gaps
                    </h4>
                    <ul className="space-y-2">
                      {runData.verification.information_gaps.map((gap, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{gap}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Investment Risk Factors */}
                {runData.verification.investment_risk_factors && runData.verification.investment_risk_factors.length > 0 && (
                  <div className="border-l-4 border-orange-500 pl-4">
                    <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-orange-600" />
                      Investment Risk Factors
                    </h4>
                    <ul className="space-y-2">
                      {runData.verification.investment_risk_factors.map((risk, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{risk}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Source Reliability */}
                {runData.verification.source_reliability && (
                  <div className="bg-muted rounded-lg p-4">
                    <h5 className="font-medium mb-2">Source Reliability</h5>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      {Object.entries(runData.verification.source_reliability).map(([source, reliability]) => (
                        <div key={source} className="text-center">
                          <div className="font-semibold">
                            {typeof reliability === 'object' ? JSON.stringify(reliability) : String(reliability)}
                          </div>
                          <div className="text-muted-foreground capitalize">{source.replace(/[_-]/g, ' ')}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Additional Verification Needed */}
                {runData.verification.additional_verification_needed && runData.verification.additional_verification_needed.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h5 className="font-medium text-blue-800 mb-2">Additional Verification Needed</h5>
                    <ul className="space-y-1">
                      {runData.verification.additional_verification_needed.map((item, idx) => (
                        <li key={idx} className="text-sm text-blue-700">• {item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Verification Summary */}
                {runData.verification.verification_summary && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h5 className="font-medium text-gray-800 mb-2">Verification Summary</h5>
                    <p className="text-sm text-gray-700">{runData.verification.verification_summary}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Errors */}
      {runData.errors && runData.errors.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-600">
                <XCircle className="h-5 w-5" />
                Errors & Issues
                <Badge variant="destructive">{runData.errors.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {runData.errors.map((error, index) => (
                  <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-red-800">{error.message}</p>
                        {error.agent && (
                          <Badge variant="outline" className="mt-2 text-red-600">
                            {error.agent}
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-red-600">
                        {new Date(error.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}