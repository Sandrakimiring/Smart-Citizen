"""RAG engine with anti-hallucination, confidence gating, and citations."""

import re
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStore
from langchain_openai import ChatOpenAI

from .config import (
    MAX_CHUNK_CHARS_IN_PROMPT,
    MIN_MEANINGFUL_CHUNK_CHARS,
    MIN_MEANINGFUL_CHUNKS,
    OPENAI_API_KEY,
    REFUSAL_TEXT,
    TOP_K_CHUNKS,
)

# Anti-hallucination system prompt: answer ONLY from context, refuse if not found
RAG_PROMPT = """You are Haki Sovereign AI - a trusted assistant for Kenyan citizens. You answer questions about official government documents (Constitution of Kenya 2010, Finance Bill 2025) using ONLY the provided context.

CRITICAL RULES:
1. Answer ONLY using information from the context below. Do NOT guess or invent information.
2. If the context contains relevant information about the topic, provide a clear answer based on what you can find.
3. Only respond EXACTLY with: "{refusal_text}" if the context has NO information at all related to the question.
4. Extract ALL specific details from the context (numbers, requirements, dates, procedures).
5. If the context mentions "prescribed by" or "according to" something else, state that clearly.
6. Use plain language that a non-technical citizen can understand.
7. Keep your answer clear and complete (2-5 sentences).
8. If the context discusses the topic but lacks a specific detail the user asked about, answer with what IS available and note what detail is not in the provided excerpts.

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


def _make_snippet(text: str, max_len: int = 400) -> str:
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
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            temperature=0.3,
        )
        self.translation_llm = translation_llm or self.llm
        self.retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K_CHUNKS})
        print("✅ Using OpenAI for LLM and translation")

    def retrieve(self, question: str):
        """Retrieve relevant chunks for a question with smart filtering.
        
        Strategy:
        1. Standard similarity search (works for general questions)
        2. If asking about a specific article/chapter, check if results match
        3. If not, do a SECONDARY search using ChromaDB metadata filters
        4. Merge and prioritize matching results
        """
        import re
        
        article_match = re.search(r'\barticle\s+(\d{1,3})\b', question, re.IGNORECASE)
        chapter_match = re.search(r'\bchapter\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|[IVX]+|\d+)\b', question, re.IGNORECASE)
        
        # First, try standard similarity search
        docs = self.retriever.invoke(question)
        
        # If asking about a specific article/chapter, filter and boost matching results
        if article_match or chapter_match:
            target_article = f"Article {article_match.group(1)}" if article_match else None
            target_chapter = f"Chapter {chapter_match.group(1).title()}" if chapter_match else None
            
            # Separate docs into matching and non-matching
            matching_docs = []
            other_docs = []
            
            for doc in docs:
                metadata = doc.metadata
                matches = False
                
                # Check primary article metadata
                if target_article and metadata.get('article') == target_article:
                    matches = True
                    print(f"✓ Found chunk with {target_article} in metadata['article']")
                # Check all articles in chunk (articles_all is pipe-separated string)
                elif target_article and 'articles_all' in metadata:
                    if target_article in str(metadata['articles_all']):
                        matches = True
                        print(f"✓ Found chunk with {target_article} in metadata['articles_all']")
                # Check chapter
                elif target_chapter and target_chapter in metadata.get('chapter', ''):
                    matches = True
                    print(f"✓ Found chunk with {target_chapter} metadata")
                # Check content
                elif target_article and target_article in doc.page_content[:500]:
                    matches = True
                    print(f"✓ Found chunk containing {target_article} in content")
                elif target_chapter and target_chapter in doc.page_content[:500]:
                    matches = True
                    print(f"✓ Found chunk containing {target_chapter} in content")
                
                if matches:
                    matching_docs.append(doc)
                else:
                    other_docs.append(doc)
            
            # If no matching docs found in similarity results, do a METADATA SEARCH
            if not matching_docs:
                print(f"⚠️ No matches in similarity results — trying metadata search...")
                try:
                    if target_article:
                        # Search by article metadata using ChromaDB where clause
                        metadata_results = self.vector_store.similarity_search(
                            target_article,  # Simple query
                            k=TOP_K_CHUNKS,
                            filter={"article": target_article}
                        )
                        if metadata_results:
                            matching_docs = metadata_results
                            print(f"📌 Metadata search found {len(matching_docs)} chunks for {target_article}")
                        else:
                            # Broader text search — look for the article reference in content
                            # Searches with multiple query variations for best coverage
                            art_num = article_match.group(1)
                            search_queries = [
                                f"{target_article} Constitution of Kenya",
                                f"{target_article} provisions oath office",
                                f"{art_num}. ",
                            ]
                            all_candidates = []
                            for sq in search_queries:
                                text_search_results = self.vector_store.similarity_search(sq, k=15)
                                all_candidates.extend(text_search_results)
                            
                            # Filter to those that actually mention the article
                            seen_keys = set()
                            for doc in all_candidates:
                                in_metadata = target_article in str(doc.metadata.get('articles_all', ''))
                                # Match "Article 74" or "74. " (article number at start of line/text)
                                import re as _re
                                in_content = (target_article in doc.page_content) or \
                                             bool(_re.search(rf'\b{art_num}\.\s', doc.page_content))
                                content_key = doc.page_content[:100]
                                if (in_metadata or in_content) and content_key not in seen_keys:
                                    seen_keys.add(content_key)
                                    matching_docs.append(doc)
                            if matching_docs:
                                print(f"📌 Content search found {len(matching_docs)} chunks mentioning {target_article}")
                    
                    if target_chapter and not matching_docs:
                        # Search for chapter using multiple query variations
                        chapter_val = chapter_match.group(1).title()
                        search_queries = [
                            f"Chapter {chapter_val} Constitution of Kenya",
                            f"CHAPTER {chapter_val.upper()}",
                            f"Chapter {chapter_val} leadership integrity",
                        ]
                        all_candidates = []
                        for sq in search_queries:
                            text_search_results = self.vector_store.similarity_search(sq, k=TOP_K_CHUNKS)
                            all_candidates.extend(text_search_results)
                        
                        seen_keys = set()
                        for doc in all_candidates:
                            chapter_meta = doc.metadata.get('chapter', '')
                            content_preview = doc.page_content[:500]
                            chapter_in_meta = f"Chapter {chapter_val}" in chapter_meta
                            chapter_in_content = f"Chapter {chapter_val}" in content_preview or \
                                                 f"CHAPTER {chapter_val.upper()}" in content_preview
                            content_key = doc.page_content[:100]
                            if (chapter_in_meta or chapter_in_content) and content_key not in seen_keys:
                                seen_keys.add(content_key)
                                matching_docs.append(doc)
                        if matching_docs:
                            print(f"📌 Chapter search found {len(matching_docs)} chunks for {target_chapter}")
                            
                except Exception as e:
                    print(f"⚠️ Metadata search failed: {e}")
            
            # Prioritize matching docs, then add others
            if matching_docs:
                print(f"📌 Found {len(matching_docs)} chunks matching the specific article/chapter")
                # Deduplicate
                seen_content = set()
                unique_matching = []
                for doc in matching_docs:
                    content_key = doc.page_content[:100]
                    if content_key not in seen_content:
                        seen_content.add(content_key)
                        unique_matching.append(doc)
                
                unique_other = []
                for doc in other_docs:
                    content_key = doc.page_content[:100]
                    if content_key not in seen_content:
                        seen_content.add(content_key)
                        unique_other.append(doc)
                
                return unique_matching + unique_other[:max(0, TOP_K_CHUNKS - len(unique_matching))]
            else:
                print(f"⚠️ No chunks found for {target_article or target_chapter}")
                if docs:
                    print(f"   Top result article metadata: {docs[0].metadata.get('article', 'NOT SET')}")
                    print(f"   Top result content preview: {docs[0].page_content[:150]}...")
        
        return docs

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
            "sources": [{"document_title": str, "page": str, "snippet": str}],
            "supported": bool,
        }
        """
        if docs is None:
            docs = self.retrieve(question)

        if not docs:
            return {"answer": REFUSAL_TEXT, "sources": [], "supported": False}

        docs = _prepare_docs(docs)

        # Retrieval confidence gate
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

        # Handle AIMessage or string response
        if hasattr(raw_answer, "content"):
            raw_answer = raw_answer.content
        raw_answer = str(raw_answer).strip()

        if _is_refusal(raw_answer):
            return {"answer": REFUSAL_TEXT, "sources": [], "supported": False}

        citations = _extract_citations(docs)

        # Translate to Kiswahili/Sheng only for supported answers
        if output_language != "en":
            raw_answer = self._translate_answer(raw_answer, output_language, question, self.translation_llm)

        return {
            "answer": raw_answer,
            "sources": citations,
            "supported": True,
        }

    def _translate_answer(self, answer_en: str, target_lang: str, question: str, llm) -> str:
        """Delegate to language module for translation."""
        from .language import translate_answer
        return translate_answer(answer_en, target_lang, question, llm)