import pymupdf
import pytest

from conftest import BANK_CSV, BANK_PDF, LOAN_XLSX, PAYSLIP_PDF, sample_bytes
from wealthwise.contracts import DocumentType
from wealthwise.ingestion.detect import detect_document_type


@pytest.mark.parametrize(
    "name, expected",
    [
        (BANK_PDF, DocumentType.BANK_STATEMENT),
        (BANK_CSV, DocumentType.BANK_STATEMENT),
        (PAYSLIP_PDF, DocumentType.PAYSLIP),
        (LOAN_XLSX, DocumentType.LOAN_STATEMENT),
    ],
)
def test_sample_files_get_the_right_type(name, expected):
    assert detect_document_type(name, sample_bytes(name)) == expected


def test_extension_is_case_insensitive():
    assert detect_document_type("STATEMENT.CSV", sample_bytes(BANK_CSV)) == DocumentType.BANK_STATEMENT


def pdf_with_text(text: str) -> bytes:
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), text)
    return doc.tobytes()


@pytest.mark.parametrize(
    "filename, content",
    [
        ("notes.txt", b"Statement Balance Net Pay"),
        ("empty.csv", b""),
        ("letter.pdf", pdf_with_text("Dear customer, thank you.")),
        ("broken.pdf", b"not really a pdf"),
        ("no_extension", b"data"),
    ],
)
def test_unsupported_empty_or_unreadable_files_give_none(filename, content):
    assert detect_document_type(filename, content) is None
