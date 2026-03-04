"""Pydantic models for Nyayo Sentinel signals and API contracts."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Fixed topic taxonomy ──────────────────────────────────────────────
TOPIC_TAXONOMY = [
    "tax",
    "land",
    "employment",
    "education",
    "security",
    "health",
    "governance",
    "rights",
    "environment",
    "infrastructure",
]

# ── Kenya counties (47) ──────────────────────────────────────────────
KENYA_COUNTIES = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo-Marakwet",
    "Embu", "Garissa", "Homa Bay", "Isiolo", "Kajiado",
    "Kakamega", "Kericho", "Kiambu", "Kilifi", "Kirinyaga",
    "Kisii", "Kisumu", "Kitui", "Kwale", "Laikipia",
    "Lamu", "Machakos", "Makueni", "Mandera", "Marsabit",
    "Meru", "Migori", "Mombasa", "Murang'a", "Nairobi",
    "Nakuru", "Nandi", "Narok", "Nyamira", "Nyandarua",
    "Nyeri", "Samburu", "Siaya", "Taita-Taveta", "Tana River",
    "Tharaka-Nithi", "Trans-Nzoia", "Turkana", "Uasin Gishu",
    "Vihiga", "Wajir", "West Pokot",
]


# ── Ingest request (from Haki webhook) ───────────────────────────────
class IngestRequest(BaseModel):
    """Payload sent from Haki API after answering a citizen question."""
    question: str = Field(..., description="The citizen's original question")
    answer: Optional[str] = Field(None, description="Haki's RAG answer")
    supported: Optional[bool] = Field(None, description="Whether Haki found an answer")
    language: Optional[str] = Field(None, description="Detected input language")
    county: Optional[str] = Field(None, description="User-provided county (from frontend)")


# ── LLM extraction result ────────────────────────────────────────────
class SignalExtraction(BaseModel):
    """Structured output from the LLM analyzer."""
    topic: str = Field(..., description="Topic from the fixed taxonomy")
    tension_score: float = Field(..., ge=0.0, le=1.0, description="0=neutral, 1=very frustrated")
    county: Optional[str] = Field(None, description="Kenya county if mentioned")


# ── Stored signal record ─────────────────────────────────────────────
class Signal(BaseModel):
    """A single question signal stored in the database."""
    id: Optional[int] = None
    question: str
    answer: Optional[str] = None
    topic: str
    tension_score: float
    county: Optional[str] = None
    supported: Optional[bool] = None
    language: Optional[str] = None
    created_at: Optional[datetime] = None


# ── API response models ──────────────────────────────────────────────
class TopicCount(BaseModel):
    topic: str
    count: int


class TopicTrend(BaseModel):
    topic: str
    current_count: int
    previous_count: int
    change_percent: float
    direction: str  # "up", "down", "stable"


class CountyTension(BaseModel):
    county: str
    avg_tension: float
    question_count: int


class KnowledgeGap(BaseModel):
    total_questions: int
    unanswered_count: int
    no_answer_rate: float
    sample_unanswered: list[str]


class SentinelStats(BaseModel):
    total_signals: int
    topics: list[TopicCount]
    avg_tension: float
    counties_covered: int
