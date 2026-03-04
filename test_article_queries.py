"""Test script to verify article/chapter queries work correctly."""

import sys
from src.haki_engine import create_engine

def test_article_queries():
    """Test specific article queries."""
    print("=" * 80)
    print("Testing Article/Chapter Query Improvements")
    print("=" * 80)
    
    # Initialize engine
    print("\n🚀 Initializing Haki Sovereign Engine...")
    engine = create_engine(force_rebuild=False)
    print("✅ Engine loaded!\n")
    
    # Test cases for article/chapter queries
    test_queries = [
        "What does Article 74 say?",
        "Tell me about Article 73",
        "What is in Chapter Six?",
        "What does Article 27 say about equality?",
        "Article 10 national values",
        "What are the powers in Article 138?",
    ]
    
    print("=" * 80)
    print("Running Test Queries")
    print("=" * 80)
    
    for i, question in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {question}")
        print("=" * 80)
        
        try:
            response = engine.ask(question, language="en")
            
            print(f"\n📊 Result:")
            print(f"   Supported: {response.supported}")
            print(f"   Answer: {response.answer[:200]}..." if len(response.answer) > 200 else f"   Answer: {response.answer}")
            
            if response.sources:
                print(f"\n📚 Sources ({len(response.sources)}):")
                for idx, source in enumerate(response.sources[:3], 1):
                    print(f"   {idx}. {source['document_title']} - Page {source['page']}")
                    if source.get('snippet'):
                        snippet = source['snippet'][:150]
                        print(f"      \"{snippet}...\"")
            else:
                print("\n⚠️ No sources found!")
            
            # Check if answer is meaningful
            if response.supported and len(response.answer) > 50:
                print(f"\n✅ PASSED - Got meaningful answer")
            else:
                print(f"\n❌ FAILED - Answer not meaningful or not supported")
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)

if __name__ == "__main__":
    test_article_queries()
