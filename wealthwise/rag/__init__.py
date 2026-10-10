"""Task C3: "Ask WealthWise" questions over the user's own data. Spec: docs/specs/03-dashboard-and-rag.md#c3-ask-wealthwise-answer_question"""

from wealthwise.contracts import FinancialProfile, Report


def answer_question(profile: FinancialProfile, report: Report, question: str) -> str:
    raise NotImplementedError("C3 answer_question")
