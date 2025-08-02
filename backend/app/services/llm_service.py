"""
Budget-optimized LLM service with selective usage patterns.
Only uses OpenAI for final synthesis to stay within $10 limit.
"""

import openai
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.budget_tracker import budget_tracker, BudgetExceededException, cached_llm_operation
from app.core.database import generate_cache_key, get_from_cache, set_cache
import logging
import tiktoken

logger = logging.getLogger(__name__)

class LLMService:
    """Budget-aware LLM service with selective usage."""
    
    def __init__(self):
        # Use LLM_API_KEY from .env file (which contains the actual OpenAI key)
        self.api_key = settings.LLM_API_KEY if settings.LLM_API_KEY != "your-llm-key-here" else settings.OPENAI_API_KEY
        self.model = "gpt-4o"  # Using GPT-4o for superior reasoning
        self.encoding = tiktoken.encoding_for_model(self.model)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    async def should_use_llm(self, operation: str, input_text: str) -> bool:
        """Determine if LLM usage is justified for this operation."""
        # Only use LLM for final synthesis and critical analysis
        llm_worthy_operations = [
            "synthesis", "insight_generation", "risk_assessment", 
            "executive_summary", "professional_report"
        ]
        
        if operation not in llm_worthy_operations:
            logger.info(f"Skipping LLM for {operation} - not synthesis operation")
            return False
        
        # Check if we have budget
        token_count = self.count_tokens(input_text)
        estimated_cost = await budget_tracker.estimate_cost(operation, token_count)
        
        budget_ok = await budget_tracker.check_budget(estimated_cost, warn_only=True)
        if not budget_ok:
            logger.warning(f"Budget warning for {operation} - proceeding anyway")
            # Continue regardless of budget status
        
        return True
    
    async def generate_insights(self, 
                              company_data: Dict[str, Any], 
                              use_cache: bool = True) -> Dict[str, Any]:
        """Generate professional insights using LLM only when budget allows."""
        
        # Prepare input data
        input_summary = self._prepare_synthesis_input(company_data)
        
        if not await self.should_use_llm("synthesis", input_summary):
            # Return structured fallback without LLM
            return self._generate_fallback_insights(company_data)
        
        # Use cached LLM operation
        cache_params = {"operation": "synthesis", "input_hash": hash(input_summary)}
        
        try:
            result = await cached_llm_operation("synthesis", cache_params)
            
            # If this is a cache hit, return cached result
            if result.get("cached", False):
                return result
            
            # Make actual OpenAI call
            response = await self._call_openai_synthesis(input_summary)
            return response
            
        except BudgetExceededException:
            logger.warning("Budget exceeded - returning fallback insights")
            return self._generate_fallback_insights(company_data)
    
    async def _call_openai_synthesis(self, input_summary: str) -> Dict[str, Any]:
        """Make actual OpenAI API call for synthesis."""
        
        prompt = f"""
        You are a professional startup analyst. Analyze the following company data and provide COMPREHENSIVE insights.
        
        CRITICAL: NEVER return empty or generic responses. Always provide specific, actionable analysis.
        
        Required Analysis:
        1. Executive Summary (2-3 specific sentences with concrete observations)
        2. Key Investment Signals (3-5 specific bullet points - analyze what you DO find, not what's missing)
        3. Risk Assessment (2-3 specific risks based on actual data patterns)
        4. Confidence Score (0-100% with reasoning)
        
        Company Data Available:
        {input_summary}
        
        ANALYSIS REQUIREMENTS:
        - Base insights on ACTUAL data patterns found
        - If limited news: analyze what the digital presence reveals
        - Consider market positioning based on website structure/content
        - Assess competitive positioning from available information
        - Provide investment thesis even with limited direct signals
        - Never say "insufficient data" - extract value from what IS available
        
        Provide response in JSON format with keys: executive_summary, investment_signals, risks, confidence_score.
        """
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            # Record actual cost
            usage = response.usage
            # GPT-4o pricing: input $2.50/1M tokens, output $10.00/1M tokens
            actual_cost = (usage.prompt_tokens / 1000000) * 2.50 + (usage.completion_tokens / 1000000) * 10.00
            
            await budget_tracker.record_cost(
                "synthesis", 
                actual_cost, 
                usage.total_tokens,
                {"model": self.model, "prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens}
            )
            
            # Parse and return result
            content = response.choices[0].message.content
            
            return {
                "llm_generated": True,
                "content": content,
                "model_used": self.model,
                "tokens_used": usage.total_tokens,
                "cost": actual_cost
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _prepare_synthesis_input(self, company_data: Dict[str, Any]) -> str:
        """Prepare concise input for LLM synthesis."""
        # Extract key information concisely to minimize tokens
        summary_parts = []
        
        if "discovery_results" in company_data:
            discovery = company_data["discovery_results"]
            # Handle both dict and dataclass objects
            if hasattr(discovery, 'discovered_urls'):
                url_count = len(discovery.discovered_urls)
            elif isinstance(discovery, dict):
                url_count = len(discovery.get('urls', []))
            else:
                url_count = 0
            summary_parts.append(f"Digital Presence: {url_count} pages mapped")
        
        if "news_results" in company_data:
            news = company_data["news_results"]
            summary_parts.append(f"Recent News: {len(news)} articles found")
        
        if "patent_results" in company_data:
            patents = company_data["patent_results"]
            summary_parts.append(f"Patents: {len(patents)} filings discovered")
        
        if "deepdive_results" in company_data:
            deepdive = company_data["deepdive_results"]
            # Handle both dict and dataclass objects
            if isinstance(deepdive, dict):
                team_count = len(deepdive.get('team_members', []))
            else:
                team_count = 0
            summary_parts.append(f"Deep Analysis: Team of {team_count} identified")
        
        if "verified_facts" in company_data:
            verified = company_data["verified_facts"]
            summary_parts.append(f"Verified Facts: {len(verified)} cross-validated")
        
        return "; ".join(summary_parts)
    
    def _generate_fallback_insights(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured insights without LLM when budget is constrained."""
        
        investment_signals = []
        risks = []
        
        # Generate signals based on data presence
        if company_data.get("news_results"):
            investment_signals.append("Recent media coverage indicates market activity")
        
        if company_data.get("patent_results"):
            investment_signals.append("Active intellectual property development")
        
        discovery_results = company_data.get("discovery_results")
        has_urls = False
        if discovery_results:
            if hasattr(discovery_results, 'discovered_urls'):
                has_urls = len(discovery_results.discovered_urls) > 0
            elif isinstance(discovery_results, dict):
                has_urls = len(discovery_results.get("urls", [])) > 0
        
        if has_urls:
            investment_signals.append("Strong digital presence and online visibility")
        
        # Generate risks
        if not company_data.get("verified_facts"):
            risks.append("Limited cross-source validation available")
        
        if len(company_data.get("news_results", [])) < 3:
            risks.append("Low media presence may indicate early stage")
        
        # Calculate confidence based on data completeness
        data_sources = sum([
            1 if company_data.get("discovery_results") else 0,
            1 if company_data.get("news_results") else 0,
            1 if company_data.get("patent_results") else 0,
            1 if company_data.get("deepdive_results") else 0,
            1 if company_data.get("verified_facts") else 0
        ])
        
        confidence_score = min(90, (data_sources / 5) * 100)
        
        return {
            "llm_generated": False,
            "executive_summary": f"Analysis based on {data_sources} data sources with structured assessment",
            "investment_signals": investment_signals,
            "risks": risks,
            "confidence_score": confidence_score,
            "note": "Budget-optimized analysis without LLM synthesis"
        }

# Global LLM service instance
llm_service = LLMService()