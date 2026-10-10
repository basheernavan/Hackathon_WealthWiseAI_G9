"""Task A2: parse the bank statement CSV. Spec: docs/specs/01-ingestion.md#a2-bank-statement-csv

Also reads a simpler export, `Date,Category,Amount` with unsigned amounts (test_data/jan_2026/):
the category becomes the description, and income-like categories are money in, the rest money out.
"""

import csv
import io
import re
from datetime import date

from wealthwise.contracts import Transaction

INCOME = re.compile(r"\b(?:salary|income|wages?|refund)\b", re.IGNORECASE)


def parse_bank_csv(content: bytes) -> tuple[list[Transaction], list[str]]:
    """Return (transactions in file order, warnings)."""
    transactions: list[Transaction] = []
    warnings: list[str] = []
    try:
        rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error) as e:
        return [], [f"Could not read CSV: {e}"]
    unsigned = bool(rows) and "Description" not in rows[0] and "Category" in rows[0]
    for i, row in enumerate(rows, start=1):
        try:
            balance = (row.get("Balance") or "").strip()
            description = (row["Category"] if unsigned else row["Description"]).strip()
            amount = float(row["Amount"])
            if unsigned and not INCOME.search(description):
                amount = -abs(amount)
            transactions.append(
                Transaction(
                    date=date.fromisoformat(row["Date"].strip()),
                    description=description,
                    amount=amount,
                    balance=float(balance) if balance else None,
                )
            )
        except (KeyError, ValueError, TypeError, AttributeError):
            warnings.append(f"Skipped row {i}: could not read it")
    if unsigned:
        income = sorted({t.description for t in transactions if t.amount > 0})
        warnings.append(f"Amounts have no sign: treated {', '.join(income) or 'nothing'} as income, the rest as spending")
    return transactions, warnings
