"""
Test script for the Discovery Agent to verify LLM integration works correctly.
"""

import asyncio
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.agents.discovery_agent import discovery_agent
from app.core.config import settings

async def test_discovery_agent():
    """Test the Discovery Agent with a simple company."""
    
    print("Testing Discovery Agent...")
    print(f"OpenAI API Key configured: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
    print(f"Tavily API Key configured: {'Yes' if settings.TAVILY_API_KEY else 'No'}")
    
    # Test with a well-known company
    company_name = "Anthropic"
    company_domain = "anthropic.com"
    
    print(f"\nTesting discovery for: {company_name}")
    print(f"Domain: {company_domain}")
    
    try:
        # Run the discovery agent
        results = await discovery_agent.discover_company(
            company_name=company_name,
            company_domain=company_domain,
            run_id="test_001"
        )
        
        print(f"\n=== DISCOVERY RESULTS ===")
        print(f"Company: {company_name}")
        print(f"Base URL: {results.base_url}")
        print(f"URLs Found: {len(results.discovered_urls)}")
        print(f"Company Aliases: {results.company_aliases}")
        print(f"Key Pages: {results.key_pages}")
        print(f"Confidence Score: {results.confidence_score:.2f}")
        
        print(f"\n=== LLM ANALYSIS ===")
        print(results.llm_analysis[:500] + "..." if len(results.llm_analysis) > 500 else results.llm_analysis)
        
        if results.discovered_urls:
            print(f"\n=== DISCOVERED URLS (first 5) ===")
            for i, url in enumerate(results.discovered_urls[:5]):
                print(f"{i+1}. {url}")
        
        print(f"\n✅ Discovery Agent test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Discovery Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_discovery_agent())
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)