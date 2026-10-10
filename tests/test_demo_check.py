"""D2: the demo dry run script (scripts/demo_check.py) passes offline on main and catches a wrong figure."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("demo_check", ROOT / "scripts" / "demo_check.py")
demo_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo_check)


@pytest.fixture
def expected() -> dict:
    return json.loads((ROOT / "samples" / "expected.json").read_text(encoding="utf-8"))


def statuses(run, name_part: str) -> set[str]:
    return {c.status for c in run.checks if name_part in c.name}


def test_offline_demo_has_no_failures(monkeypatch, expected):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    run = demo_check.DryRun()
    demo_check.demo_mode(run, expected, key=None, with_key=False)
    failures = [c for c in run.checks if c.status in (demo_check.FAIL, demo_check.WARN)]
    assert not failures, failures
    assert statuses(run, "CSV gives identical numbers") == {demo_check.PASS}


def test_a_wrong_health_score_is_reported(monkeypatch, expected):
    import wealthwise.analysis
    from wealthwise.contracts import HealthScore

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(wealthwise.analysis, "score_health", lambda metrics: HealthScore(score=50, band="fair", components=[]))
    run = demo_check.DryRun()
    demo_check.demo_in_app(run, demo_check.BANK_PDF, expected, with_key=False)
    assert statuses(run, "Health Score 67") == {demo_check.FAIL}


def test_report_numbers_ignore_llm_wording(expected):
    from wealthwise.contracts import Report

    report = Report.model_validate_json((ROOT / "samples" / "mock_report.json").read_text(encoding="utf-8"))
    reworded = report.model_copy(
        update={"llm_used": not report.llm_used, "recommendations": [r.model_copy(update={"title": "x", "detail": "y"}) for r in report.recommendations]}
    )
    assert demo_check.report_numbers(report) == demo_check.report_numbers(reworded)
