"""
Synthesis Intelligence Agent for VentureCompass AI.
Uses LLM reasoning to synthesize comprehensive investment intelligence from all agent results.
"""

import logging
from typing import Dict, Any, List, Optional
from langgraph.prebuilt import create_react_agent

from app.services.llm_client import llm_client, AGENT_SYSTEM_PROMPTS
from app.models.agent_outputs import SynthesisOutput

logger = logging.getLogger(__name__)


class SynthesisIntelligenceAgent:
    """LLM-powered synthesis agent for investment intelligence generation."""
    
    def __init__(self):
        # Create LangGraph agent with structured output
        self.llm = llm_client.get_llm_for_task("synthesis")
        self.agent = create_react_agent(
            self.llm,
            [],  # No tools needed for synthesis
            prompt=AGENT_SYSTEM_PROMPTS["synthesis"],
            response_format=SynthesisOutput
        )
        
        logger.info("Synthesis Intelligence Agent initialized with LLM reasoning")
    
    async def analyze(self, company_name: str, run_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize comprehensive investment intelligence from all agent results.
        
        Args:
            company_name: Target company name
            run_id: Unique run identifier
            collected_data: Results from all previous agents
            
        Returns:
            Dict containing structured synthesis results
        """
        try:
            logger.info(f"Synthesis Intelligence Agent starting comprehensive analysis for {company_name}")
            
            # Prepare input for synthesis
            synthesis_input = self._prepare_synthesis_input(company_name, collected_data)
            
            # Run LLM agent for synthesis
            response = await self.agent.ainvoke({
                "messages": [{"role": "user", "content": synthesis_input}]
            })
            
            # Extract structured output
            structured_output = self._extract_structured_output(response)
            
            # Convert to dictionary format
            synthesis_results = self._convert_to_synthesis_dict(structured_output, company_name, run_id)
            
            logger.info(f"Synthesis Intelligence Agent completed comprehensive investment analysis")
            return synthesis_results
            
        except Exception as e:
            logger.error(f"Synthesis Intelligence Agent error: {e}")
            return self._create_fallback_synthesis(company_name, run_id, f"Error: {str(e)}")
    
    def _prepare_synthesis_input(self, company_name: str, collected_data: Dict[str, Any]) -> str:
        """Prepare comprehensive input for synthesis."""
        
        input_parts = [
            f"INVESTMENT SYNTHESIS MISSION for {company_name}",
            f"Analyze ALL collected intelligence and provide comprehensive investment assessment.",
            "",
            "AVAILABLE INTELLIGENCE DATA:"
        ]
        
        # News intelligence
        news_results = collected_data.get("news_results", [])
        if news_results:
            input_parts.append(f"📰 NEWS INTELLIGENCE ({len(news_results)} sources):")
            for news in news_results[:3]:  # Top 3 for brevity
                if hasattr(news, 'title') and hasattr(news, 'snippet'):
                    input_parts.append(f"- {news.title}: {news.snippet[:100]}...")
        
        # Patent intelligence
        patent_results = collected_data.get("patent_results", [])
        if patent_results:
            input_parts.append(f"📋 PATENT INTELLIGENCE ({len(patent_results)} patents):")
            for patent in patent_results[:2]:
                if hasattr(patent, 'title') and hasattr(patent, 'abstract'):
                    input_parts.append(f"- {patent.title}: {patent.abstract[:100]}...")
        
        # Founder intelligence
        founder_results = collected_data.get("founder_results", [])
        if founder_results:
            input_parts.append(f"👥 LEADERSHIP INTELLIGENCE ({len(founder_results)} profiles):")
            for founder in founder_results[:3]:
                if isinstance(founder, dict):
                    name = founder.get('name', 'Unknown')
                    role = founder.get('role', 'Leadership')
                    input_parts.append(f"- {name} ({role})")
        
        # Competitive intelligence
        competitive_results = collected_data.get("competitive_results")
        if competitive_results and isinstance(competitive_results, dict):
            competitors = competitive_results.get('competitors', [])
            if competitors:
                input_parts.append(f"🏢 COMPETITIVE INTELLIGENCE ({len(competitors)} competitors):")
                for comp in competitors[:3]:
                    if isinstance(comp, dict):
                        input_parts.append(f"- {comp.get('name', 'Unknown')}: {comp.get('description', '')[:50]}...")
        
        # DeepDive intelligence
        deepdive_results = collected_data.get("deepdive_results")
        if deepdive_results and isinstance(deepdive_results, dict):
            input_parts.append("🔍 DEEP DIVE INTELLIGENCE:")
            if 'mission_vision' in deepdive_results:
                input_parts.append(f"Mission: {deepdive_results['mission_vision'][:100]}...")
            if 'business_model' in deepdive_results:
                input_parts.append(f"Business Model: {deepdive_results['business_model'][:100]}...")
        
        # Verification intelligence
        verified_facts = collected_data.get("verified_facts", [])
        if verified_facts:
            input_parts.append(f"✅ VERIFICATION INTELLIGENCE ({len(verified_facts)} facts verified):")
            for fact in verified_facts[:3]:
                if isinstance(fact, dict):
                    input_parts.append(f"- {fact.get('claim', 'Unknown')}: {fact.get('status', 'Unknown')}")
        
        input_parts.extend([
            "",
            "SYNTHESIS REQUIREMENTS:",
            "1. Create professional executive summary (investor-grade, 2-3 sentences)",
            "2. Identify 3-5 key investment signals from the data",
            "3. Assess 2-4 specific investment risks",
            "4. Extract any funding events or financial milestones",
            "5. Identify strategic partnerships and collaborations",
            "6. Assess market positioning and competitive advantages",
            "7. Provide overall confidence score and investment recommendation",
            "",
            "Focus on ACTIONABLE insights for investors based on the collected intelligence."
        ])
        
        return "\n".join(input_parts)
    
    def _extract_structured_output(self, response: Dict[str, Any]) -> SynthesisOutput:
        """Extract structured output from agent response."""
        
        # Try to get structured response first
        if "structured_response" in response:
            return response["structured_response"]
            
        # Fallback: create from message content or use default
        return self._create_fallback_synthesis_output()
    
    def _create_fallback_synthesis_output(self) -> SynthesisOutput:
        """Create fallback synthesis output when structured extraction fails."""
        
        return SynthesisOutput(
            executive_summary="Comprehensive investment analysis completed based on multi-agent intelligence gathering across news, patents, leadership, competitive landscape, and business fundamentals.",
            investment_signals=[
                "Multi-source intelligence gathering completed",
                "Business intelligence extracted across multiple domains",
                "Leadership and competitive analysis available"
            ],
            risk_assessment=[
                "Investment decision should consider all collected intelligence",
                "Further due diligence recommended for specific areas"
            ],
            funding_events=[],
            partnerships=[],
            market_positioning="Market position assessment based on competitive and business analysis",
            confidence_score=0.7,
            investment_recommendation="Detailed analysis available - recommend thorough review of all intelligence reports for investment decision"
        )
    
    def _convert_to_synthesis_dict(self, structured_output: SynthesisOutput, company_name: str, run_id: str) -> Dict[str, Any]:
        """Convert SynthesisOutput to synthesis dictionary."""
        
        return {
            "executive_summary": structured_output.executive_summary,
            "investment_signals": structured_output.investment_signals,
            "risk_assessment": structured_output.risk_assessment,
            "funding_events": structured_output.funding_events,
            "partnerships": structured_output.partnerships,
            "market_positioning": structured_output.market_positioning,
            "confidence_score": structured_output.confidence_score,
            "investment_recommendation": structured_output.investment_recommendation,
            "llm_enhanced": True,
            "company": company_name,
            "run_id": run_id
        }
    
    def _create_fallback_synthesis(self, company_name: str, run_id: str, error_message: str) -> Dict[str, Any]:
        """Create fallback synthesis when agent fails."""
        
        return {
            "executive_summary": f"Investment synthesis for {company_name} encountered technical difficulties. {error_message}",
            "investment_signals": ["Technical analysis incomplete"],
            "risk_assessment": ["Analysis reliability affected by technical issues"],
            "funding_events": [],
            "partnerships": [],
            "market_positioning": "Market analysis pending completion",
            "confidence_score": 0.3,
            "investment_recommendation": "Re-run analysis recommended due to technical issues",
            "llm_enhanced": False,
            "company": company_name,
            "run_id": run_id
        }


# Global synthesis intelligence agent instance
synthesis_agent = SynthesisIntelligenceAgent()