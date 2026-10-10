import pytest

from conftest import BANK_PDF, sample_bytes
from test_data_jan import JAN_BANK_PDF, jan_bytes
from test_detect import pdf_with_text
from wealthwise.ingestion.bank_pdf import parse_bank_pdf


def test_sample_pdf_gives_sample_profile_transactions(sample_profile):
    transactions, warnings = parse_bank_pdf(sample_bytes(BANK_PDF))
    assert warnings == []
    assert len(transactions) == len(sample_profile.transactions)
    for actual, expected in zip(transactions, sample_profile.transactions):
        assert (actual.date, actual.description) == (expected.date, expected.description)
        assert actual.amount == pytest.approx(expected.amount, abs=0.01)
        assert actual.balance == pytest.approx(expected.balance, abs=0.01)


def test_line_based_statement_gives_signed_amounts_and_running_balance():
    transactions, warnings = parse_bank_pdf(jan_bytes(JAN_BANK_PDF))
    assert len(transactions) == 12
    first, last = transactions[0], transactions[-1]
    assert (str(first.date), first.description, first.amount, first.balance) == ("2026-01-02", "Monthly Salary", 3272.0, 5422.0)
    assert (last.description, last.amount) == ("Cinema", -32.0)
    assert last.balance == pytest.approx(3640.13, abs=0.01)
    # The printed closing balance (3,490.13) disagrees with the transactions; say so rather than hide it.
    assert len(warnings) == 1 and "Closing balance" in warnings[0]


def test_pdf_without_transactions_gives_a_warning():
    transactions, warnings = parse_bank_pdf(pdf_with_text("Statement Balance nothing else"))
    assert transactions == [] and len(warnings) == 1


def test_unreadable_bytes_give_a_warning():
    transactions, warnings = parse_bank_pdf(b"not a pdf")
    assert transactions == [] and len(warnings) == 1
