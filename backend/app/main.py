from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import init_db

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="VentureCompass AI API",
    description="""
    🎯 **AI-powered company intelligence and risk assessment platform**
    
    Generate investor-grade dossiers with comprehensive research using:
    - **6-Agent LangGraph System**: Discovery, Research, Verification & Synthesis
    - **Complete Tavily API Integration**: Map, Search, Crawl & Extract
    - **Multi-phase Analysis**: News, Patents, Deep-dive content analysis
    - **Real-time Processing**: Async workflows with status monitoring
    
    ## 🚀 Quick Start
    1. **Create Analysis**: `POST /api/run/` with company name
    2. **Monitor Progress**: `GET /api/run/{id}` for real-time status
    3. **Export Results**: `GET /api/run/{id}/export.json` for full data
    
    ## 💰 Budget Tracking
    - **Budget Status**: `GET /api/run/budget/status` 
    - **Usage History**: `GET /api/run/budget/history`
    
    ## 🔗 Architecture
    - **Backend**: FastAPI + LangGraph + MongoDB
    - **AI Services**: Tavily Search + OpenAI/Anthropic LLMs
    - **Frontend**: React + TypeScript (port 5173)
    """,
    version="2.0.0",
    lifespan=lifespan,
    contact={
        "name": "VentureCompass AI",
        "url": "https://github.com/mayankchrs/VentureCompassAI",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "VentureCompass AI API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/test-logging")
async def test_logging():
    """Test endpoint to verify logging is working."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 Test logging endpoint accessed!")
    logger.warning("⚠️ This is a warning message")
    logger.error("❌ This is an error message")
    
    print("🖨️ PRINT STATEMENT: Test endpoint accessed!")
    
    return {
        "message": "Logging test completed",
        "timestamp": datetime.utcnow().isoformat(),
        "check_console": "You should see logs above this message"
    }