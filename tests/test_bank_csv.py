from conftest import BANK_CSV, sample_bytes
from wealthwise.ingestion.bank_csv import parse_bank_csv


def test_sample_csv_gives_sample_profile_transactions(sample_profile):
    transactions, warnings = parse_bank_csv(sample_bytes(BANK_CSV))
    assert transactions == sample_profile.transactions
    assert warnings == []


def test_unreadable_row_is_skipped_with_a_warning():
    content = b"Date,Description,Amount,Balance\n2026-07-01,TESCO,-10.00,90.00\nnot-a-date,X,abc,\n"
    transactions, warnings = parse_bank_csv(content)
    assert [t.description for t in transactions] == ["TESCO"]
    assert len(warnings) == 1 and "row 2" in warnings[0]
