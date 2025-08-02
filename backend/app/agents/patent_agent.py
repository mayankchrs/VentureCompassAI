"""
Patent Intelligence Agent - LLM-powered intellectual property analysis.
Researches patents, IP portfolios, and innovation landscapes for investment intelligence.
"""

import logging
from typing import List, Optional, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from app.tools.tavily_tools import tavily_tools
from app.services.llm_client import llm_client, AGENT_SYSTEM_PROMPTS
from app.models.schemas import DiscoveryResults, PatentDoc
from app.models.agent_outputs import PatentOutput

logger = logging.getLogger(__name__)


class PatentIntelligenceAgent:
    """LLM agent for comprehensive patent and IP analysis."""
    
    def __init__(self):
        self.llm = llm_client.get_llm_for_task("analysis")
        self.tools = tavily_tools
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            prompt=AGENT_SYSTEM_PROMPTS["patent"],
            response_format=PatentOutput
        )
        logger.info("Patent Intelligence Agent initialized with GPT-4o")
    
    async def analyze_ip_portfolio(
        self, 
        company_name: str, 
        discovery_results: Optional[DiscoveryResults] = None,
        founder_profiles: Optional[List[Dict[str, Any]]] = None,
        run_id: str = None
    ) -> List[PatentDoc]:
        """Conduct comprehensive patent and IP analysis using LLM reasoning."""
        
        try:
            logger.info(f"Patent Intelligence Agent starting IP analysis for {company_name}")
            
            # Create comprehensive patent research task
            patent_task = self._create_patent_research_task(
                company_name, discovery_results, founder_profiles
            )
            
            # Let the LLM agent plan and execute patent research
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=patent_task)]
            })
            
            # Extract structured output from agent response
            if "structured_response" in response:
                structured_output = response["structured_response"]
                patent_docs = self._convert_to_patent_docs(structured_output, company_name, run_id)
            else:
                # Fallback to text parsing
                agent_output = self._extract_agent_output(response)
                patent_docs = self._create_patent_documents_legacy(company_name, run_id, agent_output)
            
            logger.info(f"Patent Intelligence Agent analyzed {len(patent_docs)} patent documents")
            return patent_docs
            
        except Exception as e:
            logger.error(f"Patent Intelligence Agent error: {e}")
            return self._create_fallback_patents(company_name, run_id, f"Error: {str(e)}")
    
    def _create_patent_research_task(
        self, 
        company_name: str, 
        discovery_results: Optional[DiscoveryResults] = None,
        founder_profiles: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Create a comprehensive patent research task for the LLM agent."""
        
        # Build context from discovery and founder results
        context_info = ""
        if discovery_results:
            context_info += f"""
DISCOVERY CONTEXT:
- Company Website: {discovery_results.base_url}
- Technology Insights: {discovery_results.llm_analysis[:200]}...
"""
        
        founder_info = ""
        if founder_profiles:
            founder_names = [profile.get('name', '') for profile in founder_profiles[:3]]
            founder_info = f"Key Founders: {', '.join(founder_names)}"
        
        task = f"""
PATENT INTELLIGENCE MISSION: Comprehensive IP Portfolio Analysis

PRIMARY TARGET: {company_name}
{founder_info}
{context_info}

Your mission is to conduct THOROUGH patent and intellectual property research to provide investment-grade IP intelligence and innovation analysis.

CRITICAL REQUIREMENTS:
1. NEVER return incomplete patent analysis
2. Research patent portfolios using multiple search strategies
3. Analyze technology focus areas and innovation patterns
4. Assess IP strength, competitive moats, and defensive positioning
5. Investigate inventor networks and key technical personnel
6. Always provide strategic IP assessment for investment decisions

RESEARCH OBJECTIVES:
1. **Patent Portfolio Discovery**:
   - Filed and granted patents under company name
   - Patent applications and pending filings
   - Patent family analysis and international coverage
   - Patent prosecution timeline and strategy

2. **Inventor-Based Research**:
   - Patents filed by founders and key technical personnel
   - Inventor collaboration networks and expertise areas
   - Previous company IP contributions and track records
   - Academic and research institution affiliations

3. **Technology Innovation Analysis**:
   - Core technology areas and patent classifications
   - Innovation focus areas and R&D direction
   - Technical depth and patent claim analysis
   - Competitive differentiation through IP

4. **IP Strategy Assessment**:
   - Patent filing frequency and consistency
   - Geographic coverage and market protection
   - Patent citation analysis and forward references
   - Defensive vs offensive patent strategy

RESEARCH STRATEGY:
Phase 1 - Company Patent Discovery:
- Search for "[Company] patent application grant USPTO"
- Look for company name variations and subsidiary filings
- Find recent patent filings and application trends
- Search for "[Company] intellectual property patent portfolio"

Phase 2 - Inventor-Based Research:
- Search for founder/CTO patents using "[Founder Name] inventor patent"
- Look for key technical personnel patent contributions
- Find patent collaboration networks and co-inventors
- Research "[Founder Name] [Company] patent filing"

Phase 3 - Technology Area Analysis:
- Search for technology-specific patents in company's domain
- Look for "[Company technology area] patent landscape"
- Find competitive patent analysis in the space
- Research patent classification and technical focus areas

Phase 4 - IP Intelligence Extraction:
- Use tavily_extract on key patent documents for detailed analysis
- Extract patent abstracts, claims, and technical descriptions
- Analyze patent strength and commercial relevance
- Assess competitive IP landscape and freedom to operate

ADAPTIVE SEARCH STRATEGY:
If direct patent searches yield limited results:
1. Search for company technology domain patent landscapes
2. Look for founder academic research and publications
3. Search for industry patent trends and key players
4. Find patent analytics and IP intelligence reports
5. Research competitive patent filings in similar technologies

MANDATORY OUTPUT REQUIREMENTS:
- ALWAYS provide IP assessment, even with limited patent findings
- Analyze innovation strategy based on available information
- Include assessment of IP strength and competitive positioning
- Provide investment implications of IP portfolio quality
- Never leave patent analysis incomplete - provide strategic insights

EXAMPLE SEARCH QUERIES:
- "[Company] patent portfolio USPTO filings"
- "[Founder Name] inventor patent applications"
- "[Company] [Technology] patent intellectual property"
- "[Company domain] patent landscape competitive analysis"
- "[Company] innovation R&D patent strategy"

OUTPUT STRUCTURE:
For each patent or IP finding, provide:
- Patent title and filing/grant dates
- Inventor names and assignee information
- Technology area and patent classification
- Patent abstract and key claims summary
- Commercial relevance and competitive significance
- IP strength assessment and investment implications
"""
        
        return task
    
    def _extract_structured_output(self, response, company_name: str, run_id: str) -> List[PatentDoc]:
        """Extract structured output from agent response."""
        try:
            # Get the last message which should contain the structured output
            if hasattr(response, 'messages') and response.messages:
                last_message = response.messages[-1]
                
                # Check if it's already a PatentOutput instance
                if hasattr(last_message, 'content') and hasattr(last_message.content, 'patents'):
                    structured_output = last_message.content
                    return self._convert_to_patent_docs(structured_output, company_name, run_id)
                
                # Try to parse as structured content
                content = last_message.content
                if hasattr(content, 'patents'):
                    return self._convert_to_patent_docs(content, company_name, run_id)
                    
            # Fallback to creating fallback patents
            return self._create_fallback_patents(company_name, run_id, "Could not extract structured output")
            
        except Exception as e:
            logger.error(f"Error extracting structured output: {e}")
            return self._create_fallback_patents(company_name, run_id, f"Extraction error: {str(e)}")
    
    def _extract_agent_output(self, response) -> str:
        """Extract the agent's analysis from the LangGraph response."""
        if hasattr(response, 'messages') and response.messages:
            return response.messages[-1].content
        elif isinstance(response, dict) and 'output' in response:
            return response['output']
        else:
            return str(response)
    
    def _convert_to_patent_docs(
        self, 
        structured_output: PatentOutput, 
        company_name: str, 
        run_id: str
    ) -> List[PatentDoc]:
        """Convert PatentOutput to PatentDoc objects."""
        patent_docs = []
        
        for i, patent in enumerate(structured_output.patent_records):
            patent_doc = PatentDoc(
                id=f"patent_{run_id}_{i}",
                run_id=run_id,
                title=patent.title,
                assignee=patent.assignee,
                filing_date=patent.filing_date,  # These will be string dates from schema
                grant_date=None,  # PatentRecord doesn't have grant_date
                abstract=patent.abstract[:1000] if patent.abstract else "",  # Limit abstract length
                cpc=[patent.technology_area] if patent.technology_area else [],  # Map technology_area to cpc
                url=""  # PatentRecord doesn't have url
            )
            patent_docs.append(patent_doc)
        
        # If no patents found, create analysis summary
        if not patent_docs:
            patent_docs.append(PatentDoc(
                id=f"patent_{run_id}_analysis",
                run_id=run_id,
                title=f"Patent Intelligence Analysis for {company_name}",
                assignee=company_name,
                filing_date=None,
                grant_date=None,
                abstract=structured_output.ip_strength_assessment[:500] if structured_output.ip_strength_assessment else "Comprehensive IP analysis completed",
                cpc=None,
                url=""
            ))
        
        return patent_docs[:10]  # Limit to top 10 patents
    
    def _create_patent_documents_legacy(
        self, 
        company_name: str, 
        run_id: str, 
        agent_output: str
    ) -> List[PatentDoc]:
        """Create structured patent documents from agent analysis."""
        
        patents = []
        lines = agent_output.split('\n')
        current_patent = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for patent titles or patent numbers
            if any(keyword in line.lower() for keyword in ['patent', 'application', 'filing', 'granted']):
                if current_patent and current_patent.get('title'):
                    patents.append(current_patent)
                
                current_patent = {
                    "id": f"patent_{run_id}_{len(patents)}",
                    "run_id": run_id,
                    "title": self._extract_patent_title(line),
                    "assignee": company_name,
                    "filing_date": self._extract_date(line),
                    "grant_date": None,
                    "abstract": "",
                    "cpc": self._extract_classification(line),
                    "url": "",
                    "inventors": [],
                    "technology_area": "",
                    "commercial_relevance": "",
                    "ip_strength_assessment": ""
                }
            elif current_patent and line:
                # Add details to current patent
                if any(keyword in line.lower() for keyword in ['abstract', 'summary', 'description']):
                    current_patent["abstract"] += f" {line}"
                elif any(keyword in line.lower() for keyword in ['inventor', 'filed by', 'created by']):
                    inventor_name = self._extract_inventor_name(line)
                    if inventor_name:
                        current_patent["inventors"].append(inventor_name)
                elif any(keyword in line.lower() for keyword in ['technology', 'field', 'area', 'classification']):
                    current_patent["technology_area"] += f" {line}"
                elif any(keyword in line.lower() for keyword in ['commercial', 'market', 'application']):
                    current_patent["commercial_relevance"] += f" {line}"
                elif any(keyword in line.lower() for keyword in ['strength', 'assessment', 'competitive']):
                    current_patent["ip_strength_assessment"] += f" {line}"
        
        # Add the last patent
        if current_patent and current_patent.get('title'):
            patents.append(current_patent)
        
        # If no patents found, create analysis summary
        if not patents:
            patents.append({
                "id": f"patent_{run_id}_analysis",
                "run_id": run_id,
                "title": f"Patent Intelligence Analysis for {company_name}",
                "assignee": company_name,
                "filing_date": None,
                "grant_date": None,
                "abstract": agent_output[:500] if len(agent_output) > 500 else agent_output,
                "cpc": None,
                "url": "",
                "inventors": ["Patent Intelligence Team"],
                "technology_area": "Comprehensive IP Analysis",
                "commercial_relevance": "Investment-grade patent portfolio assessment completed",
                "ip_strength_assessment": agent_output[-300:] if len(agent_output) > 300 else "Strategic IP analysis provided"
            })
        
        # Convert to PatentDoc objects
        patent_docs = []
        for patent_data in patents[:10]:  # Limit to top 10 patents
            patent_doc = PatentDoc(
                id=patent_data["id"],
                run_id=patent_data["run_id"],
                title=patent_data["title"],
                assignee=patent_data["assignee"],
                filing_date=patent_data["filing_date"],
                grant_date=patent_data["grant_date"],
                abstract=patent_data["abstract"][:1000],  # Limit abstract length
                cpc=patent_data["cpc"],
                url=patent_data["url"]
            )
            patent_docs.append(patent_doc)
        
        return patent_docs
    
    def _extract_patent_title(self, line: str) -> str:
        """Extract patent title from a line of text."""
        # Simple title extraction logic
        if ':' in line:
            parts = line.split(':')
            if len(parts) > 1:
                return parts[1].strip()
        return line.strip()
    
    def _extract_date(self, line: str) -> Optional[str]:
        """Extract filing/grant date from a line of text."""
        import re
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{1,2}/\d{1,2}/\d{2,4}'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group()
        return None
    
    def _extract_classification(self, line: str) -> Optional[str]:
        """Extract patent classification from a line of text."""
        # Look for CPC classifications like G06F, H04N, etc.
        import re
        cpc_pattern = r'[A-H]\d{2}[A-Z]\d+'
        match = re.search(cpc_pattern, line)
        return match.group() if match else None
    
    def _extract_inventor_name(self, line: str) -> Optional[str]:
        """Extract inventor name from a line of text."""
        # Simple name extraction from inventor lines
        words = line.split()
        for i, word in enumerate(words):
            if word.lower() in ['inventor', 'filed', 'by']:
                if i + 1 < len(words):
                    return ' '.join(words[i+1:i+3])  # Take next 1-2 words as name
        return None
    
    def _create_fallback_patents(
        self, 
        company_name: str, 
        run_id: str, 
        error_message: str
    ) -> List[PatentDoc]:
        """Create fallback patent documents when analysis fails."""
        
        return [PatentDoc(
            id=f"patent_{run_id}_fallback",
            run_id=run_id,
            title=f"Patent Intelligence Analysis for {company_name}",
            assignee=company_name,
            filing_date=None,
            grant_date=None,
            abstract=f"Patent Intelligence Agent will provide comprehensive IP portfolio analysis. {error_message}",
            cpc=None,
            url=""
        )]


# Global patent intelligence agent instance
patent_agent = PatentIntelligenceAgent()