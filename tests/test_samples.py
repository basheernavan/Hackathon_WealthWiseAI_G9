"""Guards the shared fixtures: if these fail, the samples and the contract disagree."""

import csv
import json
from pathlib import Path

import pytest

from wealthwise.contracts import FinancialProfile, Report

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@pytest.fixture(scope="module")
def profile() -> FinancialProfile:
    return FinancialProfile.model_validate_json((SAMPLES / "expected_profile.json").read_text(encoding="utf-8"))


def test_mock_report_matches_contract():
    Report.model_validate_json((SAMPLES / "mock_report.json").read_text(encoding="utf-8"))


def test_csv_and_profile_hold_the_same_transactions(profile):
    with (SAMPLES / "bank_statement_jul-sep_2026.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [(r["Date"], r["Description"], float(r["Amount"])) for r in rows] == [
        (t.date.isoformat(), t.description, t.amount) for t in profile.transactions
    ]


def test_salary_credits_equal_payslip_net_pay(profile):
    salaries = [t.amount for t in profile.transactions if t.description.startswith("SALARY")]
    assert salaries == [profile.payslips[0].net_pay] * 3


def test_answer_key_has_one_category_per_transaction(profile):
    key = json.loads((SAMPLES / "expected.json").read_text(encoding="utf-8"))
    assert len(key["transaction_categories"]) == len(profile.transactions)


def test_shared_fixtures_load(categorised_profile, expected_metrics):
    assert all(t.category is not None for t in categorised_profile.transactions)
    assert expected_metrics.months_covered == 3
