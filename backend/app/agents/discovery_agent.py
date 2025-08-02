"""
Discovery Agent - True LLM Agent using LangGraph create_react_agent.
Uses LLM decision-making to map company digital presence and plan research strategy.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState

from app.tools.tavily_tools import TavilyMapTool, TavilySearchTool, TavilyExtractTool
from app.services.llm_client import llm_client, AGENT_SYSTEM_PROMPTS
from app.models.schemas import DiscoveryResults
from app.models.agent_outputs import DiscoveryOutput

logger = logging.getLogger(__name__)


class DiscoveryAgent:
    """
    Discovery Agent - True LLM agent that uses reasoning to discover company digital presence.
    
    This agent uses LLM decision-making to:
    1. Plan discovery strategy based on available company information
    2. Choose which tools to use and when
    3. Analyze discovered content and decide on next steps
    4. Generate structured discovery results with strategic insights
    """
    
    def __init__(self):
        # Get LLM configured for analysis tasks
        self.llm = llm_client.get_llm_for_task("analysis")
        
        # Available tools for the agent
        self.tools = [
            TavilyMapTool(),
            TavilySearchTool(), 
            TavilyExtractTool()
        ]
        
        # Create the ReAct agent with structured output
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            prompt=AGENT_SYSTEM_PROMPTS["discovery"],
            response_format=DiscoveryOutput
        )
        
        logger.info("Discovery Agent initialized with LLM decision-making capabilities")
    
    async def discover_company(self, company_name: str, company_domain: str = None, run_id: str = None) -> DiscoveryResults:
        """
        Use LLM-driven discovery to map company digital presence.
        
        Args:
            company_name: Name of the company to discover
            company_domain: Optional company domain/website
            run_id: Optional run identifier for tracking
            
        Returns:
            DiscoveryResults with structured findings
        """
        try:
            # Check budget before starting
            if not await llm_client.check_budget_for_operation("discovery", 1500):
                logger.warning("Insufficient budget for Discovery Agent LLM operations")
                return self._create_fallback_results(company_name, run_id, "Budget constraints")
            
            # Prepare the discovery task for the LLM agent
            discovery_task = self._create_discovery_task(company_name, company_domain)
            
            logger.info(f"Discovery Agent starting LLM-driven analysis for {company_name}")
            
            # Let the LLM agent plan and execute discovery with structured output
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=discovery_task)]
            })
            
            # Extract structured output directly
            structured_output = self._extract_structured_output(response)
            discovery_results = self._create_discovery_results_from_structured(
                company_name, run_id, structured_output
            )
            
            logger.info(f"Discovery Agent completed analysis - found {len(discovery_results.discovered_urls)} URLs")
            return discovery_results
            
        except Exception as e:
            logger.error(f"Discovery Agent error: {e}")
            return self._create_fallback_results(company_name, run_id, f"Error: {str(e)}")
    
    def _create_discovery_task(self, company_name: str, company_domain: str = None) -> str:
        """Create a comprehensive discovery task for the LLM agent."""
        
        task = f"""
DISCOVERY MISSION: Comprehensive Company Intelligence Gathering

Company: {company_name}
Domain: {company_domain or "Unknown - need to find"}

Your task is to THOROUGHLY discover and analyze this company's digital presence to build a comprehensive foundation for investment intelligence gathering.

CRITICAL REQUIREMENTS:
1. NEVER return incomplete or shallow analysis
2. Extract maximum strategic value from every piece of information
3. If website mapping yields limited results, use alternative discovery methods
4. Always provide business intelligence insights, not just technical findings
5. Analyze competitive positioning based on available information

DISCOVERY OBJECTIVES:
1. Map the company's website structure and key pages
2. Identify high-value content areas (about, team, products, funding)
3. Discover company aliases, alternative names, or brand variations
4. Assess the richness and quality of available information
5. Extract business intelligence insights from discovered content
6. Provide strategic recommendations for deeper analysis

EXECUTION STRATEGY:
Phase 1 - Initial Mapping:
- If domain provided: Use tavily_map to explore website structure
- If no domain: Use tavily_search to find official website first
- Focus on discovering key page categories (about, team, products, news)

Phase 2 - Content Assessment:
- Use tavily_extract on 2-3 most promising pages for initial content assessment
- Look for company aliases, founding information, key personnel
- Assess information density and quality

Phase 3 - Strategic Analysis:
- Evaluate which pages would be most valuable for deeper analysis
- Identify gaps that might need additional research
- Recommend optimal approach for other agents

EXPECTED DELIVERABLES:
- Categorized list of discovered URLs (about, team, products, etc.)
- Company aliases or alternative names found
- Assessment of information richness (high/medium/low)
- Key insights or red flags discovered
- Recommendations for next phase analysis

BUDGET AWARENESS:
You have limited API credits. Make strategic decisions about tool usage.
Prioritize quality discoveries over exhaustive mapping.

Begin your discovery analysis now. Use your tools strategically and provide structured findings.
"""
        return task
    
    def _extract_structured_output(self, response: Dict[str, Any]) -> DiscoveryOutput:
        """Extract structured output from agent response."""
        
        # Try to get structured response first
        if "structured_response" in response:
            return response["structured_response"]
            
        # Fallback: create from message content
        messages = response.get("messages", [])
        if not messages:
            return self._create_fallback_discovery_output()
        
        # Find the last AI message with content
        for message in reversed(messages):
            if hasattr(message, 'content') and message.content:
                try:
                    # Try to parse as JSON if it looks like structured data
                    import json
                    if message.content.strip().startswith('{'):
                        data = json.loads(message.content)
                        return DiscoveryOutput(**data)
                except:
                    pass
                break
        
        return self._create_fallback_discovery_output()
    
    def _create_fallback_discovery_output(self) -> DiscoveryOutput:
        """Create fallback discovery output when parsing fails."""
        return DiscoveryOutput(
            discovered_urls=[],
            company_aliases=[],
            confidence_score=0.3,
            digital_presence_summary="Unable to complete discovery analysis",
            key_insights=["Discovery analysis incomplete due to parsing error"],
            website_analysis="Website analysis unavailable"
        )
    
    def _extract_agent_output(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - Extract structured output from agent response."""
        
        # Get the final message from the agent
        messages = response.get("messages", [])
        if not messages:
            return {"analysis": "No agent output received", "urls": [], "insights": []}
        
        # Find the last AI message with the analysis
        agent_analysis = ""
        for message in reversed(messages):
            if hasattr(message, 'content') and message.content:
                if not message.content.startswith("I'll") and not message.content.startswith("Let me"):
                    agent_analysis = message.content
                    break
        
        # Parse the agent's analysis to extract structured information
        discovered_urls = self._extract_urls_from_analysis(agent_analysis)
        company_aliases = self._extract_aliases_from_analysis(agent_analysis)
        key_insights = self._extract_insights_from_analysis(agent_analysis)
        
        return {
            "analysis": agent_analysis,
            "urls": discovered_urls,
            "aliases": company_aliases,
            "insights": key_insights
        }
    
    def _extract_urls_from_analysis(self, analysis: str) -> List[str]:
        """Extract URLs mentioned in the agent's analysis."""
        import re
        
        # Look for URL patterns in the analysis
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, analysis)
        
        # Clean and deduplicate URLs
        clean_urls = []
        for url in urls:
            # Remove trailing punctuation
            url = url.rstrip('.,;:!?')
            if url not in clean_urls and len(url) > 10:
                clean_urls.append(url)
        
        return clean_urls[:20]  # Limit to prevent overwhelming downstream agents
    
    def _extract_aliases_from_analysis(self, analysis: str) -> List[str]:
        """Extract company aliases from the agent's analysis."""
        aliases = []
        
        # Look for patterns like "also known as", "aka", "formerly", etc.
        alias_patterns = [
            r'also known as ([^,.\n]+)',
            r'aka ([^,.\n]+)',
            r'formerly ([^,.\n]+)', 
            r'brand name[s]? ([^,.\n]+)',
            r'operating as ([^,.\n]+)'
        ]
        
        for pattern in alias_patterns:
            import re
            matches = re.findall(pattern, analysis, re.IGNORECASE)
            for match in matches:
                alias = match.strip().strip('"\'')
                if alias and len(alias) > 1 and alias not in aliases:
                    aliases.append(alias)
        
        return aliases[:5]  # Limit aliases
    
    def _extract_insights_from_analysis(self, analysis: str) -> List[str]:
        """Extract key insights from the agent's analysis."""
        insights = []
        
        # Look for insight patterns
        insight_indicators = [
            "key finding", "important", "notable", "significant",
            "recommendation", "suggests", "indicates", "reveals"
        ]
        
        sentences = analysis.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Skip very short sentences
                for indicator in insight_indicators:
                    if indicator.lower() in sentence.lower():
                        insights.append(sentence)
                        break
        
        return insights[:5]  # Limit insights
    
    def _create_discovery_results(self, company_name: str, run_id: str, agent_output: Dict[str, Any]) -> DiscoveryResults:
        """Create structured DiscoveryResults from agent output."""
        
        discovered_urls = agent_output.get("urls", [])
        
        # Categorize URLs based on path patterns
        key_pages = {}
        for url in discovered_urls:
            url_lower = url.lower()
            if any(keyword in url_lower for keyword in ["about", "company", "story"]):
                key_pages["about"] = url
            elif any(keyword in url_lower for keyword in ["team", "leadership", "people"]):
                key_pages["team"] = url
            elif any(keyword in url_lower for keyword in ["product", "service", "solution"]):
                key_pages["products"] = url
            elif any(keyword in url_lower for keyword in ["blog", "news", "press"]):
                key_pages["news"] = url
            elif any(keyword in url_lower for keyword in ["career", "job", "hiring"]):
                key_pages["careers"] = url
        
        return DiscoveryResults(
            id=f"discovery_{run_id or 'unknown'}",
            run_id=run_id or "unknown",
            base_url=discovered_urls[0] if discovered_urls else "",
            discovered_urls=discovered_urls,
            company_aliases=[company_name] + agent_output.get("aliases", []),
            social_media_links=[],  # Could be enhanced to extract social links
            key_pages=key_pages,
            llm_analysis=agent_output.get("analysis", ""),
            confidence_score=self._assess_discovery_confidence(agent_output),
            timestamp=datetime.utcnow()
        )
    
    def _create_discovery_results_from_structured(
        self, 
        company_name: str, 
        run_id: str, 
        structured_output: DiscoveryOutput
    ) -> DiscoveryResults:
        """Create DiscoveryResults from structured output."""
        
        # Categorize URLs based on path patterns
        key_pages = {}
        for url in structured_output.discovered_urls:
            url_lower = url.lower()
            if any(keyword in url_lower for keyword in ["about", "company", "story"]):
                key_pages["about"] = url
            elif any(keyword in url_lower for keyword in ["team", "leadership", "people"]):
                key_pages["team"] = url
            elif any(keyword in url_lower for keyword in ["product", "service", "solution"]):
                key_pages["products"] = url
            elif any(keyword in url_lower for keyword in ["blog", "news", "press"]):
                key_pages["news"] = url
            elif any(keyword in url_lower for keyword in ["career", "job", "hiring"]):
                key_pages["careers"] = url
        
        return DiscoveryResults(
            id=f"discovery_{run_id or 'unknown'}",
            run_id=run_id or "unknown",
            base_url=structured_output.discovered_urls[0] if structured_output.discovered_urls else "",
            discovered_urls=structured_output.discovered_urls,
            company_aliases=[company_name] + structured_output.company_aliases,
            social_media_links=[],  # Could be enhanced later
            key_pages=key_pages,
            llm_analysis=structured_output.digital_presence_summary,
            confidence_score=structured_output.confidence_score,
            timestamp=datetime.utcnow(),
            key_insights=structured_output.key_insights,
            website_analysis=structured_output.website_analysis
        )
    
    def _assess_discovery_confidence(self, agent_output: Dict[str, Any]) -> float:
        """Assess confidence in discovery results based on output quality."""
        
        confidence = 0.0
        
        # Base confidence on number of URLs found
        urls_found = len(agent_output.get("urls", []))
        confidence += min(0.4, urls_found * 0.05)  # Up to 0.4 for URLs
        
        # Add confidence for analysis quality
        analysis = agent_output.get("analysis", "")
        if len(analysis) > 200:
            confidence += 0.2
        if len(analysis) > 500:
            confidence += 0.1
        
        # Add confidence for insights
        insights = agent_output.get("insights", [])
        confidence += min(0.2, len(insights) * 0.05)  # Up to 0.2 for insights
        
        # Add confidence for aliases found
        aliases = agent_output.get("aliases", [])
        confidence += min(0.1, len(aliases) * 0.02)  # Up to 0.1 for aliases
        
        return min(1.0, confidence)
    
    def _create_fallback_results(self, company_name: str, run_id: str, reason: str) -> DiscoveryResults:
        """Create fallback results when LLM agent cannot operate."""
        
        logger.warning(f"Creating fallback discovery results: {reason}")
        
        return DiscoveryResults(
            id=f"discovery_{run_id or 'unknown'}",
            run_id=run_id or "unknown",
            base_url="",
            discovered_urls=[],
            company_aliases=[company_name],
            social_media_links=[],
            key_pages={},
            llm_analysis=f"Discovery analysis unavailable: {reason}",
            confidence_score=0.1,
            timestamp=datetime.utcnow()
        )


# Global discovery agent instance
discovery_agent = DiscoveryAgent()