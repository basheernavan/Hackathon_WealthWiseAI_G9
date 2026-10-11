"""Task A4: parse the payslip PDF. Spec: docs/specs/01-ingestion.md#a4-payslip-pdf

Two layouts: a `Description | Amount (EUR)` table (samples/), or `Label: EUR 1,234.00` text lines
(test_data/jan_2026/). Either way Gross comes first, Net Pay last, and every amount between is a deduction.
"""

import re
from datetime import date, datetime

import pymupdf
from pydantic import ValidationError

from wealthwise.contracts import Payslip

FIELD = re.compile(r"^(Employer|Employee|Pay date)\s*:\s*(.+)$", re.IGNORECASE)
AMOUNT_LINE = re.compile(r"^(.+?)\s*:\s*(?:EUR\s*)?([\d,]+\.\d{2})$", re.IGNORECASE)
GROSS = ("gross pay", "gross salary", "gross")


def money(text: str) -> float:
    return float(text.replace(",", "").strip())


def parse_date(text: str) -> date:
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"pay date {text!r}")


def parse_payslip_pdf(content: bytes) -> tuple[Payslip | None, list[str]]:
    """Return (payslip, warnings). The payslip is None, with a warning, when it can't be read or doesn't add up."""
    try:
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            page = doc[0]
            lines = [line.strip() for line in page.get_text().splitlines() if line.strip()]
            tables = [t.extract() for t in page.find_tables().tables]
    except Exception as e:
        return None, [f"Could not read payslip: {e}"]

    fields = {m.group(1).lower(): m.group(2).strip() for m in map(FIELD.match, lines) if m}
    table = next((rows for rows in tables if rows and rows[0][:2] == ["Description", "Amount (EUR)"]), None)
    try:
        if table:
            amounts = [(label.strip(), money(value)) for label, value in table[1:]]
        else:
            amounts = [(m.group(1).strip(), money(m.group(2))) for m in map(AMOUNT_LINE.match, lines) if m]
    except (ValueError, TypeError, AttributeError):
        return None, ["Payslip skipped: could not read the amounts"]

    labels = [label.lower() for label, _ in amounts]
    gross_at = next((i for i, label in enumerate(labels) if label in GROSS), None)
    net_at = next((i for i, label in enumerate(labels) if label == "net pay"), None)
    if gross_at is None or net_at is None or net_at < gross_at:
        return None, ["Not a payslip: no Gross and Net Pay amounts found"]

    try:
        payslip = Payslip(
            employer=fields.get("employer") or lines[0],
            employee=fields["employee"],
            pay_date=parse_date(fields["pay date"]),
            gross_pay=amounts[gross_at][1],
            deductions=dict(amounts[gross_at + 1 : net_at]),
            net_pay=amounts[net_at][1],
        )
    except ValidationError:
        return None, ["Payslip skipped: net pay doesn't equal gross pay minus deductions"]
    except (KeyError, ValueError) as e:
        return None, [f"Payslip skipped: could not read {e}"]
    return payslip, []
