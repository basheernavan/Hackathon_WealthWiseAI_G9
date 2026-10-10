"""Stream A: turn uploaded files into a FinancialProfile. Spec: docs/specs/01-ingestion.md"""

from wealthwise.contracts import FinancialProfile, UploadedDocument


def load_profile(documents: list[UploadedDocument]) -> FinancialProfile:
    raise NotImplementedError("Stream A - see docs/specs/01-ingestion.md")
