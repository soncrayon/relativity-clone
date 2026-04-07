"""
Extracts plain text from an uploaded document.

Supported formats  →  library used
  .pdf             →  pdfminer.six  (pure Python, no system deps)
  .docx            →  python-docx   (reads the Open XML format)
  .txt             →  built-in open()
  .eml             →  built-in email module
"""

import email
from io import StringIO
from pathlib import Path

from docx import Document as DocxDocument
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

SUPPORTED_TYPES = {"pdf", "docx", "txt", "eml"}


def extract_text(file_path: Path, file_type: str) -> str:
    """
    Read a file from disk and return its plain-text content as a string.

    Raises ValueError for unsupported file types so the caller can set
    processing_status = 'failed' and surface a useful error message.
    """
    if file_type == "pdf":
        return _extract_pdf(file_path)
    if file_type == "docx":
        return _extract_docx(file_path)
    if file_type == "txt":
        return _extract_txt(file_path)
    if file_type == "eml":
        return _extract_eml(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")


def get_file_type(filename: str) -> str:
    """
    Derive the normalized file type from the filename extension.
    Returns the extension without the dot, lowercased: "pdf", "docx", etc.
    Raises ValueError if the extension is not in SUPPORTED_TYPES.
    """
    suffix = Path(filename).suffix.lstrip(".").lower()
    if suffix not in SUPPORTED_TYPES:
        raise ValueError(
            f"'{suffix}' files are not supported. Accepted types: {', '.join(sorted(SUPPORTED_TYPES))}"
        )
    return suffix


# ── private helpers ────────────────────────────────────────────────────────────

def _extract_pdf(path: Path) -> str:
    """Use pdfminer's high-level API to pull all text from a PDF."""
    output = StringIO()
    with path.open("rb") as f:
        extract_text_to_fp(f, output, laparams=LAParams())
    return output.getvalue()


def _extract_docx(path: Path) -> str:
    """Grab the text from every paragraph in the document, joined by newlines."""
    doc = DocxDocument(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _extract_txt(path: Path) -> str:
    """Plain read — try UTF-8 first, fall back to latin-1 for legacy files."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _extract_eml(path: Path) -> str:
    """
    Parse an .eml file with Python's built-in email library.
    Prefers the plaintext part; falls back to HTML stripped of tags.
    """
    raw = path.read_bytes()
    msg = email.message_from_bytes(raw)

    body_parts: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body_parts.append(payload.decode("utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body_parts.append(payload.decode("utf-8", errors="replace"))

    return "\n".join(body_parts)
