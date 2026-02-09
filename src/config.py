"""Configuration for Haki Sovereign AI Engine."""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DB_DIR = PROJECT_ROOT / "vectorstores" / "haki_sovereign"
COLLECTION_NAME = "haki_knowledge_base"

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

# Retrieval
TOP_K_CHUNKS = 6
MIN_RELEVANCE_SCORE = 0.3  # For anti-hallucination threshold

# LLM
OLLAMA_MODEL = "llama3.2"

# Languages
SUPPORTED_LANGUAGES = ("en", "sw", "sheng")
