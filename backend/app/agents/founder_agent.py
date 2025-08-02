"""
Founder Intelligence Agent - LLM-powered leadership analysis.
Researches founders, executives, and key personnel for investment intelligence.
"""

import logging
from typing import List, Optional, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from app.tools.tavily_tools import tavily_tools
from app.services.llm_client import llm_client, AGENT_SYSTEM_PROMPTS
from app.models.schemas import DiscoveryResults
from app.models.agent_outputs import FounderOutput

logger = logging.getLogger(__name__)


class FounderIntelligenceAgent:
    """LLM agent for comprehensive founder and leadership team analysis."""
    
    def __init__(self):
        self.llm = llm_client.get_llm_for_task("analysis")
        self.tools = tavily_tools
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            prompt=AGENT_SYSTEM_PROMPTS["founder"],
            response_format=FounderOutput
        )
        logger.info("Founder Intelligence Agent initialized with GPT-4o")
    
    async def analyze_leadership_team(
        self, 
        company_name: str, 
        discovery_results: Optional[DiscoveryResults] = None,
        run_id: str = None
    ) -> List[Dict[str, Any]]:
        """Conduct comprehensive leadership team analysis using LLM reasoning."""
        
        try:
            logger.info(f"Founder Intelligence Agent starting leadership analysis for {company_name}")
            
            # Create comprehensive founder research task
            founder_task = self._create_founder_research_task(
                company_name, discovery_results
            )
            
            # Let the LLM agent plan and execute founder research
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=founder_task)]
            })
            
            # Extract structured output and create founder profiles
            structured_output = self._extract_structured_founder_output(response)
            founder_profiles = self._create_founder_profiles_from_structured(company_name, run_id, structured_output)
            
            logger.info(f"Founder Intelligence Agent analyzed {len(founder_profiles)} leadership profiles")
            return founder_profiles
            
        except Exception as e:
            logger.error(f"Founder Intelligence Agent error: {e}")
            return self._create_fallback_profiles(company_name, run_id, f"Error: {str(e)}")
    
    def _create_founder_research_task(
        self, 
        company_name: str, 
        discovery_results: Optional[DiscoveryResults] = None
    ) -> str:
        """Create a comprehensive founder research task for the LLM agent."""
        
        # Build context from discovery results
        context_info = ""
        if discovery_results:
            context_info = f"""
DISCOVERY CONTEXT:
- Website: {discovery_results.base_url}
- Team Pages Found: {len([url for url in discovery_results.discovered_urls if 'team' in url.lower() or 'about' in url.lower()])} pages
- Company Insights: {discovery_results.llm_analysis[:300]}...
"""
        
        task = f"""
FOUNDER INTELLIGENCE MISSION: Comprehensive Leadership Team Analysis

PRIMARY TARGET: {company_name}
{context_info}

Your mission is to conduct THOROUGH research on the founding team, executives, and key personnel to provide investment-grade leadership intelligence.

CRITICAL REQUIREMENTS:
1. NEVER return incomplete leadership analysis
2. Research founders' backgrounds, previous companies, track records
3. Analyze leadership team composition and experience diversity
4. Investigate previous successes, failures, and learning experiences
5. Assess leadership credibility and execution capability
6. Always provide strategic assessment of leadership strength

RESEARCH OBJECTIVES:
1. **Founder Background Analysis**:
   - Educational background and expertise areas
   - Previous company experience and roles
   - Track record of successes and failures
   - Industry recognition and thought leadership

2. **Leadership Team Composition**:
   - Key executives and their backgrounds
   - Team diversity and complementary skills
   - Advisory board and investor connections
   - Organizational structure and decision-making

3. **Execution Capability Assessment**:
   - Previous company exits and outcomes
   - Fundraising history and investor relations
   - Product development and go-to-market experience
   - Crisis management and pivot capability

4. **Market Credibility Analysis**:
   - Industry recognition and awards
   - Speaking engagements and thought leadership
   - Media presence and public perception
   - Peer recognition and network strength

RESEARCH STRATEGY:
Phase 1 - Direct Leadership Research:
- Search for "[Founder Name] [Company] background experience"
- Look for LinkedIn profiles, company bios, and press coverage
- Find interviews, podcasts, and speaking engagements

Phase 2 - Track Record Investigation:
- Search for previous companies and roles
- Look for exit outcomes, funding rounds, and achievements
- Find any failures or learning experiences

Phase 3 - Industry Standing Analysis:
- Search for industry recognition, awards, or thought leadership
- Look for media coverage and expert opinions
- Find peer recognition and network connections

Phase 4 - Team Dynamics Assessment:
- Use tavily_extract on team pages for detailed analysis
- Research co-founder relationships and working history
- Analyze team composition for skill complementarity

ADAPTIVE SEARCH STRATEGY:
If direct founder searches yield limited results:
1. Search for company founding story and early team
2. Look for industry interviews or conference presentations
3. Search for academic or professional backgrounds
4. Find any mention in startup ecosystem coverage
5. Research alumni networks or university connections

MANDATORY OUTPUT REQUIREMENTS:
- ALWAYS provide leadership assessment, even with limited direct information
- Analyze leadership strength based on available information
- Include assessment of execution capability and market credibility
- Provide investment implications of leadership team quality
- Never leave leadership analysis incomplete

EXAMPLE SEARCH QUERIES:
- "[Founder Name] founder CEO background experience"
- "[Founder Name] previous company track record"
- "[Company] founding team leadership backgrounds"
- "[Founder Name] interview podcast speaking"
- "[Company] leadership team executives"

OUTPUT STRUCTURE:
For each leader identified, provide:
- Name and current role
- Background summary and key experiences
- Previous companies and outcomes
- Unique value proposition and expertise
- Leadership strengths and potential concerns
- Investment implications assessment
"""
        
        return task
    
    def _extract_agent_output(self, response) -> str:
        """Extract the agent's analysis from the LangGraph response."""
        if hasattr(response, 'messages') and response.messages:
            return response.messages[-1].content
        elif isinstance(response, dict) and 'output' in response:
            return response['output']
        else:
            return str(response)
    
    def _create_founder_profiles(
        self, 
        company_name: str, 
        run_id: str, 
        agent_output: str
    ) -> List[Dict[str, Any]]:
        """Create structured founder profiles from agent analysis."""
        
        # Parse the agent output and create structured profiles
        profiles = []
        
        # Extract key findings from the agent's analysis
        lines = agent_output.split('\n')
        current_profile = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for leadership names or roles
            if any(keyword in line.lower() for keyword in ['ceo', 'founder', 'cto', 'cmo', 'executive']):
                if current_profile:
                    profiles.append(current_profile)
                
                current_profile = {
                    "id": f"founder_{run_id}_{len(profiles)}",
                    "run_id": run_id,
                    "company": company_name,
                    "name": self._extract_name_from_line(line),
                    "role": self._extract_role_from_line(line),
                    "background_summary": "",
                    "previous_experience": [],
                    "key_achievements": [],
                    "investment_assessment": "",
                    "source_confidence": "medium"
                }
            elif current_profile and line:
                # Add details to current profile
                if any(keyword in line.lower() for keyword in ['background', 'experience', 'previous']):
                    current_profile["background_summary"] += f" {line}"
                elif any(keyword in line.lower() for keyword in ['achievement', 'success', 'founded', 'led']):
                    current_profile["key_achievements"].append(line)
                elif any(keyword in line.lower() for keyword in ['assessment', 'investment', 'strength']):
                    current_profile["investment_assessment"] += f" {line}"
        
        # Add the last profile
        if current_profile:
            profiles.append(current_profile)
        
        # If no structured profiles found, create a summary profile
        if not profiles:
            profiles.append({
                "id": f"founder_{run_id}_summary",
                "run_id": run_id,
                "company": company_name,
                "name": "Leadership Team",
                "role": "Collective Analysis",
                "background_summary": agent_output[:500],
                "previous_experience": ["Analysis based on available information"],
                "key_achievements": ["Leadership team analysis completed"],
                "investment_assessment": agent_output[-300:] if len(agent_output) > 300 else agent_output,
                "source_confidence": "medium"
            })
        
        return profiles[:5]  # Limit to top 5 profiles
    
    def _extract_name_from_line(self, line: str) -> str:
        """Extract person name from a line of text."""
        # Simple name extraction logic
        words = line.split()
        for i, word in enumerate(words):
            if word.lower() in ['ceo', 'founder', 'cto', 'cmo']:
                if i > 0:
                    return ' '.join(words[:i]).strip(':-,')
        return "Leadership Team Member"
    
    def _extract_role_from_line(self, line: str) -> str:
        """Extract role/title from a line of text."""
        role_keywords = ['ceo', 'founder', 'cto', 'cmo', 'president', 'director', 'head']
        line_lower = line.lower()
        for keyword in role_keywords:
            if keyword in line_lower:
                return keyword.upper()
        return "Executive"
    
    def _create_fallback_profiles(
        self, 
        company_name: str, 
        run_id: str, 
        error_message: str
    ) -> List[Dict[str, Any]]:
        """Create fallback founder profiles when analysis fails."""
        
        return [{
            "id": f"founder_{run_id}_fallback",
            "run_id": run_id,
            "company": company_name,
            "name": "Leadership Team",
            "role": "Analysis Pending",
            "background_summary": f"Founder Intelligence Agent will provide comprehensive leadership analysis. {error_message}",
            "previous_experience": ["Detailed background research pending"],
            "key_achievements": ["Leadership analysis in progress"],
            "investment_assessment": "Leadership team assessment requires additional research",
            "source_confidence": "low"
        }]
    
    def _extract_structured_founder_output(self, response: Dict[str, Any]) -> FounderOutput:
        """Extract structured output from agent response."""
        
        # Try to get structured response first
        if "structured_response" in response:
            return response["structured_response"]
            
        # Fallback: create from message content
        messages = response.get("messages", [])
        if not messages:
            return self._create_fallback_founder_output()
        
        # Find the last AI message with content
        for message in reversed(messages):
            if hasattr(message, 'content') and message.content:
                try:
                    # Try to parse as JSON if it looks like structured data
                    import json
                    if message.content.strip().startswith('{'):
                        data = json.loads(message.content)
                        return FounderOutput(**data)
                except:
                    pass
                
                # Fallback: parse from text content
                return self._parse_founder_output_from_text(message.content)
        
        return self._create_fallback_founder_output()
    
    def _create_fallback_founder_output(self) -> FounderOutput:
        """Create fallback founder output when parsing fails."""
        from app.models.agent_outputs import FounderProfile
        
        return FounderOutput(
            founder_profiles=[],
            team_composition_analysis="Unable to complete founder analysis",
            leadership_assessment="Leadership analysis pending",
            execution_capability="Assessment unavailable",
            investment_implications="Leadership evaluation requires completion",
            confidence_score=0.3
        )
    
    def _parse_founder_output_from_text(self, content: str) -> FounderOutput:
        """Parse founder output from text content."""
        from app.models.agent_outputs import FounderProfile
        
        # Basic parsing from text content
        founder_profiles = []
        
        # Look for leader names and roles in the text
        lines = content.split('\n')
        current_founder = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for founder/leadership indicators
            if any(keyword in line.lower() for keyword in ['ceo', 'founder', 'cto', 'cmo', 'president']):
                if current_founder:
                    founder_profiles.append(current_founder)
                
                name = self._extract_name_from_line(line)
                role = self._extract_role_from_line(line)
                
                current_founder = FounderProfile(
                    name=name or "Leadership Team Member",
                    role=role or "Executive",
                    background_summary=line,
                    previous_experience=[],
                    key_achievements=[],
                    education_background=None,
                    investment_assessment="Analysis based on text parsing"
                )
            elif current_founder and len(line) > 20:
                # Add content to current founder's background
                if 'background' in line.lower() or 'experience' in line.lower():
                    current_founder.background_summary += f" {line}"
                elif 'achievement' in line.lower() or 'founded' in line.lower():
                    current_founder.key_achievements.append(line)
        
        if current_founder:
            founder_profiles.append(current_founder)
        
        return FounderOutput(
            founder_profiles=founder_profiles[:5],  # Limit profiles
            team_composition_analysis="Analysis based on text parsing",
            leadership_assessment="Medium confidence from text analysis",
            execution_capability="Assessment pending detailed analysis",
            investment_implications="Leadership evaluation based on available content",
            confidence_score=0.6
        )
    
    def _create_founder_profiles_from_structured(self, company_name: str, run_id: str, structured_output: FounderOutput) -> List[Dict[str, Any]]:
        """Create founder profile dictionaries from structured output."""
        
        profiles = []
        
        for i, founder in enumerate(structured_output.founder_profiles):
            profile = {
                "id": f"founder_{run_id}_{i}",
                "run_id": run_id or "unknown",
                "company": company_name,
                "name": founder.name,
                "role": founder.role,
                "background_summary": founder.background_summary,
                "previous_experience": founder.previous_experience,
                "key_achievements": founder.key_achievements,
                "education_background": founder.education_background,
                "investment_assessment": founder.investment_assessment,
                "source_confidence": "high"  # Structured output has higher confidence
            }
            profiles.append(profile)
        
        # If no profiles found, create a summary profile
        if not profiles:
            profiles.append({
                "id": f"founder_{run_id}_summary",
                "run_id": run_id or "unknown",
                "company": company_name,
                "name": "Leadership Team",
                "role": "Executive Team",
                "background_summary": structured_output.team_composition_analysis,
                "previous_experience": [],
                "key_achievements": [],
                "education_background": None,
                "investment_assessment": structured_output.investment_implications,
                "source_confidence": "medium"
            })
            
        return profiles


# Global founder intelligence agent instance
founder_agent = FounderIntelligenceAgent()