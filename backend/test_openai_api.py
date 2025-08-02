"""
Test script to verify OpenAI API key configuration.
"""

import os
import asyncio
from openai import AsyncOpenAI
from app.core.config import settings

async def test_openai_api():
    """Test OpenAI API key and basic functionality."""
    
    print("🔍 Testing OpenAI API Configuration...")
    # Check both possible API key locations
    api_key = settings.LLM_API_KEY if settings.LLM_API_KEY != "your-llm-key-here" else settings.OPENAI_API_KEY
    print(f"LLM_API_KEY: {settings.LLM_API_KEY[:20]}..." if settings.LLM_API_KEY else "❌ No LLM_API_KEY found")
    print(f"OPENAI_API_KEY: {settings.OPENAI_API_KEY[:20]}..." if settings.OPENAI_API_KEY else "❌ No OPENAI_API_KEY found")
    print(f"Using API Key: {api_key[:20]}..." if api_key else "❌ No API key available")
    
    # Check environment variable directly
    env_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key from env: {env_key[:20]}..." if env_key else "❌ No API key in environment")
    
    if not api_key or api_key.startswith("your-"):
        print("❌ OpenAI API key is not properly configured!")
        print("Please set LLM_API_KEY in your .env file or environment variables")
        return False
    
    try:
        # Test API connection
        client = AsyncOpenAI(api_key=api_key)
        
        print("🚀 Testing OpenAI API call...")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI API Response: {result}")
        print(f"💰 Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_api())
    if success:
        print("\n🎉 OpenAI API is working correctly!")
    else:
        print("\n💥 OpenAI API configuration failed!")
        print("Please check your API key configuration.")