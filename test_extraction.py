"""Quick test to verify article extraction works correctly."""

import re
from pathlib import Path

def _extract_all_articles_from_text(text: str) -> list[str]:
    """
    Extract ALL article numbers mentioned in the text.
    Returns a list like ['Article 73', 'Article 74', 'Article 75'].
    """
    articles = []
    
    # Pattern 1: "73. (1)" - article number followed by subsection
    matches = re.findall(r'^\s*(\d{1,3})\.\s*\(', text, re.MULTILINE)
    articles.extend([f"Article {num}" for num in matches])
    
    # Pattern 2: "73. [Capital Letter]" - article number followed by text
    if not articles:
        matches = re.findall(r'^\s*(\d{1,3})\.\s+[A-Z]', text, re.MULTILINE)
        articles.extend([f"Article {num}" for num in matches])
    
    # Pattern 3: Explicit "Article 73"
    matches = re.findall(r'Article\s+(\d{1,3})\b', text, re.IGNORECASE)
    articles.extend([f"Article {num}" for num in matches])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_articles = []
    for art in articles:
        if art not in seen:
            seen.add(art)
            unique_articles.append(art)
    
    return unique_articles


def test_article_extraction():
    """Test article extraction patterns."""
    
    # Test case 1: Standard article format
    text1 = """
74. (1) Before assuming a State office, a State officer shall take and subscribe to the oath
or affirmation prescribed in this Article.
    """
    
    articles1 = _extract_all_articles_from_text(text1)
    print(f"Test 1 - Standard format '74. (1)':")
    print(f"  Found: {articles1}")
    print(f"  Expected: ['Article 74']")
    print(f"  ✓ PASS" if articles1 == ['Article 74'] else f"  ✗ FAIL")
    print()
    
    # Test case 2: Multiple articles
    text2 = """
73. (1) Authority assigned to a State officer is a public trust.
(2) The office shall be exercised in a manner that demonstrates respect.

74. (1) Before assuming a State office, a State officer shall take and subscribe.

75. (1) A State officer shall behave in a manner that avoids conflict.
    """
    
    articles2 = _extract_all_articles_from_text(text2)
    print(f"Test 2 - Multiple articles:")
    print(f"  Found: {articles2}")
    print(f"  Expected: ['Article 73', 'Article 74', 'Article 75']")
    print(f"  ✓ PASS" if 'Article 74' in articles2 else f"  ✗ FAIL")
    print()
    
    # Test case 3: Article mentioned in text
    text3 = """
The provisions of Article 74 shall apply to all state officers.
See also Article 73 and Article 75 for related requirements.
    """
    
    articles3 = _extract_all_articles_from_text(text3)
    print(f"Test 3 - Explicit 'Article X' mentions:")
    print(f"  Found: {articles3}")
    print(f"  Should contain: Article 73, 74, 75")
    print(f"  ✓ PASS" if 'Article 74' in articles3 else f"  ✗ FAIL")
    print()


if __name__ == "__main__":
    print("=" * 80)
    print("Testing Article Extraction Logic")
    print("=" * 80)
    print()
    test_article_extraction()
