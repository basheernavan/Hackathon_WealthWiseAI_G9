import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from wealthwise.contracts import Report
from wealthwise.dashboard import format_eur, format_pct

MOCK_REPORT = Path(__file__).resolve().parents[1] / "samples" / "mock_report.json"


@pytest.fixture
def mock_report():
    return Report.model_validate_json(MOCK_REPORT.read_text(encoding="utf-8"))


def run_report(report, profile=None):
    profile_setup = ""
    profile_argument = ""
    if profile is not None:
        profile_setup = (
            "from wealthwise.contracts import FinancialProfile\n"
            f"profile = FinancialProfile.model_validate_json({profile.model_dump_json()!r})\n"
        )
        profile_argument = ", profile=profile"
    script = "\n".join(
        (
            "from wealthwise.contracts import Report",
            "from wealthwise.dashboard import render_report",
            f"report = Report.model_validate_json({report.model_dump_json()!r})",
            profile_setup + f"render_report(report{profile_argument})",
        )
    )
    return AppTest.from_string(script).run(timeout=10)


def test_format_eur_shows_euros_with_two_decimal_places():
    assert format_eur(1234.5) == "€1,234.50"


def test_format_eur_places_negative_sign_before_currency_symbol():
    assert format_eur(-12) == "-€12.00"


def test_format_eur_formats_zero():
    assert format_eur(0) == "€0.00"


def test_format_pct_converts_fraction_to_one_decimal_percent():
    assert format_pct(0.0681) == "6.8%"


@pytest.mark.parametrize(("fraction", "expected"), [(0, "0.0%"), (-0.125, "-12.5%")])
def test_format_pct_handles_zero_and_negative_fractions(fraction, expected):
    assert format_pct(fraction) == expected


def test_render_report_shows_health_score_and_four_component_bars(mock_report):
    at = run_report(mock_report)

    assert not at.exception
    score_metric = next(metric for metric in at.metric if metric.label == "Financial Health Score")
    assert score_metric.value == "67/100"
    assert not score_metric.delta
    assert "Band: Fair" in [caption.value for caption in at.caption]
    assert sum("points" in caption.value for caption in at.caption) == 4


def test_render_report_shows_verified_financial_overview_cards(mock_report):
    at = run_report(mock_report)
    metrics = {metric.label: metric.value for metric in at.metric}
    headings = {heading.value for heading in at.subheader}

    assert "Financial Health Score" in headings
    assert "Financial Overview" in headings
    assert "AI Recommendations" in headings
    assert "Spending breakdown" in headings
    assert "Debt repayment plan" in headings
    assert metrics["Monthly income"] == "€3,150.00"
    assert metrics["Monthly spending"] == "€2,935.60"
    assert metrics["Monthly surplus"] == "€214.40"
    assert metrics["Total debt"] == "€9,900.00"
    assert metrics["Reported balance"] == "€3,843.20"
    assert metrics["Recurring subscriptions"] == "€67.97"
    assert metrics["Emergency fund"] == "1.31"
    assert "per month; 3 identified" in [caption.value for caption in at.caption]
    assert "months of spending; current balance vs monthly spending" in [
        caption.value for caption in at.caption
    ]


def test_render_report_shows_three_scenarios_and_wide_supporting_evidence(mock_report):
    at = run_report(mock_report)
    rendered_markdown = " ".join(element.value for element in at.markdown)

    assert "Review your takeaway spending" in rendered_markdown
    assert "Consider the avalanche debt plan" in rendered_markdown
    assert "Build a 3-month emergency fund" in rendered_markdown
    assert len(at.expander) == 1
    impact_metrics = {
        metric.label: metric.value for metric in at.metric
    }
    assert [
        impact_metrics[label]
        for label in ("Potential monthly cut", "Monthly extra payment", "Monthly savings")
    ] == [
        "€107.56",
        "€160.98",
        "€160.98",
    ]
    assert any("not additional savings" in element.value.lower() for element in at.caption)
    assert len(at.dataframe) == 2


def test_supporting_evidence_shows_full_transactions_and_debt_assumptions(
    mock_report, sample_profile
):
    at = run_report(mock_report, sample_profile)

    spending_rows = at.dataframe[0].value
    assert len(spending_rows) == 18
    assert "UBER EATS" in " ".join(spending_rows["Merchant / description"])

    at.selectbox[0].select("Debt repayment scenario").run()
    debt_rows = at.dataframe[0].value
    assert "Northwind Bank Visa Credit Card" in " ".join(debt_rows["Debt"])
    assert "APR" in debt_rows.columns
    assert "Scheduled monthly payment" in debt_rows.columns


def test_render_report_shows_spending_breakdown_and_subscriptions_table(mock_report):
    at = run_report(mock_report)

    assert "Spending breakdown" in [heading.value for heading in at.subheader]
    assert len(at.dataframe) == 2
    assert "NETFLIX.COM" in at.dataframe[-1].value.to_string()


def test_spending_chart_orders_categories_and_labels_values_in_euros(mock_report):
    at = run_report(mock_report)

    assert not at.exception
    charts = at.get("vega_lite_chart")
    assert len(charts) == 2
    chart = json.loads(charts[1].proto.spec)
    bars, labels = chart["layer"]
    assert bars["encoding"]["y"]["sort"] == "-x"
    assert bars["encoding"]["x"]["title"] == "Monthly spending (€ / month)"
    assert bars["encoding"]["x"]["axis"]["format"] == ",.0f"
    assert bars["encoding"]["x"]["scale"]["domainMax"] == pytest.approx(1552.5)
    assert bars["encoding"]["tooltip"][1]["format"] == ",.2f"
    assert bars["mark"]["color"] == "#28734B"
    assert labels["encoding"]["text"]["field"] == "Amount label"


def test_report_explains_when_spending_categories_and_subscriptions_are_empty(mock_report):
    metrics = mock_report.metrics.model_copy(update={"spending_by_category": {}})
    report = mock_report.model_copy(update={"metrics": metrics, "subscriptions": []})

    at = run_report(report)

    assert not at.exception
    assert "No spending categories are available." in [message.value for message in at.info]
    assert "No subscriptions identified." in [message.value for message in at.info]


def test_render_report_shows_avalanche_debt_plan_summary(mock_report):
    at = run_report(mock_report)
    visible_text = " ".join(
        element.value for element in (*at.markdown, *at.caption, *at.info, *at.metric)
    )

    assert "Debt repayment plan" in [heading.value for heading in at.subheader]
    assert "Northwind Bank Visa Credit Card" in visible_text
    assert "Northwind Bank Car Loan" in visible_text
    assert "Debt-free in 20 months (8 months earlier)" in visible_text
    assert "€513.39" in visible_text


def test_render_report_omits_debt_plan_section_when_plan_is_missing(mock_report):
    report_without_plan = mock_report.model_copy(update={"debt_plan": None})
    at = run_report(report_without_plan)

    assert not at.exception
    assert "Financial Health Score" in [heading.value for heading in at.subheader]
    assert "Debt repayment plan" not in [heading.value for heading in at.subheader]
