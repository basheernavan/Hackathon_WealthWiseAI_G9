"""Task A5: parse the loan statement XLSX. Spec: docs/specs/01-ingestion.md#a5-loan-statement-xlsx"""

import io

import openpyxl

from wealthwise.contracts import Debt, DebtKind

KINDS = {"loan": DebtKind.LOAN, "credit card": DebtKind.CREDIT_CARD}


def parse_loan_xlsx(content: bytes) -> tuple[list[Debt], list[str]]:
    """Return (debts in sheet order, warnings)."""
    try:
        rows = list(openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
    except Exception as e:
        return [], [f"Could not read loan statement: {e}"]

    header_at = next((i for i, r in enumerate(rows) if "Balance (EUR)" in r), None)
    if header_at is None:
        return [], ["No 'Balance (EUR)' header row found in loan statement"]
    header = [str(h).strip() if h is not None else "" for h in rows[header_at]]

    debts: list[Debt] = []
    warnings: list[str] = []
    for n, row in enumerate(rows[header_at + 1 :], start=1):
        if all(v is None or str(v).strip() == "" for v in row):
            break
        cell = dict(zip(header, row))
        try:
            term = cell.get("Remaining Term (months)")
            debts.append(
                Debt(
                    name=f"{cell['Lender']} {cell['Product']}",
                    kind=KINDS[str(cell["Type"]).strip().lower()],
                    balance=float(cell["Balance (EUR)"]),
                    annual_interest_rate=float(cell["APR (%)"]),
                    monthly_payment=float(cell["Monthly Payment (EUR)"]),
                    remaining_term_months=int(term) if term not in (None, "") else None,
                )
            )
        except (KeyError, ValueError, TypeError):
            warnings.append(f"Skipped debt row {n}: could not read it")
    return debts, warnings
