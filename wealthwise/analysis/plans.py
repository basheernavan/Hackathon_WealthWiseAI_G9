"""Task B5: identified cuts, avalanche debt plan and savings plan. Spec: docs/specs/02-analysis.md#b5-plans"""

from wealthwise.contracts import Debt, DebtPayoffPlan, Metrics, SavingsPlan


def build_plans(metrics: Metrics, debts: list[Debt]) -> tuple[float, DebtPayoffPlan | None, SavingsPlan]:
    """Return (identified_cuts, debt_plan or None when there are no debts, savings_plan)."""
    raise NotImplementedError("B5 build_plans")
