"""Rebuild vector store with improved article/chapter metadata."""

import shutil
from pathlib import Path
from src.haki_engine import create_engine
from src.config import DB_DIR

def rebuild_vector_store():
    """Rebuild the vector store from scratch."""
    print("=" * 80)
    print("Rebuilding Vector Store with Enhanced Article Metadata")
    print("=" * 80)
    
    # Delete existing vector store
    if DB_DIR.exists():
        print(f"\n🗑️  Deleting existing vector store at {DB_DIR}")
        try:
            shutil.rmtree(DB_DIR)
            print("✅ Old vector store deleted")
        except Exception as e:
            print(f"⚠️  Warning: Could not delete old store: {e}")
    
    # Rebuild with force_rebuild=True
    print("\n🔨 Building new vector store...")
    print("This will:")
    print("  1. Load all PDFs")
    print("  2. Extract chapter/article metadata")
    print("  3. Create enhanced chunks with metadata tags")
    print("  4. Build new vector embeddings")
    print()
    
    try:
        engine = create_engine(force_rebuild=True)
        print("\n✅ Vector store rebuilt successfully!")
        
        # Get stats
        collection = engine.rag.vector_store._collection
        count = collection.count()
        print(f"\n📊 Stats:")
        print(f"   Total chunks in vector store: {count}")
        
        # Sample a few chunks to verify metadata
        print("\n🔍 Sampling chunks to verify metadata...")
        sample_docs = engine.rag.vector_store.similarity_search("Article 74", k=3)
        
        for i, doc in enumerate(sample_docs, 1):
            print(f"\n   Sample {i}:")
            print(f"   - Article: {doc.metadata.get('article', 'N/A')}")
            print(f"   - Chapter: {doc.metadata.get('chapter', 'N/A')}")
            print(f"   - Content preview: {doc.page_content[:150]}...")
        
        print("\n" + "=" * 80)
        print("✅ Rebuild Complete! You can now test article queries.")
        print("=" * 80)
        print("\nNext step: Run 'python test_article_queries.py' to test")
        
    except Exception as e:
        print(f"\n❌ Error during rebuild: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = rebuild_vector_store()
    exit(0 if success else 1)
