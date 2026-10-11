"""Task C2: render a Report in Streamlit, plus money/percent formatting."""

import altair as alt
import streamlit as st

from wealthwise.analysis.categorise import category_for
from wealthwise.analysis.plans import MAX_MONTHS
from wealthwise.contracts import Category, DebtKind, FinancialProfile, Report


def format_eur(amount: float) -> str:
    """1234.5 -> '€1,234.50'; -12 -> '-€12.00'."""
    sign = "-" if amount < 0 else ""
    return f"{sign}€{abs(amount):,.2f}"


def format_pct(fraction: float) -> str:
    """0.0681 -> '6.8%'."""
    return f"{fraction * 100:.1f}%"


COMPONENT_LABELS = {
    "savings_rate": "Savings rate",
    "debt_to_income": "Debt-to-income",
    "emergency_fund": "Emergency fund",
    "discretionary_share": "Discretionary share",
}


def score_gauge_svg(score: int) -> str:
    """Semicircle gauge filled to score/100; the number itself is the st.metric drawn over it."""
    filled = max(0, min(score, 100))
    return (
        '<svg viewBox="0 0 220 125" width="100%" style="max-width:260px;display:block;margin:0 auto" '
        f'role="img" aria-label="Financial Health Score gauge, {filled} out of 100">'
        '<defs><linearGradient id="ww-gauge" x1="0" x2="1"><stop offset="0" stop-color="#0EA5A0"/>'
        '<stop offset="1" stop-color="#22C55E"/></linearGradient></defs>'
        '<path d="M 20 110 A 90 90 0 0 1 200 110" fill="none" stroke="#E6F2FF" stroke-width="18" '
        'stroke-linecap="round"/>'
        '<path d="M 20 110 A 90 90 0 0 1 200 110" fill="none" stroke="url(#ww-gauge)" stroke-width="18" '
        f'stroke-linecap="round" pathLength="100" stroke-dasharray="{filled} 100"/></svg>'
    )


def component_bar_html(name: str, value: float, progress: float) -> str:
    """One score component: label, its measured value and a coloured progress bar."""
    shown = f"{value:.1f} months" if name == "emergency_fund" else format_pct(value)
    progress = max(0.0, min(progress, 1.0))
    colour = "#22C55E" if progress >= 0.75 else "#F59E0B" if progress >= 0.4 else "#EF4444"
    return (
        f'<div class="ww-component"><span>{COMPONENT_LABELS.get(name, name.replace("_", " ").title())}</span>'
        f"<span>{shown}</span></div>"
        f'<div class="ww-bar"><div style="width:{progress * 100:.0f}%;background:{colour}"></div></div>'
    )


def debt_summary(profile: FinancialProfile | None) -> str:
    """'2 loans / 1 credit card' from the profile, or a generic note without one."""
    if profile is None or not profile.debts:
        return "Outstanding balance in the report"
    loans = sum(debt.kind == DebtKind.LOAN for debt in profile.debts)
    cards = len(profile.debts) - loans
    return f"{loans} loan{'s' * (loans != 1)} / {cards} credit card{'s' * (cards != 1)}"


def render_report(report: Report, profile: FinancialProfile | None = None) -> None:
    st.markdown(
        """
        <style>
            .st-key-health-score-card {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 1rem;
                padding: 1.25rem 1.5rem 1rem;
                box-shadow: 0 6px 20px rgba(11, 45, 91, 0.06);
            }
            .st-key-score-gauge [data-testid="stMetric"] {
                background: transparent;
                border: none;
                padding: 0;
                margin-top: -4.6rem;
                text-align: center;
            }
            .st-key-score-gauge [data-testid="stMetricValue"] {
                color: #0B2D5B;
                font-size: 2.6rem;
                font-weight: 700;
                justify-content: center;
            }
            .st-key-score-gauge [data-testid="stMetricValue"] > div {
                margin: 0 auto;
            }
            .st-key-score-gauge [data-testid="stCaptionContainer"] {
                text-align: center;
            }
            .st-key-score-gauge [data-testid="stCaptionContainer"] p {
                display: inline-block;
                background: #FEF3C7;
                color: #92400E;
                border-radius: 999px;
                padding: 0.1rem 0.8rem;
                font-weight: 600;
            }
            .st-key-score-band-good [data-testid="stCaptionContainer"] p {
                background: #DCFCE7;
                color: #166534;
            }
            .st-key-score-band-needs-attention [data-testid="stCaptionContainer"] p {
                background: #FEE2E2;
                color: #991B1B;
            }
            .ww-component {
                display: flex;
                justify-content: space-between;
                font-size: 0.92rem;
                color: #0B2D5B;
                margin-top: 0.35rem;
            }
            .ww-component span:last-child {
                font-weight: 600;
            }
            .ww-bar {
                background: #E6F2FF;
                border-radius: 999px;
                height: 8px;
                overflow: hidden;
                margin: 0.3rem 0 0.15rem;
            }
            .ww-bar > div {
                height: 100%;
                border-radius: 999px;
            }
            [data-testid="stMetric"] {
                background: #FFFFFF;
                border-radius: 0.7rem;
                padding: 0.4rem 0.2rem;
            }
            [data-testid="stMetricLabel"] {
                color: #5B6B82;
            }
            [data-testid="stMetricValue"] {
                color: #0B2D5B;
                font-weight: 700;
            }
            [class*="st-key-overview-"] {
                background: #FFFFFF;
                border-color: #E2E8F0 !important;
                border-top: 3px solid #0EA5A0 !important;
                border-radius: 1rem;
                min-height: 150px;
                padding: 0.9rem;
            }
            .st-key-overview-monthly-spending {
                border-top-color: #F59E0B !important;
            }
            .st-key-overview-total-debt {
                border-top-color: #EF4444 !important;
            }
            .st-key-overview-monthly-surplus,
            .st-key-overview-emergency-fund {
                border-top-color: #22C55E !important;
            }
            [class*="st-key-recommendation-"] {
                background: #FFFFFF;
                border-color: #E2E8F0 !important;
                border-radius: 1rem;
                min-height: 380px;
                padding: 1rem;
            }
            .st-key-recommendation-spending {
                border-top: 4px solid #F59E0B !important;
            }
            .st-key-recommendation-debt {
                border-top: 4px solid #EF4444 !important;
            }
            .st-key-recommendation-savings {
                border-top: 4px solid #22C55E !important;
            }
            .st-key-recommendation-spending [data-testid="stMetricValue"],
            .st-key-recommendation-debt [data-testid="stMetricValue"],
            .st-key-recommendation-savings [data-testid="stMetricValue"] {
                font-size: 1.55rem !important;
            }
            @media (max-width: 900px) {
                div[data-testid="stHorizontalBlock"] {
                    flex-wrap: wrap;
                }
                div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
                    min-width: min(100%, 300px) !important;
                    flex: 1 1 100% !important;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    score = report.health_score
    st.subheader("Financial Health Score", anchor="dashboard")
    with st.container(border=True, key="health-score-card"):
        gauge_column, components_column = st.columns((2, 3), vertical_alignment="center")
        with gauge_column.container(key="score-gauge"):
            st.markdown(score_gauge_svg(score.score), unsafe_allow_html=True)
            st.metric("Financial Health Score", f"{score.score}/100", label_visibility="collapsed")
            with st.container(key=f"score-band-{score.band.replace(' ', '-')}"):
                st.caption(f"Band: {score.band.title()}")
        with components_column:
            for component in score.components:
                progress = component.points / component.max_points if component.max_points else 0
                st.markdown(component_bar_html(component.name, component.value, progress), unsafe_allow_html=True)
                st.caption(f"{component.points:g} / {component.max_points} points")

    metrics = report.metrics
    st.subheader("Financial Overview")
    subscription_total = round(sum(item.monthly_amount for item in report.subscriptions), 2)
    overview_cards = [
        ("Monthly income", format_eur(metrics.monthly_income), f"Average across {metrics.months_covered} months"),
        (
            "Monthly spending",
            format_eur(metrics.monthly_spending),
            f"Across {len(metrics.spending_by_category)} categories; includes debt repayments",
        ),
        ("Monthly surplus", format_eur(metrics.monthly_surplus), "Historical average; not a guarantee"),
        ("Total debt", format_eur(metrics.total_debt), debt_summary(profile)),
        ("Reported balance", format_eur(metrics.current_balance), "Latest account balance in the transactions"),
        (
            "Emergency fund",
            f"{metrics.emergency_fund_months:.2f}",
            "months of spending; current balance vs monthly spending",
        ),
    ]
    if report.subscriptions:
        overview_cards.append(
            (
                "Recurring subscriptions",
                format_eur(subscription_total),
                f"per month; {len(report.subscriptions)} identified",
            )
        )
    for start in range(0, len(overview_cards), 3):
        row = overview_cards[start : start + 3]
        for column, (label, value, description) in zip(st.columns(3), row):
            with column:
                with st.container(border=True, key=f"overview-{label.lower().replace(' ', '-')}"):
                    st.metric(label, value)
                    st.caption(description)

    st.subheader("AI Recommendations", anchor="recommendations")
    recommendations = {recommendation.agent.value: recommendation for recommendation in report.recommendations}
    ordered_recommendations = [
        recommendations[agent]
        for agent in ("spending", "debt", "savings")
        if agent in recommendations
    ]
    if ordered_recommendations:
        recommendation_columns = st.columns(len(ordered_recommendations))
    else:
        recommendation_columns = []
        st.info("No recommendations are available for this report.")
    takeaway = metrics.spending_by_category.get(Category.TAKEAWAY, 0.0)
    for column, recommendation in zip(recommendation_columns, ordered_recommendations):
        with column.container(border=True, key=f"recommendation-{recommendation.agent.value}"):
            agent = recommendation.agent.value
            st.caption(agent.title())
            if agent == "spending":
                st.markdown("**Review your takeaway spending**")
                st.write(
                    f"Takeaway averaged {format_eur(takeaway)}/month over "
                    f"{metrics.months_covered} months."
                )
                st.metric("Potential monthly cut", format_eur(report.identified_cuts))
                st.progress(0.5, text="Illustration: 50% lower takeaway spending")
                st.caption("Optional scenario only; compare it with other priorities.")
            elif agent == "debt" and report.debt_plan is not None:
                plan = report.debt_plan
                st.markdown("**Consider the avalanche debt plan**")
                projection_complete = (
                    plan.months_to_debt_free_current < MAX_MONTHS
                    and plan.months_to_debt_free_with_extra < MAX_MONTHS
                )
                if projection_complete:
                    st.write(
                        f"With an extra {format_eur(plan.extra_monthly_payment)}/month, payoff is projected "
                        f"in {plan.months_to_debt_free_with_extra} months, {plan.months_saved} months sooner, "
                        f"with {format_eur(plan.interest_saved)} less interest."
                    )
                else:
                    st.write(
                        f"An extra {format_eur(plan.extra_monthly_payment)}/month is an illustrative allocation. "
                        f"Payoff is not reached within the {MAX_MONTHS}-month modelling period, so no "
                        "payoff date or interest saving is shown."
                    )
                st.metric("Monthly extra payment", format_eur(plan.extra_monthly_payment))
                if projection_complete and plan.months_to_debt_free_current > 0:
                    st.progress(
                        min(plan.months_to_debt_free_with_extra / plan.months_to_debt_free_current, 1.0),
                        text=(
                            f"Projected payoff: {plan.months_to_debt_free_with_extra} months "
                            f"vs {plan.months_to_debt_free_current} on scheduled payments"
                        ),
                    )
                if projection_complete:
                    st.caption("Projection assumes the recorded balances, APRs and monthly payments stay unchanged.")
            elif agent == "debt":
                st.markdown("**No debt plan available**")
                st.write("No loan or credit-card balances were identified in this report.")
                st.caption("Check the uploaded loan statement if you expected a debt plan.")
            else:
                plan = report.savings_plan
                st.markdown("**Build a 3-month emergency fund**")
                st.write(
                    f"Reported balance: {format_eur(metrics.current_balance)} "
                    f"({metrics.emergency_fund_months:.2f} months of spending). "
                    f"Three-month target: {format_eur(plan.target_amount)}."
                )
                st.metric("Monthly savings", format_eur(plan.monthly_amount))
                progress = min(max(metrics.current_balance / plan.target_amount, 0.0), 1.0) if plan.target_amount else 0.0
                st.progress(progress, text="Progress toward the report's 3-month target")
                if plan.months_to_target is not None:
                    st.caption(f"At this allocation, the estimate is {plan.months_to_target} months.")

    allocable = round(max(metrics.monthly_surplus + report.identified_cuts, 0.0), 2)
    allocation_text = (
        f"If you choose the spending scenario, the illustrative allocation is "
        f"{format_eur(metrics.monthly_surplus)} average monthly surplus + "
        f"{format_eur(report.identified_cuts)} potential cuts = {format_eur(allocable)}. "
    )
    if report.debt_plan is not None:
        allocation_text += (
            f"The report splits that scenario into {format_eur(report.debt_plan.extra_monthly_payment)} "
            f"for extra debt payments and {format_eur(report.savings_plan.monthly_amount)} for savings. "
        )
    else:
        allocation_text += f"The report allocates {format_eur(report.savings_plan.monthly_amount)} to savings. "
    allocation_text += "The hypothetical cuts first offset any shortfall. Destinations split this same scenario amount; they are not additional savings."
    st.caption(allocation_text)

    st.subheader("Supporting evidence")
    evidence_labels = {
        "Spending scenario": "spending",
        "Debt repayment scenario": "debt",
        "Savings allocation": "savings",
    }
    selected_evidence = st.selectbox(
        "Choose a recommendation to inspect",
        list(evidence_labels),
        key="recommendation_evidence_choice",
    )
    evidence_kind = evidence_labels[selected_evidence]
    with st.expander("View supporting evidence", expanded=True):
        if evidence_kind == "spending":
            transactions = (
                [
                    transaction
                    for transaction in profile.transactions
                    if transaction.amount < 0 and category_for(transaction) == Category.TAKEAWAY
                ]
                if profile is not None
                else next(
                    (
                        item.evidence
                        for item in ordered_recommendations
                        if item.agent.value == "spending"
                    ),
                    [],
                )
            )
            if transactions:
                st.dataframe(
                    [
                        {
                            "Date": transaction.date.isoformat(),
                            "Merchant / description": transaction.description,
                            "Category": (category_for(transaction) or "").value
                            if category_for(transaction)
                            else "",
                            "Amount": format_eur(transaction.amount),
                        }
                        for transaction in sorted(transactions, key=lambda item: item.date, reverse=True)
                    ],
                    hide_index=True,
                    width="stretch",
                )
                if profile is None:
                    st.caption("Representative report evidence only; full transactions are available in the source statement.")
            else:
                st.info("No takeaway transactions are available to show.")
        elif evidence_kind == "debt":
            if profile is not None and profile.debts:
                st.dataframe(
                    [
                        {
                            "Debt": debt.name,
                            "Type": debt.kind.value.replace("_", " ").title(),
                            "Balance": format_eur(debt.balance),
                            "APR": f"{debt.annual_interest_rate:.2f}%",
                            "Scheduled monthly payment": format_eur(debt.monthly_payment),
                            "Remaining term": (
                                f"{debt.remaining_term_months} months"
                                if debt.remaining_term_months is not None
                                else "Not stated"
                            ),
                        }
                        for debt in profile.debts
                    ],
                    hide_index=True,
                    width="stretch",
                )
                st.caption("Interest projections use these reported balances, APRs and monthly payments.")
            else:
                st.info("Individual debt balances and terms are not available in this report view.")
        else:
            st.info(
                f"Savings target: {format_eur(report.savings_plan.target_amount)} "
                f"(3 months of reported spending). Current reported balance: "
                f"{format_eur(metrics.current_balance)}. Monthly allocation: "
                f"{format_eur(report.savings_plan.monthly_amount)}."
            )

    st.subheader("Monthly income and spending")
    comparison_data = [
        {"Measure": "Income", "Monthly amount": metrics.monthly_income, "Colour": "Income"},
        {"Measure": "Spending", "Monthly amount": metrics.monthly_spending, "Colour": "Spending"},
    ]
    comparison_chart = (
        alt.Chart(alt.Data(values=comparison_data))
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(
                "Monthly amount:Q",
                title="EUR per month",
                axis=alt.Axis(format=",.0f"),
            ),
            y=alt.Y("Measure:N", sort=["Income", "Spending"], title=None),
            color=alt.Color(
                "Colour:N",
                scale=alt.Scale(domain=["Income", "Spending"], range=["#0EA5A0", "#F59E0B"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Measure:N"),
                alt.Tooltip("Monthly amount:Q", title="Monthly amount", format=",.2f"),
            ],
        )
        .properties(height=100)
        .configure_view(strokeOpacity=0)
        .configure_axis(gridColor="#E6F2FF", labelColor="#5B6B82", titleColor="#5B6B82")
    )
    st.altair_chart(
        comparison_chart,
        width="stretch",
        alt="Monthly average income compared with monthly average spending.",
    )

    st.subheader("Spending breakdown", anchor="spending")
    chart_data = [
        {
            "Category": category.value.replace("_", " ").title(),
            "Monthly spending": amount,
            "Amount label": f"{format_eur(amount)}",
        }
        for category, amount in metrics.spending_by_category.items()
    ]
    chart_data.sort(key=lambda row: row["Monthly spending"], reverse=True)
    if chart_data:
        chart_data_source = alt.Data(values=chart_data)
        domain_max = max(chart_data[0]["Monthly spending"] * 1.15, 1.0)
        bars = (
            alt.Chart(chart_data_source)
            .mark_bar(color="#0EA5A0", cornerRadiusEnd=4)
            .encode(
                x=alt.X(
                    "Monthly spending:Q",
                    title="Monthly spending (€ / month)",
                    axis=alt.Axis(format=",.0f"),
                    scale=alt.Scale(domainMax=domain_max),
                ),
                y=alt.Y("Category:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
                tooltip=[
                    alt.Tooltip("Category:N"),
                    alt.Tooltip("Monthly spending:Q", title="Monthly amount", format=",.2f"),
                ],
            )
        )
        value_labels = (
            alt.Chart(chart_data_source)
            .mark_text(align="left", baseline="middle", dx=7, color="#0B2D5B", fontSize=12)
            .encode(
                x="Monthly spending:Q",
                y=alt.Y("Category:N", sort="-x"),
                text="Amount label:N",
            )
        )
        spending_chart = (
            alt.layer(bars, value_labels)
            .properties(height=max(220, len(chart_data) * 36))
            .configure_view(strokeOpacity=0)
            .configure_axis(gridColor="#E6F2FF", labelColor="#5B6B82", titleColor="#5B6B82")
        )
        st.altair_chart(
            spending_chart,
            width="stretch",
            alt="Monthly spending by category, ordered from highest to lowest, with euro amounts.",
        )
        st.caption("All amounts are EUR per month.")
    else:
        st.info("No spending categories are available.")

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
    if subscription_rows:
        st.dataframe(subscription_data, hide_index=True, width="stretch")
    else:
        st.info("No subscriptions identified.")

    if report.debt_plan is not None:
        plan = report.debt_plan
        st.subheader("Debt repayment plan", anchor="debt")
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
            st.metric("Extra monthly payment", format_eur(plan.extra_monthly_payment))
            projection_complete = (
                plan.months_to_debt_free_current < MAX_MONTHS
                and plan.months_to_debt_free_with_extra < MAX_MONTHS
            )
            if projection_complete:
                st.info(
                    f"Debt-free in {plan.months_to_debt_free_with_extra} months "
                    f"({plan.months_saved} months earlier)"
                )
                st.metric("Interest saved", format_eur(plan.interest_saved))
            else:
                st.info(
                    f"Payoff was not reached within {MAX_MONTHS} months; "
                    "a payoff date and interest saving cannot be estimated."
                )
