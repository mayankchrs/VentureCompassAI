from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal, Annotated
from datetime import datetime
from dataclasses import dataclass, field
from typing_extensions import TypedDict
import operator

def merge_costs(left: Dict[str, int], right: Dict[str, int]) -> Dict[str, int]:
    """Custom reducer to merge cost dictionaries by adding values for matching keys."""
    result = left.copy()
    for key, value in right.items():
        result[key] = result.get(key, 0) + value
    return result

def merge_queries(left: Dict[str, List[str]], right: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Custom reducer to merge query dictionaries by extending lists for matching keys."""
    result = left.copy()
    for key, value in right.items():
        if key in result:
            result[key].extend(value)
        else:
            result[key] = value
    return result

def merge_results(left: Dict[str, List[Any]], right: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
    """Custom reducer to merge results dictionaries by extending lists for matching keys."""
    result = left.copy()
    for key, value in right.items():
        if key in result:
            result[key].extend(value)
        else:
            result[key] = value
    return result

def merge_confidence_scores(left: Dict[str, float], right: Dict[str, float]) -> Dict[str, float]:
    """Custom reducer to merge confidence score dictionaries, taking the maximum value for each key."""
    result = left.copy()
    for key, value in right.items():
        if key in result:
            result[key] = max(result[key], value)  # Take the higher confidence score
        else:
            result[key] = value
    return result

def merge_status(left: str, right: str) -> str:
    """Custom reducer to handle concurrent status updates.
    Priority: error > partial > running > complete > pending"""
    status_priority = {"error": 5, "partial": 4, "running": 3, "complete": 2, "pending": 1}
    left_priority = status_priority.get(left, 0)
    right_priority = status_priority.get(right, 0)
    return left if left_priority >= right_priority else right

def merge_phase(left: str, right: str) -> str:
    """Custom reducer to handle concurrent phase updates.
    Priority: synthesis > verification > research > discovery"""
    phase_priority = {"synthesis": 4, "verification": 3, "research": 2, "discovery": 1}
    left_priority = phase_priority.get(left, 0)
    right_priority = phase_priority.get(right, 0)
    return left if left_priority >= right_priority else right

class RunCreate(BaseModel):
    company: str
    domain: Optional[str] = None

class RunStateDTO(BaseModel):
    run_id: str
    status: Literal["pending", "running", "partial", "complete", "completed", "error"]
    company: Dict[str, Any]
    insights: Optional[List[Dict[str, Any]]] = None
    patents: Optional[List[Dict[str, Any]]] = None
    risks: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    founders: Optional[List[Dict[str, Any]]] = None
    competitive: Optional[Dict[str, Any]] = None
    deepdive: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    cost: Dict[str, Any]
    errors: Optional[List[Dict[str, Any]]] = None

@dataclass
class SourceDoc:
    id: str
    run_id: str
    title: str
    url: str
    snippet: Optional[str]
    published_at: Optional[datetime]
    domain: Optional[str]
    type: Optional[str] = "general"  # news, funding, partnership, etc.

@dataclass
class PatentDoc:
    id: str
    run_id: str
    title: str
    assignee: Optional[str]
    filing_date: Optional[datetime]
    grant_date: Optional[datetime]
    abstract: Optional[str]
    cpc: Optional[List[str]]
    url: str

@dataclass
class RiskItem:
    category: str
    severity: str
    summary: str
    citations: List[str]

@dataclass
class DiscoveryResults:
    """Results from Discovery Agent using Tavily Map API"""
    id: str
    run_id: str
    base_url: str
    discovered_urls: List[str]
    company_aliases: List[str]
    social_media_links: List[str]
    key_pages: Dict[str, str]  # page_type -> url
    llm_analysis: str = ""  # LLM agent's analysis and reasoning
    confidence_score: float = 0.0  # Agent's confidence in findings
    timestamp: datetime = field(default_factory=datetime.utcnow)
    key_insights: List[str] = field(default_factory=list)  # Key strategic insights
    website_analysis: str = ""  # Website structure and content analysis

@dataclass
class DeepDiveResults:
    """Results from DeepDive Agent using Tavily Crawl + Extract APIs"""
    id: str
    run_id: str
    crawled_pages: List[Dict[str, Any]]
    extracted_content: Dict[str, str]  # url -> extracted_text
    team_members: List[Dict[str, Any]]
    company_timeline: List[Dict[str, Any]]
    product_info: Dict[str, Any]
    timestamp: datetime

@dataclass
class VerifiedFact:
    """Verified information with confidence scoring"""
    fact_id: str
    claim: str
    sources: List[str]
    confidence_score: float  # 0.0 to 1.0
    verification_method: str
    conflicting_sources: List[str] = field(default_factory=list)

class RunState(TypedDict):
    run_id: str
    company: Dict[str, Any]
    
    # Phase 1: Discovery
    discovery_results: Optional[DiscoveryResults]
    company_aliases: Annotated[List[str], operator.add]
    
    # Phase 2: Research (enhanced)
    queries: Annotated[Dict[str, List[str]], merge_queries]
    results: Annotated[Dict[str, List[Any]], merge_results]
    deepdive_results: Optional[DeepDiveResults]
    
    # Phase 3: Verification & Synthesis  
    verified_facts: Annotated[List[VerifiedFact], operator.add]
    confidence_scores: Annotated[Dict[str, float], merge_confidence_scores]
    insights: Optional[Dict[str, Any]]
    risks: Optional[List[RiskItem]]
    
    # Metadata
    citations: Annotated[List[str], operator.add]
    cost: Annotated[Dict[str, int], merge_costs]
    status: Annotated[str, merge_status]
    current_phase: Annotated[str, merge_phase]  # discovery | research | verification | synthesis
    errors: Annotated[List[Dict[str, Any]], operator.add]