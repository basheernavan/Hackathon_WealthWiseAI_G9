"""Task B5: identified cuts, avalanche debt plan and savings plan. Spec: docs/specs/02-analysis.md#b5-plans"""

import math

from wealthwise.contracts import Category, Debt, DebtPayoffPlan, Metrics, SavingsPlan

MAX_MONTHS = 600


def avalanche_order(debts: list[Debt]) -> list[Debt]:
    """Highest APR first, then smallest balance."""
    return sorted(debts, key=lambda d: (-d.annual_interest_rate, d.balance))


def simulate(debts: list[Debt], extra: float) -> tuple[int, float]:
    """Return (months until every debt is paid, total interest), paying minimums then avalanche."""
    balances = [d.balance for d in debts]
    order = sorted(range(len(debts)), key=lambda i: (-debts[i].annual_interest_rate, debts[i].balance))
    budget = sum(d.monthly_payment for d in debts) + extra
    months, interest = 0, 0.0
    while any(b > 0.005 for b in balances) and months < MAX_MONTHS:
        months += 1
        for i, d in enumerate(debts):
            charge = balances[i] * d.annual_interest_rate / 100 / 12
            balances[i] += charge
            interest += charge
        remaining = budget
        for i, d in enumerate(debts):
            pay = min(d.monthly_payment, balances[i])
            balances[i] -= pay
            remaining -= pay
        for i in order:
            pay = min(remaining, balances[i])
            balances[i] -= pay
            remaining -= pay
    return months, interest


def build_plans(metrics: Metrics, debts: list[Debt]) -> tuple[float, DebtPayoffPlan | None, SavingsPlan]:
    """Return (identified_cuts, debt_plan or None when there are no debts, savings_plan)."""
    identified_cuts = round(0.5 * metrics.spending_by_category.get(Category.TAKEAWAY, 0.0), 2)
    freed = round(max(metrics.monthly_surplus + identified_cuts, 0.0), 2)

    debt_plan = None
    if debts:
        extra = round(freed / 2, 2)
        savings_monthly = round(freed - extra, 2)
        months_current, interest_current = simulate(debts, 0.0)
        months_extra, interest_extra = simulate(debts, extra)
        projection_complete = months_current < MAX_MONTHS and months_extra < MAX_MONTHS
        debt_plan = DebtPayoffPlan(
            payoff_order=[d.name for d in avalanche_order(debts)],
            extra_monthly_payment=extra,
            months_to_debt_free_current=months_current,
            months_to_debt_free_with_extra=months_extra,
            months_saved=months_current - months_extra if projection_complete else 0,
            interest_saved=round(interest_current - interest_extra, 2) if projection_complete else 0.0,
        )
    else:
        savings_monthly = round(freed, 2)

    target = round(3 * metrics.monthly_spending, 2)
    shortfall = max(target - metrics.current_balance, 0.0)
    savings_plan = SavingsPlan(
        monthly_amount=savings_monthly,
        target_amount=target,
        months_to_target=math.ceil(shortfall / savings_monthly) if savings_monthly > 0 else None,
    )
    return identified_cuts, debt_plan, savings_plan
