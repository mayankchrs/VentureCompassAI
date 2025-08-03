from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import Dict, Any, List
import uuid
from datetime import datetime
from bson import ObjectId
import logging
import json
import io

from app.models.schemas import RunCreate, RunStateDTO
from app.core.database import get_database
from app.core.budget_tracker import budget_tracker
from app.agents.llm_orchestrator import run_llm_analysis

router = APIRouter()

logger = logging.getLogger(__name__)

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
             🤖 **Start comprehensive AI-powered company intelligence analysis**
             
             This endpoint triggers an **8-agent LangGraph workflow** showcasing complete Tavily API integration:
             
             **Phase 1: Discovery**
             - **Discovery Agent**: Digital footprint mapping (Tavily Map API)
             
             **Phase 2: Parallel Research (Fan-out)**
             - **News Agent**: Recent news analysis (Tavily Search API)
             - **Founder Agent**: Leadership team research (Tavily Search API)
             - **Competitive Agent**: Market landscape analysis (Tavily Search API)
             - **Patent Agent**: IP portfolio research (Tavily Search API)
             - **DeepDive Agent**: Content extraction (Tavily Crawl + Extract APIs)
             
             **Phase 3: Verification & Synthesis (Fan-in)**
             - **Verification Agent**: Cross-source validation with confidence scoring
             - **Synthesis Agent**: Professional investment reports (GPT-4o)
             
             **Advanced LangGraph**: Multi-phase coordination with conditional routing and state sharing.
             
             **Processing**: Runs asynchronously in background, use GET /{run_id} to monitor progress.
             
             **Budget**: Tracks Tavily + OpenAI costs in real-time with $10 hard limit.
             """,
             tags=["Company Analysis"])
async def create_run(run_data: RunCreate, background_tasks: BackgroundTasks):
    run_id = f"r_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"🚀 Starting new analysis run: {run_id}")
    logger.info(f"🏢 Company: {run_data.company} | Domain: {run_data.domain}")
    
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
    logger.info(f"✅ Run document created in database: {run_id}")
    
    # Add the background task
    background_tasks.add_task(run_llm_analysis, run_id, run_data.company, run_data.domain)
    logger.info(f"📋 Background task added for run: {run_id}")
    
    return {"run_id": run_id, "status": "running"}

@router.get("/history",
            summary="Get All Analysis Runs History",
            description="""
            📋 **Retrieve complete history of company analysis runs**
            
            Returns a list of all analysis runs with essential metadata:
            - **Run ID**: Unique identifier for each analysis
            - **Company Info**: Company name and domain
            - **Status**: Current run status (pending, running, completed, error, partial)
            - **Timestamps**: Created and completion timestamps
            - **Cost Summary**: Total Tavily credits and OpenAI costs
            - **Error Count**: Number of errors encountered
            
            **Use Cases**:
            - Display run history in frontend
            - Track analysis performance over time
            - Monitor system usage and patterns
            - Quick access to previous analyses
            
            **Sorting**: Returns most recent runs first (by created_at)
            """,
            tags=["Company Analysis"])
async def get_runs_history():
    """Get all analysis runs history with essential metadata."""
    db = get_database()
    
    # Get all runs, sorted by most recent first
    runs_cursor = db.runs.find(
        {},
        {
            "run_id": 1,
            "company": 1, 
            "status": 1,
            "created_at": 1,
            "completed_at": 1,
            "cost": 1,
            "errors": 1,
            "_id": 0  # Exclude MongoDB _id field
        }
    ).sort("created_at", -1).limit(100)  # Limit to last 100 runs
    
    runs_list = await runs_cursor.to_list(100)
    
    # Add derived fields for better frontend experience
    for run in runs_list:
        # Add error count
        run["error_count"] = len(run.get("errors", []))
        
        # Add total cost (approximate USD)
        cost_data = run.get("cost", {})
        tavily_credits = cost_data.get("tavily_credits", 0)
        openai_usd = cost_data.get("openai_usd", 0.0)
        # Rough estimate: 1000 Tavily credits ≈ $1 USD
        estimated_tavily_usd = tavily_credits / 1000.0
        run["estimated_total_cost_usd"] = round(estimated_tavily_usd + openai_usd, 4)
        
        # Add duration if completed
        if run.get("completed_at") and run.get("created_at"):
            duration_seconds = (run["completed_at"] - run["created_at"]).total_seconds()
            run["duration_minutes"] = round(duration_seconds / 60, 1)
        else:
            run["duration_minutes"] = None
    
    return {
        "runs": runs_list,
        "total_count": len(runs_list),
        "page_info": {
            "limit": 100,
            "has_more": len(runs_list) == 100
        }
    }

@router.get("/{run_id}", 
            response_model=RunStateDTO,
            summary="Get Analysis Results & Status",
            description="""
            📊 **Retrieve comprehensive analysis results and real-time status**
            
            Returns complete analysis data from all 8 agents including:
            - **Status**: pending, running, completed, error, partial
            - **Insights**: Executive summary, investment signals, risk assessment
            - **Sources**: News articles, patents, founder profiles, competitive analysis
            - **Deep Analysis**: Content extraction, verification scores, synthesis
            - **Costs**: Detailed breakdown of Tavily credits and OpenAI usage
            - **Errors**: Any issues encountered during processing
            
            **Real-time**: Poll this endpoint to monitor 8-agent workflow progress.
            
            **Data Sources**: Complete Tavily API integration (Map, Search, Crawl, Extract) + GPT-4o synthesis.
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
            📋 **Export complete 8-agent analysis dataset in JSON format**
            
            Provides comprehensive raw data from all workflow phases:
            - **Run Metadata**: Timestamps, status, company information
            - **Discovery Data**: Digital footprint mapping results (Tavily Map)
            - **Research Results**: News, patents, founders, competitive intel (Tavily Search)
            - **Deep Analysis**: Content extraction and processing (Tavily Crawl + Extract)
            - **Verification**: Cross-validated facts with confidence scores
            - **Synthesis**: Professional investment intelligence reports (GPT-4o)
            - **Cost Breakdown**: Granular Tavily + OpenAI usage tracking
            
            **Use Cases**: 
            - Data analysis and research
            - Integration with external systems
            - Audit trails and compliance
            - Custom reporting and visualization
            - Tavily API integration showcase
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
    
    return {
        "run_id": run_id,
        "company": converted_run_doc["company"],
        "status": converted_run_doc["status"],
        "insights": converted_insights,
        "patents": converted_patents,
        "risks": converted_risks,
        "sources": converted_sources,
        "founders": converted_founders,
        "competitive": converted_competitive,
        "deepdive": converted_deepdive,
        "verification": converted_verification,
        "cost": converted_run_doc["cost"],
        "created_at": converted_run_doc["created_at"],
        "completed_at": converted_run_doc.get("completed_at"),
        "export_timestamp": datetime.utcnow().isoformat(),
        "export_version": "2.0"
    }

@router.get("/{run_id}/export.html",
            response_class=HTMLResponse,
            summary="Export as Interactive HTML Report",
            description="""
            🌐 **Export analysis as beautiful interactive HTML report**
            
            Features:
            - Interactive charts with Chart.js/D3.js
            - Professional styling with CSS
            - Collapsible sections for easy navigation
            - Direct browser viewing and printing
            - Embedded visualizations for patents, sources, risk metrics
            - Mobile-responsive design
            """,
            tags=["Data Export"])
async def export_run_html(run_id: str):
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
    
    # Convert ObjectIds
    converted_run_doc = convert_objectid_to_str(run_doc)
    converted_insights = convert_documents_list(insights)
    converted_patents = convert_documents_list(patents)
    converted_risks = convert_documents_list(risks)
    converted_sources = convert_documents_list(sources)
    converted_founders = convert_documents_list(founders)
    converted_competitive = convert_objectid_to_str(competitive_analysis) if competitive_analysis else None
    converted_deepdive = convert_objectid_to_str(deepdive_analysis) if deepdive_analysis else None
    converted_verification = convert_objectid_to_str(verification_analysis) if verification_analysis else None
    
    # Generate HTML report
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Analysis Report - {converted_run_doc['company']['name']}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0; }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
        .header p {{ margin: 10px 0 0; opacity: 0.9; font-size: 1.1em; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; font-weight: 400; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #3498db; }}
        .metric-title {{ font-weight: 600; color: #2c3e50; margin-bottom: 5px; }}
        .metric-value {{ font-size: 1.3em; color: #27ae60; }}
        .source-item {{ background: white; border: 1px solid #e9ecef; padding: 15px; margin: 10px 0; border-radius: 6px; }}
        .source-title {{ font-weight: 600; color: #2c3e50; }}
        .source-url {{ color: #6c757d; font-size: 0.9em; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .status-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.9em; font-weight: 600; }}
        .status-completed {{ background: #d4edda; color: #155724; }}
        .status-running {{ background: #fff3cd; color: #856404; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #2c3e50; }}
        .collapsible {{ background: #3498db; color: white; cursor: pointer; padding: 15px; border: none; border-radius: 6px; margin: 10px 0; width: 100%; text-align: left; font-size: 1.1em; }}
        .collapsible:hover {{ background: #2980b9; }}
        .collapsible-content {{ padding: 0; max-height: 0; overflow: hidden; transition: max-height 0.2s ease-out; }}
        .collapsible-content.active {{ padding: 20px; max-height: 1000px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{converted_run_doc['company']['name']} Analysis Report</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | 
               Status: <span class="status-badge status-{converted_run_doc['status']}">{converted_run_doc['status'].title()}</span></p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 Executive Summary</h2>
                <div class="metric-card">
                    <div class="metric-title">Total Sources Analyzed</div>
                    <div class="metric-value">{len(converted_sources)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Patents Found</div>
                    <div class="metric-value">{len(converted_patents)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Risk Items Identified</div>
                    <div class="metric-value">{len(converted_risks)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Founders Analyzed</div>
                    <div class="metric-value">{len(converted_founders)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Analysis Cost</div>
                    <div class="metric-value">${converted_run_doc['cost'].get('openai_usd', 0):.4f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Facts Verified</div>
                    <div class="metric-value">{len(converted_verification.get('verified_facts', [])) if converted_verification else 0}</div>
                </div>
            </div>

            <button class="collapsible" onclick="toggleSection('insights')">💡 Key Insights</button>
            <div class="collapsible-content" id="insights">
                {''.join([f'''
                <div class="metric-card">
                    <div class="metric-title">Executive Summary</div>
                    <p>{insight.get("executive_summary", "No executive summary available")}</p>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Investment Signals</div>
                    <ul>{''.join([f'<li>{signal}</li>' for signal in insight.get("investment_signals", [])])}</ul>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Risk Assessment</div>
                    <ul>{''.join([f'<li>{risk}</li>' for risk in insight.get("risk_assessment", [])])}</ul>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Confidence Score</div>
                    <div class="metric-value">{insight.get("confidence_score", 0):.2f}</div>
                </div>
                ''' for insight in converted_insights])}
            </div>

            <button class="collapsible" onclick="toggleSection('sources')">📰 News & Sources</button>
            <div class="collapsible-content" id="sources">
                {''.join([f'<div class="source-item"><div class="source-title">{source.get("title", "Untitled")}</div><p>{source.get("content", "No content available")[:200]}...</p><div class="source-url">{source.get("url", "No URL")}</div></div>' for source in converted_sources])}
            </div>

            <button class="collapsible" onclick="toggleSection('patents')">🔬 Patent Portfolio</button>
            <div class="collapsible-content" id="patents">
                <table>
                    <thead><tr><th>Patent Title</th><th>Filing Date</th><th>Assignee</th></tr></thead>
                    <tbody>
                        {''.join([f'<tr><td>{patent.get("title", "Unknown")}</td><td>{patent.get("filing_date", "N/A")}</td><td>{patent.get("assignee", "Unknown")}</td></tr>' for patent in converted_patents])}
                    </tbody>
                </table>
            </div>

            <button class="collapsible" onclick="toggleSection('risks')">⚠️ Risk Assessment</button>
            <div class="collapsible-content" id="risks">
                {''.join([f'<div class="metric-card"><div class="metric-title">{risk.get("category", "General Risk")}</div><p>{risk.get("description", "No description available")}</p><div class="metric-value">Severity: {risk.get("severity", "Unknown")}</div></div>' for risk in converted_risks])}
            </div>

            <button class="collapsible" onclick="toggleSection('founders')">👥 Leadership Team</button>
            <div class="collapsible-content" id="founders">
                {''.join([f'''
                <div class="source-item">
                    <div class="source-title">{founder.get("name", "Unknown")} - {founder.get("role", "Unknown Role")}</div>
                    <p><strong>Background:</strong> {founder.get("background_summary", "No background available")}</p>
                    <p><strong>Investment Assessment:</strong> {founder.get("investment_assessment", "No assessment available")}</p>
                    <div class="metric-value">Confidence: {founder.get("source_confidence", "Unknown")}</div>
                </div>
                ''' for founder in converted_founders])}
            </div>

            <button class="collapsible" onclick="toggleSection('competitive')">🏆 Competitive Analysis</button>
            <div class="collapsible-content" id="competitive">
                {f'''
                <div class="metric-card">
                    <div class="metric-title">Market Position</div>
                    <p>{converted_competitive.get("market_positioning", "No positioning data available")}</p>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Key Competitors</div>
                    <table>
                        <thead><tr><th>Company</th><th>Category</th><th>Market Position</th></tr></thead>
                        <tbody>
                            {''.join([f'<tr><td>{comp.get("name", "Unknown")}</td><td>{comp.get("category", "Unknown")}</td><td>{comp.get("market_position", "Unknown")}</td></tr>' for comp in converted_competitive.get("competitors", [])])}
                        </tbody>
                    </table>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Competitive Advantages</div>
                    <ul>{''.join([f'<li>{adv}</li>' for adv in converted_competitive.get("competitive_advantages", [])])}</ul>
                </div>
                ''' if converted_competitive else '<p>No competitive analysis available</p>'}
            </div>

            <button class="collapsible" onclick="toggleSection('deepdive')">🔍 Deep Dive Analysis</button>
            <div class="collapsible-content" id="deepdive">
                {f'''
                <div class="metric-card">
                    <div class="metric-title">Business Model</div>
                    <p>{converted_deepdive.get("company_profile", {}).get("business_model", "No business model data available")}</p>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Value Proposition</div>
                    <p>{converted_deepdive.get("company_profile", {}).get("value_proposition", "No value proposition data available")}</p>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Investment Insights</div>
                    <ul>{''.join([f'<li>{insight}</li>' for insight in converted_deepdive.get("investment_insights", [])])}</ul>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Confidence Score</div>
                    <div class="metric-value">{converted_deepdive.get("confidence_score", 0):.2f}</div>
                </div>
                ''' if converted_deepdive else '<p>No deep dive analysis available</p>'}
            </div>

            <button class="collapsible" onclick="toggleSection('verification')">✅ Fact Verification</button>
            <div class="collapsible-content" id="verification">
                {f'''
                <div class="metric-card">
                    <div class="metric-title">Verification Summary</div>
                    <p>{converted_verification.get("verification_summary", "No verification summary available")}</p>
                </div>
                <table>
                    <thead><tr><th>Claim</th><th>Status</th><th>Confidence</th><th>Sources</th></tr></thead>
                    <tbody>
                        {''.join([f'<tr><td>{fact.get("claim", "Unknown")}</td><td>{fact.get("status", "Unknown")}</td><td>{fact.get("confidence", 0):.2f}</td><td>{", ".join(fact.get("sources", []))}</td></tr>' for fact in converted_verification.get("verified_facts", [])])}
                    </tbody>
                </table>
                ''' if converted_verification else '<p>No verification analysis available</p>'}
            </div>

            <div class="section">
                <h2>🔍 Analysis Metadata</h2>
                <table>
                    <tr><td><strong>Run ID</strong></td><td>{run_id}</td></tr>
                    <tr><td><strong>Company Domain</strong></td><td>{converted_run_doc['company'].get('domain', 'N/A')}</td></tr>
                    <tr><td><strong>Started</strong></td><td>{converted_run_doc['created_at']}</td></tr>
                    <tr><td><strong>Completed</strong></td><td>{converted_run_doc.get('completed_at', 'In Progress')}</td></tr>
                    <tr><td><strong>Tavily Credits Used</strong></td><td>{converted_run_doc['cost'].get('tavily_credits', 0)}</td></tr>
                </table>
            </div>
        </div>
    </div>

    <script>
        function toggleSection(sectionId) {{
            var content = document.getElementById(sectionId);
            content.classList.toggle('active');
        }}
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)

@router.get("/{run_id}/export.csv",
            summary="Export as CSV Data",
            description="""
            📊 **Export analysis data in CSV format for Excel/spreadsheet analysis**
            
            Features:
            - Structured data format compatible with Excel, Google Sheets
            - Multiple sheets: sources, patents, risks, insights
            - Easy data manipulation and analysis
            - Import into business intelligence tools
            """,
            tags=["Data Export"])
async def export_run_csv(run_id: str):
    db = get_database()
    
    run_doc = await db.runs.find_one({"run_id": run_id})
    if not run_doc:
        raise HTTPException(status_code=404, detail="Run not found")
    
    sources = await db.sources.find({"run_id": run_id}).to_list(None)
    patents = await db.patents.find({"run_id": run_id}).to_list(None)
    
    # Convert ObjectIds
    converted_sources = convert_documents_list(sources)
    converted_patents = convert_documents_list(patents)
    
    # Generate CSV content
    csv_content = f"# Company Analysis Report - {run_doc['company']['name']}\\n"
    csv_content += f"# Generated: {datetime.now().isoformat()}\\n\\n"
    
    csv_content += "Section,Title,Content,URL,Date\\n"
    
    for source in converted_sources:
        title = str(source.get('title', '')).replace('"', '""')
        content = str(source.get('content', ''))[:100].replace('"', '""')
        url = str(source.get('url', '')).replace('"', '""')
        csv_content += f'"Sources","{title}","{content}","{url}","{source.get("date", "")}"\\n'
    
    for patent in converted_patents:
        title = str(patent.get('title', '')).replace('"', '""')
        assignee = str(patent.get('assignee', '')).replace('"', '""')
        csv_content += f'"Patents","{title}","{assignee}","","{patent.get("filing_date", "")}"\\n'
    
    # Return as streaming response
    response = StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={run_id}_analysis.csv"}
    )
    return response

@router.get("/budget/status",
            summary="Get Real-time Budget Status", 
            description="""
            💰 **Monitor API usage and budget consumption in real-time**
            
            Returns current budget status for Tavily interview assignment:
            - **Total Spend**: Current USD expenditure across Tavily + OpenAI
            - **Remaining Budget**: Available funds before hitting $10 limit
            - **Service Breakdown**: Tavily credits vs GPT-4o costs
            - **Usage Trends**: Recent API consumption patterns
            - **Budget Alerts**: Warnings when approaching limits
            
            **Budget Controls**: 
            - **$10 hard limit** for Tavily interview assignment
            - Automatic throttling when approaching caps
            - Cost-per-operation tracking across 8-agent workflow
            - Real-time monitoring during multi-phase analysis
            """,
            tags=["Budget Tracking"])
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
            tags=["Budget Tracking"])
async def get_budget_history():
    """Get detailed budget usage history."""
    db = get_database()
    history = await db.budget_tracking.find().sort("timestamp", -1).limit(50).to_list(50)
    
    return {
        "history": history,
        "total_operations": len(history)
    }