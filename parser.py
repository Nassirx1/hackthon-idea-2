"""PDF text extraction — tries pdfplumber first, falls back to PyMuPDF."""
import io
import os


def extract_text_from_path(pdf_path: str) -> str:
    text = _try_pdfplumber_path(pdf_path)
    if not text or len(text.strip()) < 50:
        text = _try_pymupdf_path(pdf_path)
    return text or ""


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    text = _try_pdfplumber_bytes(pdf_bytes)
    if not text or len(text.strip()) < 50:
        text = _try_pymupdf_bytes(pdf_bytes)
    return text or ""


# ── pdfplumber ────────────────────────────────────────────────────────────────

def _try_pdfplumber_path(path: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return ""


def _try_pdfplumber_bytes(data: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return ""


# ── PyMuPDF ───────────────────────────────────────────────────────────────────

def _try_pymupdf_path(path: str) -> str:
    try:
        import fitz
        doc = fitz.open(path)
        pages = [doc[i].get_text() for i in range(len(doc))]
        doc.close()
        return "\n".join(pages)
    except Exception:
        return ""


def _try_pymupdf_bytes(data: bytes) -> str:
    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        pages = [doc[i].get_text() for i in range(len(doc))]
        doc.close()
        return "\n".join(pages)
    except Exception:
        return ""
