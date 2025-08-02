from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import uuid
from datetime import datetime
from bson import ObjectId

from app.models.schemas import RunCreate, RunStateDTO
from app.core.database import get_database
from app.core.budget_tracker import budget_tracker
from app.agents.llm_orchestrator import run_llm_analysis

router = APIRouter()


def convert_objectid_to_str(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB ObjectId objects to strings for JSON serialization."""
    if doc is None:
        return doc
    
    converted = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            converted[key] = str(value)
        elif isinstance(value, dict):
            converted[key] = convert_objectid_to_str(value)
        elif isinstance(value, list):
            converted[key] = [convert_objectid_to_str(item) if isinstance(item, dict) else str(item) if isinstance(item, ObjectId) else item for item in value]
        else:
            converted[key] = value
    return converted


def convert_documents_list(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert a list of MongoDB documents, handling ObjectIds."""
    return [convert_objectid_to_str(doc) for doc in docs]

@router.post("/", 
             response_model=Dict[str, str],
             summary="Create Company Analysis Run",
             description="""
             🤖 **Start comprehensive LLM-powered company intelligence analysis**
             
             This endpoint triggers a 6-agent LangGraph workflow using **GPT-4o** for decision-making:
             - **Discovery Agent**: LLM plans and executes digital footprint mapping (Tavily Map as tool)
             - **News Agent**: LLM generates strategic queries and analyzes relevance (Tavily Search as tool) 
             - **Patent Agent**: LLM develops IP research strategy and evaluates portfolio strength (coming soon)
             - **DeepDive Agent**: LLM prioritizes content and extracts structured insights (coming soon)
             - **Verification Agent**: LLM cross-validates facts and generates confidence scores (coming soon)
             - **Synthesis Agent**: LLM creates professional investment intelligence reports
             
             **True Generative AI**: Each agent uses LLM reasoning for planning, decision-making, and analysis.
             
             **Processing**: Runs asynchronously in background, use GET /{run_id} to monitor progress.
             
             **Budget**: Tracks Tavily + GPT-4o costs in real-time with $10 hard limit.
             """,
             tags=["Company Analysis"])
async def create_run(run_data: RunCreate, background_tasks: BackgroundTasks):
    run_id = f"r_{uuid.uuid4().hex[:8]}"
    
    db = get_database()
    
    run_doc = {
        "run_id": run_id,
        "company": {"name": run_data.company, "domain": run_data.domain},
        "status": "pending",
        "created_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
        "cost": {"tavily_credits": 0, "llm_tokens": 0, "openai_usd": 0.0},
        "errors": []
    }
    
    await db.runs.insert_one(run_doc)
    
    background_tasks.add_task(run_llm_analysis, run_id, run_data.company, run_data.domain)
    
    return {"run_id": run_id, "status": "running"}

@router.get("/{run_id}", 
            response_model=RunStateDTO,
            summary="Get Analysis Results & Status",
            description="""
            📊 **Retrieve comprehensive analysis results and real-time status**
            
            Returns complete analysis data including:
            - **Status**: pending, running, completed, error, partial
            - **Insights**: Executive summary, investment signals, risk assessment
            - **Sources**: News articles, patents, verified content
            - **Costs**: Detailed breakdown of Tavily credits and LLM usage
            - **Errors**: Any issues encountered during processing
            
            **Real-time**: Poll this endpoint to monitor analysis progress.
            
            **Data Sources**: Aggregated from news (Tavily), patents (search), and deep-dive content extraction.
            """,
            tags=["Company Analysis"])
async def get_run(run_id: str):
    db = get_database()
    
    run_doc = await db.runs.find_one({"run_id": run_id})
    if not run_doc:
        raise HTTPException(status_code=404, detail="Run not found")
    
    insights = await db.insights.find({"run_id": run_id}).to_list(None)
    patents = await db.patents.find({"run_id": run_id}).to_list(None)
    risks = await db.risks.find({"run_id": run_id}).to_list(None)
    sources = await db.sources.find({"run_id": run_id}).to_list(None)
    founders = await db.founders.find({"run_id": run_id}).to_list(None)
    competitive_analysis = await db.competitive_analysis.find_one({"run_id": run_id})
    deepdive_analysis = await db.deepdive_analysis.find_one({"run_id": run_id})
    verification_analysis = await db.verification_analysis.find_one({"run_id": run_id})
    
    # Convert MongoDB ObjectIds to strings for JSON serialization
    converted_run_doc = convert_objectid_to_str(run_doc)
    converted_insights = convert_documents_list(insights)
    converted_patents = convert_documents_list(patents)
    converted_risks = convert_documents_list(risks)
    converted_sources = convert_documents_list(sources)
    converted_founders = convert_documents_list(founders)
    converted_competitive = convert_objectid_to_str(competitive_analysis) if competitive_analysis else None
    converted_deepdive = convert_objectid_to_str(deepdive_analysis) if deepdive_analysis else None
    converted_verification = convert_objectid_to_str(verification_analysis) if verification_analysis else None
    
    return RunStateDTO(
        run_id=converted_run_doc["run_id"],
        status=converted_run_doc["status"],
        company=converted_run_doc["company"],
        insights=converted_insights,
        patents=converted_patents,
        risks=converted_risks,
        sources=converted_sources,
        founders=converted_founders,
        competitive=converted_competitive,
        deepdive=converted_deepdive,
        verification=converted_verification,
        cost=converted_run_doc["cost"],
        errors=converted_run_doc.get("errors", [])
    )

@router.get("/{run_id}/export.json",
            summary="Export Complete Analysis Data",
            description="""
            📋 **Export full analysis dataset in JSON format**
            
            Provides complete raw data dump including:
            - **Run Metadata**: Created, started, completed timestamps
            - **All Sources**: Raw news articles, patent documents, extracted content
            - **Detailed Insights**: Complete analysis with confidence scores
            - **Cost Breakdown**: Granular usage tracking
            - **Verification Data**: Cross-validated facts and evidence
            
            **Use Cases**: 
            - Data analysis and research
            - Integration with external systems
            - Audit trails and compliance
            - Custom reporting and visualization
            """,
            tags=["Data Export"])
async def export_run(run_id: str):
    db = get_database()
    
    run_doc = await db.runs.find_one({"run_id": run_id})
    if not run_doc:
        raise HTTPException(status_code=404, detail="Run not found")
    
    insights = await db.insights.find({"run_id": run_id}).to_list(None)
    patents = await db.patents.find({"run_id": run_id}).to_list(None)
    risks = await db.risks.find({"run_id": run_id}).to_list(None)
    sources = await db.sources.find({"run_id": run_id}).to_list(None)
    
    return {
        "run_id": run_id,
        "company": run_doc["company"],
        "status": run_doc["status"],
        "insights": insights,
        "patents": patents,
        "risks": risks,
        "sources": sources,
        "cost": run_doc["cost"],
        "created_at": run_doc["created_at"],
        "completed_at": run_doc.get("completed_at")
    }

@router.get("/budget/status",
            summary="Get Real-time Budget Status", 
            description="""
            💰 **Monitor API usage and budget consumption in real-time**
            
            Returns current budget status including:
            - **Total Spend**: Current USD expenditure across all services
            - **Remaining Budget**: Available funds before hitting limits
            - **Service Breakdown**: Tavily credits vs LLM costs
            - **Usage Trends**: Recent consumption patterns
            - **Budget Alerts**: Warnings when approaching limits
            
            **Budget Controls**: 
            - $10 hard limit for interview assignment
            - Automatic throttling when approaching caps
            - Cost-per-operation tracking
            """,
            tags=["Budget Management"])
async def get_budget_status():
    """Get real-time budget status and usage statistics."""
    budget_status = await budget_tracker.get_budget_status()
    return budget_status

@router.get("/budget/history",
            summary="Get Budget Usage History",
            description="""
            📈 **View detailed historical budget consumption data**
            
            Provides comprehensive usage analytics:
            - **Transaction History**: Last 50 operations with timestamps
            - **Cost per Operation**: Individual API call costs
            - **Usage Patterns**: Trends over time
            - **Service Attribution**: Which agents/APIs consumed budget
            - **Run Correlation**: Link spending to specific analysis runs
            
            **Analytics**: Use for cost optimization and usage forecasting.
            """,
            tags=["Budget Management"])
async def get_budget_history():
    """Get detailed budget usage history."""
    db = get_database()
    history = await db.budget_tracking.find().sort("timestamp", -1).limit(50).to_list(50)
    
    return {
        "history": history,
        "total_operations": len(history)
    }