# Test data

Extra fictional documents in layouts that differ from `samples/`, to check that the parsers aren't tied to one format. Hand-made, unlike `samples/` (which is generated and holds the answer keys). Never put real financial documents here.

| Folder | Person, period | Files | Layout |
| --- | --- | --- | --- |
| `jan_2026/` | John Murphy, January 2026 | bank statement PDF, payslip PDF, loan PDF, transactions CSV | text lines (`Label: EUR 1,234.00`), not tables; loan as PDF; CSV is `Date,Category,Amount` with unsigned amounts |

Known quirks, kept on purpose:

- The bank statement's printed closing balance (EUR 3,490.13) doesn't match its transactions (EUR 3,640.13), so the app shows a warning.
- The CSV covers the same month as the bank PDF, so uploading both ignores the CSV with an "Overlaps" warning.

Tests: `tests/test_data_jan.py`. To add a set, make a new folder `<mon>_<yyyy>/` and a matching test file.
