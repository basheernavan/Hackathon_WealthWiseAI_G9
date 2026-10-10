"""End-to-end acceptance tests. Each one skips until every piece it needs is merged, then runs automatically."""

import pytest

from conftest import BANK_CSV, BANK_PDF, LOAN_XLSX, PAYSLIP_PDF, assert_matches, sample_document
from wealthwise.analysis import build_report
from wealthwise.ingestion import load_profile


def run_or_skip(fn, *args):
    try:
        return fn(*args)
    except NotImplementedError as e:
        pytest.skip(f"not built yet: {e}")


def test_sample_files_give_expected_profile(sample_profile):
    profile = run_or_skip(load_profile, [sample_document(n) for n in (BANK_PDF, PAYSLIP_PDF, LOAN_XLSX)])
    assert_matches(profile.model_dump(mode="json"), sample_profile.model_dump(mode="json"))


def test_csv_gives_same_transactions_as_pdf():
    from_pdf = run_or_skip(load_profile, [sample_document(BANK_PDF)])
    from_csv = run_or_skip(load_profile, [sample_document(BANK_CSV)])
    assert from_csv.transactions == from_pdf.transactions


def test_both_bank_files_are_not_double_counted():
    profile = run_or_skip(load_profile, [sample_document(BANK_PDF), sample_document(BANK_CSV)])
    assert len(profile.transactions) == 87
    assert any("Overlaps" in w for s in profile.sources for w in s.warnings)


def test_sample_profile_gives_expected_report(sample_profile, expected):
    report = run_or_skip(build_report, sample_profile)
    dumped = report.model_dump(mode="json")
    for key in ("metrics", "health_score", "subscriptions", "identified_cuts", "debt_plan", "savings_plan"):
        assert_matches(dumped[key], expected[key], key)
