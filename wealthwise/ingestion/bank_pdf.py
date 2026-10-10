"""Task A3: parse the bank statement PDF. Spec: docs/specs/01-ingestion.md#a3-bank-statement-pdf"""

from wealthwise.contracts import Transaction


def parse_bank_pdf(content: bytes) -> tuple[list[Transaction], list[str]]:
    """Return (transactions in statement order, warnings naming any skipped page/row)."""
    raise NotImplementedError("A3 parse_bank_pdf")
