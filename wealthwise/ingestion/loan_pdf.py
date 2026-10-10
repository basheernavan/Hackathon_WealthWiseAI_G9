"""Parse a one-loan PDF statement made of `Label: value` lines (test_data/jan_2026/). The XLSX layout is loan_xlsx.py."""

import re

import pymupdf

from wealthwise.contracts import Debt, DebtKind

FIELDS = {
    "balance": r"(?:Current|Outstanding)\s+Balance",
    "rate": r"(?:Interest Rate|APR)",
    "payment": r"Monthly\s+(?:Repayment|Payment)",
    "term": r"Remaining\s+Term",
}


def number(text: str) -> float:
    return float(re.sub(r"[^\d.]", "", text))


def title(line: str) -> str:
    """'AIB PERSONAL LOAN' -> 'AIB Personal Loan': short all-caps words stay as acronyms."""
    return " ".join(w if len(w) <= 3 and w.isupper() else w.capitalize() for w in line.split())


def parse_loan_pdf(content: bytes) -> tuple[list[Debt], list[str]]:
    """Return (debts, warnings)."""
    try:
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            text = "\n".join(page.get_text() for page in doc)
    except Exception as e:
        return [], [f"Could not read loan statement: {e}"]

    found = {}
    for key, label in FIELDS.items():
        match = re.search(rf"^{label}\s*:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
        if match:
            found[key] = match.group(1)
    missing = [k for k in ("balance", "rate", "payment") if k not in found]
    if missing:
        return [], [f"Loan statement skipped: no {', '.join(missing)} found"]

    first_line = next(line.strip() for line in text.splitlines() if line.strip())
    try:
        debt = Debt(
            name=title(first_line),
            kind=DebtKind.CREDIT_CARD if "credit card" in text.lower() else DebtKind.LOAN,
            balance=number(found["balance"]),
            annual_interest_rate=number(found["rate"]),
            monthly_payment=number(found["payment"]),
            remaining_term_months=int(number(found["term"])) if "term" in found else None,
        )
    except ValueError as e:
        return [], [f"Loan statement skipped: {e}"]
    return [debt], []
