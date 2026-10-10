"""Task C2: render a Report in Streamlit, plus money/percent formatting. Spec: docs/specs/03-dashboard-and-rag.md#c2-report-view-wealthwisedashboardpy

app.py (task C1) calls render_report; this placeholder keeps the app running until C2 is built.
"""

import streamlit as st

from wealthwise.contracts import Report


def format_eur(amount: float) -> str:
    """1234.5 -> '€1,234.50'; -12 -> '-€12.00'."""
    sign = "-" if amount < 0 else ""
    return f"{sign}€{abs(amount):,.2f}"


def format_pct(fraction: float) -> str:
    """0.0681 -> '6.8%'."""
    return f"{fraction * 100:.1f}%"


def render_report(report: Report) -> None:
    score = report.health_score
    st.subheader("Financial Health Score")
    st.metric("Financial Health Score", f"{score.score}/100")
    st.caption(f"Band: {score.band.title()}")

    component_columns = st.columns(len(score.components))
    for column, component in zip(component_columns, score.components):
        progress = component.points / component.max_points if component.max_points else 0
        with column:
            st.caption(component.name.replace("_", " ").title())
            st.progress(max(0, min(progress, 1)))
            st.caption(f"{component.points:g} / {component.max_points} points")

    metrics = report.metrics
    st.subheader("Financial metrics")
    metric_values = (
        ("Monthly income", format_eur(metrics.monthly_income)),
        ("Monthly spending", format_eur(metrics.monthly_spending)),
        ("Monthly surplus", format_eur(metrics.monthly_surplus)),
        ("Total debt", format_eur(metrics.total_debt)),
        ("Emergency fund", f"{metrics.emergency_fund_months:.2f} months"),
    )
    for column, (label, value) in zip(st.columns(len(metric_values)), metric_values):
        column.metric(label, value)

    st.subheader("Recommendations")
    recommendations = {recommendation.agent.value: recommendation for recommendation in report.recommendations}
    ordered_recommendations = [
        recommendations[agent]
        for agent in ("spending", "debt", "savings")
        if agent in recommendations
    ]
    for column, recommendation in zip(st.columns(len(ordered_recommendations)), ordered_recommendations):
        with column.container(border=True):
            st.caption(recommendation.agent.value.title())
            st.markdown(f"**{recommendation.title}**")
            st.write(recommendation.detail)
            if recommendation.monthly_impact is not None:
                st.caption(f"Monthly impact: {format_eur(recommendation.monthly_impact)}/month")
            with st.expander("Evidence transactions"):
                evidence_rows = [
                    {
                        "Date": transaction.date.isoformat(),
                        "Description": transaction.description,
                        "Amount": format_eur(transaction.amount),
                        "Balance": "" if transaction.balance is None else format_eur(transaction.balance),
                        "Category": "" if transaction.category is None else transaction.category.value,
                    }
                    for transaction in recommendation.evidence
                ]
                table_data = evidence_rows or {
                    "Date": [],
                    "Description": [],
                    "Amount": [],
                    "Balance": [],
                    "Category": [],
                }
                st.dataframe(table_data, hide_index=True, width="stretch")

    st.subheader("Spending breakdown")
    chart_data = [
        {
            "Category": category.value.replace("_", " ").title(),
            "Monthly spending": amount,
        }
        for category, amount in metrics.spending_by_category.items()
    ]
    st.bar_chart(chart_data, x="Category", y="Monthly spending", horizontal=True, width="stretch")

    st.caption("Subscriptions")
    subscription_rows = [
        {
            "Subscription": subscription.name,
            "Monthly amount": format_eur(subscription.monthly_amount),
            "Months seen": subscription.months_seen,
        }
        for subscription in report.subscriptions
    ]
    subscription_data = subscription_rows or {
        "Subscription": [],
        "Monthly amount": [],
        "Months seen": [],
    }
    st.dataframe(subscription_data, hide_index=True, width="stretch")

    if report.debt_plan is not None:
        plan = report.debt_plan
        st.subheader("Debt repayment plan")
        payoff_column, summary_column = st.columns((2, 1))
        with payoff_column:
            st.caption(f"Strategy: {plan.strategy.title()}")
            st.markdown("**Avalanche payoff order**")
            if plan.payoff_order:
                for position, debt_name in enumerate(plan.payoff_order, start=1):
                    st.markdown(f"{position}. {debt_name}")
            else:
                st.caption("No debts in the payoff order.")
        with summary_column:
            st.info(
                f"Debt-free in {plan.months_to_debt_free_with_extra} months "
                f"({plan.months_saved} months earlier)"
            )
            st.metric("Extra monthly payment", format_eur(plan.extra_monthly_payment))
            st.metric("Interest saved", format_eur(plan.interest_saved))
