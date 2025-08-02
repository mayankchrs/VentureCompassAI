"""
New LLM-based orchestrator using true LangGraph agents.
Coordinates the 6 LLM agents for comprehensive company intelligence.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import MessagesState

from app.agents.discovery_agent import discovery_agent
from app.agents.news_agent import news_agent
from app.agents.founder_agent import founder_agent
from app.agents.competitive_agent import competitive_agent
from app.agents.patent_agent import patent_agent
from app.agents.deepdive_agent import deepdive_agent
from app.agents.verification_agent import verification_agent
from app.agents.synthesis_agent import synthesis_agent
from app.models.schemas import RunState, SourceDoc, PatentDoc, RiskItem
from app.core.database import get_database
from app.core.budget_tracker import budget_tracker

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    New orchestrator using true LLM agents with GPT-4o decision-making.
    
    This orchestrator coordinates 8 LLM agents:
    1. Discovery Agent - Maps digital presence using LLM reasoning
    2. News Agent - Strategic news research with LLM analysis
    3. Founder Agent - Leadership team analysis with background research
    4. Competitive Agent - Market landscape and competitive intelligence
    5. Patent Agent - IP intelligence and patent portfolio analysis
    6. DeepDive Agent - Comprehensive content analysis and intelligence extraction
    7. Verification Agent - Fact-checking and cross-source validation
    8. Synthesis Agent - Professional investment reports with LLM synthesis
    """
    
    def __init__(self):
        self.graph = self._build_llm_graph()
        logger.info("LLM Orchestrator initialized with GPT-4o agents")
    
    def _build_llm_graph(self) -> StateGraph:
        """Build LangGraph workflow with true LLM agents."""
        
        # Use MessagesState for LLM agent coordination
        graph = StateGraph(Dict[str, Any])
        
        # Phase 1: Discovery (LLM-driven)
        graph.add_node("discovery_llm_agent", self.discovery_llm_node)
        
        # Phase 2: Research Agents (LLM-driven)
        graph.add_node("news_llm_agent", self.news_llm_node)
        graph.add_node("founder_llm_agent", self.founder_llm_node)
        graph.add_node("competitive_llm_agent", self.competitive_llm_node)
        graph.add_node("patent_llm_agent", self.patent_llm_node)
        graph.add_node("deepdive_llm_agent", self.deepdive_llm_node)
        
        # Phase 3: Validation & Synthesis (LLM-driven)
        graph.add_node("verification_llm_agent", self.verification_llm_node)
        graph.add_node("synthesis_llm", self.synthesis_llm_node)
        
        # Build sequential workflow to avoid concurrent state updates
        graph.add_edge(START, "discovery_llm_agent")
        
        # Sequential execution to avoid concurrent state conflicts
        graph.add_edge("discovery_llm_agent", "news_llm_agent")
        graph.add_edge("news_llm_agent", "founder_llm_agent")
        graph.add_edge("founder_llm_agent", "competitive_llm_agent")
        graph.add_edge("competitive_llm_agent", "patent_llm_agent")
        graph.add_edge("patent_llm_agent", "deepdive_llm_agent")
        graph.add_edge("deepdive_llm_agent", "verification_llm_agent")
        graph.add_edge("verification_llm_agent", "synthesis_llm")
        graph.add_edge("synthesis_llm", END)
        
        return graph.compile()
    
    async def discovery_llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: True LLM Discovery Agent"""
        logger.info(f"🤖 LLM Discovery Agent starting for run {state['run_id']}")
        
        try:
            company_name = state["company"]["name"]
            company_domain = state["company"].get("domain")
            run_id = state["run_id"]
            
            # Use the true LLM discovery agent
            discovery_results = await discovery_agent.discover_company(
                company_name=company_name,
                company_domain=company_domain,
                run_id=run_id
            )
            
            logger.info(f"✅ LLM Discovery Agent found {len(discovery_results.discovered_urls)} URLs with confidence {discovery_results.confidence_score:.2f}")
            
            return {
                **state,
                "discovery_results": discovery_results,
                "company_aliases": discovery_results.company_aliases,
                "current_phase": "research",
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"❌ LLM Discovery Agent error: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [{"agent": "discovery_llm", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    async def news_llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: True LLM News Agent"""
        logger.info(f"🤖 LLM News Agent starting for run {state['run_id']}")
        
        try:
            company_name = state["company"]["name"]
            company_aliases = state.get("company_aliases", [company_name])
            discovery_results = state.get("discovery_results")
            run_id = state["run_id"]
            
            # Use the true LLM news agent
            news_sources = await news_agent.research_company_news(
                company_name=company_name,
                company_aliases=company_aliases,
                discovery_results=discovery_results,
                run_id=run_id
            )
            
            logger.info(f"✅ LLM News Agent found {len(news_sources)} relevant sources")
            
            # Update state with news results
            current_results = state.get("results", {})
            current_results["news"] = news_sources
            
            return {
                **state,
                "results": current_results,
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"❌ LLM News Agent error: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [{"agent": "news_llm", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    async def founder_llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: True LLM Founder Intelligence Agent"""
        logger.info(f"🤖 LLM Founder Agent starting for run {state['run_id']}")
        
        try:
            company_name = state["company"]["name"]
            discovery_results = state.get("discovery_results")
            run_id = state["run_id"]
            
            # Use the true LLM founder agent
            founder_profiles = await founder_agent.analyze_leadership_team(
                company_name=company_name,
                discovery_results=discovery_results,
                run_id=run_id
            )
            
            logger.info(f"✅ LLM Founder Agent analyzed {len(founder_profiles)} leadership profiles")
            
            # Update state with founder results
            current_results = state.get("results", {})
            current_results["founders"] = founder_profiles
            
            return {
                **state,
                "results": current_results,
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"❌ LLM Founder Agent error: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [{"agent": "founder_llm", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    async def competitive_llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: True LLM Competitive Intelligence Agent"""
        logger.info(f"🤖 LLM Competitive Agent starting for run {state['run_id']}")
        
        try:
            company_name = state["company"]["name"]
            discovery_results = state.get("discovery_results")
            run_id = state["run_id"]
            
            # Use the true LLM competitive agent
            competitive_analysis = await competitive_agent.analyze_competitive_landscape(
                company_name=company_name,
                discovery_results=discovery_results,
                run_id=run_id
            )
            
            logger.info(f"✅ LLM Competitive Agent identified {len(competitive_analysis.get('competitors', []))} competitors")
            
            # Update state with competitive results
            current_results = state.get("results", {})
            current_results["competitive"] = competitive_analysis
            
            return {
                **state,
                "results": current_results,
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"❌ LLM Competitive Agent error: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [{"agent": "competitive_llm", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    async def patent_llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: True LLM Patent Intelligence Agent"""
        logger.info(f"🤖 LLM Patent Agent starting for run {state['run_id']}")
        
        try:
            company_name = state["company"]["name"]
            discovery_results = state.get("discovery_results")
            founder_profiles = state.get("results", {}).get("founders", [])
            run_id = state["run_id"]
            
            # Use the true LLM patent agent
            patent_docs = await patent_agent.analyze_ip_portfolio(
                company_name=company_name,
                discovery_results=discovery_results,
                founder_profiles=founder_profiles,
                run_id=run_id
            )
            
            logger.info(f"✅ LLM Patent Agent analyzed {len(patent_docs)} patent documents")
            
            # Update state with patent results
            current_results = state.get("results", {})
            current_results["patents"] = patent_docs
            
            return {
                **state,
                "results": current_results,
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"❌ LLM Patent Agent error: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [{"agent": "patent_llm", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    async def deepdive_llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: True LLM DeepDive Content Agent"""
        logger.info(f"🤖 LLM DeepDive Agent starting for run {state['run_id']}")
        
        try:
            company_name = state["company"]["name"]
            discovery_results = state.get("discovery_results")
            run_id = state["run_id"]
            
            # Use the true LLM deepdive agent
            deepdive_analysis = await deepdive_agent.analyze_company_content(
                company_name=company_name,
                discovery_results=discovery_results,
                run_id=run_id
            )
            
            logger.info(f"✅ LLM DeepDive Agent completed comprehensive content analysis")
            
            # Update state with deepdive results
            return {
                **state,
                "deepdive_results": deepdive_analysis,
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"❌ LLM DeepDive Agent error: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [{"agent": "deepdive_llm", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    async def verification_llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: True LLM Verification Intelligence Agent"""
        logger.info(f"🤖 LLM Verification Agent starting for run {state['run_id']}")
        
        try:
            company_name = state["company"]["name"]
            run_id = state["run_id"]
            
            # Gather all agent results for verification
            all_agent_results = {
                "discovery_results": state.get("discovery_results"),
                "results": state.get("results", {}),
                "deepdive_results": state.get("deepdive_results", {})
            }
            
            # Use the true LLM verification agent
            verification_analysis = await verification_agent.verify_company_intelligence(
                company_name=company_name,
                all_agent_results=all_agent_results,
                run_id=run_id
            )
            
            logger.info(f"✅ LLM Verification Agent validated {len(verification_analysis.get('verified_facts', []))} facts")
            
            # Update state with verification results
            return {
                **state,
                "verified_facts": verification_analysis.get("verified_facts", []),
                "confidence_scores": verification_analysis.get("confidence_scores", {}),
                "verification_results": verification_analysis,
                "current_phase": "synthesis",
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"❌ LLM Verification Agent error: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [{"agent": "verification_llm", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    async def patent_placeholder_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for Patent LLM Agent (to be implemented)"""
        logger.info(f"📋 Patent Placeholder (LLM Agent pending) for run {state['run_id']}")
        
        # Create placeholder patent results
        placeholder_patents = [
            PatentDoc(
                id=f"patent_placeholder_{state['run_id']}",
                run_id=state['run_id'],
                title=f"Patent research for {state['company']['name']} - LLM Agent pending implementation",
                assignee=state['company']['name'],
                filing_date=None,
                grant_date=None,
                abstract="Patent LLM Agent will be implemented to provide comprehensive IP analysis with GPT-4o reasoning.",
                cpc=None,
                url=""
            )
        ]
        
        current_results = state.get("results", {})
        current_results["patents"] = placeholder_patents
        
        return {
            **state,
            "results": current_results,
            "status": "running" 
        }
    
    async def deepdive_placeholder_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for DeepDive LLM Agent (to be implemented)"""
        logger.info(f"📋 DeepDive Placeholder (LLM Agent pending) for run {state['run_id']}")
        
        # For now, return minimal deepdive results
        return {
            **state,
            "deepdive_results": {
                "team_analysis": "DeepDive LLM Agent pending implementation",
                "content_insights": "Will provide comprehensive content analysis with GPT-4o reasoning"
            },
            "status": "running"
        }
    
    async def verification_placeholder_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for Verification LLM Agent (to be implemented)"""
        logger.info(f"📋 Verification Placeholder (LLM Agent pending) for run {state['run_id']}")
        
        # Simple verification logic for now
        news_count = len(state.get("results", {}).get("news", []))
        patent_count = len(state.get("results", {}).get("patents", []))
        
        confidence_scores = {
            "news_reliability": min(1.0, news_count / 10),
            "patent_coverage": min(1.0, patent_count / 5),
            "overall": 0.7  # Placeholder confidence
        }
        
        return {
            **state,
            "verified_facts": [],  # Will be populated by real LLM agent
            "confidence_scores": confidence_scores,
            "current_phase": "synthesis",
            "status": "running"
        }
    
    async def synthesis_llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: LLM-powered synthesis and report generation"""
        logger.info(f"🤖 LLM Synthesis starting for run {state['run_id']}")
        
        try:
            # Prepare data for synthesis agent
            company_name = state.get("company", {}).get("name", "Unknown")
            run_id = state["run_id"]
            
            collected_data = {
                "discovery_results": state.get("discovery_results"),
                "news_results": state.get("results", {}).get("news", []),
                "patent_results": state.get("results", {}).get("patents", []),
                "founder_results": state.get("results", {}).get("founders", []),
                "competitive_results": state.get("results", {}).get("competitive"),
                "deepdive_results": state.get("deepdive_results"),
                "verified_facts": state.get("verified_facts", [])
            }
            
            # Check budget before LLM synthesis
            budget_status = await budget_tracker.get_budget_status()
            logger.info(f"💰 Budget status: ${budget_status.get('current_spend', 0):.2f}/${budget_status.get('max_budget', 10):.2f}")
            
            # Use synthesis agent for structured analysis
            synthesis_result = await synthesis_agent.analyze(company_name, run_id, collected_data)
            
            # Add data source statistics
            synthesis_result["data_sources"] = {
                "news_articles": len(collected_data.get("news_results", [])),
                "patents_found": len(collected_data.get("patent_results", [])),
                "pages_analyzed": 0,  # From discovery if available
                "verified_facts": len(collected_data.get("verified_facts", []))
            }
            
            insights = synthesis_result
            
            logger.info(f"✅ LLM Synthesis completed - Enhanced: {insights.get('llm_enhanced', False)}")
            
            return {
                **state,
                "insights": insights,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"❌ LLM Synthesis error: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [{"agent": "synthesis_llm", "message": str(e), "timestamp": datetime.utcnow()}],
                "status": "partial"
            }
    
    def _structure_insights(self, synthesis_result: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure insights from LLM synthesis."""
        
        base_insights = {
            "executive_summary": synthesis_result.get("executive_summary", "Analysis completed"),
            "investment_signals": synthesis_result.get("investment_signals", []),
            "risk_assessment": synthesis_result.get("risks", []),
            "confidence_score": synthesis_result.get("confidence_score", 0.5),
            "llm_enhanced": synthesis_result.get("llm_generated", False)
        }
        
        # Add data source statistics
        discovery_results = company_data.get("discovery_results")
        pages_analyzed = 0
        if discovery_results and hasattr(discovery_results, 'discovered_urls'):
            pages_analyzed = len(discovery_results.discovered_urls)
        
        base_insights["data_sources"] = {
            "news_articles": len(company_data.get("news_results", [])),
            "patents_found": len(company_data.get("patent_results", [])),
            "pages_analyzed": pages_analyzed,
            "verified_facts": len(company_data.get("verified_facts", []))
        }
        
        # Extract funding and partnerships from news
        news_results = company_data.get("news_results", [])
        base_insights["funding_events"] = self._extract_funding_events(news_results)
        base_insights["partnerships"] = self._extract_partnerships(news_results)
        
        return base_insights
    
    def _extract_funding_events(self, news_sources: List[SourceDoc]) -> List[Dict[str, Any]]:
        """Extract funding events from news sources."""
        funding_keywords = ["funding", "investment", "raised", "series", "round", "capital"]
        events = []
        
        for source in news_sources:
            if hasattr(source, 'snippet') and source.snippet:
                snippet_lower = source.snippet.lower()
                if any(keyword in snippet_lower for keyword in funding_keywords):
                    events.append({
                        "summary": source.title,
                        "source_id": source.id,
                        "url": source.url,
                        "published_date": getattr(source, 'published_at', None)
                    })
        return events[:5]  # Limit results
    
    def _extract_partnerships(self, news_sources: List[SourceDoc]) -> List[Dict[str, Any]]:
        """Extract partnership announcements from news sources."""
        partnership_keywords = ["partnership", "collaboration", "agreement", "deal", "alliance"]
        partnerships = []
        
        for source in news_sources:
            if hasattr(source, 'snippet') and source.snippet:
                snippet_lower = source.snippet.lower()
                if any(keyword in snippet_lower for keyword in partnership_keywords):
                    partnerships.append({
                        "summary": source.title,
                        "source_id": source.id,
                        "url": source.url,
                        "published_date": getattr(source, 'published_at', None)
                    })
        return partnerships[:5]  # Limit results


# Global LLM orchestrator instance
llm_orchestrator = LLMOrchestrator()


async def run_llm_analysis(run_id: str, company: str, domain: str = None):
    """
    Run complete LLM-based analysis using true generative AI agents.
    
    This function coordinates 6 LLM agents to provide comprehensive
    company intelligence with GPT-4o reasoning and decision-making.
    """
    db = get_database()
    
    # Reset budget tracker for fresh run tracking
    await budget_tracker.reset_for_new_run(run_id)
    
    # Update run status to running
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
        # Initial state for LLM workflow
        initial_state = {
            "run_id": run_id,
            "company": {"name": company, "domain": domain},
            "discovery_results": None,
            "company_aliases": [company],
            "results": {"news": [], "patents": [], "founders": [], "competitive": None},
            "deepdive_results": None,
            "verified_facts": [],
            "confidence_scores": {},
            "verification_results": None,
            "insights": None,
            "cost": {"tavily_credits": 0, "llm_tokens": 0, "openai_usd": 0.0},
            "status": "running",
            "current_phase": "discovery",
            "errors": []
        }
        
        logger.info(f"🚀 Starting LLM-powered analysis for run {run_id}")
        logger.info(f"🏢 Company: {company} | Domain: {domain}")
        
        # Execute the LLM agent workflow
        final_state = await llm_orchestrator.graph.ainvoke(initial_state)
        
        # Get actual cost data from budget tracker
        budget_status = await budget_tracker.get_budget_status()
        actual_costs = {
            "tavily_credits": budget_status.get("tavily_spend", 0),
            "llm_tokens": budget_status.get("total_tokens", 0),
            "openai_usd": budget_status.get("current_spend", 0.0),
            "operations_count": budget_status.get("operations_count", 0)
        }
        
        # Update final state with actual costs
        final_state["cost"] = actual_costs
        
        # Persist results to database
        await _persist_llm_results_to_db(db, final_state)
        
        # Update run completion with actual costs
        await db.runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": final_state.get("status", "completed"),
                    "completed_at": datetime.utcnow(),
                    "cost": actual_costs,
                    "errors": final_state.get("errors", [])
                }
            }
        )
        
        logger.info(f"✅ LLM analysis completed for run {run_id} with status: {final_state.get('status')}")
        
    except Exception as e:
        logger.error(f"❌ LLM analysis failed for run {run_id}: {e}")
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


async def _persist_llm_results_to_db(db, state: Dict[str, Any]):
    """Persist LLM agent results to MongoDB collections."""
    
    run_id = state["run_id"]
    
    try:
        # Persist news sources with unique IDs
        news_sources = state.get("results", {}).get("news", [])
        if news_sources:
            news_docs = []
            for idx, source in enumerate(news_sources):
                unique_id = f"news_{run_id}_{idx}"  # Ensure unique IDs
                
                # Handle both SourceDoc objects and dictionaries
                if hasattr(source, 'title'):  # SourceDoc object
                    news_doc = {
                        "_id": unique_id,
                        "run_id": run_id,
                        "type": "news",
                        "title": source.title or 'No title',
                        "url": source.url or '',
                        "snippet": (source.snippet or '')[:500],
                        "domain": source.domain,
                        "agent_type": "llm_news_agent",
                        "created_at": datetime.utcnow()
                    }
                else:  # Dictionary fallback
                    news_doc = {
                        "_id": unique_id,
                        "run_id": run_id,
                        "type": "news",
                        "title": source.get('title', 'No title'),
                        "url": source.get('url', ''),
                        "snippet": source.get('snippet', '')[:500],
                        "domain": source.get('domain'),
                        "agent_type": "llm_news_agent",
                        "created_at": datetime.utcnow()
                    }
                news_docs.append(news_doc)
            
            if news_docs:
                # Use insert_many with ordered=False to continue on duplicates
                try:
                    await db.sources.insert_many(news_docs, ordered=False)
                    logger.info(f"✅ Persisted {len(news_docs)} news sources")
                except Exception as e:
                    logger.warning(f"⚠️ Some news sources may be duplicates: {e}")
        else:
            logger.warning(f"⚠️ No news sources found in state for run {run_id}")
        
        # Persist patents with unique IDs
        patent_docs = state.get("results", {}).get("patents", [])
        if patent_docs:
            patent_records = []
            for idx, patent in enumerate(patent_docs):
                unique_id = f"patent_{run_id}_{idx}"  # Ensure unique IDs
                
                # Handle both PatentDoc objects and dictionaries
                if hasattr(patent, 'title'):  # PatentDoc object
                    patent_record = {
                        "_id": unique_id,
                        "run_id": run_id,
                        "title": patent.title or 'No title',
                        "assignee": patent.assignee or '',
                        "abstract": (patent.abstract or '')[:1000],
                        "url": patent.url or '',
                        "agent_type": "llm_patent_agent",
                        "created_at": datetime.utcnow()
                    }
                else:  # Dictionary fallback
                    patent_record = {
                        "_id": unique_id,
                        "run_id": run_id,
                        "title": patent.get('title', 'No title'),
                        "assignee": patent.get('assignee', ''),
                        "abstract": patent.get('abstract', '')[:1000],
                        "url": patent.get('url', ''),
                        "agent_type": "llm_patent_agent",
                        "created_at": datetime.utcnow()
                    }
                patent_records.append(patent_record)
            
            if patent_records:
                try:
                    await db.patents.insert_many(patent_records, ordered=False)
                    logger.info(f"✅ Persisted {len(patent_records)} patents")
                except Exception as e:
                    logger.warning(f"⚠️ Some patents may be duplicates: {e}")
        
        # Persist founder profiles
        founder_profiles = state.get("results", {}).get("founders", [])
        if founder_profiles:
            founder_docs = []
            for idx, founder in enumerate(founder_profiles):
                unique_id = f"founder_{run_id}_{idx}"
                
                founder_doc = {
                    "_id": unique_id,
                    "run_id": run_id,
                    "type": "founder",
                    "name": founder.get('name', 'Unknown'),
                    "role": founder.get('role', 'Leadership'),
                    "background_summary": founder.get('background_summary', ''),
                    "previous_experience": founder.get('previous_experience', []),
                    "key_achievements": founder.get('key_achievements', []),
                    "investment_assessment": founder.get('investment_assessment', ''),
                    "source_confidence": founder.get('source_confidence', 'medium'),
                    "agent_type": "llm_founder_agent",
                    "created_at": datetime.utcnow()
                }
                founder_docs.append(founder_doc)
            
            if founder_docs:
                try:
                    await db.founders.insert_many(founder_docs, ordered=False)
                    logger.info(f"✅ Persisted {len(founder_docs)} founder profiles")
                except Exception as e:
                    logger.warning(f"⚠️ Some founder profiles may be duplicates: {e}")
        
        # Persist competitive analysis
        competitive_analysis = state.get("results", {}).get("competitive")
        if competitive_analysis:
            competitive_doc = {
                "_id": f"competitive_{run_id}",
                "run_id": run_id,
                "type": "competitive_analysis",
                "company": competitive_analysis.get('company', ''),
                "competitors": competitive_analysis.get('competitors', []),
                "market_positioning": competitive_analysis.get('market_positioning', ''),
                "competitive_advantages": competitive_analysis.get('competitive_advantages', []),
                "market_threats": competitive_analysis.get('market_threats', []),
                "market_opportunities": competitive_analysis.get('market_opportunities', []),
                "market_insights": competitive_analysis.get('market_insights', []),
                "competitive_assessment": competitive_analysis.get('competitive_assessment', ''),
                "investment_implications": competitive_analysis.get('investment_implications', ''),
                "agent_type": "llm_competitive_agent",
                "created_at": datetime.utcnow()
            }
            
            try:
                await db.competitive_analysis.replace_one(
                    {"run_id": run_id},
                    competitive_doc,
                    upsert=True
                )
                logger.info(f"✅ Persisted competitive analysis for run {run_id}")
            except Exception as e:
                logger.warning(f"⚠️ Competitive analysis persistence error: {e}")
        
        # Persist deepdive analysis
        deepdive_analysis = state.get("deepdive_results")
        if deepdive_analysis:
            deepdive_doc = {
                "_id": f"deepdive_{run_id}",
                "run_id": run_id,
                "type": "deepdive_analysis",
                "company": deepdive_analysis.get('company', ''),
                "company_profile": deepdive_analysis.get('company_profile', {}),
                "team_analysis": deepdive_analysis.get('team_analysis', {}),
                "product_analysis": deepdive_analysis.get('product_analysis', {}),
                "business_traction": deepdive_analysis.get('business_traction', {}),
                "content_sources": deepdive_analysis.get('content_sources', []),
                "investment_insights": deepdive_analysis.get('investment_insights', []),
                "comprehensive_assessment": deepdive_analysis.get('comprehensive_assessment', ''),
                "confidence_score": deepdive_analysis.get('confidence_score', 0.0),
                "agent_type": "llm_deepdive_agent",
                "created_at": datetime.utcnow()
            }
            
            try:
                await db.deepdive_analysis.replace_one(
                    {"run_id": run_id},
                    deepdive_doc,
                    upsert=True
                )
                logger.info(f"✅ Persisted deepdive analysis for run {run_id}")
            except Exception as e:
                logger.warning(f"⚠️ DeepDive analysis persistence error: {e}")
        
        # Persist verification analysis
        verification_analysis = state.get("verification_results")
        if verification_analysis:
            verification_doc = {
                "_id": f"verification_{run_id}",
                "run_id": run_id,
                "type": "verification_analysis",
                "company": verification_analysis.get('company', ''),
                "verified_facts": verification_analysis.get('verified_facts', []),
                "confidence_scores": verification_analysis.get('confidence_scores', {}),
                "inconsistencies_found": verification_analysis.get('inconsistencies_found', []),
                "information_gaps": verification_analysis.get('information_gaps', []),
                "red_flags": verification_analysis.get('red_flags', []),
                "source_reliability": verification_analysis.get('source_reliability', {}),
                "verification_summary": verification_analysis.get('verification_summary', ''),
                "investment_risk_factors": verification_analysis.get('investment_risk_factors', []),
                "additional_verification_needed": verification_analysis.get('additional_verification_needed', []),
                "agent_type": "llm_verification_agent",
                "created_at": datetime.utcnow()
            }
            
            try:
                await db.verification_analysis.replace_one(
                    {"run_id": run_id},
                    verification_doc,
                    upsert=True
                )
                logger.info(f"✅ Persisted verification analysis for run {run_id}")
            except Exception as e:
                logger.warning(f"⚠️ Verification analysis persistence error: {e}")
        
        # Persist insights
        insights = state.get("insights")
        if insights:
            insights_doc = {
                "run_id": run_id,
                "executive_summary": insights.get("executive_summary", ""),
                "investment_signals": insights.get("investment_signals", []),
                "risk_assessment": insights.get("risk_assessment", []),
                "confidence_score": insights.get("confidence_score", 0),
                "llm_enhanced": insights.get("llm_enhanced", False),
                "data_sources": insights.get("data_sources", {}),
                "funding_events": insights.get("funding_events", []),
                "partnerships": insights.get("partnerships", []),
                "created_at": datetime.utcnow()
            }
            
            # Replace existing insights for this run
            await db.insights.replace_one(
                {"run_id": run_id},
                insights_doc,
                upsert=True
            )
            logger.info(f"✅ Persisted insights for run {run_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to persist LLM results to DB: {e}")
        # Don't raise - let the analysis complete even if persistence fails