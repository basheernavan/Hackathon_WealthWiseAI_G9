"""Stream A: turn uploaded files into a FinancialProfile. Spec: docs/specs/01-ingestion.md

Task A6 builds load_profile: detect each file's type, call the matching parser, and combine the results.
The parsers live in their own modules (tasks A1-A5); call them through this module's names, e.g.
`bank_csv.parse_bank_csv(...)`, so A6's tests can monkeypatch them before they are built.
"""

from wealthwise.contracts import FinancialProfile, UploadedDocument
from wealthwise.ingestion import bank_csv, bank_pdf, detect, loan_xlsx, payslip_pdf  # noqa: F401


def load_profile(documents: list[UploadedDocument]) -> FinancialProfile:
    raise NotImplementedError("A6 load_profile")
