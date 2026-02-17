"""FastAPI backend for Haki Sovereign AI."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any, Union
import os

from src.haki_engine import create_engine

# Initialize FastAPI
app = FastAPI(
    title="Haki Sovereign AI API",
    description="AI-powered assistant for Kenyan government documents",
    version="1.0.0",
)

# CORS middleware (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engine (singleton)
engine = None

@app.on_event("startup")
async def startup_event():
    """Load engine on startup."""
    global engine
    print("Loading Haki Sovereign AI Engine...")
    engine = create_engine()
    print("Engine loaded successfully!")

# Request/Response models
class AskRequest(BaseModel):
    question: str = Field(..., description="User's question in English, Kiswahili, or Sheng")
    language: Optional[Literal["en", "sw", "sheng"]] = Field(
        None, 
        description="Output language (auto-detected if not provided)"
    )
    auto_detect_language: bool = Field(
        True, 
        description="Automatically detect input language"
    )

class Source(BaseModel):
    document_title: str
    page: str
    snippet: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    supported: bool
    language_used: str
    input_language_detected: str

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Haki Sovereign AI",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check with engine status."""
    return {
        "status": "healthy",
        "engine_loaded": engine is not None,
        "documents": ["Constitution of Kenya 2010"]
    }

@app.post("/api/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question about Kenyan government documents.
    
    **Example requests:**
    
    English:
```json
    {
        "question": "What are the qualifications to be president?",
        "language": "en"
    }
```
    
    Kiswahili:
```json
    {
        "question": "Haki zangu ni nini?",
        "language": "sw"
    }
```
    
    Auto-detect:
```json
    {
        "question": "Seneti ina majukumu gani?"
    }
```
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        # Ask the engine
        response = engine.ask(
            question=request.question,
            language=request.language,
            auto_detect_language=request.auto_detect_language
        )
        
        # Format sources
        sources = [
            Source(
                document_title=s["document_title"],
                page=str(s["page"]), 
                snippet=s.get("snippet")
            )
            for s in response.sources
        ]
        
        return AskResponse(
            answer=response.answer,
            sources=sources,
            supported=response.supported,
            language_used=response.language_used,
            input_language_detected=response.input_language_detected
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/api/documents")
async def list_documents():
    """List available documents in the knowledge base."""
    from src.config import DOCUMENTS
    
    return {
        "documents": [
            {"filename": k, "title": v} 
            for k, v in DOCUMENTS.items()
        ],
        "total": len(DOCUMENTS)
    }

@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    from src.config import DOCUMENTS
    
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    # Get collection stats
    collection = engine.rag.vector_store._collection
    count = collection.count()
    
    return {
        "total_chunks": count,
        "total_documents": len(DOCUMENTS),
        "supported_languages": ["en", "sw", "sheng"],
        "features": {
            "multilingual": True,
            "anti_hallucination": True,
            "citations": True,
            "query_translation": True
        }
    }

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    # uvicorn api.main:app --reload