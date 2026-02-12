"""Configuration for Haki Sovereign AI Engine."""

from pathlib import Path
import os 
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DB_DIR = PROJECT_ROOT / "vectorstores" / "haki_sovereign"
COLLECTION_NAME = "haki_knowledge_base"

# Non-negotiable refusal text (must be exact)
REFUSAL_TEXT = "I can't find that information in the official documents provided."

# Document registry: file_name -> display title
DOCUMENTS = {
    "The_Constitution_of_Kenya_2010.pdf": "Constitution of Kenya 2010",
    "THE FINANCE BILL 2025 (Compressed Copy)_2.pdf": "Finance Bill 2025",
}

# Embedding model. Use paraphrase-multilingual-MiniLM-L12-v2 for better Kiswahili retrieval
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Context cleaning / trimming (before LLM)
MAX_CHUNK_CHARS_IN_PROMPT = 1600
MIN_MEANINGFUL_CHUNK_CHARS = 250
MIN_MEANINGFUL_CHUNKS = 2

# Retrieval
TOP_K_CHUNKS = 6
MIN_RELEVANCE_SCORE = 0.3  # For anti-hallucination threshold

# LLM
OLLAMA_MODEL = "llama3.2"
TRANSLATION_MODEL = "phi3:mini"  # smaller/faster model for translation (optional)


import os

# OpenAI API key 
# Production will use local Ollama models for data sovereignty
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)
USE_OPENAI_FOR_TRANSLATION = True  

# Languages
SUPPORTED_LANGUAGES = ("en", "sw", "sheng")

# OCR (Windows stability)
# Set these if OCR fails on Windows (Finance Bill reliability).
# Example:
#   TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
#   POPPLER_BIN = r"C:\poppler\Library\bin"
TESSERACT_CMD: str | None = None
POPPLER_BIN: str | None = None

TESSERACT_CMD: str | None = r"C:\Users\Sandra\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
POPPLER_BIN: str | None = r"C:\poppler-25.12.0\Library\bin"

