"""
Haki Sovereign AI Engine - Main API.

Verified Government Knowledge Base for the SmartCitizen AI platform.
Answers questions about official Kenyan documents using only verified sources.

Built during Kenya National AI Hackathon 2026 - National Security Track
Team: SmartCitizen AI
Focus: Information warfare defense through verified government information access
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
        """Normalize question for caching."""
        q = (q or "").strip().lower()
        q = re.sub(r"\s+", " ", q)
        return q

    def _expand_structural_query(self, question: str) -> str:
        """
        Automatically expand article/chapter/section queries for better retrieval.
        
        This makes queries like "What does Article 73 say?" work reliably
        by adding the article reference directly to the search.
        
        Works for ANY document - no manual mapping needed!
        """
        import re
        
        # Extract article/chapter/section/schedule numbers from the question
        article_match = re.search(r'\barticle\s+(\d{1,3})\b', question, re.IGNORECASE)
        chapter_match = re.search(r'\bchapter\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|[IVX]+|\d+)\b', question, re.IGNORECASE)
        section_match = re.search(r'\b(?:section|part)\s+([IVX]+|\d+)\b', question, re.IGNORECASE)
        schedule_match = re.search(r'\b(first|second|third|fourth|fifth|sixth)\s+schedule\b', question, re.IGNORECASE)
        
        # Build expanded query with explicit markers
        expanded_parts = [question]
        
        if article_match:
            article_num = article_match.group(1)
            expanded_parts.append(f"Article {article_num}")
            expanded_parts.append(f"[Article {article_num}]")
            print(f"🔍 Searching for Article {article_num}")
        
        if chapter_match:
            chapter_num = chapter_match.group(1).title()
            expanded_parts.append(f"Chapter {chapter_num}")
            expanded_parts.append(f"[Chapter {chapter_num}]")
            # Add Constitution chapter theme for better context
            from .config import CONSTITUTION_CHAPTERS
            if chapter_num in CONSTITUTION_CHAPTERS:
                expanded_parts.append(CONSTITUTION_CHAPTERS[chapter_num])
            print(f"🔍 Searching for Chapter {chapter_num}")
        
        if section_match:
            section_num = section_match.group(1)
            expanded_parts.append(f"Section {section_num}")
            # Treat Section as Article synonym for Constitution
            if section_num.isdigit():
                expanded_parts.append(f"Article {section_num}")
            print(f"🔍 Searching for Section {section_num}")
        
        if schedule_match:
            schedule_name = schedule_match.group(1).title()
            expanded_parts.append(f"{schedule_name} Schedule")
            print(f"🔍 Searching for {schedule_name} Schedule")
        
        # If we found structural elements, add them multiple times for emphasis
        if article_match or chapter_match or section_match or schedule_match:
            base_query = " ".join(expanded_parts)
            # Duplicate key terms to boost relevance
            if article_match:
                base_query += f" Article {article_match.group(1)} provisions"
            if chapter_match:
                base_query += f" Chapter {chapter_match.group(1).title()}"
            return base_query
        
        # For non-structural queries, try LLM expansion if available
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                
                prompt = f"""You are helping improve search queries for a Kenyan government document database.

The user asked: "{question}"

Add 2-3 relevant keywords that would help find this information in official documents.

For example:
- "What are presidential powers?" → "What are presidential powers? president authority executive functions"
- "How is the senate formed?" → "How is the senate formed? senate composition members election"

Respond with ONLY the expanded query (original + keywords), nothing else.

Expanded query:"""
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=50,
                )
                
                expanded = response.choices[0].message.content.strip()
                
                # Validate response
                if question.lower()[:15] in expanded.lower():
                    return expanded
                    
            except Exception as e:
                print(f"⚠️ Query expansion failed: {e}")
        
        # Fallback: return original question
        return question

    def _translate_query_to_english(self, question: str, detected_lang: str) -> str:
        """Translate non-English queries to English for better retrieval."""
        # First translate to English if needed
        if detected_lang != "en":
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
                question = response.choices[0].message.content.strip()
        
        # Then expand structural queries (works for ANY language after translation)
        return self._expand_structural_query(question)

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

        # Translate and expand query for better retrieval
        search_query = self._translate_query_to_english(question, input_lang)
        
        # Get answer using expanded query
        result = self.rag.answer(search_query, output_language=language)

        # Cache successful results
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
    """
    Factory to create and return the Haki engine (Singleton).
    
    SmartCitizen AI - Kenya National AI Hackathon 2026
    Cognitive Defense System for Information Integrity
    """
    return HakiSovereignEngine.get_instance(force_rebuild=force_rebuild)