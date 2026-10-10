"""Stream B: turn a FinancialProfile into a Report. Spec: docs/specs/02-analysis.md

Already wired: each step lives in its own module (tasks B1-B6). build_report raises NotImplementedError
until every step is built; the dashboard falls back to samples/mock_report.json meanwhile.
"""

from wealthwise.analysis.agents import run_agents
from wealthwise.analysis.categorise import categorise
from wealthwise.analysis.metrics import compute_metrics
from wealthwise.analysis.plans import build_plans
from wealthwise.analysis.score import score_health
from wealthwise.analysis.subscriptions import find_subscriptions
from wealthwise.contracts import FinancialProfile, Report


def build_report(profile: FinancialProfile) -> Report:
    transactions = categorise(profile.transactions)
    profile = profile.model_copy(update={"transactions": transactions})
    metrics = compute_metrics(profile)
    identified_cuts, debt_plan, savings_plan = build_plans(metrics, profile.debts)
    recommendations, llm_used = run_agents(transactions, metrics, identified_cuts, debt_plan, savings_plan)
    return Report(
        metrics=metrics,
        health_score=score_health(metrics),
        subscriptions=find_subscriptions(transactions),
        identified_cuts=identified_cuts,
        debt_plan=debt_plan,
        savings_plan=savings_plan,
        recommendations=recommendations,
        llm_used=llm_used,
    )
