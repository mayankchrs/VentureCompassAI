import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.core.database import generate_cache_key, get_from_cache, set_cache
import logging
import asyncio
from datetime import datetime, timedelta
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class TavilyClient:
    def __init__(self, api_key: str):
        self.session = httpx.AsyncClient(
            base_url="https://api.tavily.com",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
        # Rate limiting state
        self._last_request_time = 0
        self._request_count = 0
        self._reset_time = time.time() + 60  # Rate limit window
        self._max_requests_per_minute = 30  # Conservative rate limit
    
    async def _rate_limit_check(self):
        """Implement intelligent rate limiting with backoff."""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time >= self._reset_time:
            self._request_count = 0
            self._reset_time = current_time + 60
        
        # Check if we've hit the rate limit
        if self._request_count >= self._max_requests_per_minute:
            sleep_time = self._reset_time - current_time
            logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time + 1)  # Add 1 second buffer
            self._request_count = 0
            self._reset_time = time.time() + 60
        
        # Implement minimum delay between requests
        min_delay = 1.0  # 1 second between requests
        time_since_last = current_time - self._last_request_time
        if time_since_last < min_delay:
            delay = min_delay - time_since_last
            await asyncio.sleep(delay)
        
        self._request_count += 1
        self._last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError))
    )
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make rate-limited HTTP request with intelligent backoff."""
        await self._rate_limit_check()
        
        try:
            response = await self.session.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                retry_after = int(e.response.headers.get("Retry-After", 60))
                logger.warning(f"API rate limited, waiting {retry_after} seconds")
                await asyncio.sleep(retry_after)
                raise  # Retry with tenacity
            elif e.response.status_code >= 500:  # Server error
                logger.warning(f"Server error {e.response.status_code}, retrying")
                raise  # Retry with tenacity
            else:
                logger.error(f"API error {e.response.status_code}: {e.response.text}")
                raise  # Don't retry for client errors
        except httpx.RequestError as e:
            logger.warning(f"Request error: {e}, retrying")
            raise  # Retry with tenacity

    async def search(
        self,
        query: str,
        topic: str = "news",
        depth: str = "basic",
        time_range: str = "month",
        max_results: int = 10,
        include_answer: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        cache_ttl: int = 24
    ) -> Dict[str, Any]:
        # Generate cache key for this search
        cache_params = {
            "query": query,
            "topic": topic,
            "depth": depth,
            "time_range": time_range,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains
        }
        cache_key = generate_cache_key("tavily_search", cache_params)
        
        # Try cache first
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for search query: {query[:50]}...")
            return cached_result
        
        # Make API call
        payload = {
            "query": query,
            "topic": topic,
            "search_depth": depth,
            "time_range": time_range,
            "max_results": max_results,
            "include_answer": include_answer,
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        logger.info(f"Cache miss - making Tavily search API call for: {query[:50]}...")
        result = await self._make_request("POST", "/search", json=payload)
        
        # Cache the result
        await set_cache(cache_key, result, cache_ttl)
        return result

    async def extract(self, urls: List[str], depth: str = "basic", cache_ttl: int = 24) -> Dict[str, Any]:
        # Generate cache key
        cache_params = {"urls": sorted(urls), "depth": depth}
        cache_key = generate_cache_key("tavily_extract", cache_params)
        
        # Try cache first
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for extract: {len(urls)} URLs")
            return cached_result
        
        payload = {
            "urls": urls,
            "extraction_depth": depth
        }
        
        logger.info(f"Cache miss - making Tavily extract API call for {len(urls)} URLs")
        result = await self._make_request("POST", "/extract", json=payload, timeout=60.0)
        
        # Cache the result
        await set_cache(cache_key, result, cache_ttl)
        return result

    async def map(
        self,
        url: str,
        max_depth: int = 2,
        limit: int = 20,
        select_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        cache_ttl: int = 24
    ) -> Dict[str, Any]:
        """
        Map website structure and discover key pages using Tavily Map API
        """
        # Generate cache key
        cache_params = {
            "url": url,
            "max_depth": max_depth,
            "limit": limit,
            "select_domains": select_domains,
            "exclude_domains": exclude_domains
        }
        cache_key = generate_cache_key("tavily_map", cache_params)
        
        # Try cache first
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for map: {url}")
            return cached_result
        
        payload = {
            "url": url,
            "max_depth": max_depth,
            "limit": limit
        }
        
        if select_domains:
            payload["select_domains"] = select_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        logger.info(f"Cache miss - making Tavily map API call for: {url}")
        result = await self._make_request("POST", "/map", json=payload, timeout=45.0)
        
        # Cache the result
        await set_cache(cache_key, result, cache_ttl)
        return result

    async def crawl(
        self,
        url: str,
        max_depth: int = 1,
        limit: int = 50,
        max_breadth: int = 20,
        select_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        cache_ttl: int = 24
    ) -> Dict[str, Any]:
        """
        Crawl multiple pages from a website using Tavily Crawl API
        """
        # Generate cache key
        cache_params = {
            "url": url,
            "max_depth": max_depth,
            "limit": limit,
            "max_breadth": max_breadth,
            "select_paths": select_paths,
            "exclude_paths": exclude_paths,
            "categories": categories
        }
        cache_key = generate_cache_key("tavily_crawl", cache_params)
        
        # Try cache first
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for crawl: {url}")
            return cached_result
        
        payload = {
            "url": url,
            "max_depth": max_depth,
            "limit": limit,
            "max_breadth": max_breadth
        }
        
        if select_paths:
            payload["select_paths"] = select_paths
        if exclude_paths:
            payload["exclude_paths"] = exclude_paths
        if categories:
            payload["categories"] = categories
        
        logger.info(f"Cache miss - making Tavily crawl API call for: {url}")
        result = await self._make_request("POST", "/crawl", json=payload, timeout=90.0)
        
        # Cache the result
        await set_cache(cache_key, result, cache_ttl)
        return result

    async def close(self):
        await self.session.aclose()

tavily_client = TavilyClient(settings.TAVILY_API_KEY)