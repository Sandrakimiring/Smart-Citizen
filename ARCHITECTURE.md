# Architecture — Haki Sovereign AI Engine

This document explains what each file does and how the system fits together.

---

## File-by-File Guide

| File | Purpose |
|------|---------|
| **config.py** | Central configuration: paths to data/vector store, document registry (which PDFs to ingest), embedding model name, chunk size, retrieval settings, and LLM model name. Edit here to add new documents or change models. |
| **document_loader.py** | Document ingestion. Loads PDFs, extracts text with PyPDF; falls back to OCR (pdf2image + pytesseract) for scanned/image pages. Chunks text and attaches metadata: document_title, page_number, file_name, extraction_method. |
| **vector_store.py** | Chroma vector database. Builds embeddings for chunks and stores them, or loads an existing store. Uses HuggingFace sentence-transformers for embeddings. |
| **rag_engine.py** | RAG logic. Retrieves relevant chunks, sends them to the LLM with an anti-hallucination prompt, and formats citations. Never invents information—refuses when context is insufficient. |
| **language.py** | Multilingual support. Detects input language (EN/Kiswahili/Sheng) and translates LLM answers to Kiswahili or Sheng. Uses Sheng→Kiswahili fallback when phrasing is unclear. |
| **haki_engine.py** | Main public API. `HakiSovereignEngine.ask(question, language)` orchestrates retrieval, RAG, and translation. Returns structured `HakiResponse` with answer, sources, and supported flag. |
| **demo_questions.py** | 10 acceptance-test questions for MVP 1 (Constitution, Finance Bill, unsupported). Used by `run.py --demo`. |
| **run.py** | CLI entry point. Accepts `-q` (single question), `-f` (file of questions), `--demo`, `--rebuild`, and `-l` (output language). |
| **mvp1_constitution.py** | Original MVP script (Constitution-only). Kept for reference; superseded by the Haki engine. |

---

## Data Flow

```
PDFs (data/raw/)  →  document_loader  →  chunks + metadata
                                              ↓
                         vector_store  ←  embeddings (HuggingFace)
                                              ↓
User question  →  haki_engine  →  rag_engine  →  retrieve chunks
                                              ↓
                                    LLM (Ollama) + anti-hallucination prompt
                                              ↓
                         language module (if sw/sheng)  →  HakiResponse
```

---

## Efficiency & LLM Options

**When you need efficiency**, you have several options:

| Approach | What to do | Use case |
|----------|------------|----------|
| **Smaller LLM** | Change `OLLAMA_MODEL` in `config.py` to a smaller model (e.g. `llama3.2:1b`, `phi3:mini`) | Faster responses, lower quality |
| **Add a second LLM** | Use a small/fast model for retrieval routing or translation, and a larger model only for the main answer | Hybrid speed + quality |
| **Caching** | Cache embeddings and answers for repeated questions (not implemented yet) | Reduce redundant compute |
| **Async / batch** | Process multiple questions in parallel | Throughput for many users |
| **Lighter embeddings** | Use `all-MiniLM-L6-v2` (already default) instead of multilingual models | Faster ingestion and retrieval |
| **Reuse engine** | Keep one `HakiSovereignEngine` instance instead of creating it per question | Avoid reloading vector store and models |

The current design uses a single Ollama model. To add a separate “efficiency” LLM (e.g. for translation only), you would:

1. Add a second LLM in `config.py` (e.g. `OLLAMA_MODEL_FAST = "phi3:mini"`).
2. In `language.py`, use the fast model for translation instead of the main RAG LLM.

---

## Adding New Documents

1. Put the PDF in `data/raw/`.
2. Add it to `DOCUMENTS` in `config.py`:
   ```python
   DOCUMENTS = {
       "existing.pdf": "Existing Doc",
       "new_document.pdf": "New Document Title",
   }
   ```
3. Rebuild: `python -m src.run --rebuild`
