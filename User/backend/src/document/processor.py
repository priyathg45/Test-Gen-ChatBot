"""Extract text from PDFs and images for chatbot context.
Uses PyMuPDF/PyPDF2 first; for scanned/image-only PDFs falls back to OCR (pdf2image + Tesseract).
"""
import io
import logging
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Max pages to extract from a single PDF (avoids hang on huge/scanned PDFs)
PDF_MAX_PAGES = 500
# Timeout in seconds for PDF extraction (avoids stuck upload/chat)
PDF_EXTRACTION_TIMEOUT = 45
# If text extraction yields fewer than this, try OCR (scanned PDFs)
PDF_MIN_TEXT_CHARS_DEFAULT = 100

# Optional imports with fallbacks (PyMuPDF is sometimes importable as fitz)
try:
    import pymupdf
    _PDF_MODULE = pymupdf
    HAS_PYMUPDF = True
except ImportError:
    try:
        import fitz as pymupdf
        _PDF_MODULE = pymupdf
        HAS_PYMUPDF = True
    except ImportError:
        _PDF_MODULE = None
        HAS_PYMUPDF = False

try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from pdf2image import convert_from_bytes
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

# Single-thread executor for PDF extraction (avoids spawning many threads)
_pdf_executor: Optional[ThreadPoolExecutor] = None


def _get_pdf_executor() -> ThreadPoolExecutor:
    global _pdf_executor
    if _pdf_executor is None:
        _pdf_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pdf_extract")
    return _pdf_executor


def _extract_text_from_pdf_impl(content: bytes, filename: str, max_pages: int) -> str:
    """
    Actual PDF extraction logic. Runs in a thread; one bad page or slow PDF
    won't block the caller indefinitely. Tries multiple extraction methods
    so that PDFs with different encodings/layouts still yield text.
    """
    doc = None
    try:
        # PyMuPDF: open from bytes
        doc = _PDF_MODULE.open(stream=content, filetype="pdf")
        parts: List[str] = []
        page_count = 0
        for page in doc:
            if page_count >= max_pages:
                logger.warning("PDF %s truncated at %d pages", filename or "(stream)", max_pages)
                break
            page_text = ""
            try:
                # Primary: plain text with layout sort
                page_text = page.get_text("text", sort=True)
            except Exception as e:
                logger.debug("get_text('text') failed for page %s: %s", page_count + 1, e)
            if not (page_text or "").strip():
                try:
                    # Fallback: default text extraction
                    page_text = page.get_text()
                except Exception as e:
                    logger.debug("get_text() fallback failed for page %s: %s", page_count + 1, e)
            if not (page_text or "").strip():
                try:
                    # Fallback: dict blocks (some PDFs expose text only this way)
                    block_dict = page.get_text("dict")
                    if block_dict and "blocks" in block_dict:
                        for block in block_dict.get("blocks", []):
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    page_text += (span.get("text") or "") + " "
                except Exception as e:
                    logger.debug("get_text('dict') fallback failed for page %s: %s", page_count + 1, e)
            parts.append((page_text or "").strip())
            page_count += 1
        text = "\n\n".join(p for p in parts if p).strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text
    except Exception as e:
        logger.warning("PyMuPDF open/extract failed for %s: %s", filename or "stream", e)
        return ""
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception as e:
                logger.warning("Error closing PDF document: %s", e)


def extract_text_from_pdf(
    content: bytes,
    filename: str = "",
    timeout: Optional[int] = None,
    max_pages: Optional[int] = None,
) -> str:
    """
    Extract text from a PDF file with a timeout and per-page safety so the
    process never hangs the upload or chat.

    Tries PyMuPDF/fitz first (fast and layout-aware). If that is not
    available or returns empty text, falls back to PyPDF2 as a secondary
    extractor so we still get something for most PDFs.

    Args:
        content: Raw PDF bytes
        filename: Optional filename for logging
        timeout: Max seconds for extraction (default PDF_EXTRACTION_TIMEOUT)
        max_pages: Max pages to extract (default PDF_MAX_PAGES)

    Returns:
        Extracted text or empty string on failure/timeout.
    """
    timeout = timeout if timeout is not None else PDF_EXTRACTION_TIMEOUT
    max_pages = max_pages if max_pages is not None else PDF_MAX_PAGES

    text = ""

    # First try PyMuPDF / fitz when available.
    if HAS_PYMUPDF and _PDF_MODULE is not None:
        try:
            future = _get_pdf_executor().submit(_extract_text_from_pdf_impl, content, filename, max_pages)
            text = future.result(timeout=timeout) or ""
            if text.strip():
                logger.info("Extracted %d characters from PDF %s via PyMuPDF", len(text), filename or "(stream)")
                return text
        except FuturesTimeoutError:
            logger.warning("PDF extraction (PyMuPDF) timed out after %ds for %s", timeout, filename or "stream")
        except Exception as e:
            logger.warning("PDF extraction via PyMuPDF failed for %s: %s", filename or "stream", e)

    # Fallback: try PyPDF2 if installed.
    try:
        import PyPDF2  # type: ignore

        try:
            reader = PyPDF2.PdfReader(io.BytesIO(content))
        except Exception as e:
            logger.warning("PyPDF2 could not open PDF %s: %s", filename or "stream", e)
        else:
            parts: List[str] = []
            num_pages = len(reader.pages)
            for i in range(min(num_pages, max_pages)):
                try:
                    page = reader.pages[i]
                    parts.append(page.extract_text() or "")
                except Exception as e:
                    logger.warning("PyPDF2 page %s failed for %s: %s", i + 1, filename or "stream", e)
                    parts.append("")
            text = "\n\n".join(parts).strip()
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r"[ \t]+", " ", text)
            if text:
                logger.info("Extracted %d characters from PDF %s via PyPDF2", len(text), filename or "(stream)")
                return text
    except ImportError:
        logger.warning("PyPDF2 not installed; PDF fallback extractor unavailable")
    except Exception as e:
        logger.warning("PyPDF2 extraction failed for %s: %s", filename or "stream", e)

    # If we got very little text, treat as scanned PDF and try OCR
    try:
        from src.config import config
        min_chars = getattr(config, "PDF_MIN_TEXT_CHARS", PDF_MIN_TEXT_CHARS_DEFAULT)
    except Exception:
        min_chars = PDF_MIN_TEXT_CHARS_DEFAULT
    if len((text or "").strip()) < min_chars:
        try:
            from src.config import config as _config
            ocr_max = getattr(_config, "PDF_OCR_MAX_PAGES", 50)
        except Exception:
            ocr_max = 50
        ocr_pages = min(max_pages, ocr_max)
        ocr_text = extract_text_from_pdf_ocr(content, filename, ocr_pages)
        if ocr_text.strip():
            logger.info("Extracted %d characters from PDF %s via OCR (scanned)", len(ocr_text), filename or "(stream)")
            return ocr_text
        # Keep whatever we got from text extraction even if short
        if text.strip():
            return text

    logger.warning("PDF extraction produced no text for %s", filename or "stream")
    return text if text else ""


def extract_text_from_pdf_ocr(
    content: bytes,
    filename: str = "",
    max_pages: int = 50,
) -> str:
    """
    Extract text from a PDF by rendering each page to an image and running OCR (Tesseract).
    Use for scanned or image-only PDFs when normal text extraction yields nothing.
    Requires: pdf2image (and system poppler), pytesseract (and system Tesseract).
    """
    if not HAS_PDF2IMAGE:
        logger.warning("pdf2image not installed; install with: pip install pdf2image (and poppler)")
        return ""
    if not HAS_OCR:
        logger.warning("PIL/pytesseract not available for PDF OCR")
        return ""
    try:
        images = convert_from_bytes(content, first_page=1, last_page=max_pages, dpi=200)
        parts: List[str] = []
        for i, img in enumerate(images):
            try:
                page_text = pytesseract.image_to_string(img).strip()
                if page_text:
                    parts.append(page_text)
            except Exception as e:
                logger.warning("OCR failed for page %s of %s: %s", i + 1, filename or "PDF", e)
        text = "\n\n".join(parts).strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text
    except Exception as e:
        logger.warning("PDF OCR failed for %s: %s (is poppler installed?)", filename or "stream", e)
        return ""


def extract_text_from_image(content: bytes, filename: str = "") -> str:
    """
    Extract text from an image using OCR (Tesseract).

    Args:
        content: Raw image bytes
        filename: Optional filename for logging

    Returns:
        Extracted text or empty string if OCR not available or fails.
    """
    if not HAS_OCR:
        logger.warning(
            "PIL/pytesseract not installed; cannot extract image text. "
            "Install with: pip install Pillow pytesseract (and install Tesseract binary)"
        )
        return ""

    try:
        img = Image.open(io.BytesIO(content))
        # Convert to RGB if necessary
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        text = pytesseract.image_to_string(img).strip()
        logger.info("Extracted %d characters from image %s", len(text), filename or "(stream)")
        return text
    except Exception as e:
        logger.error("Image OCR failed for %s: %s", filename or "stream", e)
        return ""


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[str]:
    """
    Split text into overlapping chunks for retrieval.

    Args:
        text: Full text to chunk
        chunk_size: Target characters per chunk
        overlap: Overlap between consecutive chunks

    Returns:
        List of text chunks
    """
    if not text or chunk_size <= 0:
        return []
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        # Prefer breaking at sentence or paragraph
        if end < len(text):
            for sep in ("\n\n", "\n", ". ", " "):
                idx = text.rfind(sep, start, end + 1)
                if idx > start:
                    end = idx + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        next_start = end - overlap if overlap < (end - start) else end
        if next_start <= start:
            start += max(1, chunk_size - overlap) # Force forward progress
        else:
            start = next_start
    return chunks
