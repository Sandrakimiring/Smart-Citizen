"""RAG engine with anti-hallucination, confidence gating, and citations."""

import re
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStore

from .config import (
    MAX_CHUNK_CHARS_IN_PROMPT,
    MIN_MEANINGFUL_CHUNK_CHARS,
    MIN_MEANINGFUL_CHUNKS,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    REFUSAL_TEXT,
    TOP_K_CHUNKS,
)

# Anti-hallucination system prompt: answer ONLY from context, refuse if not found
RAG_PROMPT = """You are Haki Sovereign AI - a trusted assistant for Kenyan citizens. You answer questions about official government documents (Constitution of Kenya 2010, Finance Bill 2025) using ONLY the provided context.

CRITICAL RULES:
1. Answer ONLY using information from the context below. Do NOT guess or invent information.
2. If the context does not contain enough information to answer the question, respond EXACTLY with: "{refusal_text}"
3. Extract ALL specific details from the context (numbers, requirements, dates, procedures).
4. If the context mentions "prescribed by" or "according to" something else, state that clearly.
5. Use plain language that a non-technical citizen can understand.
6. Keep your answer clear and complete (2-5 sentences).

Context from official documents:
{context}

Question: {question}

Answer (include all relevant details from the context):"""


def _clean_text(text: str) -> str:
    """Normalize whitespace and remove excessive blank lines."""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _trim_for_prompt(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def _meaningful(doc) -> bool:
    content = _clean_text(doc.page_content or "")
    return len(content) >= MIN_MEANINGFUL_CHUNK_CHARS


def _prepare_docs(docs: list) -> list:
    """Clean and trim retrieved docs, dropping near-empty/noisy ones."""
    prepared = []
    for doc in docs:
        cleaned = _clean_text(doc.page_content or "")
        if not cleaned:
            continue
        # store cleaned for snippets / prompt
        doc.page_content = _trim_for_prompt(cleaned, MAX_CHUNK_CHARS_IN_PROMPT)
        prepared.append(doc)
    return prepared


def _format_context(docs: list) -> str:
    """Format retrieved documents as context for the LLM."""
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        title = meta.get("document_title", meta.get("doc_title", "Unknown"))
        page = meta.get("page_display", meta.get("page", "N/A"))
        parts.append(f"[{i}] ({title} - Page {page})\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _make_snippet(text: str, min_len: int = 160, max_len: int = 400) -> str:
    text = _clean_text(text)
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"


def _extract_citations(docs: list) -> list[dict]:
    """Extract citation info from source documents (with evidence snippet)."""
    seen = set()
    citations = []
    for doc in docs:
        meta = doc.metadata
        title = meta.get("document_title", meta.get("doc_title", "Unknown Document"))
        page = meta.get("page_display", meta.get("page", "N/A"))
        key = (title, page)
        if key not in seen:
            seen.add(key)
            citations.append(
                {
                    "document_title": title,
                    "page": page,
                    "snippet": _make_snippet(doc.page_content or ""),
                }
            )
    return citations


def _is_refusal(answer: str) -> bool:
    """Deterministic refusal detection (exact match)."""
    return (answer or "").strip() == REFUSAL_TEXT


class HakiRAGEngine:
    """RAG engine with anti-hallucination and citations."""

    def __init__(self, vector_store: VectorStore, llm=None, translation_llm=None):
        self.vector_store = vector_store
        
        # Use OpenAI if API key available (for cloud deployment)
        if OPENAI_API_KEY and not llm:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=OPENAI_API_KEY,
                    temperature=0.3
                )
                self.translation_llm = self.llm
                print(" Using OpenAI for LLM and translation")
            except ImportError:
                print("langchain-openai not installed, falling back to Ollama")
                self.llm = OllamaLLM(model=OLLAMA_MODEL)
                self.translation_llm = translation_llm
                print("Using Ollama for LLM")
        else:
            # No OpenAI key or llm provided - use Ollama
            self.llm = llm or OllamaLLM(model=OLLAMA_MODEL)
            self.translation_llm = translation_llm
            print("Using Ollama for LLM (no API key)")
        
        self.retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K_CHUNKS})

    def retrieve(self, question: str):
        """Retrieve relevant chunks for a question."""
        return self.retriever.invoke(question)

    def answer(
        self,
        question: str,
        docs: list | None = None,
        output_language: str = "en",
    ) -> dict:
        """
        Generate an answer with citations. Returns:
        {
            "answer": str,
            "sources": [{"document_title": str, "page": str}],
            "supported": bool,  # True if answer is from documents
        }
        """
        if docs is None:
            docs = self.retrieve(question)

        if not docs:
            return {"answer": REFUSAL_TEXT, "sources": [], "supported": False}

        docs = _prepare_docs(docs)

        # Retrieval confidence gate (refuse early if evidence is weak)
        meaningful = [d for d in docs if _meaningful(d)]
        if len(meaningful) < MIN_MEANINGFUL_CHUNKS:
            return {"answer": REFUSAL_TEXT, "sources": [], "supported": False}

        context = _format_context(docs)
        prompt = PromptTemplate(
            template=RAG_PROMPT,
            input_variables=["context", "question"],
            partial_variables={"refusal_text": REFUSAL_TEXT},
        )

        chain = prompt | self.llm
        raw_answer = chain.invoke({"context": context, "question": question})
        
        # Handle different response types (string or AIMessage)
        if hasattr(raw_answer, 'content'):
            raw_answer = raw_answer.content
        raw_answer = str(raw_answer).strip()
        
        supported = not _is_refusal(raw_answer)
        citations = _extract_citations(docs)

        if not supported:
            return {"answer": REFUSAL_TEXT, "sources": [], "supported": False}

        # Translate to Kiswahili/Sheng only for supported answers
        if output_language != "en":
            translation_llm = self.translation_llm or self.llm
            raw_answer = self._translate_answer(raw_answer, output_language, question, translation_llm)

        return {
            "answer": raw_answer,
            "sources": citations,
            "supported": True,
        }

    def _translate_answer(self, answer_en: str, target_lang: str, question: str, llm) -> str:
        """Delegate to language module for translation."""
        from .language import translate_answer
        return translate_answer(answer_en, target_lang, question, llm)