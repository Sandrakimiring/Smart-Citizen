"""Configuration for Haki Sovereign AI Engine."""

from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Paths
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DB_DIR = PROJECT_ROOT / "vectorstores" / "haki_sovereign"
COLLECTION_NAME = "haki_knowledge_base"

# Non-negotiable refusal text (must be exact)
REFUSAL_TEXT = "I can't find that information in the official documents provided."

# Document registry: file_name -> display title
DOCUMENTS = {
    "The_Constitution_of_Kenya_2010.pdf": "Constitution of Kenya 2010",
    "THE FINANCE BILL 2025 (Compressed Copy)_2.pdf": "Finance Bill 2025",
    "Access To Information Act No31 of 2016 (1).pdf": "Access to Information Act No. 31 of 2016",
    "Computer Misuse and Cybercrimes Act 2018.pdf": "Computer Misuse and Cybercrimes Act 2018",
    "KE_Prevention_Terrorism_Act.pdf": "Prevention of Terrorism Act",
    "National-Strategy-to-Counter-Violent-Extremism-NSCVE-1.pdf": "National Strategy to Counter Violent Extremism",
    "TheDataProtectionAct__No24of2019.pdf": "Data Protection Act No. 24 of 2019",
    "national-security-council-bill-2012.pdf": "National Security Council Bill 2012",
}

# Constitution chapter mapping (18 chapters) for better metadata tagging
CONSTITUTION_CHAPTERS = {
    "One": "Sovereignty of the People",
    "Two": "The Republic",
    "Three": "Citizenship",
    "Four": "The Bill of Rights",
    "Five": "Land and Environment",
    "Six": "Leadership and Integrity",
    "Seven": "Representation of the People",
    "Eight": "The Legislature",
    "Nine": "The Executive",
    "Ten": "Judiciary",
    "Eleven": "Devolved Government",
    "Twelve": "Public Finance",
    "Thirteen": "The Public Service",
    "Fourteen": "National Security",
    "Fifteen": "Commissions and Independent Offices",
    "Sixteen": "Amendment of this Constitution",
    "Seventeen": "General Provisions",
    "Eighteen": "Transitional and Consequential Provisions",
}

# Embedding model (used only for local/HuggingFace fallback)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)
USE_OPENAI_FOR_TRANSLATION = True

# Chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Context cleaning / trimming (before LLM)
MAX_CHUNK_CHARS_IN_PROMPT = 1600
MIN_MEANINGFUL_CHUNK_CHARS = 250
MIN_MEANINGFUL_CHUNKS = 2

# Retrieval
TOP_K_CHUNKS = 10  # Increased to get more context for specific articles
MIN_RELEVANCE_SCORE = 0.3

# LLM
OLLAMA_MODEL = "llama3.2"
TRANSLATION_MODEL = "phi3:mini"

# Languages
SUPPORTED_LANGUAGES = ("en", "sw", "sheng")

# OCR - only used locally, not on Render
# On Windows, set these in .env or environment variables
# On Render/Linux, these should be None (OCR not supported in cloud deployment)
TESSERACT_CMD: str | None = os.environ.get("TESSERACT_CMD", None)
POPPLER_BIN: str | None = os.environ.get("POPPLER_BIN", None)