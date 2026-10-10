"""Task B2: monthly metrics. Spec: docs/specs/02-analysis.md#b2-metrics"""

from wealthwise.contracts import FinancialProfile, Metrics


def compute_metrics(profile: FinancialProfile) -> Metrics:
    """`profile.transactions` already have categories set."""
    raise NotImplementedError("B2 compute_metrics")
