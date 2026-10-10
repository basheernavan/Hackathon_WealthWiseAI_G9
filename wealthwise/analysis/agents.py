"""Task B6: the LangGraph spending, debt and savings agents. Spec: docs/specs/02-analysis.md#b6-agents-langgraph

Code fills agent, monthly_impact and evidence; the LLM only rewrites title and detail from the given
figures (ADR-0001). Without a key, or if a call fails, the template text stands and llm_used is False.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from wealthwise.contracts import (
    AgentName,
    Category,
    DebtPayoffPlan,
    Metrics,
    Recommendation,
    SavingsPlan,
    Transaction,
)
from wealthwise.llm import get_chat_model

ORDER = [AgentName.SPENDING, AgentName.DEBT, AgentName.SAVINGS]
PROMPT = (
    "You are WealthWise, a plain-spoken financial coach. Rewrite this {agent} recommendation for the user. "
    "Use only these figures and quote them exactly; do not invent numbers. "
    "Title: 12 words or fewer. Detail: at most 2 sentences.\n\nFigures:\n{figures}\n\nDraft title: {title}\nDraft detail: {detail}"
)


class Wording(BaseModel):
    title: str
    detail: str


class State(TypedDict):
    transactions: list[Transaction]
    metrics: Metrics
    identified_cuts: float
    debt_plan: DebtPayoffPlan | None
    savings_plan: SavingsPlan
    recommendations: Annotated[list[tuple[Recommendation, bool]], operator.add]


def eur(amount: float) -> str:
    return f"EUR {amount:,.2f}"


def worded(draft: Recommendation, figures: dict) -> tuple[Recommendation, bool]:
    """Return (recommendation, whether the LLM wrote its words)."""
    model = get_chat_model()
    if model is None:
        return draft, False
    try:
        lines = "\n".join(f"- {k}: {v}" for k, v in figures.items())
        prompt = PROMPT.format(agent=draft.agent.value, figures=lines, title=draft.title, detail=draft.detail)
        wording = model.with_structured_output(Wording).invoke(prompt)
        return draft.model_copy(update={"title": wording.title, "detail": wording.detail}), True
    except Exception:
        return draft, False


def spending_agent(state: State) -> dict:
    takeaway = state["metrics"].spending_by_category.get(Category.TAKEAWAY, 0.0)
    cuts = state["identified_cuts"]
    evidence = sorted((t for t in state["transactions"] if t.category == Category.TAKEAWAY), key=lambda t: t.amount)[:5]
    if takeaway:
        title, detail = "Halve takeaway spending", f"Takeaway averages {eur(takeaway)}/month. Cutting it in half frees {eur(cuts)}/month."
    else:
        share = state["metrics"].discretionary_share
        title, detail = "Keep discretionary spending in check", f"Discretionary spending is {share:.0%} of what you spend each month."
    draft = Recommendation(agent=AgentName.SPENDING, title=title, detail=detail, monthly_impact=cuts, evidence=evidence)
    return {"recommendations": [worded(draft, {"takeaway per month": eur(takeaway), "identified cuts per month": eur(cuts)})]}


def debt_agent(state: State) -> dict:
    plan = state["debt_plan"]
    evidence = [t for t in state["transactions"] if t.category == Category.DEBT_REPAYMENT]
    if plan is None:
        draft = Recommendation(agent=AgentName.DEBT, title="No debts to pay off", detail="No loans or credit cards were found in your documents.", evidence=evidence)
        return {"recommendations": [worded(draft, {"debts": "none"})]}
    figures = {
        "pay first": plan.payoff_order[0],
        "extra per month": eur(plan.extra_monthly_payment),
        "months saved": plan.months_saved,
        "interest saved": eur(plan.interest_saved),
    }
    draft = Recommendation(
        agent=AgentName.DEBT,
        title=f"Pay off the {plan.payoff_order[0]} first",
        detail=f"Adding {eur(plan.extra_monthly_payment)}/month makes you debt-free {plan.months_saved} months earlier "
        f"and saves {eur(plan.interest_saved)} in interest.",
        monthly_impact=plan.extra_monthly_payment,
        evidence=evidence,
    )
    return {"recommendations": [worded(draft, figures)]}


def savings_agent(state: State) -> dict:
    plan = state["savings_plan"]
    if plan.months_to_target is None:
        detail = f"Free up money each month to start a {eur(plan.target_amount)} emergency fund (3 months of spending)."
    elif plan.months_to_target == 0:
        detail = f"Your balance already covers 3 months of spending ({eur(plan.target_amount)}). Keep it there."
    else:
        detail = f"Save {eur(plan.monthly_amount)}/month to reach {eur(plan.target_amount)} in {plan.months_to_target} months."
    figures = {"save per month": eur(plan.monthly_amount), "target": eur(plan.target_amount), "months to target": plan.months_to_target}
    draft = Recommendation(agent=AgentName.SAVINGS, title="Build a 3-month emergency fund", detail=detail, monthly_impact=plan.monthly_amount)
    return {"recommendations": [worded(draft, figures)]}


def compose(state: State) -> dict:
    return {}  # ordering happens on the way out, since the reducer only appends


def build_graph():
    graph = StateGraph(State)
    for name, node in [("spending_agent", spending_agent), ("debt_agent", debt_agent), ("savings_agent", savings_agent)]:
        graph.add_node(name, node)
        graph.add_edge(START, name)
        graph.add_edge(name, "compose")
    graph.add_node("compose", compose)
    graph.add_edge("compose", END)
    return graph.compile()


def run_agents(
    transactions: list[Transaction],
    metrics: Metrics,
    identified_cuts: float,
    debt_plan: DebtPayoffPlan | None,
    savings_plan: SavingsPlan,
) -> tuple[list[Recommendation], bool]:
    """Return (recommendations in spending, debt, savings order, llm_used).

    `transactions` already have categories set. Works with no API key (template text, llm_used False).
    """
    state = build_graph().invoke(
        {
            "transactions": transactions,
            "metrics": metrics,
            "identified_cuts": identified_cuts,
            "debt_plan": debt_plan,
            "savings_plan": savings_plan,
            "recommendations": [],
        }
    )
    results = sorted(state["recommendations"], key=lambda r: ORDER.index(r[0].agent))
    return [r for r, _ in results], all(used for _, used in results)
