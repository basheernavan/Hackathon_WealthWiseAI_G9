"""Task B6: the LangGraph spending, debt and savings agents. Spec: docs/specs/02-analysis.md#b6-agents-langgraph"""

from wealthwise.contracts import DebtPayoffPlan, Metrics, Recommendation, SavingsPlan, Transaction


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
    raise NotImplementedError("B6 run_agents")
