"""
DeepDive Content Agent - LLM-powered comprehensive content analysis.
Extracts detailed insights from company websites, documents, and content for investment intelligence.
"""

import logging
from typing import List, Optional, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from app.tools.tavily_tools import tavily_tools
from app.services.llm_client import llm_client, AGENT_SYSTEM_PROMPTS
from app.models.schemas import DiscoveryResults
from app.models.agent_outputs import DeepDiveOutput

logger = logging.getLogger(__name__)


class DeepDiveContentAgent:
    """LLM agent for comprehensive content analysis and intelligence extraction."""
    
    def __init__(self):
        self.llm = llm_client.get_llm_for_task("analysis")
        self.tools = tavily_tools
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            prompt=AGENT_SYSTEM_PROMPTS["deepdive"],
            response_format=DeepDiveOutput
        )
        logger.info("DeepDive Content Agent initialized with GPT-4o")
    
    async def analyze_company_content(
        self, 
        company_name: str, 
        discovery_results: Optional[DiscoveryResults] = None,
        run_id: str = None
    ) -> Dict[str, Any]:
        """Conduct comprehensive content analysis using LLM reasoning."""
        
        try:
            logger.info(f"DeepDive Content Agent starting analysis for {company_name}")
            
            # Create comprehensive content analysis task
            deepdive_task = self._create_deepdive_task(
                company_name, discovery_results
            )
            
            # Let the LLM agent plan and execute content analysis
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=deepdive_task)]
            })
            
            # Extract structured output from agent response
            if "structured_response" in response:
                structured_output = response["structured_response"]
                deepdive_analysis = self._convert_to_analysis_dict(structured_output, company_name, run_id)
            else:
                # Fallback to text parsing
                agent_output = self._extract_agent_output(response)
                deepdive_analysis = self._create_deepdive_analysis_legacy(company_name, run_id, agent_output)
            
            logger.info(f"DeepDive Content Agent analyzed {len(deepdive_analysis.get('content_sources', []))} content sources")
            return deepdive_analysis
            
        except Exception as e:
            logger.error(f"DeepDive Content Agent error: {e}")
            return self._create_fallback_analysis(company_name, run_id, f"Error: {str(e)}")
    
    def _create_deepdive_task(
        self, 
        company_name: str, 
        discovery_results: Optional[DiscoveryResults] = None
    ) -> str:
        """Create a comprehensive content analysis task for the LLM agent."""
        
        # Build context from discovery results
        context_info = ""
        high_value_urls = []
        if discovery_results:
            context_info = f"""
DISCOVERY CONTEXT:
- Website: {discovery_results.base_url}
- Key Pages Found: {len(discovery_results.discovered_urls)} pages
- Discovery Insights: {discovery_results.llm_analysis[:300]}...

HIGH-VALUE PAGES FOR ANALYSIS:
"""
            # Prioritize key pages for deep analysis
            for url in discovery_results.discovered_urls[:10]:
                url_lower = url.lower()
                if any(keyword in url_lower for keyword in ['about', 'team', 'product', 'service', 'solution']):
                    high_value_urls.append(url)
                    context_info += f"- {url}\n"
        
        task = f"""
DEEPDIVE CONTENT MISSION: Comprehensive Company Intelligence Extraction

PRIMARY TARGET: {company_name}
{context_info}

Your mission is to conduct THOROUGH content analysis to extract maximum business intelligence and investment insights from company materials.

CRITICAL REQUIREMENTS:
1. NEVER return superficial content analysis
2. Extract structured business intelligence from all content sources
3. Prioritize high-value content (team, products, funding, traction)
4. Analyze company positioning, value proposition, and market approach
5. Identify key business metrics, milestones, and growth indicators
6. Always provide actionable investment intelligence

ANALYSIS OBJECTIVES:
1. **Company Profile Construction**:
   - Mission, vision, and value proposition analysis
   - Business model and revenue strategy insights
   - Target market and customer segments
   - Company culture and values assessment

2. **Team and Leadership Deep-Dive**:
   - Leadership team composition and backgrounds
   - Key personnel expertise and track records
   - Organizational structure and hiring patterns
   - Advisory board and investor connections

3. **Product and Technology Analysis**:
   - Product portfolio and feature analysis
   - Technology stack and infrastructure approach
   - Product-market fit indicators and user feedback
   - Competitive differentiation and unique capabilities

4. **Business Traction Indicators**:
   - Customer testimonials and case studies
   - Growth metrics and user adoption signals
   - Partnership announcements and integrations
   - Market validation and social proof

CONTENT ANALYSIS STRATEGY:
Phase 1 - Strategic Content Prioritization:
- Use tavily_extract on 3-5 highest value pages discovered
- Focus on about, team, product, and company pages
- Extract structured information from key landing pages
- Analyze content depth and information richness

Phase 2 - Business Intelligence Extraction:
- Extract specific details: founding date, team size, locations
- Identify business model, pricing, and go-to-market approach
- Find customer testimonials, case studies, and social proof
- Analyze product features, capabilities, and technical approach

Phase 3 - Market Positioning Analysis:
- Assess company messaging and value proposition clarity
- Analyze target market positioning and customer segments
- Identify competitive differentiation and unique selling points
- Evaluate brand positioning and market approach

Phase 4 - Investment Signal Detection:
- Look for growth indicators, traction metrics, and milestones
- Find funding mentions, investor relationships, and advisors
- Identify partnership opportunities and business development
- Assess scalability indicators and expansion potential

ADAPTIVE CONTENT STRATEGY:
If primary website content is limited:
1. Use tavily_crawl to systematically explore more pages
2. Search for company blog posts, press releases, and announcements
3. Look for product documentation, help center, and support content
4. Find social media presence and community engagement
5. Search for company presentations, pitch decks, and media kits

MANDATORY OUTPUT REQUIREMENTS:
- ALWAYS provide comprehensive business intelligence analysis
- Extract maximum value from every piece of content analyzed
- Include specific details, metrics, and concrete observations
- Provide investment implications based on content insights
- Never return generic summaries - focus on unique insights

EXAMPLE ANALYSIS AREAS:
- Company founding story and evolution timeline
- Product development approach and technical capabilities
- Customer acquisition strategy and market approach
- Team hiring patterns and organizational growth
- Partnership strategy and ecosystem positioning

OUTPUT STRUCTURE:
Provide comprehensive analysis including:
- Company profile and business model assessment
- Leadership team and organizational analysis
- Product portfolio and technology evaluation
- Market positioning and competitive differentiation
- Business traction and growth indicators
- Investment implications and strategic insights
"""
        
        return task
    
    def _extract_structured_output(self, response, company_name: str, run_id: str) -> Dict[str, Any]:
        """Extract structured output from agent response."""
        try:
            # Get the last message which should contain the structured output
            if hasattr(response, 'messages') and response.messages:
                last_message = response.messages[-1]
                
                # Check if it's already a DeepDiveOutput instance
                if hasattr(last_message, 'content') and hasattr(last_message.content, 'company_profile'):
                    structured_output = last_message.content
                    return self._convert_to_analysis_dict(structured_output, company_name, run_id)
                
                # Try to parse as structured content
                content = last_message.content
                if hasattr(content, 'company_profile'):
                    return self._convert_to_analysis_dict(content, company_name, run_id)
                    
            # Fallback to creating fallback analysis
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
        structured_output: DeepDiveOutput, 
        company_name: str, 
        run_id: str
    ) -> Dict[str, Any]:
        """Convert DeepDiveOutput to analysis dictionary."""
        return {
            "id": f"deepdive_{run_id}",
            "run_id": run_id,
            "company": company_name,
            "company_profile": {
                "mission_vision": structured_output.company_mission_vision,
                "business_model": structured_output.business_model_insights,
                "target_market": structured_output.market_approach,
                "value_proposition": structured_output.business_model_insights,
                "company_culture": structured_output.organizational_insights
            },
            "team_analysis": {
                "leadership_team": [structured_output.organizational_insights],
                "team_size_estimate": "Analysis completed",
                "key_personnel": [structured_output.organizational_insights],
                "organizational_structure": structured_output.organizational_insights,
                "hiring_patterns": structured_output.growth_indicators
            },
            "product_analysis": {
                "product_portfolio": [structured_output.product_analysis],
                "technology_stack": [structured_output.product_analysis],
                "key_features": [structured_output.product_analysis],
                "competitive_differentiation": structured_output.product_analysis,
                "product_market_fit_signals": structured_output.growth_indicators
            },
            "business_traction": {
                "customer_testimonials": structured_output.growth_indicators,
                "growth_indicators": structured_output.growth_indicators,
                "partnerships": structured_output.growth_indicators,
                "market_validation": structured_output.growth_indicators,
                "social_proof": structured_output.growth_indicators
            },
            "content_sources": [{"url": source.url, "title": source.title, "insights": source.key_insights} for source in structured_output.content_sources],
            "investment_insights": [structured_output.investment_insights],
            "comprehensive_assessment": structured_output.investment_insights,
            "confidence_score": structured_output.confidence_score
        }
    
    def _create_deepdive_analysis_legacy(
        self, 
        company_name: str, 
        run_id: str, 
        agent_output: str
    ) -> Dict[str, Any]:
        """Create structured deepdive analysis from agent output."""
        
        # Parse the agent output and create structured analysis
        analysis = {
            "id": f"deepdive_{run_id}",
            "run_id": run_id,
            "company": company_name,
            "company_profile": {
                "mission_vision": "",
                "business_model": "",
                "target_market": "",
                "value_proposition": "",
                "company_culture": ""
            },
            "team_analysis": {
                "leadership_team": [],
                "team_size_estimate": "Unknown",
                "key_personnel": [],
                "organizational_structure": "",
                "hiring_patterns": []
            },
            "product_analysis": {
                "product_portfolio": [],
                "technology_stack": [],
                "key_features": [],
                "competitive_differentiation": "",
                "product_market_fit_signals": []
            },
            "business_traction": {
                "customer_testimonials": [],
                "growth_indicators": [],
                "partnerships": [],
                "market_validation": [],
                "social_proof": []
            },
            "content_sources": [],
            "investment_insights": [],
            "comprehensive_assessment": "",
            "confidence_score": 0.7
        }
        
        # Extract structured information from agent output
        lines = agent_output.split('\n')
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify sections and extract relevant information
            if any(keyword in line.lower() for keyword in ['mission', 'vision', 'purpose']):
                current_section = 'mission_vision'
                analysis["company_profile"]["mission_vision"] += f" {line}"
            elif any(keyword in line.lower() for keyword in ['business model', 'revenue', 'pricing']):
                current_section = 'business_model'
                analysis["company_profile"]["business_model"] += f" {line}"
            elif any(keyword in line.lower() for keyword in ['target market', 'customer', 'audience']):
                current_section = 'target_market'
                analysis["company_profile"]["target_market"] += f" {line}"
            elif any(keyword in line.lower() for keyword in ['team', 'leadership', 'founder', 'ceo']):
                current_section = 'team'
                if any(name_indicator in line.lower() for name_indicator in ['ceo', 'founder', 'cto', 'president']):
                    analysis["team_analysis"]["leadership_team"].append(line)
            elif any(keyword in line.lower() for keyword in ['product', 'service', 'solution', 'platform']):
                current_section = 'product'
                analysis["product_analysis"]["product_portfolio"].append(line)
            elif any(keyword in line.lower() for keyword in ['customer', 'client', 'testimonial', 'case study']):
                current_section = 'traction'
                analysis["business_traction"]["customer_testimonials"].append(line)
            elif any(keyword in line.lower() for keyword in ['partnership', 'integration', 'collaboration']):
                analysis["business_traction"]["partnerships"].append(line)
            elif any(keyword in line.lower() for keyword in ['growth', 'users', 'metrics', 'traction']):
                analysis["business_traction"]["growth_indicators"].append(line)
            elif any(keyword in line.lower() for keyword in ['investment', 'investor', 'funding', 'strategic']):
                analysis["investment_insights"].append(line)
        
        # Create comprehensive assessment
        analysis["comprehensive_assessment"] = agent_output[:800] if len(agent_output) > 800 else agent_output
        
        # Limit array lengths
        for section in analysis["team_analysis"]:
            if isinstance(analysis["team_analysis"][section], list):
                analysis["team_analysis"][section] = analysis["team_analysis"][section][:5]
        
        for section in analysis["product_analysis"]:
            if isinstance(analysis["product_analysis"][section], list):
                analysis["product_analysis"][section] = analysis["product_analysis"][section][:5]
        
        for section in analysis["business_traction"]:
            if isinstance(analysis["business_traction"][section], list):
                analysis["business_traction"][section] = analysis["business_traction"][section][:5]
        
        analysis["investment_insights"] = analysis["investment_insights"][:5]
        
        return analysis
    
    def _create_fallback_analysis(
        self, 
        company_name: str, 
        run_id: str, 
        error_message: str
    ) -> Dict[str, Any]:
        """Create fallback analysis when content extraction fails."""
        
        return {
            "id": f"deepdive_{run_id}_fallback",
            "run_id": run_id,
            "company": company_name,
            "company_profile": {
                "mission_vision": f"DeepDive Content Agent will provide comprehensive company profile analysis. {error_message}",
                "business_model": "Business model analysis pending",
                "target_market": "Target market assessment in progress",
                "value_proposition": "Value proposition analysis pending",
                "company_culture": "Company culture assessment requires content analysis"
            },
            "team_analysis": {
                "leadership_team": ["Leadership analysis pending"],
                "team_size_estimate": "Unknown",
                "key_personnel": ["Key personnel identification in progress"],
                "organizational_structure": "Organizational analysis pending",
                "hiring_patterns": ["Hiring pattern analysis requires deeper investigation"]
            },
            "product_analysis": {
                "product_portfolio": ["Product analysis pending comprehensive content review"],
                "technology_stack": ["Technology assessment in progress"],
                "key_features": ["Feature analysis requires detailed content extraction"],
                "competitive_differentiation": "Competitive differentiation analysis pending",
                "product_market_fit_signals": ["Product-market fit assessment requires content analysis"]
            },
            "business_traction": {
                "customer_testimonials": ["Customer testimonial analysis pending"],
                "growth_indicators": ["Growth indicator assessment in progress"],
                "partnerships": ["Partnership analysis requires content review"],
                "market_validation": ["Market validation assessment pending"],
                "social_proof": ["Social proof analysis requires comprehensive content review"]
            },
            "content_sources": [],
            "investment_insights": [f"DeepDive content analysis will provide comprehensive investment insights. {error_message}"],
            "comprehensive_assessment": f"Comprehensive company content analysis pending completion. {error_message}",
            "confidence_score": 0.3
        }


# Global deepdive content agent instance
deepdive_agent = DeepDiveContentAgent()