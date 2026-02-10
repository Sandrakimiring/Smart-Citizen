"""Document ingestion: PDF text extraction with OCR fallback."""

import hashlib
import re
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
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
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean_ocr_text(text: str) -> str:
    """Light OCR cleanup: normalize whitespace, drop obvious garbage runs."""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_with_pypdf(file_path: Path) -> list[Document]:
    """Extract text using PyPDF (native text)."""
    loader = PyPDFLoader(str(file_path))
    pages = loader.load()
    return pages


def _extract_with_ocr(file_path: Path) -> list[Document]:
    """Extract text using OCR for scanned/image PDFs."""
    if not OCR_AVAILABLE:
        raise ImportError("pdf2image and pytesseract required for OCR. Install: pip install pdf2image pytesseract")
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    images = convert_from_path(file_path, poppler_path=POPPLER_BIN)
    docs = []
    for i, img in enumerate(images):
        text = _clean_ocr_text(pytesseract.image_to_string(img))
        if len(text) < 50:
            continue
        docs.append(Document(page_content=text, metadata={"page": i, "extraction_method": "ocr"}))
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
    pdf_sha256 = _sha256_file(file_path)
    pages = _extract_with_pypdf(file_path)

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
                        if len(ocr_text) < 50:
                            continue
                        pages[i] = Document(
                            page_content=ocr_text,
                            metadata={**page.metadata, "extraction_method": "ocr"},
                        )
                except Exception:
                    pass

    for page in pages:
        page.metadata["document_title"] = document_title
        page.metadata["file_name"] = file_path.name
        page.metadata["pdf_sha256"] = pdf_sha256
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
