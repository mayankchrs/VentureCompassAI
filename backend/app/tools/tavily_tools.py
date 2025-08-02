"""
Tavily API tools for LangGraph agents.
These tools allow LLM agents to use Tavily's APIs for web research.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.tavily_client import tavily_client
from app.core.budget_tracker import budget_tracker

logger = logging.getLogger(__name__)


class TavilyMapInput(BaseModel):
    """Input schema for Tavily Map tool."""
    url: str = Field(description="The website URL to map and explore")
    max_depth: int = Field(default=2, description="Maximum depth to crawl (1-3)")
    limit: int = Field(default=10, description="Maximum number of URLs to return")


class TavilySearchInput(BaseModel):
    """Input schema for Tavily Search tool."""
    query: str = Field(description="The search query to execute")
    topic: str = Field(default="general", description="Search topic: 'general', 'news', or 'finance'")
    depth: str = Field(default="basic", description="Search depth: 'basic' or 'advanced'")
    time_range: str = Field(default="month", description="Time range: 'day', 'week', 'month', 'year'")
    max_results: int = Field(default=5, description="Maximum number of results to return")


class TavilyExtractInput(BaseModel):
    """Input schema for Tavily Extract tool."""
    urls: List[str] = Field(description="List of URLs to extract content from")
    depth: str = Field(default="basic", description="Extraction depth: 'basic' or 'advanced'")


class TavilyCrawlInput(BaseModel):
    """Input schema for Tavily Crawl tool."""
    url: str = Field(description="The base URL to start crawling from")
    max_depth: int = Field(default=1, description="Maximum crawl depth")
    limit: int = Field(default=20, description="Maximum number of pages to crawl")


class TavilyMapTool(BaseTool):
    """Tool for mapping website structure using Tavily Map API."""
    
    name: str = "tavily_map"
    description: str = """
    Map and discover the structure of a website. Use this to:
    - Find all pages and sections of a company website
    - Discover social media links and key pages
    - Understand the digital footprint of a company
    - Get an overview of available content before deep diving
    
    Best for: Initial company discovery and website exploration.
    """
    args_schema: type[BaseModel] = TavilyMapInput

    async def _arun(self, url: str, max_depth: int = 2, limit: int = 10) -> str:
        """Map website structure using Tavily Map API."""
        try:
            # Check budget (warning only, continue regardless)
            await budget_tracker.check_budget(1.0)  # Logs warning but continues
            
            logger.info(f"Mapping website structure for {url}")
            
            response = await tavily_client.map(
                url=url,
                max_depth=max_depth,
                limit=limit
            )
            
            # Track actual cost (Tavily credits, not USD)
            await budget_tracker.record_cost(
                "tavily_map", 0.01, 1,  # Much lower cost for Tavily API
                {"url": url, "depth": max_depth, "limit": limit}
            )
            
            if not response.get("results"):
                return f"No pages found for {url}. The website may be inaccessible or have restrictions."
            
            # Format results for LLM consumption
            discovered_urls = response["results"][:limit]
            
            # Categorize discovered pages
            categorized = {
                "about_pages": [],
                "team_pages": [],
                "product_pages": [],
                "blog_pages": [],
                "career_pages": [],
                "other_pages": []
            }
            
            for discovered_url in discovered_urls:
                url_lower = discovered_url.lower()
                if any(keyword in url_lower for keyword in ["about", "company", "story"]):
                    categorized["about_pages"].append(discovered_url)
                elif any(keyword in url_lower for keyword in ["team", "leadership", "founder", "people"]):
                    categorized["team_pages"].append(discovered_url)
                elif any(keyword in url_lower for keyword in ["product", "service", "solution", "feature"]):
                    categorized["product_pages"].append(discovered_url)
                elif any(keyword in url_lower for keyword in ["blog", "news", "article", "post"]):
                    categorized["blog_pages"].append(discovered_url)
                elif any(keyword in url_lower for keyword in ["career", "job", "hiring", "work"]):
                    categorized["career_pages"].append(discovered_url)
                else:
                    categorized["other_pages"].append(discovered_url)
            
            result = f"Website mapping for {url} found {len(discovered_urls)} pages:\n\n"
            
            for category, urls in categorized.items():
                if urls:
                    category_name = category.replace("_", " ").title()
                    result += f"{category_name}: {len(urls)} pages\n"
                    for url in urls[:3]:  # Show top 3 per category
                        result += f"  - {url}\n"
                    if len(urls) > 3:
                        result += f"  - ... and {len(urls) - 3} more\n"
                    result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Tavily Map tool error: {e}")
            return f"Error mapping website: {str(e)}"

    def _run(self, url: str, max_depth: int = 2, limit: int = 10) -> str:
        """Sync version - not implemented for async tool."""
        return "This tool requires async execution."


class TavilySearchTool(BaseTool):
    """Tool for searching the web using Tavily Search API."""
    
    name: str = "tavily_search"
    description: str = """
    Search the web for specific information. Use this to:
    - Find recent news about companies, funding, partnerships
    - Search for patents and intellectual property information
    - Discover industry information and market trends
    - Find specific information about people, products, or events
    
    Best for: Targeted information gathering and fact-finding.
    """
    args_schema: type[BaseModel] = TavilySearchInput

    async def _arun(
        self, 
        query: str, 
        topic: str = "general",
        depth: str = "basic",
        time_range: str = "month",
        max_results: int = 5
    ) -> str:
        """Search the web using Tavily Search API."""
        try:
            # Check budget (warning only, continue regardless)
            await budget_tracker.check_budget(1.0)  # Logs warning but continues
            
            logger.info(f"Searching for: {query}")
            
            response = await tavily_client.search(
                query=query,
                topic=topic,
                depth=depth,
                time_range=time_range,
                max_results=max_results
            )
            
            # Track actual cost (Tavily credits, not USD)
            await budget_tracker.record_cost(
                "tavily_search", 0.01, 1,  # Much lower cost for Tavily API
                {"query": query, "topic": topic, "max_results": max_results}
            )
            
            results = response.get("results", [])
            if not results:
                return f"No results found for query: {query}"
            
            # Format results for LLM consumption
            formatted_results = f"Search results for '{query}' ({len(results)} results):\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("url", "No URL")
                content = result.get("content", "No content")[:300] + "..."
                score = result.get("score", 0)
                
                formatted_results += f"{i}. {title}\n"
                formatted_results += f"   URL: {url}\n"
                formatted_results += f"   Relevance: {score:.2f}\n"
                formatted_results += f"   Summary: {content}\n\n"
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Tavily Search tool error: {e}")
            return f"Error searching: {str(e)}"

    def _run(
        self, 
        query: str, 
        topic: str = "general",
        depth: str = "basic", 
        time_range: str = "month",
        max_results: int = 5
    ) -> str:
        """Sync version - not implemented for async tool."""
        return "This tool requires async execution."


class TavilyExtractTool(BaseTool):
    """Tool for extracting clean content from web pages using Tavily Extract API."""
    
    name: str = "tavily_extract"
    description: str = """
    Extract clean, structured content from specific web pages. Use this to:
    - Get full text content from company pages, articles, or documents
    - Extract structured information like team members, product details
    - Pull clean content for analysis without HTML noise
    - Get detailed information from discovered URLs
    
    Best for: Deep content analysis and information extraction.
    """
    args_schema: type[BaseModel] = TavilyExtractInput

    async def _arun(self, urls: List[str], depth: str = "basic") -> str:
        """Extract content from URLs using Tavily Extract API."""
        try:
            # Check budget (warning only, continue regardless)
            await budget_tracker.check_budget(1.0)  # Logs warning but continues
            
            # Limit URLs to prevent budget overrun
            limited_urls = urls[:5]
            logger.info(f"Extracting content from {len(limited_urls)} URLs")
            
            response = await tavily_client.extract(
                urls=limited_urls,
                depth=depth
            )
            
            # Track actual cost (Tavily credits, not USD)
            await budget_tracker.record_cost(
                "tavily_extract", 0.01, 1,  # Much lower cost for Tavily API
                {"urls_count": len(limited_urls), "depth": depth}
            )
            
            results = response.get("results", [])
            if not results:
                return f"No content extracted from URLs: {limited_urls}"
            
            # Format extracted content for LLM consumption
            formatted_content = f"Extracted content from {len(results)} pages:\n\n"
            
            for i, result in enumerate(results, 1):
                url = result.get("url", "Unknown URL")
                content = result.get("raw_content", "No content available")
                
                # Truncate very long content
                if len(content) > 2000:
                    content = content[:2000] + "... [truncated]"
                
                formatted_content += f"Page {i}: {url}\n"
                formatted_content += f"Content:\n{content}\n"
                formatted_content += "-" * 50 + "\n\n"
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"Tavily Extract tool error: {e}")
            return f"Error extracting content: {str(e)}"

    def _run(self, urls: List[str], depth: str = "basic") -> str:
        """Sync version - not implemented for async tool."""
        return "This tool requires async execution."


class TavilyCrawlTool(BaseTool):
    """Tool for crawling multiple pages from a website using Tavily Crawl API."""
    
    name: str = "tavily_crawl"
    description: str = """
    Crawl multiple pages from a website to gather comprehensive information. Use this to:
    - Systematically explore all pages of a company website
    - Gather comprehensive content from multiple related pages
    - Build a complete picture of a company's online presence
    - Collect structured data from interconnected pages
    
    Best for: Comprehensive website analysis and bulk content gathering.
    """
    args_schema: type[BaseModel] = TavilyCrawlInput

    async def _arun(self, url: str, max_depth: int = 1, limit: int = 20) -> str:
        """Crawl website pages using Tavily Crawl API."""
        try:
            # Check budget (warning only, continue regardless)
            await budget_tracker.check_budget(2.0)  # Logs warning but continues
            
            logger.info(f"Crawling website {url} with depth {max_depth}")
            
            response = await tavily_client.crawl(
                url=url,
                max_depth=max_depth,
                limit=limit
            )
            
            # Track actual cost (Tavily credits, not USD)
            await budget_tracker.record_cost(
                "tavily_crawl", 0.02, 1,  # Much lower cost for Tavily API
                {"url": url, "max_depth": max_depth, "limit": limit}
            )
            
            results = response.get("results", [])
            if not results:
                return f"No pages crawled from {url}"
            
            # Format crawled content for LLM consumption
            formatted_content = f"Crawled {len(results)} pages from {url}:\n\n"
            
            for i, result in enumerate(results, 1):
                page_url = result.get("url", "Unknown URL")
                content = result.get("content", "No content")
                
                # Truncate long content
                if len(content) > 1500:
                    content = content[:1500] + "... [truncated]"
                
                formatted_content += f"Page {i}: {page_url}\n"
                formatted_content += f"Content Preview:\n{content}\n"
                formatted_content += "-" * 40 + "\n\n"
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"Tavily Crawl tool error: {e}")
            return f"Error crawling website: {str(e)}"

    def _run(self, url: str, max_depth: int = 1, limit: int = 20) -> str:
        """Sync version - not implemented for async tool."""
        return "This tool requires async execution."


# Tool instances for use in agents
tavily_tools = [
    TavilyMapTool(),
    TavilySearchTool(),
    TavilyExtractTool(),
    TavilyCrawlTool()
]