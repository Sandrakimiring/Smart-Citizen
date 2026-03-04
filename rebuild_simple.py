"""Rebuild vector store - simpler version without emoji."""

import shutil
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import DB_DIR
from src.vector_store import get_embeddings, build_vector_store
from src.document_loader import load_all_documents

def rebuild():
    """Rebuild vector store from scratch."""
    print("=" * 80)
    print("Rebuilding Vector Store")
    print("=" * 80)
    print()
    
    # Delete existing
    if DB_DIR.exists():
        print(f"Deleting old vector store at {DB_DIR}")
        try:
            shutil.rmtree(DB_DIR)
            print("Old store deleted")
        except Exception as e:
            print(f"Warning: {e}")
            return False
    
    print()
    print("Loading documents and building new vector store...")
    print()
    
    try:
        # Load documents
        docs = load_all_documents()
        
        if not docs:
            print("ERROR: No documents loaded!")
            return False
        
        print()
        print(f"Building embeddings for {len(docs)} chunks...")
        
        # Get embeddings
        embeddings = get_embeddings()
        
        # Build vector store
        vector_store = build_vector_store(docs, embeddings)
        
        # Get stats
        count = vector_store._collection.count()
        print()
        print("=" * 80)
        print(f"SUCCESS! Vector store rebuilt with {count} chunks")
        print("=" * 80)
        print()
        print("Next: Run 'python test_article_queries.py'")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = rebuild()
    sys.exit(0 if success else 1)
