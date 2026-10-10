from conftest import assert_matches
from wealthwise.analysis.metrics import compute_metrics
from wealthwise.contracts import FinancialProfile


def test_sample_profile_gives_expected_metrics(categorised_profile, expected):
    assert_matches(compute_metrics(categorised_profile).model_dump(mode="json"), expected["metrics"])


def test_empty_profile_gives_all_zeros():
    metrics = compute_metrics(FinancialProfile())
    assert metrics.months_covered == 0
    assert metrics.spending_by_category == {}
    assert all(v == 0 for k, v in metrics.model_dump().items() if k not in ("months_covered", "spending_by_category"))
