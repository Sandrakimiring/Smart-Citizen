from pathlib import Path
from langchain_community.vectorstores import Chroma
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from .config import DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return embedding model (multilingual for Kiswahili/Sheng)."""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def build_vector_store(documents: list, embeddings: HuggingFaceEmbeddings) -> Chroma:
    """Build a new Chroma vector store from documents."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(DB_DIR),
    )


def load_vector_store(embeddings: HuggingFaceEmbeddings) -> Chroma:
    """Load existing Chroma vector store."""
    return Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )


def get_vector_store(embeddings: HuggingFaceEmbeddings, force_rebuild: bool = False):
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
