"""Task A2: parse the bank statement CSV. Spec: docs/specs/01-ingestion.md#a2-bank-statement-csv"""

from wealthwise.contracts import Transaction


def parse_bank_csv(content: bytes) -> tuple[list[Transaction], list[str]]:
    """Return (transactions in file order, warnings)."""
    raise NotImplementedError("A2 parse_bank_csv")
