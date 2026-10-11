"""The hand-made January 2026 documents in test_data/jan_2026/: other layouts than samples/, same pipeline."""

from pathlib import Path

import pytest

from wealthwise.analysis.categorise import categorise
from wealthwise.analysis.metrics import compute_metrics
from wealthwise.contracts import DocumentType, UploadedDocument
from wealthwise.ingestion import load_profile
from wealthwise.ingestion.detect import detect_document_type

JAN = Path(__file__).resolve().parents[1] / "test_data" / "jan_2026"
JAN_BANK_PDF = "Bank_Statement_January_2026.pdf"
JAN_PAYSLIP_PDF = "Payslip_January_2026.pdf"
JAN_LOAN_PDF = "Personal_Loan_Statement.pdf"
JAN_CSV = "financial_transactions_demo.csv"


def jan_bytes(name: str) -> bytes:
    return (JAN / name).read_bytes()


def jan_document(name: str) -> UploadedDocument:
    return UploadedDocument(filename=name, content=jan_bytes(name))


@pytest.mark.parametrize(
    "name, expected",
    [
        (JAN_BANK_PDF, DocumentType.BANK_STATEMENT),
        (JAN_PAYSLIP_PDF, DocumentType.PAYSLIP),
        (JAN_LOAN_PDF, DocumentType.LOAN_STATEMENT),
        (JAN_CSV, DocumentType.BANK_STATEMENT),
    ],
)
def test_january_files_get_the_right_type(name, expected):
    assert detect_document_type(name, jan_bytes(name)) == expected


def test_january_pdfs_give_a_full_profile():
    profile = load_profile([jan_document(n) for n in (JAN_BANK_PDF, JAN_PAYSLIP_PDF, JAN_LOAN_PDF)])
    assert len(profile.transactions) == 12
    assert len(profile.payslips) == 1
    assert [d.name for d in profile.debts] == ["AIB Personal Loan"]
    assert [s.document_type for s in profile.sources] == [DocumentType.BANK_STATEMENT, DocumentType.PAYSLIP, DocumentType.LOAN_STATEMENT]


def test_january_csv_overlaps_the_pdf_and_is_ignored():
    profile = load_profile([jan_document(JAN_BANK_PDF), jan_document(JAN_CSV)])
    assert len(profile.transactions) == 12
    assert any("Overlaps" in w for w in profile.sources[1].warnings)


def test_january_transactions_are_all_categorised():
    profile = load_profile([jan_document(JAN_BANK_PDF), jan_document(JAN_LOAN_PDF)])
    transactions = categorise(profile.transactions)
    assert [t.description for t in transactions if t.category == "other"] == []
    metrics = compute_metrics(profile.model_copy(update={"transactions": transactions}))
    assert (metrics.months_covered, metrics.monthly_income, metrics.total_debt) == (1, 3272.0, 18450.0)
    assert metrics.debt_to_income == round(345 / 3272, 4)
