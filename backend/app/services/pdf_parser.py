import io
import re
from typing import Any

fitz: Any | None
try:
    import fitz  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    fitz = None

PdfReader: Any | None
try:
    from pypdf import PdfReader  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    PdfReader = None

pdfplumber: Any | None
try:
    import pdfplumber  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pdfplumber = None


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract readable text from a PDF file's bytes."""
    if not file_bytes:
        raise ValueError("PDF content is empty")

    if fitz is not None:
        document = fitz.open(stream=file_bytes, filetype="pdf")
        pages = [page.get_text() or "" for page in document]
        return "\n".join(page for page in pages if page).strip()

    if PdfReader is not None:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(page for page in pages if page).strip()

    if pdfplumber is not None:
        with pdfplumber.open(io.BytesIO(file_bytes)) as document:
            pages = [page.extract_text() or "" for page in document.pages]
            return "\n".join(page for page in pages if page).strip()

    raise ValueError("No PDF extraction library is installed")


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[str]:
    """Split text into roughly sized chunks with a small overlap for context retention."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap must be zero or greater")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(start + chunk_size - overlap, start + 1)

    return chunks
