# Stream A: Ingestion

**Entry point:** `wealthwise.ingestion.load_profile(documents: list[UploadedDocument]) -> FinancialProfile`
**Folder:** `wealthwise/ingestion/`. **Tests:** `tests/test_ingestion.py`. **Libraries:** PyMuPDF (`import pymupdf`), pandas, openpyxl.

Pure parsing: no LLM, no categorising (leave `Transaction.category = None`).

## Detecting the document type

| Extension | Rule |
| --- | --- |
| `.csv` | bank statement |
| `.xlsx` | loan statement |
| `.pdf` | page-1 text contains "Net Pay" → payslip; contains "Statement" and "Balance" → bank statement; otherwise unsupported |

Unsupported, unreadable or empty files are **not** errors. Skip them and add a `SourceDocument` for each with a warning, e.g. `"Could not recognise document type"`. Only raise if no supported document was read.

## Bank statement: CSV
Columns: `Date,Description,Amount,Balance`. ISO dates, signed amounts, no thousands separators. One row becomes one `Transaction`, in file order.

## Bank statement: PDF
- One table per page. Read it with `page.find_tables()` and `table.extract()`, skipping each page's header row.
- Columns: `Date | Description | Money out | Money in | Balance`.
- Dates look like `03 Jul 2026` (`%d %b %Y`). Amounts look like `1,350.00`: remove the commas.
- `amount = money_in - money_out`, treating a blank cell as 0.
- If a row can't be parsed, skip it and add a warning naming the page and row.

## Payslip: PDF
- Header text lines: `Employer: …`, `Employee: …`, `Pay date: 25 Sep 2026`.
- Table `Description | Amount (EUR)`. The row `Gross Pay` gives `gross_pay`, the row `Net Pay` gives `net_pay`, and every row between them is a deduction, keyed by its label as printed.
- The `Payslip` model checks that net = gross − deductions. If it fails, catch the error and add a warning instead of crashing.

## Loan statement: XLSX
- First sheet. Find the header row by scanning down for a row containing `Balance (EUR)`. There are title rows above it.
- Columns: `Lender, Product, Type, Balance (EUR), APR (%), Monthly Payment (EUR), Remaining Term (months)`.
- `name = f"{Lender} {Product}"`.
- `kind`: `Type` "Loan" maps to `loan`; "Credit Card" maps to `credit_card`.
- Stop at the first empty row. A blank term becomes `None`.

## Combining documents
- Transactions from all bank statements, sorted by date (stable). If a second bank statement overlaps the first one's date range, ignore it and add the warning "Overlaps <first filename>; ignored". This stops PDF + CSV of the same period being double counted.
- `sources`: one entry per uploaded file, in upload order.

## Acceptance criteria
- [ ] Bank PDF + payslip PDF + loan XLSX from `samples/` produce exactly `samples/expected_profile.json`. Compare `model_dump()` with `pytest.approx` for floats.
- [ ] The bank CSV yields the same transactions as the bank PDF.
- [ ] Uploading both bank files yields 87 transactions, not 174, plus one overlap warning.
- [ ] An unknown PDF or a `.txt` file gives a warning, not an exception.
- [ ] No network or LLM calls.
