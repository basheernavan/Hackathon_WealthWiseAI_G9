"""Shared fixtures built only from samples/, so every task can be tested without any other task being done.

expected.json holds rounded figures (ADR-0004): compare with pytest.approx(..., abs=0.01).
"""

import json
from pathlib import Path

import pytest

from wealthwise.contracts import Category, FinancialProfile, Metrics, UploadedDocument

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
BANK_PDF = "bank_statement_jul-sep_2026.pdf"
BANK_CSV = "bank_statement_jul-sep_2026.csv"
PAYSLIP_PDF = "payslip_sep_2026.pdf"
LOAN_XLSX = "loan_statement_sep_2026.xlsx"


def assert_matches(actual, expected, path: str = "") -> None:
    """Deep-compare JSON-like data, allowing 0.01 on floats. Use on model_dump(mode="json") output."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and actual.keys() == expected.keys(), f"{path}: keys differ"
        for k in expected:
            assert_matches(actual[k], expected[k], f"{path}.{k}")
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), f"{path}: length differs"
        for i, (a, e) in enumerate(zip(actual, expected)):
            assert_matches(a, e, f"{path}[{i}]")
    elif isinstance(expected, float) or isinstance(actual, float):
        assert actual == pytest.approx(expected, abs=0.01), f"{path}: {actual} != {expected}"
    else:
        assert actual == expected, f"{path}: {actual!r} != {expected!r}"


def sample_bytes(name: str) -> bytes:
    return (SAMPLES / name).read_bytes()


def sample_document(name: str) -> UploadedDocument:
    return UploadedDocument(filename=name, content=sample_bytes(name))


@pytest.fixture
def expected() -> dict:
    """The analysis answer key: samples/expected.json."""
    return json.loads((SAMPLES / "expected.json").read_text(encoding="utf-8"))


@pytest.fixture
def sample_profile() -> FinancialProfile:
    """What ingestion must produce from the sample files (categories are None)."""
    return FinancialProfile.model_validate_json((SAMPLES / "expected_profile.json").read_text(encoding="utf-8"))


@pytest.fixture
def categorised_profile(sample_profile, expected) -> FinancialProfile:
    """The sample profile with categories already set from the answer key, so analysis tasks skip the categoriser."""
    transactions = [
        t.model_copy(update={"category": Category(c)})
        for t, c in zip(sample_profile.transactions, expected["transaction_categories"], strict=True)
    ]
    return sample_profile.model_copy(update={"transactions": transactions})


@pytest.fixture
def expected_metrics(expected) -> Metrics:
    return Metrics.model_validate(expected["metrics"])
