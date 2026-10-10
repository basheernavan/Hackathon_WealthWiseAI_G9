"""Task A5: parse the loan statement XLSX. Spec: docs/specs/01-ingestion.md#a5-loan-statement-xlsx"""

from wealthwise.contracts import Debt


def parse_loan_xlsx(content: bytes) -> tuple[list[Debt], list[str]]:
    """Return (debts in sheet order, warnings)."""
    raise NotImplementedError("A5 parse_loan_xlsx")
