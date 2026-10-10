"""Task A2: parse the bank statement CSV. Spec: docs/specs/01-ingestion.md#a2-bank-statement-csv"""

import csv
import io
from datetime import date

from wealthwise.contracts import Transaction


def parse_bank_csv(content: bytes) -> tuple[list[Transaction], list[str]]:
    """Return (transactions in file order, warnings)."""
    transactions: list[Transaction] = []
    warnings: list[str] = []
    try:
        rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error) as e:
        return [], [f"Could not read CSV: {e}"]
    for i, row in enumerate(rows, start=1):
        try:
            balance = (row.get("Balance") or "").strip()
            transactions.append(
                Transaction(
                    date=date.fromisoformat(row["Date"].strip()),
                    description=row["Description"].strip(),
                    amount=float(row["Amount"]),
                    balance=float(balance) if balance else None,
                )
            )
        except (KeyError, ValueError, TypeError, AttributeError):
            warnings.append(f"Skipped row {i}: could not read it")
    return transactions, warnings
