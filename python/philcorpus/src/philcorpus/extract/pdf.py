"""PDF text extraction."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(path_or_bytes: str | bytes) -> str:
    """Extract text content from a PDF file.

    Uses PyMuPDF (fitz) for extraction, with handling for multi-column
    layouts.

    Parameters
    ----------
    path_or_bytes : str or bytes
        File path to a PDF or raw PDF bytes.

    Returns
    -------
    str
        Extracted text content.

    Raises
    ------
    ImportError
        If pymupdf is not installed.
    """
    try:
        import fitz  # pymupdf
    except ImportError:
        raise ImportError(
            "pymupdf is required for PDF extraction. "
            "Install with: pip install 'philcorpus[pdf]'"
        )

    if isinstance(path_or_bytes, str):
        doc = fitz.open(path_or_bytes)
    else:
        doc = fitz.open(stream=path_or_bytes, filetype="pdf")

    pages: list[str] = []
    try:
        for page in doc:
            # Use "blocks" sort mode for better multi-column handling
            text = page.get_text("text", sort=True)
            if text.strip():
                pages.append(text)
    finally:
        doc.close()

    return "\n\n".join(pages)
