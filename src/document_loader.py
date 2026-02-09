"""Document ingestion: PDF text extraction with OCR fallback."""

from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import RAW_DATA_DIR, DOCUMENTS, CHUNK_SIZE, CHUNK_OVERLAP

# Optional OCR imports (graceful fallback if not installed)
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def _extract_with_pypdf(file_path: Path) -> list[Document]:
    """Extract text using PyPDF (native text)."""
    loader = PyPDFLoader(str(file_path))
    pages = loader.load()
    return pages


def _extract_with_ocr(file_path: Path) -> list[Document]:
    """Extract text using OCR for scanned/image PDFs."""
    if not OCR_AVAILABLE:
        raise ImportError("pdf2image and pytesseract required for OCR. Install: pip install pdf2image pytesseract")
    images = convert_from_path(file_path)
    docs = []
    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img)
        docs.append(Document(page_content=text.strip(), metadata={"page": i}))
    return docs


def _page_has_enough_text(page: Document, min_chars: int = 50) -> bool:
    """Check if a page has sufficient extractable text."""
    return len(page.page_content.strip()) >= min_chars


def load_pdf(
    file_path: Path,
    document_title: str,
    use_ocr_fallback: bool = True,
) -> list[Document]:
    """
    Load a PDF. Uses native text extraction first; falls back to OCR for pages
    that appear to be scanned (little or no extractable text).
    """
    pages = _extract_with_pypdf(file_path)

    if use_ocr_fallback and OCR_AVAILABLE:
        for i, page in enumerate(pages):
            if not _page_has_enough_text(page):
                try:
                    images = convert_from_path(file_path, first_page=i + 1, last_page=i + 1)
                    if images:
                        ocr_text = pytesseract.image_to_string(images[0])
                        pages[i] = Document(
                            page_content=ocr_text.strip(),
                            metadata={**page.metadata, "extraction_method": "ocr"},
                        )
                except Exception:
                    pass

    for page in pages:
        page.metadata["document_title"] = document_title
        page.metadata["file_name"] = file_path.name
        if "extraction_method" not in page.metadata:
            page.metadata["extraction_method"] = "pdf_text"

    return pages


def chunk_documents(pages: list[Document]) -> list[Document]:
    """Split pages into chunks, preserving metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(pages)
    for c in chunks:
        if "page" in c.metadata and isinstance(c.metadata["page"], int):
            c.metadata["page_display"] = c.metadata["page"] + 1
        else:
            c.metadata["page_display"] = c.metadata.get("page", "N/A")
    return chunks


def load_all_documents() -> list[Document]:
    """Load and chunk all registered documents."""
    all_chunks = []

    for file_name, doc_title in DOCUMENTS.items():
        path = RAW_DATA_DIR / file_name
        if not path.exists():
            continue
        pages = load_pdf(path, doc_title)
        chunks = chunk_documents(pages)
        all_chunks.extend(chunks)

    return all_chunks
