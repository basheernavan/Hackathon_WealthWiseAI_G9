"""The hand-made April-August 2026 documents in test_data/apr_aug_2026/: bank PDFs with no "Statement" heading
and a date on the first transaction line only, monthly payslips, one payslip that doesn't add up, and CSVs."""

from pathlib import Path

import pytest

from wealthwise.analysis.categorise import categorise
from wealthwise.analysis.metrics import compute_metrics
from wealthwise.contracts import DocumentType, UploadedDocument
from wealthwise.ingestion import load_profile
from wealthwise.ingestion.detect import detect_document_type

SET = Path(__file__).resolve().parents[1] / "test_data" / "apr_aug_2026"
MONTHS = ["April", "May", "June", "July", "August"]
SALARIES = [4263.0, 4564.0, 1770.0, 3597.0, 3102.0]


def document(name: str) -> UploadedDocument:
    return UploadedDocument(filename=name, content=(SET / name).read_bytes())


def bank_pdfs() -> list[UploadedDocument]:
    return [document(f"Bank_Statement_{month}_2026.pdf") for month in MONTHS]


@pytest.mark.parametrize("month", MONTHS)
def test_files_get_the_right_type(month):
    for name, expected in [
        (f"Bank_Statement_{month}_2026.pdf", DocumentType.BANK_STATEMENT),
        (f"Payslip_{month}_2026.pdf", DocumentType.PAYSLIP),
        (f"transactions_{month.lower()}_2026.csv", DocumentType.BANK_STATEMENT),
    ]:
        assert detect_document_type(name, (SET / name).read_bytes()) == expected


def test_undated_lines_take_the_date_above_them():
    profile = load_profile([document("Bank_Statement_April_2026.pdf")])
    assert [(t.date.isoformat(), t.description, t.amount, t.balance) for t in profile.transactions] == [
        ("2026-04-01", "Monthly Salary", 4263.0, 6263.0),
        ("2026-04-01", "Rent Payment", -1200.0, 5063.0),
        ("2026-04-01", "Tesco Grocery", -150.0, 4913.0),
        ("2026-04-01", "Fuel", -80.0, 4833.0),
    ]
    assert profile.sources[0].warnings == []


def test_five_months_of_pdfs_give_a_full_profile():
    payslips = [document(f"Payslip_{month}_2026.pdf") for month in MONTHS]
    profile = load_profile(bank_pdfs() + payslips)
    assert len(profile.transactions) == 20
    assert [p.net_pay for p in profile.payslips] == SALARIES
    assert all(s.warnings == [] for s in profile.sources)

    transactions = categorise(profile.transactions)
    assert [t.description for t in transactions if t.category == "other"] == []
    metrics = compute_metrics(profile.model_copy(update={"transactions": transactions}))
    assert metrics.months_covered == 5


def test_payslip_that_does_not_add_up_is_skipped_with_a_warning():
    profile = load_profile([document("Bank_Statement_April_2026.pdf"), document("Payslip_Invalid_2026.pdf")])
    assert profile.payslips == []
    assert profile.sources[1].warnings == ["Payslip skipped: net pay doesn't equal gross pay minus deductions"]


def test_csv_for_the_same_month_as_a_pdf_is_ignored():
    profile = load_profile([document("Bank_Statement_June_2026.pdf"), document("transactions_june_2026.csv")])
    assert len(profile.transactions) == 4
    assert any("Overlaps" in w for w in profile.sources[1].warnings)
