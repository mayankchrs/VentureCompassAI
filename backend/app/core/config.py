from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    ENV: str = "dev"
    MONGODB_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "venture_compass"
    TAVILY_API_KEY: str = "your-tavily-key-here"
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str = "your-llm-key-here"
    OPENAI_API_KEY: str = "your-openai-key-here"  # Explicit OpenAI key
    S3_BUCKET: Optional[str] = None
    COST_CAP_TAVILY_CREDITS: int = 20
    RUN_CACHE_TTL_HOURS: int = 24
    MAX_BUDGET_USD: float = 10.0  # Hard budget limit
    
    class Config:
        env_file = ".env"

settings = Settings()