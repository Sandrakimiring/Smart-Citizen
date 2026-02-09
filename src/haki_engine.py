"""
Haki Sovereign AI Engine - Main API.

Verified Government Knowledge Base for the SmartCitizen AI platform.
Answers questions about official Kenyan documents using only verified sources.
"""

from dataclasses import dataclass
from typing import Literal

from .config import SUPPORTED_LANGUAGES
from .vector_store import get_embeddings, get_vector_store
from .rag_engine import HakiRAGEngine
from .language import detect_language


Language = Literal["en", "sw", "sheng"]


@dataclass
class HakiResponse:
    """Structured response from the Haki engine."""

    answer: str
    sources: list[dict]  # [{"document_title": str, "page": str}]
    supported: bool
    language_used: str
    input_language_detected: str

    def format_output(self) -> dict:
        """Return output in the required format."""
        if self.supported:
            return {
                "answer": self.answer,
                "sources": [
                    f"{s['document_title']} — Page {s['page']}"
                    for s in self.sources
                ],
                "supported": True,
            }
        return {
            "answer": self.answer,
            "sources": ["No matching official source found in the current knowledge base."],
            "supported": False,
        }


class HakiSovereignEngine:
    """
    Haki Sovereign AI Engine.

    Use ask() to query official documents. Returns structured answers with citations.
    """

    def __init__(self, force_rebuild: bool = False):
        self.embeddings = get_embeddings()
        self.vector_store = get_vector_store(self.embeddings, force_rebuild=force_rebuild)
        self.rag = HakiRAGEngine(self.vector_store)

    def ask(
        self,
        question: str,
        language: Language | None = None,
        auto_detect_language: bool = True,
    ) -> HakiResponse:
        """
        Ask a question about official documents.

        Args:
            question: User's question in English, Kiswahili, or Sheng.
            language: Output language ('en', 'sw', 'sheng'). If None, uses auto_detect.
            auto_detect_language: If True and language is None, detect from question.

        Returns:
            HakiResponse with answer, sources, and metadata.
        """
        if language is None and auto_detect_language:
            language = detect_language(question)
        if language is None or language not in SUPPORTED_LANGUAGES:
            language = "en"

        result = self.rag.answer(question, output_language=language)

        return HakiResponse(
            answer=result["answer"],
            sources=result["sources"],
            supported=result["supported"],
            language_used=language,
            input_language_detected=detect_language(question) if auto_detect_language else "en",
        )


def create_engine(force_rebuild: bool = False) -> HakiSovereignEngine:
    """Factory to create and return the Haki engine."""
    return HakiSovereignEngine(force_rebuild=force_rebuild)
