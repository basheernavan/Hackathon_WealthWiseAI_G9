"""Stream C: "Ask WealthWise" questions over the user's own data. Spec: docs/specs/03-dashboard-and-rag.md"""

from wealthwise.contracts import FinancialProfile, Report


def answer_question(profile: FinancialProfile, report: Report, question: str) -> str:
    raise NotImplementedError("Stream C - see docs/specs/03-dashboard-and-rag.md")
