"""The scenario folders in test_data/ (made by scripts/generate_test_data.py): best, worst and in-between cases through the whole pipeline."""

from pathlib import Path

import pytest

from wealthwise.analysis import build_report
from wealthwise.contracts import UploadedDocument
from wealthwise.ingestion import load_profile

TEST_DATA = Path(__file__).resolve().parents[1] / "test_data"

# folder: (band, min score, max score, has debt plan, subscriptions found)
SCENARIOS = {
    "best_saver_mar_2026": ("good", 95, 100, False, 0),
    "good_small_loan_apr_2026": ("good", 85, 100, True, 0),
    "average_mixed_may_2026": ("fair", 50, 74, True, 0),
    "worst_overspender_jun_2026": ("needs attention", 0, 35, True, 0),
    "high_debt_burden_jul_2026": ("fair", 50, 74, True, 0),
    "no_emergency_fund_aug_2026": ("fair", 50, 74, False, 0),
    "high_discretionary_sep_2026": ("good", 75, 90, False, 0),
    "subscription_creep_q1_2026": ("good", 75, 100, False, 5),
    "bank_only_no_debt_oct_2026": ("good", 95, 100, False, 0),
    "messy_csv_only_nov_2026": ("good", 75, 100, False, 0),
    "wrong_closing_balance_nov_2026": ("good", 75, 100, False, 0),
}


def report_for(folder: str):
    docs = [UploadedDocument(filename=f.name, content=f.read_bytes()) for f in sorted((TEST_DATA / folder).iterdir())]
    profile = load_profile(docs)
    return profile, build_report(profile)


@pytest.mark.parametrize("folder", SCENARIOS)
def test_scenario_score_and_plans(folder):
    band, low, high, has_debt_plan, subs = SCENARIOS[folder]
    _, report = report_for(folder)
    assert report.health_score.band == band
    assert low <= report.health_score.score <= high
    assert (report.debt_plan is not None) == has_debt_plan
    assert len(report.subscriptions) == subs


def components(folder: str) -> dict[str, float]:
    return {c.name: c.points for c in report_for(folder)[1].health_score.components}


def test_best_case_gets_full_marks_everywhere():
    assert all(p == c.max_points for p, c in zip(components("best_saver_mar_2026").values(), report_for("best_saver_mar_2026")[1].health_score.components))


def test_worst_case_has_no_savings_and_no_cushion():
    points = components("worst_overspender_jun_2026")
    assert points["savings_rate"] == 0 and points["emergency_fund"] == 0
    assert report_for("worst_overspender_jun_2026")[1].metrics.monthly_surplus < 0


def test_debt_burden_over_half_of_income_scores_zero_on_debt():
    assert components("high_debt_burden_jul_2026")["debt_to_income"] == 0


def test_empty_balance_scores_near_zero_on_emergency_fund():
    assert components("no_emergency_fund_aug_2026")["emergency_fund"] < 2


def test_heavy_discretionary_spending_scores_near_zero_on_that_component():
    assert components("high_discretionary_sep_2026")["discretionary_share"] < 5


def test_subscription_creep_is_found_every_month():
    _, report = report_for("subscription_creep_q1_2026")
    assert report.metrics.months_covered == 3
    assert {s.months_seen for s in report.subscriptions} == {3}


def test_messy_folder_warns_and_leaves_unknown_merchants_uncategorised():
    profile, report = report_for("messy_csv_only_nov_2026")
    warnings = [w for s in profile.sources for w in s.warnings]
    assert any("no sign" in w for w in warnings)
    assert report.metrics.spending_by_category["other"] > 0


def test_wrong_closing_balance_gives_a_warning():
    profile, _ = report_for("wrong_closing_balance_nov_2026")
    assert any("does not match" in w for s in profile.sources for w in s.warnings)
