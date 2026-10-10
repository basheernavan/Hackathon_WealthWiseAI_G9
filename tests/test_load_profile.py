"""A6 with fake detector and parsers, so it never depends on A1-A5."""

from datetime import date

import pytest

from wealthwise.contracts import Debt, DebtKind, DocumentType, Transaction, UploadedDocument
from wealthwise.ingestion import bank_csv, bank_pdf, detect, load_profile, loan_xlsx

TYPES = {".csv": DocumentType.BANK_STATEMENT, ".pdf": DocumentType.BANK_STATEMENT, ".xlsx": DocumentType.LOAN_STATEMENT}


def tx(day: int, month: int = 7, description: str = "X") -> Transaction:
    return Transaction(date=date(2026, month, day), description=description, amount=-1.0)


@pytest.fixture
def fakes(monkeypatch):
    monkeypatch.setattr(detect, "detect_document_type", lambda name, content: TYPES.get(name[name.rfind("."):]))
    monkeypatch.setattr(bank_pdf, "parse_bank_pdf", lambda c: ([tx(20, description="PDF"), tx(3, description="PDF")], []))
    monkeypatch.setattr(bank_csv, "parse_bank_csv", lambda c: ([tx(5, description="CSV")], ["csv warning"]))
    debt = Debt(name="Bank Loan", kind=DebtKind.LOAN, balance=100, annual_interest_rate=5, monthly_payment=10)
    monkeypatch.setattr(loan_xlsx, "parse_loan_xlsx", lambda c: ([debt], []))


def doc(name: str) -> UploadedDocument:
    return UploadedDocument(filename=name, content=b"x")


def test_overlapping_bank_statements_are_counted_once_with_a_warning(fakes):
    profile = load_profile([doc("a.pdf"), doc("b.csv")])
    assert [(t.description, t.date.day) for t in profile.transactions] == [("PDF", 3), ("PDF", 20)]
    assert profile.sources[1].warnings == ["csv warning", "Overlaps a.pdf; ignored"]


def test_unsupported_file_gives_a_warning_and_others_are_still_read(fakes):
    profile = load_profile([doc("notes.txt"), doc("loans.xlsx")])
    assert [(s.filename, s.document_type, s.warnings) for s in profile.sources] == [
        ("notes.txt", DocumentType.BANK_STATEMENT, ["Could not recognise document type"]),
        ("loans.xlsx", DocumentType.LOAN_STATEMENT, []),
    ]
    assert [d.name for d in profile.debts] == ["Bank Loan"]


def test_non_overlapping_bank_statements_are_merged_by_date(fakes, monkeypatch):
    monkeypatch.setattr(bank_csv, "parse_bank_csv", lambda c: ([tx(1, month=8, description="CSV")], []))
    profile = load_profile([doc("b.csv"), doc("a.pdf")])
    assert [t.description for t in profile.transactions] == ["PDF", "PDF", "CSV"]


def test_all_files_unsupported_raises(fakes):
    with pytest.raises(ValueError, match="No supported documents"):
        load_profile([doc("a.txt"), doc("b.docx")])
