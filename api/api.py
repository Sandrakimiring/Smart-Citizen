"""
HTTP API for Haki Sovereign AI Engine.

Run with: uvicorn src.api:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..src.haki_engine import create_engine

# Global engine (created at startup, reused for all requests)
_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create engine once at startup."""
    global _engine
    _engine = create_engine()
    yield
    _engine = None


app = FastAPI(
    title="Haki Sovereign AI API",
    description="Verified Government Knowledge — ask questions about official Kenyan documents.",
    version="1.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question in English, Kiswahili, or Sheng")
    language: str | None = Field(default=None, description="Output language: en, sw, or sheng. Default: auto-detect from question")


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    supported: bool
    language_used: str
    input_language_detected: str


@app.get("/health")
def health():
    """Liveness/readiness: app is up. For full readiness, ensure Ollama is reachable separately."""
    return {"status": "ok", "service": "haki-sovereign"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Ask a question about official documents. Returns answer with sources or refusal."""
    if _engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    try:
        resp = _engine.ask(
            req.question,
            language=req.language,
            auto_detect_language=True,
        )
        out = resp.format_output()
        return AskResponse(
            answer=out["answer"],
            sources=out["sources"],
            supported=out["supported"],
            language_used=resp.language_used,
            input_language_detected=resp.input_language_detected,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {"message": "Haki Sovereign AI API", "docs": "/docs", "health": "/health"}
