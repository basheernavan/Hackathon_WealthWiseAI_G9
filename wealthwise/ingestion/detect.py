"""Task A1: decide what kind of document a file is. Spec: docs/specs/01-ingestion.md#a1-detect-the-document-type"""

from wealthwise.contracts import DocumentType


def detect_document_type(filename: str, content: bytes) -> DocumentType | None:
    """Return the document type, or None when the file is unsupported, unreadable or empty."""
    raise NotImplementedError("A1 detect_document_type")
