# System Map — Haki Sovereign AI Engine

**Complete guide to understanding, owning, and debugging the system.**

---

## Table of Contents

1. [File Structure](#file-structure)
2. [Entry Points](#entry-points)
3. [Runtime Execution Flow](#runtime-execution-flow)
4. [Data Flow](#data-flow)
5. [Dependencies Graph](#dependencies-graph)
6. [Key Concepts](#key-concepts)
7. [How to Trace Through Code](#how-to-trace-through-code)
8. [Common Debugging Paths](#common-debugging-paths)

---

## File Structure

### Core Configuration

**`src/config.py`** — Single source of truth for all configuration

```python
# What it does:
- Defines all paths (data/, vectorstores/)
- Document registry (which PDFs to ingest)
- Model names (embedding, LLM, translation)
- Thresholds (chunk size, retrieval limits, confidence gates)
- Constants (REFUSAL_TEXT — exact phrase for "unsupported")
- Windows OCR paths (TESSERACT_CMD, POPPLER_BIN)

# Key constants:
- REFUSAL_TEXT: Exact string that means "I don't know"
- MIN_MEANINGFUL_CHUNKS: Minimum chunks needed before answering
- MIN_MEANINGFUL_CHUNK_CHARS: Minimum chars per chunk to count as "meaningful"
- MAX_CHUNK_CHARS_IN_PROMPT: Truncate chunks to this before sending to LLM
```

**Dependencies:** None (pure config)

---

### Document Ingestion Layer

**`src/document_loader.py`** — Loads PDFs, extracts text, creates chunks

```python
# Functions:
- load_pdf(file_path, document_title) → list[Document]
  - Computes SHA-256 hash of PDF (integrity)
  - Extracts text with PyPDF
  - Falls back to OCR for scanned pages
  - Attaches metadata: document_title, file_name, page, pdf_sha256, extraction_method

- chunk_documents(pages) → list[Document]
  - Splits pages into chunks (1000 chars, 200 overlap)
  - Preserves all metadata
  - Adds page_display (human-readable page number)

- load_all_documents() → list[Document]
  - Iterates DOCUMENTS registry
  - Loads + chunks each PDF
  - Returns all chunks ready for vector store

# Helper functions:
- _sha256_file(path) → str: Compute file hash
- _clean_ocr_text(text) → str: Normalize whitespace, remove noise
- _extract_with_pypdf(path) → list[Document]: Native PDF text
- _extract_with_ocr(path) → list[Document]: OCR fallback
- _page_has_enough_text(page) → bool: Check if page needs OCR
```

**Dependencies:** `config.py`, `langchain_core.documents`, `langchain_community.document_loaders`, `langchain_text_splitters`, `pdf2image`, `pytesseract` (optional)

**Data flow:** PDF files → Document objects with metadata → Chunked Document objects

---

### Vector Store Layer

**`src/vector_store.py`** — Chroma vector database management

```python
# Functions:
- get_embeddings() → HuggingFaceEmbeddings
  - Returns embedding model (sentence-transformers)
  - Used to convert text → vectors

- build_vector_store(documents, embeddings) → Chroma
  - Creates NEW vector store from documents
  - Computes embeddings for all chunks
  - Persists to disk (vectorstores/haki_sovereign/)

- load_vector_store(embeddings) → Chroma
  - Loads EXISTING vector store from disk
  - Fast (no re-embedding)

- get_vector_store(embeddings, force_rebuild) → Chroma
  - Smart wrapper: builds if missing/rebuild requested, else loads
  - Calls document_loader.load_all_documents() if building
```

**Dependencies:** `config.py`, `document_loader.py` (circular, but lazy-loaded), `langchain_community.vectorstores`, `langchain_community.embeddings`

**Data flow:** Document chunks → Embeddings (vectors) → Chroma DB (persisted)

---

### RAG Engine (Core Logic)

**`src/rag_engine.py`** — Retrieval-Augmented Generation with anti-hallucination

```python
# Class: HakiRAGEngine
- __init__(vector_store, llm=None, translation_llm=None)
  - Stores vector store
  - Creates retriever (searches vector store)
  - Initializes main LLM (Ollama llama3.2)
  - Optional: separate translation LLM (phi3:mini)

- retrieve(question) → list[Document]
  - Converts question to embedding
  - Searches vector store for top K chunks
  - Returns ranked list of Document objects

- answer(question, docs=None, output_language="en") → dict
  - Retrieves chunks (if docs not provided)
  - Cleans/trims chunks (_prepare_docs)
  - Confidence gate: requires MIN_MEANINGFUL_CHUNKS
  - Formats context for LLM
  - Calls LLM with anti-hallucination prompt
  - Checks if answer is refusal (exact match)
  - Extracts citations with snippets
  - Translates if output_language != "en"
  - Returns: {"answer": str, "sources": [...], "supported": bool}

# Helper functions:
- _clean_text(text) → str: Normalize whitespace
- _trim_for_prompt(text, max_chars) → str: Truncate long chunks
- _meaningful(doc) → bool: Check if chunk has enough content
- _prepare_docs(docs) → list: Clean + trim, drop empty
- _format_context(docs) → str: Format chunks for LLM prompt
- _make_snippet(text) → str: Extract 160-240 char snippet
- _extract_citations(docs) → list[dict]: Build citation list with snippets
- _is_refusal(answer) → bool: Exact match against REFUSAL_TEXT
```

**Dependencies:** `config.py`, `language.py`, `langchain_ollama`, `langchain_core.prompts`, `langchain_core.vectorstores`

**Data flow:** Question → Retrieve chunks → Clean/validate → LLM → Answer + Citations

---

### Language Module

**`src/language.py`** — Multilingual detection and translation

```python
# Functions:
- detect_language(text) → "en" | "sw" | "sheng"
  - Uses langdetect for Kiswahili
  - Heuristics for Sheng (slang markers)
  - Defaults to "en"

- translate_answer(answer_en, target_lang, question, llm) → str
  - If target_lang == "en": return as-is
  - If "sw": Translate to Kiswahili via LLM
  - If "sheng": Translate to Sheng, fallback to Kiswahili if unclear
  - Uses prompt templates (TRANSLATE_SWAHILI, TRANSLATE_SHENG)
```

**Dependencies:** `langchain_core.prompts`, `langchain_core.language_models`, `langdetect`

**Data flow:** English answer → LLM translation → Kiswahili/Sheng answer

---

### Main Engine API

**`src/haki_engine.py`** — Public API and orchestration

```python
# Class: HakiSovereignEngine
- __init__(force_rebuild=False)
  - Gets embeddings
  - Gets/creates vector store
  - Tries to create translation LLM (phi3:mini)
  - Creates HakiRAGEngine
  - Initializes in-memory cache

- ask(question, language=None, auto_detect_language=True) → HakiResponse
  - Detects language if not provided
  - Checks cache (normalized question + language)
  - Calls RAG engine
  - Caches result (if supported or refusal)
  - Returns HakiResponse

# Dataclass: HakiResponse
- answer: str
- sources: list[dict]  # [{"document_title": str, "page": str, "snippet": str}]
- supported: bool
- language_used: str
- input_language_detected: str

- format_output() → dict
  - Formats for display/API
  - Includes snippets in sources

# Factory: create_engine(force_rebuild=False) → HakiSovereignEngine
- Singleton pattern (reuses instance)
```

**Dependencies:** `config.py`, `vector_store.py`, `rag_engine.py`, `language.py`, `langchain_ollama`

**Data flow:** User question → Language detection → Cache check → RAG → Response

---

### CLI Entry Points

**`src/run.py`** — Interactive CLI for asking questions

```python
# main()
- Parses CLI args (-q, -f, --demo, --rebuild, -l)
- Creates engine (with rebuild if requested)
- Loads questions (single, file, or demo)
- Calls engine.ask() for each
- Prints formatted output
```

**Dependencies:** `haki_engine.py`, `demo_questions.py`

**Entry point:** `python -m src.run [args]`

---

**`src/acceptance.py`** — Acceptance test runner

```python
# main()
- Creates engine
- Runs all DEMO_QUESTIONS
- Asserts:
  - Unsupported questions → exact REFUSAL_TEXT
  - Supported questions → have sources
- Exits with code 1 if failures
```

**Dependencies:** `haki_engine.py`, `demo_questions.py`, `config.py`

**Entry point:** `python -m src.acceptance [--rebuild]`

---

### Supporting Files

**`src/demo_questions.py`** — 10 acceptance test questions

**`src/__init__.py`** — Package exports (HakiSovereignEngine, HakiResponse, create_engine)

---

## Entry Points

### 1. CLI: Interactive Questions

```bash
# Single question
python -m src.run -q "What are presidential qualifications?"

# From file
python -m src.run -f questions.txt

# Demo questions
python -m src.run --demo

# Rebuild vector store
python -m src.run --rebuild

# Output in Kiswahili
python -m src.run -q "..." -l sw
```

**Flow:** `run.py` → `create_engine()` → `engine.ask()` → prints result

---

### 2. Programmatic API

```python
from src.haki_engine import create_engine

engine = create_engine()
resp = engine.ask("What are presidential qualifications?")
print(resp.answer)
print(resp.sources)
```

**Flow:** `create_engine()` → `HakiSovereignEngine.__init__()` → `engine.ask()` → `HakiResponse`

---

### 3. Acceptance Tests

```bash
python -m src.acceptance --rebuild
```

**Flow:** `acceptance.py` → `create_engine()` → runs all demo questions → asserts behavior

---

## Runtime Execution Flow

### First Run (Building Vector Store)

```
1. User: python -m src.run --rebuild

2. run.py main()
   └─> create_engine(force_rebuild=True)

3. HakiSovereignEngine.__init__(force_rebuild=True)
   ├─> get_embeddings()
   │   └─> HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
   │       (Downloads model if first time)
   │
   ├─> get_vector_store(embeddings, force_rebuild=True)
   │   └─> Checks: DB_DIR exists? → NO (or rebuild=True)
   │       └─> load_all_documents()
   │           ├─> For each PDF in DOCUMENTS:
   │           │   ├─> load_pdf(path, title)
   │           │   │   ├─> _sha256_file(path) → hash
   │           │   │   ├─> _extract_with_pypdf(path) → pages
   │           │   │   ├─> For each page:
   │           │   │   │   └─> If < 50 chars: try OCR
   │           │   │   │       └─> _clean_ocr_text()
   │           │   │   └─> Attach metadata (title, file, hash, method)
   │           │   └─> chunk_documents(pages)
   │           │       └─> RecursiveCharacterTextSplitter
   │           │           └─> Chunks with metadata
   │           └─> Returns all chunks
   │       └─> build_vector_store(chunks, embeddings)
   │           ├─> For each chunk:
   │           │   └─> embeddings.embed_query(chunk.text) → vector
   │           └─> Chroma.from_documents(chunks, embeddings)
   │               └─> Saves to vectorstores/haki_sovereign/
   │
   ├─> Try: Ollama(model="phi3:mini") → translation_llm
   │   (Falls back silently if unavailable)
   │
   └─> HakiRAGEngine(vector_store, translation_llm)
       ├─> Creates retriever (k=6)
       └─> Creates main LLM (Ollama llama3.2)

4. engine.ask(question)
   └─> (See "Subsequent Runs" flow below)
```

---

### Subsequent Runs (Using Existing Vector Store)

```
1. User: python -m src.run -q "What are presidential qualifications?"

2. run.py main()
   └─> create_engine()  # force_rebuild=False

3. HakiSovereignEngine.__init__(force_rebuild=False)
   ├─> get_embeddings() → Returns cached model
   │
   ├─> get_vector_store(embeddings, force_rebuild=False)
   │   └─> Checks: DB_DIR exists? → YES
   │       └─> load_vector_store(embeddings)
   │           └─> Chroma(persist_directory=DB_DIR, ...)
   │               (Loads from disk, fast)
   │
   └─> HakiRAGEngine(vector_store, ...)

4. engine.ask(question, language="en")
   ├─> detect_language(question) → "en"
   │
   ├─> Cache check:
   │   └─> _normalize_question(question) → normalized
   │   └─> cache_key = (normalized, "en")
   │   └─> If in cache: return cached HakiResponse
   │
   ├─> rag.answer(question, output_language="en")
   │   ├─> retrieve(question)
   │   │   └─> retriever.invoke(question)
   │   │       ├─> embeddings.embed_query(question) → query_vector
   │   │       └─> vector_store.similarity_search(query_vector, k=6)
   │   │           └─> Returns top 6 Document chunks
   │   │
   │   ├─> _prepare_docs(docs)
   │   │   ├─> For each doc:
   │   │   │   ├─> _clean_text(doc.page_content)
   │   │   │   └─> _trim_for_prompt(cleaned, 1600 chars)
   │   │   └─> Drops empty docs
   │   │
   │   ├─> Confidence gate:
   │   │   └─> meaningful = [d for d in docs if _meaningful(d)]
   │   │   └─> If len(meaningful) < MIN_MEANINGFUL_CHUNKS:
   │   │       └─> Return {"answer": REFUSAL_TEXT, "sources": [], "supported": False}
   │   │
   │   ├─> _format_context(docs) → context_string
   │   │   └─> Formats: "[1] (Doc - Page X)\n{chunk_text}\n\n---\n\n..."
   │   │
   │   ├─> PromptTemplate + LLM
   │   │   └─> prompt | llm
   │   │       └─> invoke({"context": context_string, "question": question})
   │   │           └─> LLM generates answer
   │   │
   │   ├─> _is_refusal(raw_answer)
   │   │   └─> Check: raw_answer.strip() == REFUSAL_TEXT?
   │   │
   │   ├─> _extract_citations(docs)
   │   │   └─> For each doc:
   │   │       └─> Extract: document_title, page, snippet
   │   │
   │   └─> If output_language != "en":
   │       └─> translate_answer(answer_en, target_lang, question, llm)
   │           └─> (See language.py)
   │
   ├─> Cache result (if supported or refusal)
   │
   └─> Return HakiResponse(answer, sources, supported, ...)

5. resp.format_output()
   └─> Formats sources with snippets
   └─> Returns dict for display
```

---

## Data Flow

### Document Ingestion Pipeline

```
PDF File (data/raw/*.pdf)
    ↓
load_pdf()
    ├─> Compute SHA-256 hash
    ├─> Extract text (PyPDF)
    ├─> OCR fallback (if page < 50 chars)
    └─> Attach metadata:
        - document_title
        - file_name
        - page (0-indexed)
        - page_display (1-indexed)
        - pdf_sha256
        - extraction_method ("pdf_text" | "ocr")
    ↓
Document objects (one per page)
    ↓
chunk_documents()
    ├─> RecursiveCharacterTextSplitter
    │   - chunk_size=1000
    │   - chunk_overlap=200
    └─> Preserve all metadata
    ↓
Chunked Document objects
    ↓
build_vector_store()
    ├─> For each chunk:
    │   └─> embeddings.embed_query(chunk.text) → vector[384]
    └─> Chroma.from_documents(chunks, embeddings)
    ↓
Chroma DB (persisted to disk)
```

---

### Question Answering Pipeline

```
User Question (string)
    ↓
engine.ask(question)
    ├─> detect_language(question) → "en" | "sw" | "sheng"
    ├─> Cache check (normalized question + language)
    │   └─> If hit: return cached
    ↓
rag.answer(question)
    ├─> retrieve(question)
    │   ├─> embeddings.embed_query(question) → query_vector[384]
    │   └─> vector_store.similarity_search(query_vector, k=6)
    │       └─> Returns: top 6 Document chunks (ranked by cosine similarity)
    ↓
Retrieved Document chunks
    ↓
_prepare_docs(docs)
    ├─> _clean_text() → normalize whitespace
    ├─> _trim_for_prompt() → cap at 1600 chars
    └─> Drop empty docs
    ↓
Cleaned Document chunks
    ↓
Confidence Gate
    ├─> Filter: _meaningful(doc) → len(cleaned) >= 250 chars
    └─> If count < MIN_MEANINGFUL_CHUNKS (2):
        └─> Return REFUSAL_TEXT (early exit)
    ↓
_format_context(docs) → context_string
    └─> "[1] (Doc - Page X)\n{chunk}\n\n---\n\n..."
    ↓
LLM Prompt
    ├─> Template: RAG_PROMPT (with REFUSAL_TEXT)
    ├─> Variables: {context}, {question}
    └─> prompt | llm → invoke()
    ↓
LLM Response (raw answer string)
    ↓
_is_refusal(answer)
    └─> answer.strip() == REFUSAL_TEXT?
    ↓
If supported:
    ├─> _extract_citations(docs)
    │   └─> [{"document_title": "...", "page": "...", "snippet": "..."}]
    │
    └─> If output_language != "en":
        └─> translate_answer(answer_en, target_lang, llm)
            └─> LLM translation → translated_answer
    ↓
HakiResponse
    ├─> answer: str
    ├─> sources: list[dict]
    ├─> supported: bool
    ├─> language_used: str
    └─> input_language_detected: str
    ↓
format_output()
    └─> {"answer": "...", "sources": ["Doc — Page X — \"snippet\""], "supported": True}
```

---

## Dependencies Graph

```
config.py (no dependencies)
    ↑
    ├─ document_loader.py
    │   └─> langchain_core.documents
    │   └─> langchain_community.document_loaders
    │   └─> langchain_text_splitters
    │   └─> pdf2image (optional)
    │   └─> pytesseract (optional)
    │
    ├─ vector_store.py
    │   └─> langchain_community.vectorstores
    │   └─> langchain_community.embeddings
    │   └─> document_loader.py (lazy import)
    │
    ├─ rag_engine.py
    │   └─> langchain_ollama
    │   └─> langchain_core.prompts
    │   └─> langchain_core.vectorstores
    │   └─> language.py
    │
    ├─ language.py
    │   └─> langchain_core.prompts
    │   └─> langchain_core.language_models
    │   └─> langdetect
    │
    └─ haki_engine.py
        └─> vector_store.py
        └─> rag_engine.py
        └─> language.py
        └─> langchain_ollama
        │
        └─ run.py
            └─> haki_engine.py
            └─> demo_questions.py
        │
        └─ acceptance.py
            └─> haki_engine.py
            └─> demo_questions.py
            └─> config.py
```

**Key:** `config.py` is the root. Everything else depends on it (directly or transitively).

---

## Key Concepts

### 1. Anti-Hallucination Strategy

**Three layers:**

1. **Retrieval confidence gate**: Requires ≥2 meaningful chunks (≥250 chars each) before calling LLM
2. **Prompt engineering**: Explicit instruction to refuse if context insufficient
3. **Deterministic refusal detection**: Exact string match against `REFUSAL_TEXT`

**Why:** Legal/government info must never guess. Better to say "I don't know" than be wrong.

---

### 2. Singleton Pattern

`HakiSovereignEngine` uses a singleton (`get_instance()`) to:
- Reuse vector store (avoid reloading from disk)
- Reuse LLM instances (avoid reinitializing)
- Share cache across requests

**Trade-off:** Memory stays resident, but faster for repeated questions.

---

### 3. Caching Strategy

**Cache key:** `(normalized_question, output_language)`

**Normalization:**
- Lowercase
- Strip whitespace
- Collapse multiple spaces

**What gets cached:**
- Supported answers (have sources)
- Deterministic refusals (exact REFUSAL_TEXT)

**What doesn't:**
- Partial/uncertain answers (shouldn't happen, but safety)

---

### 4. Translation Architecture

**Two-model approach:**
- Main LLM (`llama3.2`): Reasoning, RAG answers
- Translation LLM (`phi3:mini`): Fast translation only

**Fallback:** If translation LLM unavailable, uses main LLM (slower but works).

**Why:** Translation is simpler than reasoning. Smaller model = faster + cheaper.

---

### 5. OCR Fallback Strategy

**When OCR triggers:**
- Page has < 50 characters after PyPDF extraction
- Likely scanned/image PDF

**Process:**
1. Convert page to image (`pdf2image`)
2. Run OCR (`pytesseract`)
3. Clean text (`_clean_ocr_text`)
4. Drop if still < 50 chars (likely garbage)

**Windows stability:** Requires `TESSERACT_CMD` and `POPPLER_BIN` paths set in `config.py`.

---

### 6. Chunking Strategy

**Parameters:**
- `chunk_size=1000`: Each chunk ~1000 characters
- `chunk_overlap=200`: Adjacent chunks share 200 chars

**Why overlap:** Prevents splitting sentences/phrases. Ensures context continuity.

**Metadata preservation:** All chunk metadata (title, page, hash) preserved through splitting.

---

## How to Trace Through Code

### Scenario: "Why did my question return 'I can't find that information'?"

**Step 1:** Start at entry point
```python
# src/run.py:68
resp = engine.ask(q, language=args.language)
```

**Step 2:** Follow into engine
```python
# src/haki_engine.py:93
def ask(self, question, language=None, ...):
    # Cache check (skip if cache miss)
    result = self.rag.answer(question, output_language=language)
```

**Step 3:** Check retrieval
```python
# src/rag_engine.py:125
def answer(self, question, docs=None, ...):
    if docs is None:
        docs = self.retrieve(question)  # ← Check here
```

**Step 4:** Check confidence gate
```python
# src/rag_engine.py:145-150
docs = _prepare_docs(docs)
meaningful = [d for d in docs if _meaningful(d)]
if len(meaningful) < MIN_MEANINGFUL_CHUNKS:  # ← Early refusal here
    return {"answer": REFUSAL_TEXT, ...}
```

**Step 5:** Check LLM refusal
```python
# src/rag_engine.py:160-165
raw_answer = chain.invoke(...)
supported = not _is_refusal(raw_answer)  # ← Check here
if not supported:
    return {"answer": REFUSAL_TEXT, ...}
```

**Debugging checklist:**
- [ ] Did retrieval return any chunks? (`len(docs) > 0`)
- [ ] Are chunks meaningful? (`len(meaningful) >= 2`)
- [ ] What did LLM actually return? (Check `raw_answer`)
- [ ] Does it exactly match `REFUSAL_TEXT`? (Check `_is_refusal`)

---

### Scenario: "Why is OCR not working on Windows?"

**Step 1:** Check config
```python
# src/config.py:48-49
TESSERACT_CMD: str | None = None
POPPLER_BIN: str | None = None
```

**Step 2:** Check OCR usage
```python
# src/document_loader.py:87-88
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
```

**Step 3:** Check OCR fallback trigger
```python
# src/document_loader.py:90
if not _page_has_enough_text(page):  # < 50 chars
    # Try OCR
```

**Fix:** Set paths in `config.py`:
```python
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_BIN = r"C:\path\to\poppler\Library\bin"
```

---

## Common Debugging Paths

### 1. Vector Store Not Found

**Symptom:** `ValueError: No documents found to build vector store`

**Check:**
- `data/raw/` contains PDFs listed in `DOCUMENTS`?
- File names match exactly (case-sensitive on Linux/Mac)?

**Fix:** Add PDFs to `data/raw/` and ensure names match `DOCUMENTS` keys.

---

### 2. Ollama Not Running

**Symptom:** `ConnectionError` or `Model not found`

**Check:**
- Is Ollama running? (`ollama list`)
- Is `llama3.2` pulled? (`ollama pull llama3.2`)

**Fix:** Start Ollama service and pull required models.

---

### 3. All Questions Refuse

**Symptom:** Every question returns `REFUSAL_TEXT`

**Check:**
- Vector store built? (`vectorstores/haki_sovereign/` exists?)
- Retrieval returning chunks? (Add debug print in `rag_engine.py:140`)
- Confidence gate too strict? (Check `MIN_MEANINGFUL_CHUNKS`, `MIN_MEANINGFUL_CHUNK_CHARS`)

**Fix:** Rebuild vector store, check retrieval, adjust thresholds.

---

### 4. Citations Missing Snippets

**Symptom:** Sources show "Doc — Page X" but no snippet

**Check:**
- `_extract_citations()` called with cleaned docs?
- `_make_snippet()` working? (Check `rag_engine.py:79-83`)

**Fix:** Ensure `_prepare_docs()` runs before `_extract_citations()`.

---

### 5. Translation Not Working

**Symptom:** Answers always in English even with `-l sw`

**Check:**
- `output_language` passed correctly? (Check `haki_engine.py:126`)
- Translation LLM available? (Check `haki_engine.py:69-73`)

**Fix:** Ensure `language` param passed through, check Ollama has translation model.

---

## External Dependencies

### Required

- **Python 3.10+**
- **Ollama** (with `llama3.2` model)
- **langchain** ecosystem (see `requirements.txt`)
- **ChromaDB** (vector database)
- **sentence-transformers** (embeddings)

### Optional (for OCR)

- **Tesseract OCR** (Windows: set `TESSERACT_CMD`)
- **Poppler** (Windows: set `POPPLER_BIN`)
- **pdf2image** + **pytesseract** (Python packages)

---

## Next Steps for Ownership

1. **Run acceptance tests:** `python -m src.acceptance --rebuild`
2. **Add debug prints:** Insert `print()` statements in `rag_engine.py` to see retrieval results
3. **Experiment with thresholds:** Adjust `MIN_MEANINGFUL_CHUNKS` in `config.py` and see impact
4. **Trace a question:** Pick one question, add prints at each step, watch data transform
5. **Read LangChain docs:** Understand `Chroma`, `OllamaLLM`, `PromptTemplate` APIs

---

**You now own the system. Happy debugging! 🚀**
