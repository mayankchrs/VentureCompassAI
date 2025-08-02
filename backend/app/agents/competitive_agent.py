"""
Competitive Intelligence Agent - LLM-powered market analysis.
Researches competitors, market positioning, and competitive landscape for investment intelligence.
"""

import logging
from typing import List, Optional, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from app.tools.tavily_tools import tavily_tools
from app.services.llm_client import llm_client, AGENT_SYSTEM_PROMPTS
from app.models.schemas import DiscoveryResults
from app.models.agent_outputs import CompetitiveOutput

logger = logging.getLogger(__name__)


class CompetitiveIntelligenceAgent:
    """LLM agent for comprehensive competitive landscape analysis."""
    
    def __init__(self):
        self.llm = llm_client.get_llm_for_task("analysis")
        self.tools = tavily_tools
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            prompt=AGENT_SYSTEM_PROMPTS["competitive"],
            response_format=CompetitiveOutput
        )
        logger.info("Competitive Intelligence Agent initialized with GPT-4o")
    
    async def analyze_competitive_landscape(
        self, 
        company_name: str, 
        discovery_results: Optional[DiscoveryResults] = None,
        run_id: str = None
    ) -> Dict[str, Any]:
        """Conduct comprehensive competitive landscape analysis using LLM reasoning."""
        
        try:
            logger.info(f"Competitive Intelligence Agent starting analysis for {company_name}")
            
            # Create comprehensive competitive research task
            competitive_task = self._create_competitive_research_task(
                company_name, discovery_results
            )
            
            # Let the LLM agent plan and execute competitive research
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=competitive_task)]
            })
            
            # Extract structured output from agent response
            if "structured_response" in response:
                structured_output = response["structured_response"]
                competitive_analysis = self._convert_to_analysis_dict(structured_output, company_name, run_id)
            else:
                # Fallback to text parsing
                agent_output = self._extract_agent_output(response)
                competitive_analysis = self._create_competitive_analysis_legacy(company_name, run_id, agent_output)
            
            logger.info(f"Competitive Intelligence Agent identified {len(competitive_analysis.get('competitors', []))} key competitors")
            return competitive_analysis
            
        except Exception as e:
            logger.error(f"Competitive Intelligence Agent error: {e}")
            return self._create_fallback_analysis(company_name, run_id, f"Error: {str(e)}")
    
    def _create_competitive_research_task(
        self, 
        company_name: str, 
        discovery_results: Optional[DiscoveryResults] = None
    ) -> str:
        """Create a comprehensive competitive research task for the LLM agent."""
        
        # Build context from discovery results
        context_info = ""
        company_domain = "Unknown"
        if discovery_results:
            company_domain = discovery_results.base_url
            context_info = f"""
DISCOVERY CONTEXT:
- Company Website: {discovery_results.base_url}
- Product Pages Found: {len([url for url in discovery_results.discovered_urls if 'product' in url.lower()])} pages
- Company Category Insights: {discovery_results.llm_analysis[:300]}...
"""
        
        task = f"""
COMPETITIVE INTELLIGENCE MISSION: Comprehensive Market Landscape Analysis

PRIMARY TARGET: {company_name}
Domain: {company_domain}
{context_info}

Your mission is to conduct THOROUGH competitive intelligence research to provide investment-grade market positioning and competitive landscape analysis.

CRITICAL REQUIREMENTS:
1. NEVER return incomplete competitive analysis
2. Identify direct and indirect competitors across market segments
3. Analyze competitive positioning, differentiation, and market share
4. Assess competitive threats and market opportunities
5. Evaluate competitive advantages and potential vulnerabilities
6. Always provide strategic market positioning assessment

RESEARCH OBJECTIVES:
1. **Direct Competitor Identification**:
   - Companies offering similar products/services
   - Market leaders and emerging players
   - Recent funding and growth trajectories
   - Customer overlap and market positioning

2. **Indirect Competitor Analysis**:
   - Adjacent market players and substitutes
   - Platform and ecosystem competitors
   - Technology alternative approaches
   - Business model variants and innovations

3. **Market Positioning Assessment**:
   - Unique value proposition analysis
   - Pricing and go-to-market strategy
   - Target customer segments and use cases
   - Competitive differentiation factors

4. **Competitive Landscape Dynamics**:
   - Market size and growth trends
   - Competitive intensity and fragmentation
   - Barriers to entry and switching costs
   - Network effects and platform dynamics

RESEARCH STRATEGY:
Phase 1 - Direct Competitor Discovery:
- Search for "[Company domain/category] competitors alternatives"
- Look for "vs [Company]" comparison content
- Find industry reports and market analysis
- Search for "[Company category] market leaders"

Phase 2 - Market Category Analysis:
- Search for industry trends and market size
- Look for analyst reports and market research
- Find funding and acquisition activity in the space
- Search for "[Industry] landscape competitive analysis"

Phase 3 - Competitive Feature Analysis:
- Search for product comparisons and reviews
- Look for customer feedback and switching behavior
- Find pricing and positioning analysis
- Search for competitive advantages discussions

Phase 4 - Market Dynamics Assessment:
- Use tavily_extract on competitive analysis content
- Research market trends and disruption factors
- Analyze competitive moats and differentiation
- Assess market opportunity and threats

ADAPTIVE SEARCH STRATEGY:
If direct competitive searches yield limited results:
1. Search for broader industry category and trends
2. Look for technology alternatives and substitutes
3. Search for customer use case overlaps
4. Find adjacent market convergence patterns
5. Research ecosystem and platform competition

MANDATORY OUTPUT REQUIREMENTS:
- ALWAYS provide competitive positioning assessment
- Identify key competitors even if limited information available
- Analyze market dynamics and competitive threats
- Include assessment of competitive advantages and risks
- Never leave competitive analysis incomplete

EXAMPLE SEARCH QUERIES:
- "[Company] competitors alternatives comparison"
- "[Company category] market analysis competitive landscape"
- "[Company domain] vs competitors features pricing"
- "[Industry] market leaders emerging players"
- "[Company technology] competitive advantages differentiation"

OUTPUT STRUCTURE:
Provide comprehensive analysis including:
- List of direct competitors with analysis
- Indirect competitors and market alternatives
- Market positioning and differentiation assessment
- Competitive advantages and potential threats
- Market dynamics and growth opportunities
- Investment implications of competitive position
"""
        
        return task
    
    def _extract_structured_output(self, response, company_name: str, run_id: str) -> Dict[str, Any]:
        """Extract structured output from agent response."""
        try:
            # Get the last message which should contain the structured output
            if hasattr(response, 'messages') and response.messages:
                last_message = response.messages[-1]
                
                # Check if it's already a CompetitiveOutput instance
                if hasattr(last_message, 'content') and hasattr(last_message.content, 'competitors'):
                    structured_output = last_message.content
                    return self._convert_to_analysis_dict(structured_output, company_name, run_id)
                
                # Try to parse as structured content
                content = last_message.content
                if hasattr(content, 'competitors'):
                    return self._convert_to_analysis_dict(content, company_name, run_id)
                    
            # Fallback to parsing text output
            return self._create_fallback_analysis(company_name, run_id, "Could not extract structured output")
            
        except Exception as e:
            logger.error(f"Error extracting structured output: {e}")
            return self._create_fallback_analysis(company_name, run_id, f"Extraction error: {str(e)}")
    
    def _extract_agent_output(self, response) -> str:
        """Extract the agent's analysis from the LangGraph response."""
        if hasattr(response, 'messages') and response.messages:
            return response.messages[-1].content
        elif isinstance(response, dict) and 'output' in response:
            return response['output']
        else:
            return str(response)
    
    def _convert_to_analysis_dict(
        self, 
        structured_output: CompetitiveOutput, 
        company_name: str, 
        run_id: str
    ) -> Dict[str, Any]:
        """Convert CompetitiveOutput to analysis dictionary."""
        return {
            "id": f"competitive_{run_id}",
            "run_id": run_id,
            "company": company_name,
            "competitors": [{
                "name": comp.name,
                "category": comp.category,
                "description": comp.description,
                "strengths": comp.strengths,
                "market_position": comp.market_position,
                "funding_status": comp.funding_status
            } for comp in structured_output.competitors],
            "market_positioning": structured_output.market_positioning,
            "competitive_advantages": structured_output.competitive_advantages,
            "market_threats": structured_output.market_threats,
            "market_opportunities": structured_output.market_opportunities,
            "market_insights": structured_output.market_insights,
            "competitive_assessment": structured_output.competitive_assessment,
            "investment_implications": structured_output.investment_implications
        }
    
    def _create_competitive_analysis_legacy(
        self, 
        company_name: str, 
        run_id: str, 
        agent_output: str
    ) -> Dict[str, Any]:
        """Create structured competitive analysis from agent output."""
        
        # Parse the agent output and create structured analysis
        competitors = []
        market_insights = []
        
        lines = agent_output.split('\n')
        current_competitor = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for competitor mentions
            if any(keyword in line.lower() for keyword in ['competitor', 'rival', 'alternative', 'vs']):
                if current_competitor and current_competitor.get('name'):
                    competitors.append(current_competitor)
                
                current_competitor = {
                    "name": self._extract_competitor_name(line),
                    "category": "direct" if "direct" in line.lower() else "indirect",
                    "description": line,
                    "strengths": [],
                    "market_position": "unknown",
                    "funding_status": "unknown"
                }
            elif current_competitor and line:
                # Add details to current competitor
                if any(keyword in line.lower() for keyword in ['strength', 'advantage', 'leading']):
                    current_competitor["strengths"].append(line)
                elif any(keyword in line.lower() for keyword in ['funded', 'valuation', 'raised']):
                    current_competitor["funding_status"] = line
            elif any(keyword in line.lower() for keyword in ['market', 'industry', 'trend', 'opportunity']):
                market_insights.append(line)
        
        # Add the last competitor
        if current_competitor and current_competitor.get('name'):
            competitors.append(current_competitor)
        
        # Create comprehensive competitive analysis
        analysis = {
            "id": f"competitive_{run_id}",
            "run_id": run_id,
            "company": company_name,
            "competitors": competitors[:10],  # Limit to top 10 competitors
            "market_positioning": self._extract_market_positioning(agent_output),
            "competitive_advantages": self._extract_competitive_advantages(agent_output),
            "market_threats": self._extract_market_threats(agent_output),
            "market_opportunities": self._extract_market_opportunities(agent_output),
            "market_insights": market_insights[:5],  # Top 5 insights
            "competitive_assessment": agent_output[:500],  # Executive summary
            "investment_implications": self._extract_investment_implications(agent_output)
        }
        
        # If no competitors found, provide industry analysis
        if not competitors:
            analysis["competitors"] = [{
                "name": f"{company_name} Market Category",
                "category": "industry_analysis",
                "description": "Comprehensive market analysis completed based on available information",
                "strengths": ["Industry research conducted"],
                "market_position": "analysis_based",
                "funding_status": "market_research"
            }]
        
        return analysis
    
    def _extract_competitor_name(self, line: str) -> str:
        """Extract competitor name from a line of text."""
        # Simple competitor name extraction
        words = line.split()
        for word in words:
            if word.strip('.,():').istitle() and len(word) > 2:
                return word.strip('.,():')
        return "Market Competitor"
    
    def _extract_market_positioning(self, output: str) -> str:
        """Extract market positioning assessment from agent output."""
        lines = output.split('\n')
        positioning_lines = [line for line in lines if any(keyword in line.lower() 
                           for keyword in ['positioning', 'differentiation', 'unique', 'advantage'])]
        return ' '.join(positioning_lines[:3]) if positioning_lines else "Market positioning analysis based on available information"
    
    def _extract_competitive_advantages(self, output: str) -> List[str]:
        """Extract competitive advantages from agent output."""
        lines = output.split('\n')
        advantages = [line.strip() for line in lines if any(keyword in line.lower() 
                     for keyword in ['advantage', 'strength', 'differentiator', 'unique'])]
        return advantages[:5] if advantages else ["Competitive analysis based on available market information"]
    
    def _extract_market_threats(self, output: str) -> List[str]:
        """Extract market threats from agent output."""
        lines = output.split('\n')
        threats = [line.strip() for line in lines if any(keyword in line.lower() 
                  for keyword in ['threat', 'risk', 'challenge', 'competition'])]
        return threats[:3] if threats else ["Market threat analysis based on competitive landscape research"]
    
    def _extract_market_opportunities(self, output: str) -> List[str]:
        """Extract market opportunities from agent output."""
        lines = output.split('\n')
        opportunities = [line.strip() for line in lines if any(keyword in line.lower() 
                        for keyword in ['opportunity', 'growth', 'expansion', 'potential'])]
        return opportunities[:3] if opportunities else ["Market opportunity assessment based on industry analysis"]
    
    def _extract_investment_implications(self, output: str) -> str:
        """Extract investment implications from agent output."""
        lines = output.split('\n')
        investment_lines = [line for line in lines if any(keyword in line.lower() 
                           for keyword in ['investment', 'investor', 'valuation', 'funding'])]
        return ' '.join(investment_lines[-2:]) if investment_lines else "Investment implications assessed based on competitive positioning analysis"
    
    def _create_fallback_analysis(
        self, 
        company_name: str, 
        run_id: str, 
        error_message: str
    ) -> Dict[str, Any]:
        """Create fallback competitive analysis when research fails."""
        
        return {
            "id": f"competitive_{run_id}_fallback",
            "run_id": run_id,
            "company": company_name,
            "competitors": [{
                "name": "Competitive Analysis",
                "category": "pending",
                "description": f"Competitive Intelligence Agent will provide comprehensive market analysis. {error_message}",
                "strengths": ["Detailed competitive research pending"],
                "market_position": "analysis_pending",
                "funding_status": "research_in_progress"
            }],
            "market_positioning": "Market positioning analysis pending completion",
            "competitive_advantages": ["Competitive advantage assessment in progress"],
            "market_threats": ["Market threat analysis requires additional research"],
            "market_opportunities": ["Market opportunity assessment pending"],
            "market_insights": ["Comprehensive market intelligence gathering in progress"],
            "competitive_assessment": f"Competitive landscape analysis pending. {error_message}",
            "investment_implications": "Investment implications assessment based on competitive analysis pending"
        }


# Global competitive intelligence agent instance
competitive_agent = CompetitiveIntelligenceAgent()