"""Task A1: decide what kind of document a file is. Spec: docs/specs/01-ingestion.md#a1-detect-the-document-type"""

from pathlib import PurePath

import pymupdf

from wealthwise.contracts import DocumentType


def first_page_text(content: bytes) -> str:
    try:
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            return doc[0].get_text() if doc.page_count else ""
    except Exception:
        return ""


def detect_document_type(filename: str, content: bytes) -> DocumentType | None:
    """Return the document type, or None when the file is unsupported, unreadable or empty."""
    if not content:
        return None
    extension = PurePath(filename).suffix.lower()
    if extension == ".csv":
        return DocumentType.BANK_STATEMENT
    if extension == ".xlsx":
        return DocumentType.LOAN_STATEMENT
    if extension == ".pdf":
        text = first_page_text(content)
        if "Net Pay" in text:
            return DocumentType.PAYSLIP
        if "Statement" in text and "Balance" in text:
            return DocumentType.BANK_STATEMENT
    return None
