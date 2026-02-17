"""
Haki Sovereign AI Engine - Main API.

Verified Government Knowledge Base for the SmartCitizen AI platform.
Answers questions about official Kenyan documents using only verified sources.
"""

from dataclasses import dataclass
from typing import Literal
import re

from .config import (
    REFUSAL_TEXT,
    SUPPORTED_LANGUAGES,
    USE_OPENAI_FOR_TRANSLATION,
    OPENAI_API_KEY,
)
from .vector_store import get_embeddings, get_vector_store
from .rag_engine import HakiRAGEngine
from .language import detect_language


Language = Literal["en", "sw", "sheng"]


@dataclass
class HakiResponse:
    """Structured response from the Haki engine."""

    answer: str
    sources: list[dict]
    supported: bool
    language_used: str
    input_language_detected: str

    def format_output(self) -> dict:
        """Return output in the required format."""
        if self.supported:
            return {
                "answer": self.answer,
                "sources": [
                    (
                        f"{s['document_title']} — Page {s['page']}"
                        + (f' — "{s.get("snippet", "")}"' if s.get("snippet") else "")
                    )
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

    _instance = None

    def __init__(self, force_rebuild: bool = False):
        self.embeddings = get_embeddings()
        self.vector_store = get_vector_store(self.embeddings, force_rebuild=force_rebuild)
        self.rag = HakiRAGEngine(self.vector_store)
        self._cache: dict[tuple[str, str], dict] = {}

    @classmethod
    def get_instance(cls, force_rebuild: bool = False) -> "HakiSovereignEngine":
        """Get or create the singleton instance."""
        if cls._instance is None or force_rebuild:
            cls._instance = cls(force_rebuild=force_rebuild)
        return cls._instance

    @staticmethod
    def _normalize_question(q: str) -> str:
        q = (q or "").strip().lower()
        q = re.sub(r"\s+", " ", q)
        return q

    def _translate_query_to_english(self, question: str, detected_lang: str) -> str:
        """Translate non-English queries to English for better retrieval."""
        if detected_lang == "en":
            return question

        if USE_OPENAI_FOR_TRANSLATION and OPENAI_API_KEY:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            lang_name = "Kiswahili" if detected_lang == "sw" else "Sheng"
            prompt = f"""Translate this question from {lang_name} to English. Keep it concise and clear.

{lang_name}: {question}

English:"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()

        return question

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
        input_lang = detect_language(question) if auto_detect_language else "en"

        if language is None and auto_detect_language:
            language = input_lang
        if language is None or language not in SUPPORTED_LANGUAGES:
            language = "en"

        cache_key = (self._normalize_question(question), language)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return HakiResponse(
                answer=cached["answer"],
                sources=cached["sources"],
                supported=cached["supported"],
                language_used=language,
                input_language_detected=input_lang,
            )

        search_query = self._translate_query_to_english(question, input_lang)
        result = self.rag.answer(search_query, output_language=language)

        if result["answer"].strip() == REFUSAL_TEXT or result.get("supported") is True:
            self._cache[cache_key] = result

        return HakiResponse(
            answer=result["answer"],
            sources=result["sources"],
            supported=result["supported"],
            language_used=language,
            input_language_detected=input_lang,
        )


def create_engine(force_rebuild: bool = False) -> HakiSovereignEngine:
    """Factory to create and return the Haki engine (Singleton)."""
    return HakiSovereignEngine.get_instance(force_rebuild=force_rebuild)