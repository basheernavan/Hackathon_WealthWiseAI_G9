"""Stream B: turn a FinancialProfile into a Report. Spec: docs/specs/02-analysis.md"""

from wealthwise.contracts import FinancialProfile, Report


def build_report(profile: FinancialProfile) -> Report:
    raise NotImplementedError("Stream B - see docs/specs/02-analysis.md")
