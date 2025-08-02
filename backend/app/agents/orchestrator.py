import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Union
from urllib.parse import urlparse
from langgraph.graph import StateGraph, START, END
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.database import get_database
from app.models.schemas import (
    RunState, SourceDoc, PatentDoc, RiskItem, 
    DiscoveryResults, DeepDiveResults, VerifiedFact
)
from app.services.tavily_client import tavily_client
from app.services.llm_service import llm_service
from app.core.budget_tracker import budget_tracker
from app.core.config import settings

logger = logging.getLogger(__name__)

class VentureCompassOrchestrator:
    def __init__(self):
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build v2.0 multi-phase LangGraph workflow"""
        graph = StateGraph(RunState)
        
        # Phase 1: Discovery
        graph.add_node("discovery_agent", self.discovery_agent_node)
        
        # Phase 2: Parallel Research 
        graph.add_node("news_retriever", self.news_retriever_node)
        graph.add_node("patent_hunter", self.patent_hunter_node)
        graph.add_node("deepdive_agent", self.deepdive_agent_node)
        
        # Phase 3: Verification & Synthesis
        graph.add_node("verification_agent", self.verification_agent_node)
        graph.add_node("insight_synthesizer", self.insight_synthesizer_node)
        
        # Multi-phase coordination
        graph.add_edge(START, "discovery_agent")
        graph.add_conditional_edges(
            "discovery_agent",
            self.route_after_discovery,
            {
                "parallel_research": "news_retriever",
                "fallback_search": "news_retriever"
            }
        )
        
        # Fan-out to parallel agents after news retriever
        graph.add_edge("discovery_agent", "patent_hunter")
        graph.add_edge("discovery_agent", "deepdive_agent")
        
        # Convergence to verification
        graph.add_edge("news_retriever", "verification_agent")
        graph.add_edge("patent_hunter", "verification_agent")
        graph.add_edge("deepdive_agent", "verification_agent")
        
        # Final synthesis
        graph.add_edge("verification_agent", "insight_synthesizer")
        graph.add_edge("insight_synthesizer", END)
        
        return graph.compile()
    
    def route_after_discovery(self, state: Dict[str, Any]) -> str:
        """Conditional routing based on discovery results quality"""
        discovery_results = state.get("discovery_results")
        if discovery_results and len(discovery_results.discovered_urls) > 5:
            logger.info(f"Rich discovery results ({len(discovery_results.discovered_urls)} URLs) - proceeding with full research")
            return "parallel_research"
        else:
            logger.warning("Limited discovery results - using fallback search approach")
            return "fallback_search"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def discovery_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: Discovery Agent using Tavily Map API"""
        logger.info(f"Discovery Agent starting for run {state['run_id']}")
        
        company_name = state["company"]["name"]
        company_domain = state["company"].get("domain")
        
        # Generate potential company URLs if domain not provided
        potential_urls = []
        if company_domain:
            # Clean domain - remove protocol if already present
            clean_domain = company_domain.replace('https://', '').replace('http://', '')
            potential_urls.append(f"https://{clean_domain}")
        else:
            # Generate common domain patterns
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())
            potential_urls.extend([
                f"https://{clean_name}.com",
                f"https://{clean_name}.io",
                f"https://www.{clean_name}.com"
            ])
            
        discovered_urls = []
        company_aliases = [company_name]
        social_media_links = []
        key_pages = {}
        credits_used = 0
        
        try:
            # Try to map company website structure
            for url in potential_urls[:2]:  # Limit attempts for budget control
                try:
                    logger.info(f"Mapping website structure for {url}")
                    map_response = await tavily_client.map(
                        url=url,
                        max_depth=2,
                        limit=15
                    )
                    credits_used += 1
                    
                    if map_response.get("results"):
                        discovered_urls.extend(map_response["results"])
                        
                        # Categorize discovered pages
                        for discovered_url in map_response["results"]:
                            url_path = urlparse(discovered_url).path.lower()
                            if "about" in url_path or "company" in url_path:
                                key_pages["about"] = discovered_url
                            elif "team" in url_path or "leadership" in url_path:
                                key_pages["team"] = discovered_url
                            elif "career" in url_path or "job" in url_path:
                                key_pages["careers"] = discovered_url
                            elif "blog" in url_path or "news" in url_path:
                                key_pages["blog"] = discovered_url
                                
                        break  # Success - use this URL
                        
                except Exception as e:
                    logger.warning(f"Failed to map {url}: {str(e)}")
                    continue
            
            # Generate company aliases from discovered content
            domain_parts = urlparse(discovered_urls[0] if discovered_urls else "").netloc.split('.')
            if domain_parts:
                base_name = domain_parts[0].replace('www', '').title()
                if base_name and base_name != company_name:
                    company_aliases.append(base_name)
                    
            # Create discovery results
            discovery_results = DiscoveryResults(
                id=f"discovery_{state['run_id']}",
                run_id=state['run_id'],
                base_url=discovered_urls[0] if discovered_urls else "",
                discovered_urls=discovered_urls[:10],  # Limit for performance
                company_aliases=company_aliases,
                social_media_links=social_media_links,
                key_pages=key_pages,
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"Discovery Agent found {len(discovered_urls)} URLs, {len(company_aliases)} aliases, used {credits_used} credits")
            
            return {
                "discovery_results": discovery_results,
                "company_aliases": company_aliases,
                "current_phase": "research",
                "cost": {**state["cost"], "tavily_credits": state["cost"]["tavily_credits"] + credits_used},
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"Discovery Agent error: {str(e)}")
            return {
                "company_aliases": company_aliases,  # At least return original name
                "current_phase": "research",
                "errors": [{"agent": "discovery_agent", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def news_retriever_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Enhanced NewsRetriever using Discovery context and verified company data"""
        logger.info(f"NewsRetriever starting for run {state["run_id"]}")
        
        # Use comprehensive company context from Discovery and verification
        company_names = []
        if state.get("company_aliases"):
            company_names.extend(state["company_aliases"])
        if state["company"]["name"] not in company_names:
            company_names.append(state["company"]["name"])
        
        # Add verified company names from verification agent
        if state.get("verified_facts"):
            for fact in state["verified_facts"]:
                if fact.category == "company_identity" and fact.confidence_score > 0.8:
                    potential_name = fact.claim.replace("Company name: ", "").strip()
                    if potential_name not in company_names:
                        company_names.append(potential_name)
        
        primary_name = company_names[0]
        logger.info(f"NewsRetriever using {len(company_names)} company identities: {company_names[:3]}")
        
        # Enhanced query generation with Discovery context
        queries = []
        
        # Core company queries
        for name in company_names[:2]:  # Limit to prevent budget overrun
            queries.extend([
                f"{name} news funding investment",
                f"{name} partnership collaboration deal",
                f"{name} product launch new feature"
            ])
        
        # Domain-specific queries if discovered
        discovery_results = state.get("discovery_results")
        if discovery_results and discovery_results.discovered_urls:
            domain = None
            for url in discovery_results.discovered_urls[:1]:  # Get primary domain
                try:
                    domain = urlparse(url).netloc.replace("www.", "")
                    break
                except:
                    continue
            
            if domain:
                queries.append(f"site:{domain} OR \"{primary_name}\" news funding")
                logger.info(f"Added domain-specific query for {domain}")
        
        # Industry-specific queries based on discovered content
        deepdive_results = state.get("deepdive_results")
        if deepdive_results and deepdive_results.extracted_content:
            content_sample = " ".join(list(deepdive_results.extracted_content.values())[:2])
            if any(tech_word in content_sample.lower() for tech_word in ["ai", "software", "tech", "platform", "app"]):
                queries.append(f"\"{primary_name}\" technology startup funding")
            elif any(fintech_word in content_sample.lower() for fintech_word in ["finance", "payment", "banking", "fintech"]):
                queries.append(f"\"{primary_name}\" fintech funding series")
        
        news_sources = []
        credits_used = 0
        
        try:
            for query in queries:
                if credits_used >= settings.COST_CAP_TAVILY_CREDITS // 3:  # Reserve credits for other agents
                    logger.warning(f"Credit cap reached for news retrieval: {credits_used}")
                    break
                    
                response = await tavily_client.search(
                    query=query,
                    topic="news",
                    depth="basic",
                    time_range="month",
                    max_results=5
                )
                
                credits_used += 1
                
                for result in response.get("results", []):
                    source = SourceDoc(
                        id=f"news_{len(news_sources)}",
                        run_id=state["run_id"],
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        snippet=result.get("content", "")[:500],
                        published_at=None,
                        domain=result.get("url", "").split("//")[-1].split("/")[0] if result.get("url") else None
                    )
                    news_sources.append(source)
                    
            logger.info(f"NewsRetriever found {len(news_sources)} sources, used {credits_used} credits")
            
            return {
                "queries": {**state["queries"], "news": queries},
                "results": {**state["results"], "news": news_sources},
                "cost": {**state["cost"], "tavily_credits": state["cost"]["tavily_credits"] + credits_used},
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"NewsRetriever error: {str(e)}")
            return {
                "errors": state.get("errors", []) + [{"agent": "news_retriever", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def patent_hunter_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Enhanced PatentHunter leveraging verified company names and aliases"""
        logger.info(f"PatentHunter starting for run {state["run_id"]}")
        
        # Collect all verified company identities
        company_names = [state["company"]["name"]]
        if state.get("company_aliases"):
            company_names.extend(state["company_aliases"])
        
        # Add verified company names with high confidence
        if state.get("verified_facts"):
            for fact in state["verified_facts"]:
                if fact.category == "company_identity" and fact.confidence_score > 0.8:
                    verified_name = fact.claim.replace("Company name: ", "").strip()
                    if verified_name not in company_names and len(verified_name) > 2:
                        company_names.append(verified_name)
        
        # Extract founding year and founders for more targeted searches
        founding_year = None
        founders = []
        deepdive_results = state.get("deepdive_results")
        if deepdive_results and deepdive_results.team_members:
            for member in deepdive_results.team_members:
                if any(title in member.get("role", "").lower() for title in ["founder", "ceo", "cto"]):
                    founder_name = member.get("name", "").strip()
                    if founder_name and len(founder_name) > 3:
                        founders.append(founder_name)
        
        # Try to extract founding year from content
        if deepdive_results and deepdive_results.extracted_content:
            content_text = " ".join(deepdive_results.extracted_content.values())
            year_matches = re.findall(r'founded\s+in\s+(\d{4})|established\s+(\d{4})|since\s+(\d{4})', content_text.lower())
            if year_matches:
                founding_year = next((year for match in year_matches for year in match if year), None)
        
        logger.info(f"PatentHunter using {len(company_names)} company names, {len(founders)} founders, founding year: {founding_year}")
        
        # Enhanced query generation with multiple search strategies
        queries = []
        
        # Core patent searches with all company names
        for name in company_names[:3]:  # Limit to prevent budget overrun
            queries.extend([
                f'"{name}" patent application OR grant site:uspto.gov',
                f'"{name}" assignee patent OR "patent application"',
                f'"{name}" WIPO PCT abstract site:wipo.int'
            ])
        
        # Founder-based patent searches
        for founder in founders[:2]:  # Limit founder searches
            queries.extend([
                f'"{founder}" inventor patent "{company_names[0]}"',
                f'"{founder}" assignee patent application'
            ])
        
        # Time-based searches if founding year available
        if founding_year and founding_year.isdigit():
            year_int = int(founding_year)
            queries.append(f'"{company_names[0]}" patent filing date:{year_int}..{year_int + 10}')
        
        # Technology-specific patent searches based on content analysis
        if deepdive_results and deepdive_results.extracted_content:
            content_sample = " ".join(list(deepdive_results.extracted_content.values())[:3])
            tech_keywords = []
            
            if any(ai_word in content_sample.lower() for ai_word in ["artificial intelligence", "machine learning", "ai", "neural"]):
                tech_keywords.extend(["artificial intelligence", "machine learning"])
            if any(blockchain_word in content_sample.lower() for blockchain_word in ["blockchain", "crypto", "bitcoin", "ethereum"]):
                tech_keywords.extend(["blockchain", "cryptocurrency"])
            if any(bio_word in content_sample.lower() for bio_word in ["biotech", "pharmaceutical", "medicine", "drug"]):
                tech_keywords.extend(["biotechnology", "pharmaceutical"])
            
            for keyword in tech_keywords[:2]:  # Limit tech searches
                queries.append(f'"{company_names[0]}" "{keyword}" patent OR application')
        
        patent_docs = []
        credits_used = 0
        
        try:
            for query in queries:
                if credits_used >= settings.COST_CAP_TAVILY_CREDITS // 2:
                    logger.warning(f"Credit cap reached for patent hunting: {credits_used}")
                    break
                    
                response = await tavily_client.search(
                    query=query,
                    topic="general",
                    depth="basic",
                    time_range="year",
                    max_results=10
                )
                
                credits_used += 1
                
                for result in response.get("results", []):
                    patent = PatentDoc(
                        id=f"patent_{len(patent_docs)}",
                        run_id=state["run_id"],
                        title=result.get("title", ""),
                        assignee=company_names[0],  # Use primary company name
                        filing_date=None,
                        grant_date=None,
                        abstract=result.get("content", "")[:1000],
                        cpc=None,
                        url=result.get("url", "")
                    )
                    patent_docs.append(patent)
                    
            logger.info(f"PatentHunter found {len(patent_docs)} patents, used {credits_used} credits")
            
            return {
                "queries": {**state["queries"], "patents": queries},
                "results": {**state["results"], "patents": patent_docs},
                "cost": {**state["cost"], "tavily_credits": state["cost"]["tavily_credits"] + credits_used},
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"PatentHunter error: {str(e)}")
            return {
                "errors": state.get("errors", []) + [{"agent": "patent_hunter", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def deepdive_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: DeepDive Agent using Tavily Crawl + Extract APIs"""
        logger.info(f"DeepDive Agent starting for run {state["run_id"]}")
        
        discovery_results = state.get("discovery_results")
        if not discovery_results or not discovery_results.discovered_urls:
            logger.warning("No discovery results available for DeepDive Agent")
            return {"status": "partial"}
            
        credits_used = 0
        extracted_content = {}
        team_members = []
        
        try:
            # Select high-value pages for deep dive
            priority_urls = []
            key_pages = discovery_results.key_pages
            
            # Prioritize key company pages
            for page_type in ["about", "team", "careers"]:
                if page_type in key_pages:
                    priority_urls.append(key_pages[page_type])
                    
            # Add other discovered URLs up to budget limit
            remaining_urls = [url for url in discovery_results.discovered_urls 
                            if url not in priority_urls]
            priority_urls.extend(remaining_urls[:3])  # Limit for budget control
            
            if priority_urls:
                # Use Tavily Extract API for clean content extraction
                logger.info(f"Extracting content from {len(priority_urls)} key pages")
                extract_response = await tavily_client.extract(
                    urls=priority_urls,
                    depth="advanced"
                )
                credits_used += 1
                
                if extract_response.get("results"):
                    for result in extract_response["results"]:
                        url = result.get("url", "")
                        content = result.get("raw_content", "")
                        extracted_content[url] = content[:2000]  # Limit content size
                        
                        # Extract team member information
                        if "team" in url.lower() or "about" in url.lower():
                            team_info = self._extract_team_info(content)
                            team_members.extend(team_info)
            
            # Create DeepDive results
            deepdive_results = DeepDiveResults(
                id=f"deepdive_{state["run_id"]}",
                run_id=state["run_id"],
                crawled_pages=[],
                extracted_content=extracted_content,
                team_members=team_members,
                company_timeline=[],
                product_info={},
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"DeepDive Agent extracted content from {len(extracted_content)} pages, found {len(team_members)} team members, used {credits_used} credits")
            
            return {
                "deepdive_results": deepdive_results,
                "cost": {**state["cost"], "tavily_credits": state["cost"]["tavily_credits"] + credits_used},
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"DeepDive Agent error: {str(e)}")
            return {
                "errors": state.get("errors", []) + [{"agent": "deepdive_agent", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    def _extract_team_info(self, content: str) -> List[Dict[str, Any]]:
        """Extract team member information from content"""
        team_members = []
        
        # Simple pattern matching for team information
        common_titles = ["CEO", "CTO", "CFO", "COO", "VP", "Director", "Manager", "Lead", "Head", "Founder"]
        
        lines = content.split('\n')
        for line in lines:
            for title in common_titles:
                if title.lower() in line.lower():
                    team_members.append({
                        "name": line.strip()[:100],
                        "title": title,
                        "source": "deepdive_extraction"  
                    })
                    break
                    
        return team_members[:5]  # Limit results
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def verification_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Verification Agent for cross-source validation"""
        logger.info(f"Verification Agent starting for run {state["run_id"]}")
        
        verified_facts = []
        confidence_scores = {}
        
        try:
            # Cross-validate information from different agents
            news_sources = state["results"].get("news", [])
            patent_docs = state["results"].get("patents", [])
            deepdive_results = state.get("deepdive_results")
            deepdive_content = deepdive_results.extracted_content if deepdive_results else {}
            
            # Generate confidence scores for different data types
            confidence_scores["news_reliability"] = min(1.0, len(news_sources) / 10)  # More sources = higher confidence
            confidence_scores["patent_coverage"] = min(1.0, len(patent_docs) / 5)
            confidence_scores["website_analysis"] = 1.0 if deepdive_content else 0.0
            
            # Create verified facts from high-confidence information
            if news_sources:
                for source in news_sources[:3]:  # Top 3 most relevant
                    verified_fact = VerifiedFact(
                        fact_id=f"news_{source.id}",
                        claim=source.title,
                        sources=[source.url],
                        confidence_score=0.8,  # News sources get high confidence
                        verification_method="news_source_validation"
                    )
                    verified_facts.append(verified_fact)
                    
            if patent_docs:
                for patent in patent_docs[:2]:  # Top 2 patents
                    verified_fact = VerifiedFact(
                        fact_id=f"patent_{patent.id}",
                        claim=f"Patent: {patent.title}",
                        sources=[patent.url],
                        confidence_score=0.9,  # Patent data gets very high confidence
                        verification_method="patent_database_validation"
                    )
                    verified_facts.append(verified_fact)
            
            # Overall confidence assessment
            overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
            confidence_scores["overall"] = overall_confidence
            
            logger.info(f"Verification Agent validated {len(verified_facts)} facts with overall confidence {overall_confidence:.2f}")
            
            return {
                "verified_facts": verified_facts,
                "confidence_scores": confidence_scores,
                "current_phase": "synthesis",
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"Verification Agent error: {str(e)}")
            return {
                "errors": state.get("errors", []) + [{"agent": "verification_agent", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    async def insight_synthesizer_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Enhanced InsightSynthesizer with budget-aware LLM integration"""
        logger.info(f"InsightSynthesizer starting for run {state["run_id"]}")
        
        try:
            # Collect all agent results for synthesis
            company_data = {
                "company": state["company"],
                "discovery_results": state.get("discovery_results"),
                "news_results": state["results"].get("news", []),
                "patent_results": state["results"].get("patents", []),
                "deepdive_results": state.get("deepdive_results"),
                "verified_facts": state.get("verified_facts", [])
            }
            
            # Check budget status before attempting LLM synthesis
            budget_status = await budget_tracker.get_budget_status()
            logger.info(f"Budget status: ${budget_status['current_spend']:.2f}/${budget_status['max_budget']:.2f} used")
            
            # Generate insights using budget-aware LLM service
            synthesis_result = await llm_service.generate_insights(company_data)
            
            # Create structured insights with fallback pattern
            if synthesis_result.get("llm_generated", False):
                logger.info("LLM synthesis completed successfully")
                insights = {
                    "executive_summary": synthesis_result.get("executive_summary", ""),
                    "investment_signals": synthesis_result.get("investment_signals", []),
                    "risk_assessment": synthesis_result.get("risks", []),
                    "confidence_score": synthesis_result.get("confidence_score", 0),
                    "llm_enhanced": True,
                    "synthesis_cost": synthesis_result.get("cost", 0)
                }
            else:
                logger.info("Using fallback synthesis (budget-optimized)")
                insights = {
                    "executive_summary": synthesis_result.get("executive_summary", ""),
                    "investment_signals": synthesis_result.get("investment_signals", []),
                    "risk_assessment": synthesis_result.get("risks", []),
                    "confidence_score": synthesis_result.get("confidence_score", 0),
                    "llm_enhanced": False,
                    "note": synthesis_result.get("note", "")
                }
            
            # Add structured analysis from agent results
            insights["data_sources"] = {
                "news_articles": len(company_data["news_results"]),
                "patents_found": len(company_data["patent_results"]),
                "pages_analyzed": len(company_data.get("discovery_results", {}).get("discovered_urls", [])),
                "verified_facts": len(company_data.get("verified_facts", [])),
                "team_members": len(company_data.get("deepdive_results", {}).get("team_members", []))
            }
            
            # Generate funding events and partnerships from news
            insights["funding_events"] = self._extract_funding_events(company_data["news_results"])
            insights["partnerships"] = self._extract_partnerships(company_data["news_results"])
            
            # Update cost tracking
            synthesis_cost = synthesis_result.get("cost", 0)
            total_cost = state["cost"].get("openai_usd", 0) + synthesis_cost
            
            logger.info(f"InsightSynthesizer completed - LLM Enhanced: {insights['llm_enhanced']}, Cost: ${synthesis_cost:.4f}")
            
            return {
                "insights": insights,
                "cost": {**state["cost"], "openai_usd": total_cost},
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"InsightSynthesizer error: {str(e)}")
            return {
                "errors": state.get("errors", []) + [{"agent": "insight_synthesizer", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    def _extract_funding_events(self, news_sources: List[SourceDoc]) -> List[Dict[str, Any]]:
        """Extract funding events from news sources."""
        funding_keywords = ["funding", "investment", "raised", "series", "round", "capital"]
        events = []
        
        for source in news_sources:
            snippet_lower = (source.snippet or "").lower()
            if any(keyword in snippet_lower for keyword in funding_keywords):
                events.append({
                    "summary": source.title,
                    "source_id": source.id,
                    "url": source.url,
                    "published_date": source.published_date
                })
        return events
    
    def _extract_partnerships(self, news_sources: List[SourceDoc]) -> List[Dict[str, Any]]:
        """Extract partnership announcements from news sources."""
        partnership_keywords = ["partnership", "collaboration", "agreement", "deal", "alliance"]
        partnerships = []
        
        for source in news_sources:
            snippet_lower = (source.snippet or "").lower()
            if any(keyword in snippet_lower for keyword in partnership_keywords):
                partnerships.append({
                    "summary": source.title,
                    "source_id": source.id,
                    "url": source.url,
                    "published_date": source.published_date
                })
        return partnerships
    
    async def redflag_screener_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"RedFlagScreener starting for run {state["run_id"]}")
        
        try:
            news_sources = state["results"].get("news", [])
            risks = []
            
            risk_keywords = {
                "litigation": ["lawsuit", "legal", "court", "sue", "litigation", "dispute"],
                "regulatory": ["regulatory", "compliance", "violation", "fine", "penalty", "investigation"],
                "security": ["breach", "hack", "security", "data leak", "cyber", "privacy"],
                "leadership": ["CEO resign", "scandal", "controversy", "misconduct", "investigation"]
            }
            
            for source in news_sources:
                snippet_lower = (source.snippet or "").lower()
                title_lower = (source.title or "").lower()
                content = snippet_lower + " " + title_lower
                
                for category, keywords in risk_keywords.items():
                    matches = [kw for kw in keywords if kw in content]
                    if matches:
                        risk = RiskItem(
                            category=category,
                            severity="medium",
                            summary=f"Potential {category} risk detected: {source.title[:100]}",
                            citations=[source.id]
                        )
                        risks.append(risk)
                        break
            
            logger.info(f"RedFlagScreener identified {len(risks)} potential risks")
            
            return {
                "risks": risks,
                "status": "complete"
            }
            
        except Exception as e:
            logger.error(f"RedFlagScreener error: {str(e)}")
            return {
                "errors": state.get("errors", []) + [{"agent": "redflag_screener", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "error"
            }

# Global orchestrator instance
orchestrator = VentureCompassOrchestrator()

async def run_analysis(run_id: str, company: str, domain: str = None):
    db = get_database()
    
    await db.runs.update_one(
        {"run_id": run_id},
        {
            "$set": {
                "status": "running",
                "started_at": datetime.utcnow()
            }
        }
    )
    
    try:
        initial_state = {
            "run_id": run_id,
            "company": {"name": company, "domain": domain},
            "discovery_results": None,
            "company_aliases": [],
            "queries": {"news": [], "patents": []},
            "results": {},
            "deepdive_results": None,
            "verified_facts": [],
            "confidence_scores": {},
            "insights": None,
            "risks": None,
            "citations": [],
            "cost": {"tavily_credits": 0, "llm_tokens": 0},
            "status": "running",
            "current_phase": "discovery",
            "errors": []
        }
        
        logger.info(f"Starting LangGraph workflow for run {run_id}")
        
        final_state = await orchestrator.graph.ainvoke(initial_state)
        
        await _persist_results_to_db(db, final_state)
        
        await db.runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": final_state["status"],
                    "completed_at": datetime.utcnow(),
                    "cost": final_state["cost"]
                }
            }
        )
        
        logger.info(f"Completed analysis for run {run_id} with status {final_state['status']}")
        
    except Exception as e:
        logger.error(f"Analysis failed for run {run_id}: {str(e)}")
        await db.runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": "error",
                    "completed_at": datetime.utcnow(),
                    "errors": [{"message": str(e), "timestamp": datetime.utcnow()}]
                }
            }
        )

async def _persist_results_to_db(db, state: Dict[str, Any]):
    """Persist agent results to MongoDB collections"""
    try:
        # Persist sources
        if "news" in state["results"]:
            news_docs = [{
                "_id": source.id,
                "run_id": source.run_id,
                "type": "news",
                "title": source.title,
                "url": source.url,
                "snippet": source.snippet,
                "domain": source.domain,
                "created_at": datetime.utcnow()
            } for source in state["results"]["news"]]
            
            if news_docs:
                await db.sources.insert_many(news_docs, ordered=False)
        
        # Persist patents
        if "patents" in state["results"]:
            patent_docs = [{
                "_id": patent.id,
                "run_id": patent.run_id,
                "title": patent.title,
                "assignee": patent.assignee,
                "abstract": patent.abstract,
                "url": patent.url,
                "created_at": datetime.utcnow()
            } for patent in state["results"]["patents"]]
            
            if patent_docs:
                await db.patents.insert_many(patent_docs, ordered=False)
        
        # Persist insights
        if state.get("insights"):
            insights_doc = {
                "run_id": state["run_id"],
                "overview": state["insights"].get("overview", []),
                "funding_events": state["insights"].get("funding_events", []),
                "partnerships": state["insights"].get("partnerships", []),
                "highlights": state["insights"].get("highlights", []),
                "created_at": datetime.utcnow()
            }
            await db.insights.insert_one(insights_doc)
        
        # Persist risks
        if state.get("risks"):
            risk_docs = [{
                "run_id": state["run_id"],
                "category": risk.category,
                "severity": risk.severity,
                "summary": risk.summary,
                "citations": risk.citations,
                "created_at": datetime.utcnow()
            } for risk in state["risks"]]
            
            await db.risks.insert_many(risk_docs, ordered=False)
            
    except Exception as e:
        logger.error(f"Failed to persist results to DB: {str(e)}")