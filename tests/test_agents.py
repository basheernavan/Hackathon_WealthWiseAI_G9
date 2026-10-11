import pytest

from wealthwise.analysis.agents import run_agents
from wealthwise.contracts import AgentName, Category, DebtPayoffPlan, SavingsPlan


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


@pytest.fixture
def figures(categorised_profile, expected_metrics, expected):
    return (
        categorised_profile.transactions,
        expected_metrics,
        expected["identified_cuts"],
        DebtPayoffPlan.model_validate(expected["debt_plan"]),
        SavingsPlan.model_validate(expected["savings_plan"]),
    )


def test_three_template_recommendations_in_order_without_a_key(figures):
    recommendations, llm_used = run_agents(*figures)
    assert llm_used is False
    assert [r.agent for r in recommendations] == [AgentName.SPENDING, AgentName.DEBT, AgentName.SAVINGS]
    assert [r.monthly_impact for r in recommendations] == pytest.approx([107.56, 160.98, 160.98], abs=0.01)
    assert all(r.title and r.detail for r in recommendations)
    spending = recommendations[0]
    assert spending.title == "Review your takeaway spending"
    assert "illustrative option" in spending.detail
    assert "not a recommendation" in spending.detail
    assert recommendations[1].title == "Consider the avalanche debt plan"
    assert "Adding EUR 160.98/month" in recommendations[1].detail


def test_spending_evidence_is_the_five_largest_takeaway_outflows(figures):
    transactions = figures[0]
    takeaway = sorted((t for t in transactions if t.category == Category.TAKEAWAY), key=lambda t: t.amount)[:5]
    recommendations, _ = run_agents(*figures)
    assert recommendations[0].evidence == takeaway


def test_debt_evidence_is_the_debt_repayments(figures):
    recommendations, _ = run_agents(*figures)
    assert recommendations[1].evidence == [t for t in figures[0] if t.category == Category.DEBT_REPAYMENT]


def test_no_debt_plan_still_gives_three_recommendations(figures):
    transactions, metrics, cuts, _, savings = figures
    recommendations, llm_used = run_agents(transactions, metrics, cuts, None, savings)
    assert len(recommendations) == 3 and llm_used is False
    assert recommendations[1].monthly_impact is None


def test_failing_llm_falls_back_to_templates(figures, monkeypatch):
    from wealthwise.analysis import agents

    class Broken:
        def with_structured_output(self, schema):
            raise RuntimeError("network down")

    monkeypatch.setattr(agents, "get_chat_model", lambda: Broken())
    recommendations, llm_used = run_agents(*figures)
    assert llm_used is False and len(recommendations) == 3
