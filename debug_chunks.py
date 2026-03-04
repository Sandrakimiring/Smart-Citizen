"""Debug script to check what's actually in the vector store."""

from src.haki_engine import create_engine
from src.vector_store import get_vector_store, get_embeddings

def debug_chunks():
    """Check what chunks look like and what metadata they have."""
    print("=" * 80)
    print("Debugging Vector Store Chunks")
    print("=" * 80)
    
    # Load vector store directly
    embeddings = get_embeddings()
    vector_store = get_vector_store(embeddings)
    
    # Search for Article 74 specifically
    print("\n🔍 Searching for 'Article 74' directly...")
    results = vector_store.similarity_search("Article 74", k=5)
    
    print(f"\nFound {len(results)} results\n")
    
    for i, doc in enumerate(results, 1):
        print(f"\n{'=' * 80}")
        print(f"Result {i}:")
        print(f"{'=' * 80}")
        print(f"Metadata:")
        print(f"  - article: {doc.metadata.get('article', 'NOT SET')}")
        print(f"  - chapter: {doc.metadata.get('chapter', 'NOT SET')}")
        print(f"  - chapter_full: {doc.metadata.get('chapter_full', 'NOT SET')}")
        print(f"  - page: {doc.metadata.get('page', 'NOT SET')}")
        print(f"  - document_title: {doc.metadata.get('document_title', 'NOT SET')}")
        print(f"\nContent (first 300 chars):")
        print(doc.page_content[:300])
        print(f"\nContent (last 100 chars):")
        print(doc.page_content[-100:] if len(doc.page_content) > 100 else doc.page_content)
    
    # Now search for specific text that should be in Article 74
    print("\n" + "=" * 80)
    print("Searching for 'oath' (common in Article 74)...")
    print("=" * 80)
    results2 = vector_store.similarity_search("state officer oath Article 74", k=3)
    
    for i, doc in enumerate(results2, 1):
        print(f"\nResult {i}:")
        print(f"  Article: {doc.metadata.get('article', 'NOT SET')}")
        print(f"  Content preview: {doc.page_content[:200]}")
    
    # Check collection stats
    print("\n" + "=" * 80)
    print("Collection Statistics")
    print("=" * 80)
    collection = vector_store._collection
    print(f"Total chunks: {collection.count()}")
    
    # Get a random sample of 10 chunks to see what articles are present
    print("\n" + "=" * 80)
    print("Random sample of articles in the database:")
    print("=" * 80)
    
    sample_results = vector_store.similarity_search("constitution", k=20)
    articles_found = set()
    for doc in sample_results:
        if 'article' in doc.metadata:
            articles_found.add(doc.metadata['article'])
    
    print(f"\nArticles found in sample: {sorted(articles_found)}")
    
    # Check specifically if Article 74 exists
    print("\n" + "=" * 80)
    print("Checking if Article 74 exists in ANY chunk...")
    print("=" * 80)
    
    # Get many results and check them all
    many_results = vector_store.similarity_search("Article 74 oath state officer", k=50)
    
    article_74_chunks = []
    for doc in many_results:
        if doc.metadata.get('article') == 'Article 74':
            article_74_chunks.append(doc)
        elif 'Article 74' in doc.page_content[:200]:  # Check beginning of content
            print(f"\n✓ Found 'Article 74' in content but metadata is: {doc.metadata.get('article', 'NOT SET')}")
            print(f"  Content: {doc.page_content[:200]}")
    
    if article_74_chunks:
        print(f"\n✅ Found {len(article_74_chunks)} chunks with Article 74 in metadata!")
        for chunk in article_74_chunks[:2]:
            print(f"\n  Content: {chunk.page_content[:300]}")
    else:
        print("\n❌ NO chunks found with 'Article 74' in metadata")
        print("\nThis means the article metadata is not being set correctly during document loading.")

if __name__ == "__main__":
    debug_chunks()
