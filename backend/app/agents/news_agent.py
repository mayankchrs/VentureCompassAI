"""
News Agent - True LLM Agent using LangGraph create_react_agent.
Uses LLM decision-making to find and analyze company news, funding, partnerships.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.tools.tavily_tools import TavilySearchTool, TavilyExtractTool
from app.services.llm_client import llm_client, AGENT_SYSTEM_PROMPTS
from app.models.schemas import SourceDoc, DiscoveryResults
from app.models.agent_outputs import NewsOutput

logger = logging.getLogger(__name__)


class NewsAgent:
    """
    News Agent - True LLM agent that uses reasoning to discover and analyze company news.
    
    This agent uses LLM decision-making to:
    1. Generate strategic search queries based on company context
    2. Evaluate news relevance and credibility 
    3. Analyze content for investment signals
    4. Adapt search strategy based on initial findings
    """
    
    def __init__(self):
        # Get LLM configured for analysis tasks
        self.llm = llm_client.get_llm_for_task("analysis")
        
        # Available tools for the agent
        self.tools = [
            TavilySearchTool(),
            TavilyExtractTool()
        ]
        
        # Create the ReAct agent with structured output
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            prompt=AGENT_SYSTEM_PROMPTS["news"],
            response_format=NewsOutput
        )
        
        logger.info("News Agent initialized with LLM decision-making capabilities")
    
    async def research_company_news(
        self, 
        company_name: str, 
        company_aliases: List[str] = None,
        discovery_results: Optional[DiscoveryResults] = None,
        run_id: str = None
    ) -> List[SourceDoc]:
        """
        Use LLM-driven news research to find relevant company information.
        
        Args:
            company_name: Primary company name
            company_aliases: Alternative company names/brands
            discovery_results: Context from discovery agent
            run_id: Run identifier for tracking
            
        Returns:
            List of SourceDoc with analyzed news findings
        """
        try:
            # Check budget before starting
            if not await llm_client.check_budget_for_operation("news_research", 2000):
                logger.warning("Insufficient budget for News Agent LLM operations")
                return self._create_fallback_sources(company_name, run_id, "Budget constraints")
            
            # Prepare the news research task for the LLM agent
            news_task = self._create_news_research_task(
                company_name, company_aliases, discovery_results
            )
            
            logger.info(f"News Agent starting LLM-driven research for {company_name}")
            
            # Let the LLM agent plan and execute news research with structured output
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=news_task)]
            })
            
            # Extract structured output from agent response
            if "structured_response" in response:
                structured_output = response["structured_response"]
                news_sources = self._create_news_sources_from_structured(company_name, run_id, structured_output)
            else:
                # Fallback to text parsing
                agent_output = self._extract_agent_output(response)
                news_sources = self._create_news_sources_from_text_parsing(company_name, run_id, agent_output)
            
            logger.info(f"News Agent found {len(news_sources)} relevant news sources")
            return news_sources
            
        except Exception as e:
            logger.error(f"News Agent error: {e}")
            return self._create_fallback_sources(company_name, run_id, f"Error: {str(e)}")
    
    def _create_news_research_task(
        self, 
        company_name: str, 
        company_aliases: List[str] = None, 
        discovery_results: Optional[DiscoveryResults] = None
    ) -> str:
        """Create a comprehensive news research task for the LLM agent."""
        
        # Build context from discovery results
        context_info = ""
        if discovery_results:
            context_info = f"""
DISCOVERY CONTEXT:
- Website: {discovery_results.base_url}
- Key Pages Found: {len(discovery_results.discovered_urls)} pages
- Company Aliases: {', '.join(discovery_results.company_aliases)}
- Discovery Insights: {discovery_results.llm_analysis[:300]}...
"""
        
        aliases_text = ""
        if company_aliases and len(company_aliases) > 1:
            aliases_text = f"Alternative Names: {', '.join(company_aliases[1:])}"
        
        task = f"""
NEWS INTELLIGENCE MISSION: Comprehensive Company News Analysis

PRIMARY TARGET: {company_name}
{aliases_text}
{context_info}

Your mission is to conduct THOROUGH, ITERATIVE news research to uncover investment-relevant information about this company.

CRITICAL REQUIREMENTS:
1. NEVER return "No news found" - always provide analysis and insights
2. If initial searches find limited results, try ALTERNATIVE search strategies
3. Expand search terms to include industry trends, competitors, related technologies
4. Provide strategic analysis even when direct news is limited
5. Look for indirect signals (industry reports, competitor news, market trends)

RESEARCH OBJECTIVES:
1. Find recent funding announcements, investment rounds, or financial news
2. Discover partnerships, collaborations, and business development deals
3. Identify product launches, major feature releases, or market expansion
4. Uncover leadership changes, hiring announcements, or team developments
5. Analyze market coverage, industry recognition, or competitive positioning

STRATEGIC APPROACH:
Phase 1 - Funding Intelligence:
- Search for investment, funding, Series A/B/C, venture capital news
- Look for acquisition rumors, IPO discussions, or financial milestones
- Check for investor announcements or press releases

Phase 2 - Business Development:
- Search for partnership announcements and collaboration deals
- Look for customer wins, enterprise deals, or market expansion
- Find strategic alliances or technology integrations

Phase 3 - Product & Market Analysis:
- Search for product launch announcements and feature releases
- Look for market traction indicators and user growth metrics
- Find industry awards, recognition, or thought leadership content

Phase 4 - Content Analysis:
- Use tavily_extract on 2-3 most promising articles for deeper analysis
- Extract specific details: amounts, dates, investor names, partnership terms
- Identify investment signals and market momentum indicators

SEARCH STRATEGY GUIDANCE:
- Use topic="news" for time-sensitive, recent coverage
- Try different query combinations to maximize coverage
- Focus on authoritative sources (TechCrunch, Reuters, industry publications)
- Look for both company-initiated PR and independent coverage

ANALYSIS PRIORITIES:
- Funding events: amounts, investors, valuation, use of funds
- Partnerships: strategic value, market implications, revenue potential
- Product news: market reception, competitive differentiation, adoption
- Leadership: experience, track record, strategic vision

ADAPTIVE SEARCH STRATEGY:
If direct company searches yield limited results:
1. Search for INDUSTRY trends that may affect the company
2. Look for COMPETITOR news that provides market context
3. Search for TECHNOLOGY trends related to the company's domain
4. Find MARKET REPORTS or INDUSTRY ANALYSIS mentioning the space
5. Look for FOUNDER/CEO mentions in broader industry discussions

MANDATORY OUTPUT REQUIREMENTS:
- ALWAYS provide analysis, even if based on limited information
- If no direct news: analyze industry context and competitive landscape
- Include market positioning assessment based on available information
- Provide investment implications even with limited direct coverage
- Never leave fields empty - provide meaningful insights or strategic analysis

EXAMPLE ALTERNATIVE SEARCHES (if direct company searches fail):
- "[Company domain/industry] market trends 2024"
- "[Company technology/service] industry analysis"
- "[Company space] competitive landscape"
- "[Founder name] industry insights OR interviews"
- Market positioning: industry recognition, competitive advantages

OUTPUT REQUIREMENTS:
For each significant news finding, provide:
- Headline and source credibility assessment
- Key details (dates, amounts, parties involved)
- Investment signal strength (Strong/Medium/Weak)
- Strategic implications for company growth
- Source URL and publication quality

BUDGET AWARENESS:
You have limited API credits. Make strategic search decisions.
Focus on high-impact queries that maximize information discovery.

Begin your strategic news intelligence gathering now.
"""
        return task
    
    def _extract_agent_output(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured output from agent response."""
        
        messages = response.get("messages", [])
        if not messages:
            return {"analysis": "No agent output received", "news_items": []}
        
        # Find the last substantial AI message with analysis
        agent_analysis = ""
        for message in reversed(messages):
            if hasattr(message, 'content') and message.content:
                content = message.content
                # Skip tool usage messages and short responses
                if (not content.startswith("I'll") and 
                    not content.startswith("Let me") and 
                    len(content) > 100):
                    agent_analysis = content
                    break
        
        # If no substantial content found, try to get any AI response
        if not agent_analysis:
            for message in reversed(messages):
                if hasattr(message, 'content') and message.content:
                    agent_analysis = message.content
                    break
        
        # Extract news items and insights from the analysis
        news_items = self._extract_news_items_from_analysis(agent_analysis)
        investment_signals = self._extract_investment_signals(agent_analysis)
        
        return {
            "analysis": agent_analysis,
            "news_items": news_items,
            "investment_signals": investment_signals
        }
    
    def _extract_structured_news_output(self, response: Dict[str, Any]) -> NewsOutput:
        """Extract structured output from agent response."""
        
        # Try to get structured response first
        if "structured_response" in response:
            return response["structured_response"]
            
        # Fallback: create from message content
        messages = response.get("messages", [])
        if not messages:
            return self._create_fallback_news_output()
        
        # Find the last AI message with content
        for message in reversed(messages):
            if hasattr(message, 'content') and message.content:
                try:
                    # Try to parse as JSON if it looks like structured data
                    import json
                    if message.content.strip().startswith('{'):
                        data = json.loads(message.content)
                        return NewsOutput(**data)
                except:
                    pass
                
                # Fallback: parse from text content
                return self._parse_news_output_from_text(message.content)
        
        return self._create_fallback_news_output()
    
    def _create_fallback_news_output(self) -> NewsOutput:
        """Create fallback news output when parsing fails."""
        from app.models.agent_outputs import NewsItem
        
        return NewsOutput(
            news_items=[],
            funding_signals=[],
            partnership_signals=[],
            market_signals=[],
            investment_implications="Unable to complete news analysis",
            confidence_assessment="Low confidence due to parsing error"
        )
    
    def _parse_news_output_from_text(self, content: str) -> NewsOutput:
        """Parse news output from text content."""
        from app.models.agent_outputs import NewsItem
        
        # Basic parsing from text content
        news_items = []
        funding_signals = []
        partnership_signals = []
        market_signals = []
        
        # Look for structured sections in the text
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if 'funding' in line.lower() or 'investment' in line.lower():
                current_section = 'funding'
            elif 'partnership' in line.lower() or 'collaboration' in line.lower():
                current_section = 'partnership'
            elif 'market' in line.lower() or 'competitive' in line.lower():
                current_section = 'market'
            elif line.startswith('####') or line.startswith('###'):
                # Create news item from section header
                title = line.strip('#').strip()
                news_items.append(NewsItem(
                    headline=title,
                    content=line,
                    url="",
                    relevance_score=0.5,
                    news_type="analysis"
                ))
            elif current_section and len(line) > 50:
                # Add content to appropriate section
                if current_section == 'funding':
                    funding_signals.append(line)
                elif current_section == 'partnership':
                    partnership_signals.append(line)
                elif current_section == 'market':
                    market_signals.append(line)
        
        return NewsOutput(
            news_items=news_items[:10],  # Limit items
            funding_signals=funding_signals[:5],
            partnership_signals=partnership_signals[:5],
            market_signals=market_signals[:5],
            investment_implications="Analysis based on text parsing",
            confidence_assessment="Medium confidence from text analysis"
        )
    
    def _extract_news_items_from_analysis(self, analysis: str) -> List[Dict[str, Any]]:
        """Extract individual news items from the agent's analysis."""
        news_items = []
        
        # Look for structured news mentions
        import re
        
        # Pattern for finding headlines/URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, analysis)
        
        # Create news items from structured sections
        sections = analysis.split('\n\n')
        
        # Look for Phase/Section headers and extract content
        for i, section in enumerate(sections):
            if ('####' in section or '###' in section or 
                'Phase' in section or 'Analysis' in section) and len(section) > 50:
                
                # Extract title from section
                lines = section.split('\n')
                title = lines[0].strip('#').strip()
                content = '\n'.join(lines[1:]).strip()
                
                if content:
                    news_items.append({
                        "headline": title,
                        "content": content,
                        "urls": [url for url in urls if url in section] if urls else [],
                        "relevance_score": 0.7,  # Default relevance
                        "type": "analysis"
                    })
        
        # If no structured items found, create items from major sections
        if not news_items and analysis:
            # Split by common delimiters and create news items
            major_sections = [s.strip() for s in analysis.split('\n') if len(s.strip()) > 100]
            for i, section in enumerate(major_sections[:8]):  # Limit to prevent too many items
                if section:
                    news_items.append({
                        "headline": f"News Item {i+1}",
                        "content": section[:500],  # Limit content length
                        "urls": [],
                        "relevance_score": 0.5,
                        "type": "general"
                    })
        
        return news_items[:10]  # Limit to 10 items
    
    def _extract_investment_signals(self, analysis: str) -> List[str]:
        """Extract investment signals from the analysis."""
        signals = []
        
        signal_patterns = [
            r'funding[^.]*\$[\d,]+[^.]*',
            r'investment[^.]*\$[\d,]+[^.]*',
            r'partnership with [^.]+',
            r'acquired [^.]+',
            r'launched [^.]+',
            r'hired [^.]+ as [^.]+',
            r'expanded to [^.]+'
        ]
        
        import re
        for pattern in signal_patterns:
            matches = re.findall(pattern, analysis, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:
                    signals.append(match.strip())
        
        return signals[:8]  # Limit signals
    
    def _assess_news_relevance(self, content: str) -> float:
        """Assess relevance score for news content."""
        relevance = 0.0
        
        # High value keywords
        high_value = ["funding", "investment", "acquisition", "partnership", "IPO"]
        medium_value = ["launch", "product", "hire", "expansion", "award"]
        
        content_lower = content.lower()
        
        for keyword in high_value:
            if keyword in content_lower:
                relevance += 0.3
        
        for keyword in medium_value:
            if keyword in content_lower:
                relevance += 0.2
        
        # Boost for specific numbers/amounts
        import re
        if re.search(r'\$[\d,]+', content):
            relevance += 0.2
        
        if re.search(r'\d{4}', content):  # Years
            relevance += 0.1
        
        return min(1.0, relevance)
    
    def _create_news_sources(self, company_name: str, run_id: str, agent_output: Dict[str, Any]) -> List[SourceDoc]:
        """Create SourceDoc objects from agent findings."""
        
        sources = []
        news_items = agent_output.get("news_items", [])
        
        for i, item in enumerate(news_items):
            # Use the first URL if available, otherwise create a placeholder
            url = item.get("urls", [""])[0] if item.get("urls") else ""
            
            source = SourceDoc(
                id=f"news_{run_id}_{i}",
                run_id=run_id or "unknown",
                title=item.get("headline", "News Item"),
                url=url,
                snippet=item.get("content", "")[:500],
                published_at=None,  # Could be enhanced to extract dates
                domain=self._extract_domain(url) if url else None,
                type=item.get("type", "news")
            )
            
            # Add metadata about the analysis
            source.agent_analysis = agent_output.get("analysis", "")
            source.relevance_score = item.get("relevance_score", 0.5)
            source.news_type = item.get("type", "general")
            
            sources.append(source)
        
        return sources
    
    def _create_news_sources_from_structured(self, company_name: str, run_id: str, structured_output: NewsOutput) -> List[SourceDoc]:
        """Create SourceDoc objects from structured output."""
        
        sources = []
        
        # Create sources from news items
        for i, item in enumerate(structured_output.news_items):
            source = SourceDoc(
                id=f"news_{run_id}_{i}",
                run_id=run_id or "unknown",
                title=item.headline,
                url=item.url or "",
                snippet=item.content[:500],
                published_at=None,  # Could be enhanced to parse dates
                domain=self._extract_domain(item.url) if item.url else None,
                type="news"
            )
            
            # Add metadata
            source.agent_type = "llm_news_agent"
            source.relevance_score = item.relevance_score
            source.news_type = item.news_type
            
            sources.append(source)
        
        # Create additional sources for funding signals
        for i, signal in enumerate(structured_output.funding_signals):
            source = SourceDoc(
                id=f"funding_{run_id}_{i}",
                run_id=run_id or "unknown",
                title="Funding Signal",
                url="",
                snippet=signal[:500],
                published_at=None,
                domain=None,
                type="funding"
            )
            source.agent_type = "llm_news_agent"
            sources.append(source)
        
        # Create additional sources for partnership signals
        for i, signal in enumerate(structured_output.partnership_signals):
            source = SourceDoc(
                id=f"partnership_{run_id}_{i}",
                run_id=run_id or "unknown",
                title="Partnership Signal",
                url="",
                snippet=signal[:500],
                published_at=None,
                domain=None,
                type="partnership"
            )
            source.agent_type = "llm_news_agent"
            sources.append(source)
            
        return sources
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return "unknown"
    
    def _create_fallback_sources(self, company_name: str, run_id: str, reason: str) -> List[SourceDoc]:
        """Create fallback sources when LLM agent cannot operate."""
        
        logger.warning(f"Creating fallback news sources: {reason}")
        
        return [
            SourceDoc(
                id=f"news_fallback_{run_id}",
                run_id=run_id or "unknown",
                title=f"News research for {company_name} unavailable",
                url="",
                snippet=f"News analysis could not be completed: {reason}",
                published_at=None,
                domain=None,
                type="error"
            )
        ]
    
    def _create_news_sources_from_text_parsing(self, company_name: str, run_id: str, agent_output: Dict[str, Any]) -> List[SourceDoc]:
        """Create news sources from text parsing fallback."""
        # Extract analysis text
        analysis_text = agent_output.get("analysis", str(agent_output))
        
        # Parse news items from text
        parsed_output = {
            "news_items": self._extract_news_items_from_analysis(analysis_text),
            "analysis": analysis_text
        }
        
        # Use existing method to create sources
        return self._create_news_sources(company_name, run_id, parsed_output)


# Global news agent instance
news_agent = NewsAgent()