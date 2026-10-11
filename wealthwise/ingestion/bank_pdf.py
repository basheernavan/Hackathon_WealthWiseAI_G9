"""Task A3: parse the bank statement PDF. Spec: docs/specs/01-ingestion.md#a3-bank-statement-pdf

Two layouts: a table per page (samples/), or one text line per transaction such as
`02/01/2026 Monthly Salary Credit EUR 3,272.00` (test_data/jan_2026/). A line with no date
takes the date of the line above it (test_data/apr_aug_2026/).
"""

import re
from datetime import date, datetime

import pymupdf

from wealthwise.contracts import Transaction

HEADER = ["Date", "Description", "Money out", "Money in", "Balance"]
LINE = re.compile(r"^(?:(\d{2}/\d{2}/\d{4})\s+)?(.+?)\s+(Credit|Debit)\s+(?:EUR\s*)?([\d,]+\.\d{2})$", re.IGNORECASE)
OPENING = re.compile(r"Opening Balance:\s*(?:EUR\s*)?(-?[\d,]+\.\d{2})", re.IGNORECASE)
CLOSING = re.compile(r"Closing Balance:\s*(?:EUR\s*)?(-?[\d,]+\.\d{2})", re.IGNORECASE)


def money(cell: str | None) -> float:
    cell = (cell or "").replace(",", "").strip()
    return float(cell) if cell else 0.0


def parse_bank_pdf(content: bytes) -> tuple[list[Transaction], list[str]]:
    """Return (transactions in statement order, warnings naming any skipped page/row)."""
    try:
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            pages = [(page.get_text(), [t.extract() for t in page.find_tables().tables]) for page in doc]
    except Exception as e:
        return [], [f"Could not read PDF: {e}"]

    if any(rows and rows[0] == HEADER for _, tables in pages for rows in tables):
        transactions, warnings = from_tables([tables for _, tables in pages])
    else:
        transactions, warnings = from_lines("\n".join(text for text, _ in pages))
    if not transactions and not warnings:
        warnings.append("No transactions found in bank statement")
    return transactions, warnings


def from_tables(pages: list[list[list[list[str]]]]) -> tuple[list[Transaction], list[str]]:
    transactions: list[Transaction] = []
    warnings: list[str] = []
    for page_no, tables in enumerate(pages, start=1):
        for rows in tables:
            for row_no, row in enumerate(rows[1:], start=1):
                try:
                    day, description, out, into, balance = row
                    transactions.append(
                        Transaction(
                            date=datetime.strptime(day.strip(), "%d %b %Y").date(),
                            description=description.strip(),
                            amount=round(money(into) - money(out), 2),
                            balance=money(balance) if (balance or "").strip() else None,
                        )
                    )
                except (ValueError, TypeError, AttributeError):
                    warnings.append(f"Skipped page {page_no} row {row_no}: could not read it")
    return transactions, warnings


def from_lines(text: str) -> tuple[list[Transaction], list[str]]:
    """Signed amounts from Credit/Debit; the balance runs from the opening balance when one is printed."""
    opening = OPENING.search(text)
    balance = money(opening.group(1)) if opening else None
    transactions: list[Transaction] = []
    day = None
    for line in text.splitlines():
        match = LINE.match(line.strip())
        if not match or not (match.group(1) or day):
            continue
        day = match.group(1) or day
        _, description, direction, amount = match.groups()
        signed = money(amount) if direction.lower() == "credit" else -money(amount)
        balance = round(balance + signed, 2) if balance is not None else None
        d, m, y = map(int, day.split("/"))
        transactions.append(Transaction(date=date(y, m, d), description=description.strip(), amount=signed, balance=balance))

    warnings: list[str] = []
    closing = CLOSING.search(text)
    if closing and balance is not None and transactions and abs(money(closing.group(1)) - balance) > 0.01:
        warnings.append(f"Closing balance EUR {closing.group(1)} does not match the transactions (EUR {balance:,.2f})")
    return transactions, warnings
