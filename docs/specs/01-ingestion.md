# Stream A: Ingestion

**Entry point:** `wealthwise.ingestion.load_profile(documents: list[UploadedDocument]) -> FinancialProfile`
**Libraries:** PyMuPDF (`import pymupdf`), pandas, openpyxl.

Pure parsing: no LLM, no network, no categorising (leave `Transaction.category = None`).

Each task below is independent: its stub file already exists with the exact function signature, and it tests only against `samples/`. Test helpers (`sample_bytes`, `sample_document`, the `sample_profile` fixture) are in [`tests/conftest.py`](../../tests/conftest.py).

| Task | File | Function | Test file |
| --- | --- | --- | --- |
| A1 | `wealthwise/ingestion/detect.py` | `detect_document_type` | `tests/test_detect.py` |
| A2 | `wealthwise/ingestion/bank_csv.py` | `parse_bank_csv` | `tests/test_bank_csv.py` |
| A3 | `wealthwise/ingestion/bank_pdf.py` | `parse_bank_pdf` | `tests/test_bank_pdf.py` |
| A4 | `wealthwise/ingestion/payslip_pdf.py` | `parse_payslip_pdf` | `tests/test_payslip_pdf.py` |
| A5 | `wealthwise/ingestion/loan_xlsx.py` | `parse_loan_xlsx` | `tests/test_loan_xlsx.py` |
| A6 | `wealthwise/ingestion/__init__.py` | `load_profile` | `tests/test_load_profile.py` |

Every parser returns `(result, warnings)`. A parser never raises on bad input: it skips what it can't read and adds a warning.

## A1. Detect the document type

| Extension (case-insensitive) | Rule |
| --- | --- |
| `.csv` | `bank_statement` |
| `.xlsx` | `loan_statement` |
| `.pdf` | page-1 text contains "Net Pay" → `payslip`; contains "Statement" and "Balance" → `bank_statement`; otherwise `None` |
| anything else, empty or unreadable | `None` |

**Done when:** each of the 4 sample files gives the right type; a `.txt` file, empty bytes and a PDF without those words (make one with `pymupdf.open()` + `insert_text`) give `None`.

## A2. Bank statement: CSV

Columns: `Date,Description,Amount,Balance`. ISO dates, signed amounts, no thousands separators. One row becomes one `Transaction`, in file order.

**Done when:** `parse_bank_csv(sample_bytes(BANK_CSV))` equals `sample_profile.transactions` with no warnings.

## A3. Bank statement: PDF

- One table per page. Read it with `page.find_tables()` and `table.extract()`, skipping each page's header row.
- Columns: `Date | Description | Money out | Money in | Balance`.
- Dates look like `03 Jul 2026` (`%d %b %Y`). Amounts look like `1,350.00`: remove the commas.
- `amount = money_in - money_out`, treating a blank cell as 0.
- If a row can't be parsed, skip it and add a warning naming the page and row.

**Done when:** `parse_bank_pdf(sample_bytes(BANK_PDF))` equals `sample_profile.transactions` (floats within 0.01) with no warnings.

## A4. Payslip: PDF

- Header text lines: `Employer: …`, `Employee: …`, `Pay date: 25 Sep 2026`.
- Table `Description | Amount (EUR)`. The row `Gross Pay` gives `gross_pay`, the row `Net Pay` gives `net_pay`, and every row between them is a deduction, keyed by its label as printed.
- The `Payslip` model checks that net = gross − deductions. If it fails, catch the `ValidationError`, return `None` and a warning.

**Done when:** the sample payslip equals `sample_profile.payslips[0]`; a PDF that isn't a payslip gives `(None, [warning])` without raising.

## A5. Loan statement: XLSX

- First sheet. Find the header row by scanning down for a row containing `Balance (EUR)`. There are title rows above it.
- Columns: `Lender, Product, Type, Balance (EUR), APR (%), Monthly Payment (EUR), Remaining Term (months)`.
- `name = f"{Lender} {Product}"`.
- `kind`: `Type` "Loan" maps to `loan`; "Credit Card" maps to `credit_card`.
- Stop at the first empty row. A blank term becomes `None`.

**Done when:** the sample XLSX equals `sample_profile.debts`.

## A6. Combine documents: `load_profile`

For each document, in upload order: `detect.detect_document_type`, then the matching parser (`.csv` → `bank_csv.parse_bank_csv`, a bank `.pdf` → `bank_pdf.parse_bank_pdf`, and so on). Call parsers through their module (`bank_csv.parse_bank_csv(...)`), not `from ... import`, so tests can monkeypatch them.

- `sources`: one `SourceDocument` per uploaded file, in upload order, carrying that parser's warnings. An unsupported file gets `"Could not recognise document type"`. Its `document_type` is required by the contract, so use the type implied by the extension, or `bank_statement` if there is none.
- Transactions from all bank statements, sorted by date (stable). If a later bank statement's date range overlaps an earlier one's, ignore it and add the warning `"Overlaps <first filename>; ignored"` to it. This stops PDF + CSV of the same period being double counted.
- Raise `ValueError("No supported documents")` only if nothing was read.

**Done when** (tests monkeypatch the detector and parsers with fakes, so A6 never waits for A1-A5):
- [ ] Two overlapping fake bank statements give one set of transactions plus the overlap warning.
- [ ] An unsupported file gives a warning, not an exception, and the other files are still read.
- [ ] All files unsupported raises `ValueError`.

## Stream acceptance (runs automatically)

[`tests/test_acceptance.py`](../../tests/test_acceptance.py) skips until A1-A6 are all merged, then checks: the 3 sample files produce exactly `samples/expected_profile.json`; CSV and PDF give the same transactions; both bank files give 87 transactions, not 174.
