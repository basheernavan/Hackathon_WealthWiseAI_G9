"""Task B3: Financial Health Score. Spec: docs/specs/02-analysis.md#b3-health-score"""

import math

from wealthwise.contracts import HealthScore, Metrics, ScoreComponent


def clamp(x: float) -> float:
    return min(1.0, max(0.0, x))


def score_health(metrics: Metrics) -> HealthScore:
    parts = [  # (name, value, max_points, unrounded points), in display order
        ("savings_rate", metrics.savings_rate, 30, 30 * clamp(metrics.savings_rate / 0.20)),
        ("debt_to_income", metrics.debt_to_income, 30, 30 * clamp((0.50 - metrics.debt_to_income) / 0.40)),
        ("emergency_fund", metrics.emergency_fund_months, 20, 20 * clamp(metrics.emergency_fund_months / 3)),
        ("discretionary_share", metrics.discretionary_share, 20, 20 * clamp((0.50 - metrics.discretionary_share) / 0.30)),
    ]
    score = math.floor(sum(p for *_, p in parts) + 0.5)
    band = "good" if score >= 75 else "fair" if score >= 50 else "needs attention"
    return HealthScore(
        score=score,
        band=band,
        components=[
            ScoreComponent(name=name, value=round(value, 4), points=round(points, 2), max_points=max_points)
            for name, value, max_points, points in parts
        ],
    )
