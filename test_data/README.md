# Test data

Extra fictional documents in layouts that differ from `samples/`, to check that the parsers aren't tied to one format. Hand-made, unlike `samples/` (which is generated and holds the answer keys). Never put real financial documents here.

| Folder | Person, period | Files | Layout |
| --- | --- | --- | --- |
| `jan_2026/` | John Murphy, January 2026 | bank statement PDF, payslip PDF, loan PDF, transactions CSV | text lines (`Label: EUR 1,234.00`), not tables; loan as PDF; CSV is `Date,Category,Amount` with unsigned amounts |
| `apr_aug_2026/` | Emma OBrien, April to August 2026 | 5 bank statement PDFs, 5 payslip PDFs, 1 invalid payslip, 5 transactions CSVs | as `jan_2026/`, but the bank PDFs have no "Statement" heading and only the first transaction line has a date |

Known quirks in `jan_2026/`, kept on purpose:

- The bank statement's printed closing balance (EUR 3,490.13) doesn't match its transactions (EUR 3,640.13), so the app shows a warning.
- The CSV covers the same month as the bank PDF, so uploading both ignores the CSV with an "Overlaps" warning.

Known quirks in `apr_aug_2026/`, kept on purpose:

- `Payslip_Invalid_2026.pdf`: net pay (EUR 3,500) isn't gross minus deductions (EUR 3,150), so it is skipped with a warning. Uploaded on its own, the app reports no supported documents.
- Each CSV covers the same month as that month's bank PDF, so uploading both ignores the CSV.

Tests: `tests/test_data_jan.py`, `tests/test_data_apr_aug.py`. To add a set, make a new folder `<mon>_<yyyy>/` and a matching test file.
