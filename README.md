# Smart-Citizen

**AI Hackathon 2025** — Verified Government Knowledge for Kenyan Citizens

Smart-Citizen is a platform tackling a **national security and civic participation challenge**: when citizens cannot easily access or understand official laws and policies, misinformation spreads, trust erodes, and democratic engagement weakens. We are building multiple MVPs to close this gap.

**Haki Sovereign AI Engine** is **MVP 1** — an AI-powered Verified Government Knowledge Base that helps Kenyan citizens understand official laws and policy documents. It answers questions accurately using only verified source documents (Constitution of Kenya 2010, Finance Bill 2025), with anti-hallucination safeguards and citations.

---

## MVPs (Roadmap)

| MVP | Focus |
|-----|--------|
| **MVP 1** | Haki Sovereign AI Engine — RAG over official PDFs, multilingual (EN/Kiswahili/Sheng), citations, anti-hallucination |
| MVP 2+ | CLI, Web UI, mobile, more documents, and additional features (TBD) |

---

## Step-by-Step: How to Run

### 1. Set up the environment

```bash
conda create -n smartcitizen python=3.10
conda activate smartcitizen
cd C:\Projects\Smart-Citizen
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install langchain-ollama langdetect
```

### 3. Install Ollama and pull the model

- Download [Ollama](https://ollama.ai) and install.
- In a terminal: `ollama pull llama3.2`

### 4. First run (build vector store)

```bash
python -m src.run --rebuild
```

This loads PDFs, creates embeddings, and builds the vector store. It can take several minutes the first time. Subsequent runs load the store quickly.

### 5. Ask questions

**Single question:**
```bash
python -m src.run -q "What are the qualifications for the President of Kenya?"
```

**From a file (one question per line):**
```bash
python -m src.run -f questions_example.txt
```

**Run demo acceptance questions:**
```bash
python -m src.run --demo
```

**Output in Kiswahili:**
```bash
python -m src.run -q "Kura za Rais ni ngapi?" -l sw
```

### 6. After adding new PDFs

```bash
python -m src.run --rebuild
```

---

## Programmatic API

```python
from src.haki_engine import create_engine

engine = create_engine()

resp = engine.ask("What are presidential qualifications?")
print(resp.answer)
print(resp.sources)   # [{"document_title": "...", "page": "..."}]
print(resp.supported) # True if grounded in documents

# Structured output
out = resp.format_output()
# {"answer": "...", "sources": ["Doc — Page X", ...], "supported": True}
```

---

## Project Structure

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for a file-by-file explanation, data flow, and efficiency/LLM options.

```
src/
├── config.py          # Paths, document registry, model settings
├── document_loader.py # PDF + OCR, chunking, metadata
├── vector_store.py    # Chroma vector DB
├── rag_engine.py      # RAG + anti-hallucination + citations
├── language.py        # EN/Kiswahili/Sheng
├── haki_engine.py     # Main API
├── demo_questions.py  # 10 acceptance-test questions
└── run.py             # CLI for asking questions
```

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai) with `llama3.2`
- For OCR of scanned PDFs: `pytesseract` and Tesseract installed
