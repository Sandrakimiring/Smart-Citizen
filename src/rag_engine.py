"""RAG engine with anti-hallucination and structured citations."""

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStore

from .config import TOP_K_CHUNKS, OLLAMA_MODEL

# Anti-hallucination system prompt: answer ONLY from context, refuse if not found
RAG_PROMPT = """You are Haki Sovereign AI - a trusted assistant for Kenyan citizens. You answer questions about official government documents (Constitution of Kenya 2010, Finance Bill 2025) using ONLY the provided context.

CRITICAL RULES:
1. Answer ONLY using information from the context below. Do NOT guess or invent information.
2. If the context does not contain enough information to answer the question, respond EXACTLY with: "I can't find that information in the official documents provided."
3. Prioritize correctness over completeness. A short correct answer is better than a long incorrect one.
4. Use plain language that a non-technical citizen can understand.
5. Keep your answer concise (2-4 sentences typically).

Context from official documents:
{context}

Question: {question}

Answer (plain language only, no citations in text):"""


def _format_context(docs: list) -> str:
    """Format retrieved documents as context for the LLM."""
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        title = meta.get("document_title", meta.get("doc_title", "Unknown"))
        page = meta.get("page_display", meta.get("page", "N/A"))
        parts.append(f"[{i}] ({title} - Page {page})\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _extract_citations(docs: list) -> list[dict]:
    """Extract citation info from source documents."""
    seen = set()
    citations = []
    for doc in docs:
        meta = doc.metadata
        title = meta.get("document_title", meta.get("doc_title", "Unknown Document"))
        page = meta.get("page_display", meta.get("page", "N/A"))
        key = (title, page)
        if key not in seen:
            seen.add(key)
            citations.append({"document_title": title, "page": page})
    return citations


def _is_refusal(answer: str) -> bool:
    """Check if the model refused to answer (anti-hallucination response)."""
    refusal_phrase = "I can't find that information in the official documents provided"
    return refusal_phrase.lower() in answer.lower()


class HakiRAGEngine:
    """RAG engine with anti-hallucination and citations."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.llm = OllamaLLM(model=OLLAMA_MODEL)
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
            return {
                "answer": "I can't find that information in the official documents provided.",
                "sources": [],
                "supported": False,
            }

        context = _format_context(docs)
        prompt = PromptTemplate(
            template=RAG_PROMPT,
            input_variables=["context", "question"],
        )

        chain = prompt | self.llm
        raw_answer = chain.invoke({"context": context, "question": question}).strip()
        supported = not _is_refusal(raw_answer)
        citations = _extract_citations(docs)

        if not supported:
            return {
                "answer": "I can't find that information in the official documents provided.",
                "sources": [],
                "supported": False,
            }

        # Translate to Kiswahili/Sheng only for supported answers
        if output_language != "en":
            raw_answer = self._translate_answer(raw_answer, output_language, question, self.llm)

        return {
            "answer": raw_answer,
            "sources": citations,
            "supported": True,
        }

    def _translate_answer(self, answer_en: str, target_lang: str, question: str, llm) -> str:
        """Delegate to language module for translation."""
        from .language import translate_answer
        return translate_answer(answer_en, target_lang, question, llm)
