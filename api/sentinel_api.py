"""
Nyayo Sentinel API — Standalone FastAPI application for authorities.

Provides endpoints for:
- Ingesting citizen question signals from Haki Engine
- Querying topic trends, county heatmap, knowledge gaps
- Dashboard summary statistics

Run with: uvicorn api.sentinel_api:app --port 8001 --reload
"""

import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from src.sentinel.models import (
    IngestRequest,
    Signal,
    TopicCount,
    TopicTrend,
    CountyTension,
    KnowledgeGap,
    SentinelStats,
)
from src.sentinel.analyzer import SentinelAnalyzer
from src.sentinel.database import init_db, insert_signal, get_signals
from src.sentinel.aggregator import (
    get_topic_counts,
    get_topic_trends,
    get_county_heatmap,
    get_knowledge_gaps,
    get_dashboard_stats,
)

logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────
app = FastAPI(
    title="Nyayo Sentinel API",
    description=(
        "Early Warning Dashboard for public policy monitoring. "
        "Analyzes citizen questions to detect emerging concerns, "
        "topic trends, and regional tension patterns."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globals
_analyzer: SentinelAnalyzer | None = None


@app.on_event("startup")
async def startup():
    """Initialize database and analyzer on startup."""
    global _analyzer
    init_db()
    try:
        _analyzer = SentinelAnalyzer()
        logger.info("✅ Sentinel analyzer initialized")
    except ValueError as e:
        logger.warning(f"⚠️ Sentinel analyzer not available: {e}")
        _analyzer = None


# ── Ingestion ─────────────────────────────────────────────────────────
def _process_signal(request: IngestRequest):
    """Background task: analyze question and store signal."""
    if _analyzer is None:
        logger.error("Analyzer not initialized, skipping signal")
        return

    extraction = _analyzer.analyze(request.question)

    # Prefer user-provided county, fall back to LLM extraction from question text
    county = request.county or extraction.county

    signal = Signal(
        question=request.question,
        answer=request.answer,
        topic=extraction.topic,
        tension_score=extraction.tension_score,
        county=county,
        supported=request.supported,
        language=request.language,
    )

    row_id = insert_signal(signal)
    logger.info(
        f"Signal #{row_id}: topic={extraction.topic}, "
        f"tension={extraction.tension_score}, county={county}"
    )


@app.post("/ingest", status_code=202)
async def ingest_signal(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Receive a citizen question from Haki Engine and analyze it.

    The analysis runs in the background so this returns immediately.
    Haki's response time is not affected.
    """
    background_tasks.add_task(_process_signal, request)
    return {"status": "accepted", "message": "Signal queued for analysis"}


# ── Query endpoints ───────────────────────────────────────────────────
@app.get("/topics", response_model=list[TopicCount])
async def topics(days: Optional[int] = None):
    """
    Topic frequency counts.

    Shows which issues citizens are asking about the most.

    **Query params:**
    - `days` (optional): Filter to last N days. Omit for all-time.
    """
    return get_topic_counts(days=days)


@app.get("/trends", response_model=list[TopicTrend])
async def trends(current_days: int = 1, compare_days: int = 7):
    """
    Rising and falling topics with percentage change.

    Compares the current period's daily rate against a baseline period.
    A spike suggests a policy announcement or emerging public concern.

    **Query params:**
    - `current_days`: Recent window (default: 1 = today)
    - `compare_days`: Baseline window (default: 7 = last week)
    """
    return get_topic_trends(current_days=current_days, compare_days=compare_days)


@app.get("/heatmap", response_model=list[CountyTension])
async def heatmap(days: Optional[int] = None):
    """
    Per-county average tension scores for the geographic heatmap.

    Counties with higher scores indicate areas where citizens
    are more frustrated or confused about policies.

    **Query params:**
    - `days` (optional): Filter to last N days.
    """
    return get_county_heatmap(days=days)


@app.get("/gaps", response_model=KnowledgeGap)
async def gaps(days: Optional[int] = None):
    """
    Knowledge gap analysis — tracks when the AI cannot find an answer.

    A high no-answer rate signals that government communication
    may be unclear or incomplete on certain topics.

    **Query params:**
    - `days` (optional): Filter to last N days.
    """
    return get_knowledge_gaps(days=days)


@app.get("/signals")
async def signals(
    limit: int = 50,
    offset: int = 0,
    topic: Optional[str] = None,
    county: Optional[str] = None,
    days: Optional[int] = None,
):
    """
    Raw signal log (paginated).

    Browse individual question signals with optional filters.

    **Query params:**
    - `limit`: Max results (default: 50)
    - `offset`: Pagination offset
    - `topic`: Filter by topic
    - `county`: Filter by county
    - `days`: Filter to last N days
    """
    return get_signals(limit=limit, offset=offset, topic=topic, county=county, days=days)


@app.get("/stats", response_model=SentinelStats)
async def stats(days: Optional[int] = None):
    """
    Dashboard summary statistics.

    Provides total signals, topic breakdown, average tension,
    and geographic coverage.
    """
    return get_dashboard_stats(days=days)


@app.get("/")
async def root():
    """Health check."""
    return {
        "service": "Nyayo Sentinel",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check with analyzer status."""
    return {
        "status": "healthy",
        "analyzer_ready": _analyzer is not None,
    }


# ── Local dev ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
