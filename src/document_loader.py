"""Document ingestion: PDF text extraction with OCR fallback and smart header detection."""

import hashlib
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CONSTITUTION_CHAPTERS,
    DOCUMENTS,
    POPPLER_BIN,
    RAW_DATA_DIR,
    TESSERACT_CMD,
)

# Optional OCR imports (graceful fallback if not installed)
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean_ocr_text(text: str) -> str:
    """Light OCR cleanup: normalize whitespace."""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_headers_from_text(text: str) -> dict[str, str]:
    """
    Extract structural headers (chapters, articles, sections, schedules) from text.
    Handles Constitution (18 chapters, 264 articles, 6 schedules) and legislative acts.
    """
    headers = {}
    
    # Chapter patterns - handle "CHAPTER SIX—LEADERSHIP AND INTEGRITY"
    chapter_match = re.search(
        r'CHAPTER\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN|[IVX]+|\d+)[\s—\-:]+([A-Z][A-Z\s&,]+)',
        text,
        re.IGNORECASE
    )
    if chapter_match:
        chapter_num = chapter_match.group(1).title()
        chapter_title = chapter_match.group(2).strip()
        chapter_title = re.sub(r'\s+', ' ', chapter_title)
        chapter_title = chapter_title.rstrip('—-:,. ')
        
        headers['chapter'] = f"Chapter {chapter_num}"
        # Use Constitution mapping if available
        if chapter_num in CONSTITUTION_CHAPTERS:
            headers['chapter_full'] = f"Chapter {chapter_num} - {CONSTITUTION_CHAPTERS[chapter_num]}"
        elif len(chapter_title) > 3:
            headers['chapter_full'] = f"Chapter {chapter_num} - {chapter_title}"
        else:
            headers['chapter_full'] = headers['chapter']
    
    # Article patterns - tight matching to avoid false positives
    # Only match numbers at line start followed by period (not subsection numbers)
    article_num = None
    
    # Pattern 1: "73. (1)" - article start with subsection
    if not article_num:
        match = re.search(r'^(\d{1,3})\.\s*\(1\)', text, re.MULTILINE)
        if match:
            article_num = match.group(1)
    
    # Pattern 2: "73. [Capital Letter]" at line start only
    if not article_num:
        match = re.search(r'^(\d{1,3})\.\s+[A-Z]', text, re.MULTILINE)
        if match:
            article_num = match.group(1)
    
    # Pattern 3: Explicit "Article 73"
    if not article_num:
        match = re.search(r'Article\s+(\d{1,3})\b', text, re.IGNORECASE)
        if match:
            article_num = match.group(1)
    
    if article_num:
        headers['article'] = f"Article {article_num}"
    
    # Schedule detection (Constitution has 6 Schedules)
    schedule_names = ['FIRST', 'SECOND', 'THIRD', 'FOURTH', 'FIFTH', 'SIXTH']
    schedule_match = re.search(
        r'(' + '|'.join(schedule_names) + r')\s+SCHEDULE',
        text,
        re.IGNORECASE
    )
    if schedule_match:
        schedule_name = schedule_match.group(1).title()
        headers['schedule'] = f"{schedule_name} Schedule"
    
    # Section patterns for legislative acts (e.g., "Section 5", "Part II")
    section_match = re.search(
        r'(?:Section|Part)\s+([IVX]+|\d+)\b',
        text,
        re.IGNORECASE
    )
    if section_match:
        headers['section'] = section_match.group(0)
    
    return headers


def _extract_with_pypdf(file_path: Path) -> list[Document]:
    """Extract text using PyPDF (native text)."""
    loader = PyPDFLoader(str(file_path))
    pages = loader.load()
    return pages


def _extract_with_ocr(file_path: Path) -> list[Document]:
    """Extract text using OCR for scanned/image PDFs."""
    if not OCR_AVAILABLE:
        raise ImportError("pdf2image and pytesseract required for OCR")
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    images = convert_from_path(file_path, poppler_path=POPPLER_BIN)
    docs = []
    for i, img in enumerate(images):
        text = _clean_ocr_text(pytesseract.image_to_string(img))
        if len(text) < 50:
            continue
        docs.append(Document(
            page_content=text,
            metadata={"page": i, "extraction_method": "ocr"}
        ))
    return docs


def _page_has_enough_text(page: Document, min_chars: int = 50) -> bool:
    """Check if a page has sufficient extractable text."""
    return len(page.page_content.strip()) >= min_chars


def _extract_all_articles_from_text(text: str) -> list[str]:
    """
    Extract ALL article numbers mentioned in the text.
    Returns a list like ['Article 73', 'Article 74', 'Article 75'].
    
    Uses tight matching at line start to avoid false positives from
    subsection numbers like (6) or page numbers.
    """
    articles = []
    
    # Pattern 1: "73. (1)" - article start with subsection (1)
    matches = re.findall(r'^(\d{1,3})\.\s*\(1\)', text, re.MULTILINE)
    articles.extend([f"Article {num}" for num in matches])
    
    # Pattern 2: "73. [Capital Letter]" at line start — main article text
    matches = re.findall(r'^(\d{1,3})\.\s+[A-Z]', text, re.MULTILINE)
    articles.extend([f"Article {num}" for num in matches])
    
    # Pattern 3: Explicit "Article 73" anywhere in text
    matches = re.findall(r'Article\s+(\d{1,3})\b', text, re.IGNORECASE)
    articles.extend([f"Article {num}" for num in matches])
    
    # Pattern 4: "Section 5" in legislative acts (treated as article synonym)
    section_matches = re.findall(r'Section\s+(\d{1,3})\b', text, re.IGNORECASE)
    articles.extend([f"Section {num}" for num in section_matches])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_articles = []
    for art in articles:
        if art not in seen:
            seen.add(art)
            unique_articles.append(art)
    
    return unique_articles


def _extract_cross_references(text: str) -> list[str]:
    """
    Extract cross-referenced articles (e.g., 'subject to Article 24',
    'under Article 159', 'Articles 74, 141(3), 148(5)').
    """
    refs = []
    # Match "Article(s) 74" or "Article 74, 141(3), 148(5)"
    matches = re.findall(r'Articles?\s+(\d{1,3})(?:\([^)]*\))?(?:[,\s]+(?:and\s+)?(\d{1,3})(?:\([^)]*\))?)*', text, re.IGNORECASE)
    for match_groups in matches:
        for num in match_groups:
            if num:
                refs.append(f"Article {num}")
    
    # Deduplicate
    return list(set(refs))


def _track_document_structure(pages: list[Document]) -> list[Document]:
    """
    Analyze document structure and add header context to each page.
    This makes chapters/articles searchable.
    
    NEW: Extracts ALL articles on each page, not just the first one.
    """
    current_chapter = None
    
    for page in pages:
        text = page.page_content
        
        # Check for chapter headers on this page
        headers = _extract_headers_from_text(text)
        
        # Update current chapter if new chapter found
        if 'chapter_full' in headers:
            current_chapter = headers['chapter_full']
        
        # Add chapter to metadata
        if current_chapter:
            page.metadata['chapter'] = current_chapter
        
        # Extract ALL articles on this page (not just one)
        articles_on_page = _extract_all_articles_from_text(text)
        
        # Store primary article (first one found) for backward compatibility
        if articles_on_page:
            page.metadata['article'] = articles_on_page[0]
            # Store all articles as pipe-separated string (ChromaDB requires scalar metadata)
            page.metadata['articles_all'] = '|'.join(articles_on_page)
    
    return pages


def load_pdf(
    file_path: Path,
    document_title: str,
    use_ocr_fallback: bool = True,
) -> list[Document]:
    """
    Load a PDF with smart header detection.
    Automatically detects and tracks chapters/articles/sections.
    """
    pdf_sha256 = _sha256_file(file_path)
    pages = _extract_with_pypdf(file_path)

    # OCR fallback for scanned pages
    if use_ocr_fallback and OCR_AVAILABLE:
        if TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        for i, page in enumerate(pages):
            if not _page_has_enough_text(page):
                try:
                    images = convert_from_path(
                        file_path,
                        first_page=i + 1,
                        last_page=i + 1,
                        poppler_path=POPPLER_BIN,
                    )
                    if images:
                        ocr_text = _clean_ocr_text(pytesseract.image_to_string(images[0]))
                        if len(ocr_text) >= 50:
                            pages[i] = Document(
                                page_content=ocr_text,
                                metadata={**page.metadata, "extraction_method": "ocr"},
                            )
                except Exception:
                    pass

    # Track document structure (chapters, articles)
    pages = _track_document_structure(pages)

    # Add standard metadata to all pages
    for page in pages:
        page.metadata["document_title"] = document_title
        page.metadata["file_name"] = file_path.name
        page.metadata["pdf_sha256"] = pdf_sha256
        if "extraction_method" not in page.metadata:
            page.metadata["extraction_method"] = "pdf_text"

    return pages


def chunk_documents(pages: list[Document]) -> list[Document]:
    """
    Split pages into chunks, preserving and enhancing metadata.
    Injects chapter/article context into chunk text for better searchability.
    
    NEW: Each chunk is tagged with the SPECIFIC articles it contains.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(pages)
    
    for chunk in chunks:
        # Fix page display
        if "page" in chunk.metadata and isinstance(chunk.metadata["page"], int):
            chunk.metadata["page_display"] = str(chunk.metadata["page"] + 1)
        else:
            chunk.metadata["page_display"] = str(chunk.metadata.get("page", "N/A"))
        
        # CRITICAL FIX: Extract articles directly from THIS chunk's content
        # This ensures each chunk knows which articles it actually contains
        chunk_articles = _extract_all_articles_from_text(chunk.page_content)
        
        if chunk_articles:
            # Set primary article (only Article types, not Section)
            article_types = [a for a in chunk_articles if a.startswith('Article')]
            if article_types:
                chunk.metadata['article'] = article_types[0]
            # Store all articles/sections as pipe-separated string (ChromaDB requires scalar)
            chunk.metadata['articles_all'] = '|'.join(chunk_articles)
        
        # Extract cross-references (articles referenced by "subject to Article X")
        cross_refs = _extract_cross_references(chunk.page_content)
        if cross_refs:
            chunk.metadata['cross_refs'] = '|'.join(cross_refs)
        
        # Build context tags for searchability
        context_parts = []
        
        # Add chapter context
        if "chapter" in chunk.metadata:
            chapter = chunk.metadata["chapter"]
            context_parts.append(chapter)
        
        # Add schedule context
        if "schedule" in chunk.metadata:
            context_parts.append(chunk.metadata["schedule"])
        
        # Add ALL articles found in this chunk (emphasized for search)
        if chunk_articles:
            for article in chunk_articles:
                context_parts.append(article)
                context_parts.append(article)  # Duplicate for emphasis
        
        # Add section/part context
        if "section" in chunk.metadata:
            context_parts.append(chunk.metadata["section"])
        
        if context_parts:
            # Add context to beginning of chunk text (highly searchable)
            context_line = " | ".join(context_parts)
            chunk.page_content = f"[{context_line}]\n\n{chunk.page_content}"
            
            # Also add article markers at the end
            if chunk_articles:
                article_markers = " ".join([f"--- {art} ---" for art in chunk_articles])
                chunk.page_content += f"\n\n{article_markers}"
    
    return chunks


def load_all_documents() -> list[Document]:
    """
    Load and chunk all registered documents.
    Automatically handles structure detection for any document type.
    """
    all_chunks = []

    for file_name, doc_title in DOCUMENTS.items():
        path = RAW_DATA_DIR / file_name
        if not path.exists():
            print(f"⚠️  Skipping {file_name} - file not found")
            continue
        
        print(f"📄 Loading {doc_title}...")
        pages = load_pdf(path, doc_title)
        
        # Debug: Show article coverage
        articles_found = set()
        for page in pages:
            if 'articles_all' in page.metadata:
                articles_found.update(page.metadata['articles_all'])
        if articles_found:
            sample_articles = sorted(list(articles_found))[:10]
            print(f"   📌 Detected articles: {', '.join(sample_articles)}... (total: {len(articles_found)})")
        
        chunks = chunk_documents(pages)
        all_chunks.extend(chunks)
        
        # Debug: Show sample chunk with article metadata
        chunks_with_articles = [c for c in chunks if 'article' in c.metadata]
        if chunks_with_articles:
            sample = chunks_with_articles[0]
            print(f"   📝 Sample chunk: Article={sample.metadata.get('article')}, Content={sample.page_content[:100]}...")
        
        print(f"   ✅ Created {len(chunks)} chunks")

    print(f"\n🎉 Total: {len(all_chunks)} chunks from {len(DOCUMENTS)} documents")
    return all_chunks