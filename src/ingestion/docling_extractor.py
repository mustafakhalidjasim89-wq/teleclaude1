"""
PDF text extraction.

Converts uploaded site-visit PDF reports into plain text that
downstream stages (findings matching, executive summary) can use.

NOTE: This originally used Docling, which gives higher-quality
structured/table-aware extraction but pulls in heavy ML dependencies
(docling-ibm-models -> opencv-python -> system libGL, etc.) that are
unreliable to install on constrained hosts like Streamlit Cloud's
free tier. Swapped to pypdf: pure-Python, no native/system
dependencies, no model downloads. Good enough for straightforward
text-based site reports; revisit Docling (or pdfplumber for better
table handling) if you move to a host where the extra native deps
can be installed, or if reports are scanned/image-only (pypdf can't
OCR — in that case Claude Vision on rasterized pages, or Tesseract
OCR, would be needed instead).
"""
from typing import Any


def extract_pdf_content(pdf_file: Any) -> str:
    """
    Extract plain text content from a site PDF report.

    Args:
        pdf_file: A file-like object (e.g. Streamlit UploadedFile) with
            .read()/.seek(), or a filesystem path string.

    Returns:
        Extracted text content of the PDF, pages joined with blank lines.
        Empty string if no file given.
    """
    if pdf_file is None:
        return ""

    from pypdf import PdfReader

    if hasattr(pdf_file, "seek"):
        pdf_file.seek(0)

    reader = PdfReader(pdf_file)

    pages_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(text)

    if hasattr(pdf_file, "seek"):
        pdf_file.seek(0)

    return "\n\n".join(pages_text)
