export interface Company {
  name: string;
  domain?: string;
}

export interface RunCreateRequest {
  company: string;
  domain?: string;
}

export interface RunCreateResponse {
  run_id: string;
  status: string;
}

export interface Cost {
  tavily_credits: number;
  llm_tokens: number;
  openai_usd: number;
}

export interface Source {
  id: string;
  title: string;
  url: string;
  snippet?: string;
  published_at?: string;
  domain?: string;
  type?: string;
}

export interface Patent {
  _id?: string;
  id?: string;
  run_id?: string;
  title: string;
  assignee?: string;
  filing_date?: string;
  grant_date?: string;
  abstract?: string;
  cpc?: string[];
  url: string;
  agent_type?: string;
  created_at?: string;
}

export interface Risk {
  category: string;
  severity: string;
  summary: string;
  citations: string[];
}

export interface Founder {
  _id?: string;
  id?: string;
  run_id?: string;
  type?: string;
  name: string;
  role: string;
  background_summary?: string;
  previous_experience?: string[];
  key_achievements?: string[];
  investment_assessment?: string;
  source_confidence?: 'high' | 'medium' | 'low';
  agent_type?: string;
  created_at?: string;
  // Legacy fields for backward compatibility
  bio?: string;
  linkedin?: string;
  twitter?: string;
  experience?: string[];
}

export interface Insight {
  _id?: string;
  id?: string;
  run_id: string;
  executive_summary?: string;
  investment_signals?: string[];
  risk_assessment?: string[];
  confidence_score: number;
  llm_enhanced?: boolean;
  data_sources?: {
    news_articles: number;
    patents_found: number;
    pages_analyzed: number;
    verified_facts: number;
  };
  funding_events?: any[];
  partnerships?: any[];
  created_at?: string;
  // Legacy fields for backward compatibility
  category?: string;
  title?: string;
  content?: string;
  sources?: string[];
}

export interface CompetitiveAnalysis {
  _id?: string;
  run_id?: string;
  type?: string;
  company?: string;
  competitors: Array<{
    name: string;
    category: string;
    description?: string;
    strengths?: string[];
    market_position?: string;
    funding_status?: string;
  }>;
  market_positioning?: string;
  competitive_advantages?: string[];
  market_threats?: string[];
  market_opportunities?: string[];
  market_insights?: string[];
  competitive_assessment?: string;
  investment_implications?: string;
  agent_type?: string;
  created_at?: string;
  // Legacy fields
  market_position?: string;
  threats?: string[];
  market_size?: string;
}

export interface DeepDiveAnalysis {
  _id?: string;
  run_id?: string;
  type?: string;
  company?: string;
  company_profile?: {
    mission_vision?: string;
    business_model?: string;
    target_market?: string;
    value_proposition?: string;
    company_culture?: string;
  };
  team_analysis?: any;
  product_analysis?: any;
  business_traction?: any;
  content_sources?: Array<{
    url?: string;
    title?: string;
    insights?: string[];
  } | string>;
  investment_insights?: string[];
  comprehensive_assessment?: string;
  confidence_score?: number;
  agent_type?: string;
  created_at?: string;
  // Legacy fields
  company_timeline?: Array<{
    date: string;
    event: string;
    impact: string;
  }>;
  product_info?: {
    main_products: string[];
    target_market: string[];
    pricing_model?: string;
  };
  team_size?: number;
  funding_history?: Array<{
    round: string;
    amount: string;
    date: string;
    investors: string[];
  }>;
}

export interface VerificationAnalysis {
  _id?: string;
  run_id?: string;
  type?: string;
  company?: string;
  verified_facts?: Array<{
    claim: string;
    status: string;
    confidence: number;
    sources?: string[];
    notes?: string;
  }>;
  confidence_scores?: any;
  inconsistencies_found?: any[];
  information_gaps?: string[];
  red_flags?: string[];
  source_reliability?: any;
  verification_summary?: string;
  investment_risk_factors?: string[];
  additional_verification_needed?: string[];
  agent_type?: string;
  created_at?: string;
  // Legacy fields
  overall_confidence?: number;
  data_quality_score?: number;
}

export type RunStatus = 'pending' | 'running' | 'partial' | 'complete' | 'completed' | 'error';

export interface RunState {
  run_id: string;
  status: RunStatus;
  company: Company;
  insights?: Insight[];
  patents?: Patent[];
  risks?: Risk[];
  sources?: Source[];
  founders?: Founder[];
  competitive?: CompetitiveAnalysis;
  deepdive?: DeepDiveAnalysis;
  verification?: VerificationAnalysis;
  cost: Cost;
  errors?: Array<{
    message: string;
    timestamp: string;
    agent?: string;
  }>;
}

export interface BudgetStatus {
  total_spend_usd: number;
  remaining_budget_usd: number;
  tavily_credits_used: number;
  openai_tokens_used: number;
  last_updated: string;
  warnings: string[];
}

export interface RunHistoryItem {
  run_id: string;
  company: Company;
  status: RunStatus;
  created_at: string;
  completed_at?: string;
  cost: Cost;
  errors: Array<{
    message: string;
    timestamp: string;
    agent?: string;
  }>;
  error_count: number;
  estimated_total_cost_usd: number;
  duration_minutes?: number;
}

export interface RunsHistoryResponse {
  runs: RunHistoryItem[];
  total_count: number;
  page_info: {
    limit: number;
    has_more: boolean;
  };
}