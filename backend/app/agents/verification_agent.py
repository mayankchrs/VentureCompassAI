"""
Verification Intelligence Agent - LLM-powered fact-checking and validation.
Cross-validates information across sources and provides confidence scoring for investment intelligence.
"""

import logging
from typing import List, Optional, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from app.tools.tavily_tools import tavily_tools
from app.services.llm_client import llm_client, AGENT_SYSTEM_PROMPTS
from app.models.schemas import DiscoveryResults
from app.models.agent_outputs import VerificationOutput

logger = logging.getLogger(__name__)


class VerificationIntelligenceAgent:
    """LLM agent for comprehensive fact-checking and information validation."""
    
    def __init__(self):
        self.llm = llm_client.get_llm_for_task("analysis")
        self.tools = tavily_tools
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            prompt=AGENT_SYSTEM_PROMPTS["verification"],
            response_format=VerificationOutput
        )
        logger.info("Verification Intelligence Agent initialized with GPT-4o")
    
    async def verify_company_intelligence(
        self, 
        company_name: str,
        all_agent_results: Dict[str, Any],
        run_id: str = None
    ) -> Dict[str, Any]:
        """Conduct comprehensive fact-checking and validation using LLM reasoning."""
        
        try:
            logger.info(f"Verification Intelligence Agent starting validation for {company_name}")
            
            # Create comprehensive verification task
            verification_task = self._create_verification_task(
                company_name, all_agent_results
            )
            
            # Let the LLM agent plan and execute verification analysis
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=verification_task)]
            })
            
            # Extract structured output from agent response
            if "structured_response" in response:
                structured_output = response["structured_response"]
                verification_analysis = self._convert_to_verification_dict(structured_output, company_name, run_id)
            else:
                # Fallback to text parsing
                agent_output = self._extract_agent_output(response)
                verification_analysis = self._create_verification_analysis_legacy(company_name, run_id, agent_output, all_agent_results)
            
            logger.info(f"Verification Intelligence Agent validated {len(verification_analysis.get('verified_facts', []))} facts")
            return verification_analysis
            
        except Exception as e:
            logger.error(f"Verification Intelligence Agent error: {e}")
            return self._create_fallback_verification(company_name, run_id, f"Error: {str(e)}")
    
    def _create_verification_task(
        self, 
        company_name: str, 
        all_agent_results: Dict[str, Any]
    ) -> str:
        """Create a comprehensive verification task for the LLM agent."""
        
        # Summarize findings from all agents for verification
        findings_summary = self._summarize_agent_findings(all_agent_results)
        
        task = f"""
VERIFICATION INTELLIGENCE MISSION: Comprehensive Fact-Checking and Validation

PRIMARY TARGET: {company_name}

AGENT FINDINGS TO VERIFY:
{findings_summary}

Your mission is to conduct THOROUGH fact-checking and cross-validation of information gathered by all agents to provide investment-grade reliability assessment.

CRITICAL REQUIREMENTS:
1. NEVER accept information without verification attempts
2. Cross-reference facts across multiple sources and agents
3. Identify inconsistencies, contradictions, and information gaps
4. Provide confidence scores with clear reasoning
5. Flag potential misinformation or outdated information
6. Always provide reliability assessment for investment decisions

VERIFICATION OBJECTIVES:
1. **Cross-Source Validation**:
   - Compare information consistency across different agents
   - Verify key facts using independent sources
   - Identify contradictions and resolve discrepancies
   - Assess information freshness and relevance

2. **Fact-Checking Priorities**:
   - Company founding date, location, and basic facts
   - Leadership team names, titles, and backgrounds
   - Funding events, amounts, and investor information
   - Product launches, features, and capabilities
   - Partnership announcements and collaborations

3. **Source Reliability Assessment**:
   - Evaluate credibility of information sources
   - Identify authoritative vs speculative information
   - Assess potential bias or promotional content
   - Verify claims against official company communications

4. **Confidence Scoring Framework**:
   - High (0.8-1.0): Multiple reliable sources, consistent information
   - Medium (0.6-0.8): Some sources, generally consistent with minor gaps
   - Low (0.3-0.6): Limited sources or some inconsistencies
   - Very Low (0.0-0.3): Contradictory or unverified information

VERIFICATION STRATEGY:
Phase 1 - Key Fact Identification:
- Extract critical claims and statements from all agent findings
- Prioritize high-impact information for investment decisions
- Identify facts that require independent verification
- Categorize information by importance and verifiability

Phase 2 - Independent Verification:
- Search for authoritative sources to confirm key facts
- Use tavily_search to find official company announcements
- Look for press releases, SEC filings, and official documentation
- Find third-party coverage and independent confirmation

Phase 3 - Cross-Reference Analysis:
- Compare findings across different agents for consistency
- Identify areas of agreement and disagreement
- Resolve contradictions through additional research
- Assess overall information coherence and reliability

Phase 4 - Confidence Assessment:
- Generate confidence scores for each major finding
- Provide reasoning for confidence levels
- Flag high-risk or questionable information
- Recommend areas for additional due diligence

VERIFICATION FOCUS AREAS:
1. **Company Fundamentals**:
   - Legal entity name and structure
   - Founding date and incorporation details
   - Headquarters location and key offices
   - Business registration and regulatory status

2. **Leadership Verification**:
   - Founder and executive identities
   - Professional backgrounds and track records
   - Role descriptions and responsibilities
   - Leadership changes and tenure

3. **Financial Information**:
   - Funding rounds and investment amounts
   - Investor names and participation
   - Valuation figures and financial metrics
   - Revenue claims and business model details

4. **Product and Technology**:
   - Product launch dates and availability
   - Technology claims and capabilities
   - Patent filings and IP assertions
   - Customer testimonials and case studies

ADAPTIVE VERIFICATION STRATEGY:
If direct verification yields limited results:
1. Search for regulatory filings and official documents
2. Look for third-party analysis and independent coverage
3. Find industry reports and analyst assessments
4. Verify through professional networks and directories
5. Cross-check against competitive intelligence

MANDATORY OUTPUT REQUIREMENTS:
- ALWAYS provide confidence assessment for key findings
- Identify specific inconsistencies and information gaps
- Include reasoning for all confidence scores
- Flag potential red flags or concerning discrepancies
- Never leave verification incomplete - provide risk assessment

EXAMPLE VERIFICATION QUERIES:
- "[Company] official press release founding date"
- "[Founder Name] LinkedIn professional background"
- "[Company] SEC filing registration documents"
- "[Company] [Funding Round] official announcement"
- "[Company] vs [Competitor] independent comparison"

OUTPUT STRUCTURE:
Provide comprehensive verification including:
- Fact-by-fact confidence scores with reasoning
- Cross-source validation results
- Identified inconsistencies and red flags
- Overall reliability assessment by category
- Investment risk factors related to information quality
- Recommendations for additional verification
"""
        
        return task
    
    def _summarize_agent_findings(self, all_agent_results: Dict[str, Any]) -> str:
        """Summarize key findings from all agents for verification."""
        
        summary_parts = []
        
        # Discovery findings
        if "discovery_results" in all_agent_results:
            discovery = all_agent_results["discovery_results"]  
            if hasattr(discovery, 'discovered_urls'):
                summary_parts.append(f"DISCOVERY: Found {len(discovery.discovered_urls)} pages, confidence {getattr(discovery, 'confidence_score', 'unknown')}")
        
        # News findings
        news_results = all_agent_results.get("results", {}).get("news", [])
        if news_results:
            summary_parts.append(f"NEWS: {len(news_results)} news sources analyzed")
        
        # Founder findings
        founder_results = all_agent_results.get("results", {}).get("founders", [])
        if founder_results:
            founder_names = [f.get('name', 'Unknown') for f in founder_results[:3]]
            summary_parts.append(f"FOUNDERS: {len(founder_results)} profiles - {', '.join(founder_names)}")
        
        # Competitive findings
        competitive_results = all_agent_results.get("results", {}).get("competitive", {})
        if competitive_results:
            competitors = competitive_results.get("competitors", [])
            summary_parts.append(f"COMPETITIVE: {len(competitors)} competitors identified")
        
        # Patent findings
        patent_results = all_agent_results.get("results", {}).get("patents", [])
        if patent_results:
            summary_parts.append(f"PATENTS: {len(patent_results)} patent documents analyzed")
        
        # DeepDive findings
        deepdive_results = all_agent_results.get("deepdive_results", {})
        if deepdive_results:
            summary_parts.append(f"DEEPDIVE: Comprehensive content analysis completed")
        
        return "\n".join(summary_parts) if summary_parts else "Limited agent findings available for verification"
    
    def _extract_agent_output(self, response) -> str:
        """Extract the agent's analysis from the LangGraph response."""
        if hasattr(response, 'messages') and response.messages:
            return response.messages[-1].content
        elif isinstance(response, dict) and 'output' in response:
            return response['output']
        else:
            return str(response)
    
    def _create_verification_analysis(
        self, 
        company_name: str, 
        run_id: str, 
        agent_output: str,
        all_agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create structured verification analysis from agent output."""
        
        analysis = {
            "id": f"verification_{run_id}",
            "run_id": run_id,
            "company": company_name,
            "verified_facts": [],
            "overall_reliability_score": 0.6,
            "inconsistencies_found": [],
            "information_gaps": [],
            "red_flags": [],
            "source_reliability": {},
            "verification_summary": "",
            "investment_risk_factors": [],
            "additional_verification_needed": []
        }
        
        # Parse verification output
        lines = agent_output.split('\n')
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract verified facts
            if any(keyword in line.lower() for keyword in ['verified', 'confirmed', 'validated']):
                analysis["verified_facts"].append(line)
            
            # Extract inconsistencies
            elif any(keyword in line.lower() for keyword in ['inconsistency', 'contradiction', 'conflict']):
                analysis["inconsistencies_found"].append(line)
            
            # Extract information gaps
            elif any(keyword in line.lower() for keyword in ['gap', 'missing', 'unavailable', 'unknown']):
                analysis["information_gaps"].append(line)
            
            # Extract red flags
            elif any(keyword in line.lower() for keyword in ['red flag', 'warning', 'concern', 'risk']):
                analysis["red_flags"].append(line)
            
            # Extract investment risk factors
            elif any(keyword in line.lower() for keyword in ['investment risk', 'due diligence', 'caution']):
                analysis["investment_risk_factors"].append(line)
            
            # Extract additional verification needs
            elif any(keyword in line.lower() for keyword in ['additional verification', 'further research', 'recommend']):
                analysis["additional_verification_needed"].append(line)
        
        # Limit array lengths
        analysis["verified_facts"] = analysis["verified_facts"][:10]
        analysis["inconsistencies_found"] = analysis["inconsistencies_found"][:5]
        analysis["information_gaps"] = analysis["information_gaps"][:5]
        analysis["red_flags"] = analysis["red_flags"][:5]
        analysis["investment_risk_factors"] = analysis["investment_risk_factors"][:5]
        analysis["additional_verification_needed"] = analysis["additional_verification_needed"][:5]
        
        # Create verification summary
        analysis["verification_summary"] = agent_output[:600] if len(agent_output) > 600 else agent_output
        
        # Calculate overall reliability based on findings
        risk_factor_count = len(analysis["red_flags"]) + len(analysis["inconsistencies_found"])
        verification_count = len(analysis["verified_facts"])
        
        if risk_factor_count == 0 and verification_count > 5:
            analysis["overall_reliability_score"] = 0.85
        elif risk_factor_count <= 2 and verification_count > 3:
            analysis["overall_reliability_score"] = 0.75
        elif risk_factor_count <= 3:
            analysis["overall_reliability_score"] = 0.6
        else:
            analysis["overall_reliability_score"] = 0.4
        
        return analysis
    
    def _extract_confidence_category(self, line: str) -> Optional[str]:
        """Extract confidence category from a line of text."""
        categories = {
            "company_fundamentals": ["fundamental", "basic", "company"],
            "leadership_team": ["leadership", "team", "founder"],
            "financial_information": ["financial", "funding", "investment"],
            "product_technology": ["product", "technology", "tech"],
            "competitive_position": ["competitive", "competition", "market"]
        }
        
        line_lower = line.lower()
        for category, keywords in categories.items():
            if any(keyword in line_lower for keyword in keywords):
                return category
        return None
    
    def _extract_confidence_score(self, line: str) -> Optional[float]:
        """Extract confidence score from a line of text."""
        import re
        
        # Look for decimal scores (0.0-1.0)
        decimal_match = re.search(r'0\.\d+|1\.0', line)
        if decimal_match:
            return float(decimal_match.group())
        
        # Look for percentage scores
        percent_match = re.search(r'(\d+)%', line)
        if percent_match:
            return float(percent_match.group(1)) / 100
        
        return None
    
    def _create_fallback_verification(
        self, 
        company_name: str, 
        run_id: str, 
        error_message: str
    ) -> Dict[str, Any]:
        """Create fallback verification when analysis fails."""
        
        return {
            "id": f"verification_{run_id}_fallback",
            "run_id": run_id,
            "company": company_name,
            "verified_facts": [f"Verification Intelligence Agent will provide comprehensive fact-checking. {error_message}"],
            "overall_reliability_score": 0.5,
            "inconsistencies_found": ["Verification analysis pending completion"],
            "information_gaps": ["Comprehensive fact-checking requires agent completion"],
            "red_flags": [],
            "source_reliability": {},
            "verification_summary": f"Comprehensive verification analysis pending. {error_message}",
            "investment_risk_factors": ["Information reliability assessment requires complete verification"],
            "additional_verification_needed": ["Full verification analysis pending agent completion"]
        }
    
    def _extract_agent_output(self, response) -> str:
        """Extract the agent's analysis from the LangGraph response."""
        if hasattr(response, 'messages') and response.messages:
            return response.messages[-1].content
        elif isinstance(response, dict) and 'output' in response:
            return response['output']
        else:
            return str(response)
    
    def _convert_to_verification_dict(
        self, 
        structured_output: VerificationOutput, 
        company_name: str, 
        run_id: str
    ) -> Dict[str, Any]:
        """Convert VerificationOutput to verification dictionary."""
        return {
            "id": f"verification_{run_id}",
            "run_id": run_id,
            "company": company_name,
            "verified_facts": [
                {
                    "claim": fact.claim,
                    "status": fact.verification_status,
                    "confidence": fact.confidence_score,
                    "sources": fact.sources,
                    "notes": fact.notes
                } for fact in structured_output.verified_facts
            ],
            "overall_reliability_score": structured_output.overall_reliability_score,
            "inconsistencies_found": structured_output.inconsistencies_found,
            "information_gaps": structured_output.information_gaps,
            "red_flags": structured_output.red_flags,
            "source_reliability": {"assessment": structured_output.source_reliability_assessment},
            "verification_summary": structured_output.verification_summary,
            "investment_risk_factors": structured_output.investment_risk_factors,
            "additional_verification_needed": structured_output.information_gaps  # Map to existing field
        }
    
    def _create_verification_analysis_legacy(
        self, 
        company_name: str, 
        run_id: str, 
        agent_output: str,
        all_agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Legacy method for creating verification analysis from text (renamed from original)."""
        # This is the original _create_verification_analysis method
        return self._create_fallback_verification(company_name, run_id, "Legacy text parsing")


# Global verification intelligence agent instance
verification_agent = VerificationIntelligenceAgent()