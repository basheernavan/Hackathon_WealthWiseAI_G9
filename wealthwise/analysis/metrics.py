"""Task B2: monthly metrics. Spec: docs/specs/02-analysis.md#b2-metrics"""

import pandas as pd

from wealthwise.contracts import DISCRETIONARY_CATEGORIES, Category, FinancialProfile, Metrics


def ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def compute_metrics(profile: FinancialProfile) -> Metrics:
    """`profile.transactions` already have categories set."""
    df = pd.DataFrame(
        [{"month": (t.date.year, t.date.month), "amount": t.amount, "category": t.category} for t in profile.transactions],
        columns=["month", "amount", "category"],
    )
    months = df["month"].nunique()
    outflows = df[df["amount"] < 0]
    income = ratio(df.loc[df["amount"] > 0, "amount"].sum(), months)
    spending = ratio(-outflows["amount"].sum(), months)
    by_category = {Category(c): ratio(-v, months) for c, v in sorted(outflows.groupby("category")["amount"].sum().items())}
    surplus = income - spending
    current_balance = (profile.transactions[-1].balance or 0.0) if profile.transactions else 0.0
    discretionary = sum(v for c, v in by_category.items() if c in DISCRETIONARY_CATEGORIES)

    # Full precision above; round only here (ADR-0004), money to 2 dp and fractions to 4 dp.
    return Metrics(
        months_covered=months,
        monthly_income=round(income, 2),
        monthly_spending=round(spending, 2),
        monthly_surplus=round(surplus, 2),
        spending_by_category={c: round(v, 2) for c, v in by_category.items()},
        savings_rate=round(ratio(surplus, income), 4),
        debt_to_income=round(ratio(sum(d.monthly_payment for d in profile.debts), income), 4),
        total_debt=round(sum(d.balance for d in profile.debts), 2),
        current_balance=round(current_balance, 2),
        emergency_fund_months=round(ratio(current_balance, spending), 2),
        discretionary_share=round(ratio(discretionary, spending), 4),
    )
