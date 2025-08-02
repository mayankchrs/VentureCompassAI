"""
Pydantic models for structured agent outputs.
Ensures all LLM agents return consistent, parseable data structures.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DiscoveryOutput(BaseModel):
    """Structured output for Discovery Agent."""
    discovered_urls: List[str] = Field(description="List of discovered URLs for the company")
    company_aliases: List[str] = Field(description="Alternative names and brands for the company")
    confidence_score: float = Field(description="Confidence score from 0.0 to 1.0", ge=0.0, le=1.0)
    digital_presence_summary: str = Field(description="Summary of the company's digital footprint")
    key_insights: List[str] = Field(description="Key strategic insights from discovery analysis")
    website_analysis: str = Field(description="Analysis of the main website structure and content")


class NewsItem(BaseModel):
    """Individual news item found by News Agent."""
    headline: str = Field(description="News headline or title")
    content: str = Field(description="News content or summary")
    url: Optional[str] = Field(description="Source URL if available", default="")
    relevance_score: float = Field(description="Relevance score from 0.0 to 1.0", ge=0.0, le=1.0, default=0.5)
    news_type: str = Field(description="Type of news (funding, partnership, product, etc.)", default="general")
    date_mentioned: Optional[str] = Field(description="Date mentioned in the content if found", default=None)


class NewsOutput(BaseModel):
    """Structured output for News Agent."""
    news_items: List[NewsItem] = Field(description="List of relevant news items found")
    funding_signals: List[str] = Field(description="Funding-related signals discovered")
    partnership_signals: List[str] = Field(description="Partnership and collaboration signals")
    market_signals: List[str] = Field(description="Market position and competitive signals")
    investment_implications: str = Field(description="Summary of investment implications")
    confidence_assessment: str = Field(description="Assessment of information confidence and gaps")


class FounderProfile(BaseModel):
    """Individual founder/executive profile."""
    name: str = Field(description="Full name of the person")
    role: str = Field(description="Current role/title at the company")
    background_summary: str = Field(description="Summary of professional background")
    previous_experience: List[str] = Field(description="List of previous roles and companies")
    key_achievements: List[str] = Field(description="Notable achievements and accomplishments")
    education_background: Optional[str] = Field(description="Educational background if found")
    investment_assessment: str = Field(description="Assessment of leadership capability for investment")


class FounderOutput(BaseModel):
    """Structured output for Founder Agent."""
    founder_profiles: List[FounderProfile] = Field(description="Profiles of founders and key executives")
    team_composition_analysis: str = Field(description="Analysis of team composition and strengths")
    leadership_assessment: str = Field(description="Overall leadership team assessment")
    execution_capability: str = Field(description="Assessment of team's execution capability")
    investment_implications: str = Field(description="Investment implications of leadership analysis")
    confidence_score: float = Field(description="Confidence in leadership analysis", ge=0.0, le=1.0)


class Competitor(BaseModel):
    """Individual competitor analysis."""
    name: str = Field(description="Competitor company name")
    category: str = Field(description="Type of competitor (direct, indirect, substitute)")
    description: str = Field(description="Description of competitor and their offering")
    strengths: List[str] = Field(description="Competitor's key strengths")
    market_position: str = Field(description="Market position assessment")
    funding_status: Optional[str] = Field(description="Funding status if known")


class CompetitiveOutput(BaseModel):
    """Structured output for Competitive Intelligence Agent."""
    competitors: List[Competitor] = Field(description="List of identified competitors")
    market_positioning: str = Field(description="Company's market positioning analysis")
    competitive_advantages: List[str] = Field(description="Company's competitive advantages")
    market_threats: List[str] = Field(description="Identified market threats and risks")
    market_opportunities: List[str] = Field(description="Identified market opportunities")
    market_insights: List[str] = Field(description="Key market insights and trends")
    competitive_assessment: str = Field(description="Overall competitive position assessment")
    investment_implications: str = Field(description="Investment implications of competitive analysis")


class PatentRecord(BaseModel):
    """Individual patent record."""
    title: str = Field(description="Patent title")
    abstract: str = Field(description="Patent abstract or summary")
    assignee: str = Field(description="Patent assignee/owner")
    filing_date: Optional[str] = Field(description="Patent filing date if found")
    patent_number: Optional[str] = Field(description="Patent number if available")
    technology_area: str = Field(description="Technology area or domain")
    strategic_value: str = Field(description="Assessment of strategic value")


class PatentOutput(BaseModel):
    """Structured output for Patent Intelligence Agent."""
    patent_records: List[PatentRecord] = Field(description="List of relevant patents found")
    ip_portfolio_analysis: str = Field(description="Analysis of intellectual property portfolio")
    technology_focus_areas: List[str] = Field(description="Key technology focus areas")
    innovation_assessment: str = Field(description="Assessment of innovation and R&D capability")
    competitive_ip_landscape: str = Field(description="Competitive IP landscape analysis")
    investment_implications: str = Field(description="Investment implications of IP analysis")
    ip_strength_assessment: str = Field(description="Assessment of IP strength and defensibility")
    confidence_score: float = Field(description="Confidence in patent analysis", ge=0.0, le=1.0)


class ContentSource(BaseModel):
    """Individual content source analyzed."""
    url: str = Field(description="Source URL")
    title: str = Field(description="Page or content title")
    content_type: str = Field(description="Type of content (webpage, document, etc.)")
    key_insights: List[str] = Field(description="Key insights extracted from content")
    relevance_score: float = Field(description="Relevance score from 0.0 to 1.0", ge=0.0, le=1.0)


class DeepDiveOutput(BaseModel):
    """Structured output for DeepDive Content Agent."""
    content_sources: List[ContentSource] = Field(description="List of analyzed content sources")
    company_mission_vision: str = Field(description="Company mission and vision analysis")
    business_model_insights: str = Field(description="Business model and strategy insights")
    product_analysis: str = Field(description="Product portfolio and technology analysis")
    market_approach: str = Field(description="Go-to-market and customer approach analysis")
    organizational_insights: str = Field(description="Organizational structure and culture insights")
    growth_indicators: List[str] = Field(description="Evidence of growth and traction")
    investment_insights: str = Field(description="Key investment insights from content analysis")
    confidence_score: float = Field(description="Overall confidence in analysis", ge=0.0, le=1.0)


class VerifiedFact(BaseModel):
    """Individual verified fact."""
    claim: str = Field(description="The claim or fact being verified")
    verification_status: str = Field(description="Verification status (verified, unverified, conflicting)")
    confidence_score: float = Field(description="Confidence in verification", ge=0.0, le=1.0)
    sources: List[str] = Field(description="Sources supporting or contradicting the claim")
    notes: Optional[str] = Field(description="Additional verification notes")


class VerificationOutput(BaseModel):
    """Structured output for Verification Intelligence Agent."""
    verified_facts: List[VerifiedFact] = Field(description="List of verified facts and claims")
    inconsistencies_found: List[str] = Field(description="Inconsistencies discovered across sources")
    information_gaps: List[str] = Field(description="Identified information gaps requiring attention")
    red_flags: List[str] = Field(description="Potential red flags or concerns identified")
    source_reliability_assessment: str = Field(description="Assessment of source reliability")
    overall_reliability_score: float = Field(description="Overall reliability score", ge=0.0, le=1.0)
    verification_summary: str = Field(description="Summary of verification findings")
    investment_risk_factors: List[str] = Field(description="Investment risk factors identified")


class SynthesisOutput(BaseModel):
    """Structured output for Synthesis Agent."""
    executive_summary: str = Field(description="Professional executive summary for investors (2-3 sentences)")
    investment_signals: List[str] = Field(description="Key investment signals and opportunities identified")
    risk_assessment: List[str] = Field(description="Specific investment risks and concerns identified")
    funding_events: List[str] = Field(description="Funding events or financial milestones discovered")
    partnerships: List[str] = Field(description="Strategic partnerships and collaborations identified")
    market_positioning: str = Field(description="Market positioning and competitive advantage assessment")
    confidence_score: float = Field(description="Overall confidence in analysis", ge=0.0, le=1.0)
    investment_recommendation: str = Field(description="Investment recommendation based on analysis")