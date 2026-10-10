from conftest import assert_matches
from wealthwise.analysis.score import score_health
from wealthwise.contracts import Metrics


def metrics(**overrides) -> Metrics:
    fields = dict(
        months_covered=0, monthly_income=0, monthly_spending=0, monthly_surplus=0, spending_by_category={},
        savings_rate=0, debt_to_income=0, total_debt=0, current_balance=0, emergency_fund_months=0,
        discretionary_share=0,
    )
    return Metrics(**(fields | overrides))


def test_sample_metrics_score_67_fair(expected_metrics, expected):
    score = score_health(expected_metrics)
    assert (score.score, score.band) == (67, "fair")
    assert_matches(score.model_dump(mode="json"), expected["health_score"])


def test_all_zero_metrics_give_a_valid_score():
    # savings 0/30, dti 0 -> 30, emergency 0/20, discretionary 0 -> 20
    score = score_health(metrics())
    assert (score.score, score.band) == (50, "fair")


def test_bands():
    assert score_health(metrics(savings_rate=0.2, emergency_fund_months=3)).band == "good"  # 100
    assert score_health(metrics(debt_to_income=0.9, discretionary_share=0.9)).band == "needs attention"  # 0
