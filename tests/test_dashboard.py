from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from wealthwise.contracts import Report
from wealthwise.dashboard import format_eur, format_pct

MOCK_REPORT = Path(__file__).resolve().parents[1] / "samples" / "mock_report.json"


@pytest.fixture
def mock_report():
    return Report.model_validate_json(MOCK_REPORT.read_text(encoding="utf-8"))


def run_report(report):
    script = "\n".join(
        (
            "from wealthwise.contracts import Report",
            "from wealthwise.dashboard import render_report",
            f"report = Report.model_validate_json({report.model_dump_json()!r})",
            "render_report(report)",
        )
    )
    return AppTest.from_string(script).run()


def test_format_eur_shows_euros_with_two_decimal_places():
    assert format_eur(1234.5) == "€1,234.50"


def test_format_eur_places_negative_sign_before_currency_symbol():
    assert format_eur(-12) == "-€12.00"


def test_format_eur_formats_zero():
    assert format_eur(0) == "€0.00"


def test_format_pct_converts_fraction_to_one_decimal_percent():
    assert format_pct(0.0681) == "6.8%"


def test_render_report_shows_health_score_and_four_component_bars(mock_report):
    at = run_report(mock_report)

    assert not at.exception
    score_metric = next(metric for metric in at.metric if metric.label == "Financial Health Score")
    assert score_metric.value == "67/100"
    assert not score_metric.delta
    assert "Band: Fair" in [caption.value for caption in at.caption]
    assert sum("points" in caption.value for caption in at.caption) == 4


def test_render_report_shows_five_financial_metrics(mock_report):
    at = run_report(mock_report)
    metrics = {metric.label: metric.value for metric in at.metric}

    assert metrics["Monthly income"] == "€3,150.00"
    assert metrics["Monthly spending"] == "€2,935.60"
    assert metrics["Monthly surplus"] == "€214.40"
    assert metrics["Total debt"] == "€9,900.00"
    assert metrics["Emergency fund"] == "1.31 months"


def test_render_report_shows_three_recommendation_cards_with_evidence_tables(mock_report):
    at = run_report(mock_report)
    rendered_markdown = " ".join(element.value for element in at.markdown)

    assert "Halve takeaway spending" in rendered_markdown
    assert "Pay off the Northwind Bank Visa Credit Card first" in rendered_markdown
    assert "Build a 3-month emergency fund" in rendered_markdown
    assert len(at.expander) == 3
    assert sum("Monthly impact:" in caption.value for caption in at.caption) == 3
    assert len(at.dataframe) == 4


def test_render_report_shows_spending_breakdown_and_subscriptions_table(mock_report):
    at = run_report(mock_report)

    assert "Spending breakdown" in [heading.value for heading in at.subheader]
    assert len(at.dataframe) == 4


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