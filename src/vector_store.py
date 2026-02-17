"""Vector store management - supports OpenAI embeddings (cloud) and HuggingFace (local)."""

from pathlib import Path
from langchain_community.vectorstores import Chroma
from .config import DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL, OPENAI_API_KEY


def get_embeddings():
    """
    Return embedding model.
    - Cloud/Render: OpenAI text-embedding-3-small (no torch, lightweight)
    - Local: HuggingFace sentence-transformers (requires torch)
    """
    if OPENAI_API_KEY:
        from langchain_openai import OpenAIEmbeddings
        print("✅ Using OpenAI embeddings (cloud)")
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY,
        )
    else:
        from langchain_huggingface import HuggingFaceEmbeddings
        print("✅ Using HuggingFace embeddings (local)")
        return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def build_vector_store(documents: list, embeddings) -> Chroma:
    """Build a new Chroma vector store from documents."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(DB_DIR),
    )


def load_vector_store(embeddings) -> Chroma:
    """Load existing Chroma vector store."""
    return Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )


def get_vector_store(embeddings, force_rebuild: bool = False):
    """
    Get vector store: load existing or build from documents.
    Use force_rebuild=True to rebuild after adding new documents.
    """
    if force_rebuild or not (DB_DIR.exists() and any(DB_DIR.iterdir())):
        from .document_loader import load_all_documents
        docs = load_all_documents()
        if not docs:
            raise ValueError("No documents found to build vector store")
        return build_vector_store(docs, embeddings)
    return load_vector_store(embeddings)