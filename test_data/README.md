# Test data

Extra fictional documents in layouts that differ from `samples/`, to check that the parsers aren't tied to one format. Hand-made, unlike `samples/` (which is generated and holds the answer keys). Never put real financial documents here.

| Folder | Person, period | Files | Layout |
| --- | --- | --- | --- |
| `jan_2026/` | John Murphy, January 2026 | bank statement PDF, payslip PDF, loan PDF, transactions CSV | text lines (`Label: EUR 1,234.00`), not tables; loan as PDF; CSV is `Date,Category,Amount` with unsigned amounts |

### Scenario sets

Made by `python scripts/generate_test_data.py` (same layouts as `jan_2026/`; fictional people). Upload a whole folder to see the case. Scores are what the app gives today; tests in `tests/test_data_scenarios.py`.

| Folder | Case | Score |
| --- | --- | --- |
| `best_saver_mar_2026/` | Best: high savings, no debt, big cushion | 100 good |
| `good_small_loan_apr_2026/` | Good: small car loan, healthy savings | 96 good |
| `average_mixed_may_2026/` | In between: moderate debt, thin cushion | 73 fair |
| `worst_overspender_jun_2026/` | Worst: spends more than earned, credit card + loan (XLSX) | 24 needs attention |
| `high_debt_burden_jul_2026/` | Debt repayments over 50% of income (XLSX, 2 debts) | 58 fair |
| `no_emergency_fund_aug_2026/` | Saves well but the balance is near zero | 67 fair |
| `high_discretionary_sep_2026/` | Takeaways, shopping, nights out | 82 good |
| `subscription_creep_q1_2026/` | 3 months, 5 recurring subscriptions found | 100 good |
| `bank_only_no_debt_oct_2026/` | Bank statement only: no payslip, no debt plan | 100 good |
| `messy_csv_only_nov_2026/` | Unsigned CSV, unknown merchants, a refund | 80 good |
| `wrong_closing_balance_nov_2026/` | Printed closing balance is wrong, so a warning shows | 94 good |

Known quirks of `jan_2026/`, kept on purpose:

- The bank statement's printed closing balance (EUR 3,490.13) doesn't match its transactions (EUR 3,640.13), so the app shows a warning.
- The CSV covers the same month as the bank PDF, so uploading both ignores the CSV with an "Overlaps" warning.

Tests: `tests/test_data_jan.py`. To add a set, make a new folder `<mon>_<yyyy>/` and a matching test file.
