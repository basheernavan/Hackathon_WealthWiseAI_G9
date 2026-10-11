# WealthWise test report

**Date:** 2026-10-11 · **Build:** `main` at 4743b51 plus the new `test_data/` scenario sets · **Python 3.12.10, Windows 11** · **Mode:** offline (no `OPENROUTER_API_KEY`, template text, `llm_used = False`)

## 1. Summary

| Area | Result |
| --- | --- |
| Automated tests | **158 passed, 0 failed** in about 17 s (19 of them new, for the scenario sets) |
| Scenario sets run end to end | 11 new sets plus `jan_2026`, all load and produce a report with no crash |
| Score separates good from bad | Yes: 100 / 96 / 82 / 73 / 67 / 58 / 24 across the cases, in the right order |
| App starts | Yes: `streamlit run app.py` answered HTTP 200 on port 8501 (page not clicked through) |
| Defects found | 1 bug, 5 weaknesses (section 5) |
| Not tested | The LLM path (no key), the Ask WealthWise chat on the new data, a browser walk-through |

Verdict: the numeric pipeline (parse, categorise, metrics, score, plans) is correct and consistent on every set. The weak spots are in the advice text and in a few silent assumptions, not in the numbers.

## 2. What was tested

`scripts/generate_test_data.py` builds 11 folders in `test_data/`, in the same layouts as the hand-made `jan_2026/` (text-line bank and payslip PDFs, loan as PDF or XLSX, unsigned CSV). Everyone in them is fictional. Each folder is one upload set. Every set was run through `load_profile` then `build_report`.

The score is out of 100: savings rate 30, debt-to-income 30, emergency fund 20, discretionary share 20. Bands: good 75 or more, fair 50 to 74, needs attention below 50.

## 3. Results per scenario

| Scenario | Income | Spending | Savings rate | Debt-to-income | Cushion (months) | Discretionary | Points (sav/debt/emerg/disc) | **Score** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `best_saver_mar_2026` | 4,425 | 1,694 | 61.7% | 0% | 9.99 | 3.5% | 30 / 30 / 20 / 20 | **100 good** |
| `bank_only_no_debt_oct_2026` | 3,400 | 1,723 | 49.3% | 0% | 3.18 | 12.9% | 30 / 30 / 20 / 20 | **100 good** |
| `subscription_creep_q1_2026` | 2,900 | 1,514 | 47.8% | 0% | 4.73 | 8.2% | 30 / 30 / 20 / 20 | **100 good** |
| `good_small_loan_apr_2026` | 3,328 | 2,184 | 34.4% | 4.5% | 2.45 | 8.4% | 30 / 30 / 16.3 / 20 | **96 good** |
| `wrong_closing_balance_nov_2026` | 2,900 | 1,110 | 61.7% | 0% | 2.06 | 0% | 30 / 30 / 13.7 / 20 | **94 good** |
| `high_discretionary_sep_2026` | 3,712 | 2,388 | 35.7% | 0% | 4.32 | 47.2% | 30 / 30 / 20 / 1.8 | **82 good** |
| `messy_csv_only_nov_2026` | 2,935 | 1,826 | 37.8% | 0% | 0.00 | 7.5% | 30 / 30 / 0 / 20 | **80 good** |
| `average_mixed_may_2026` | 2,884 | 2,534 | 12.1% | 7.6% | 0.73 | 12.4% | 18.2 / 30 / 4.9 / 20 | **73 fair** |
| `no_emergency_fund_aug_2026` | 3,000 | 2,681 | 10.6% | 0% | 0.12 | 1.9% | 15.9 / 30 / 0.8 / 20 | **67 fair** |
| `high_debt_burden_jul_2026` | 3,192 | 2,550 | 20.1% | 68.9% | 1.27 | 0.8% | 30 / **0** / 8.5 / 20 | **58 fair** |
| `worst_overspender_jun_2026` | 1,762 | 3,035 | -72.3% | 35.2% | -0.36 | 30.2% | **0** / 11.1 / **0** / 13.2 | **24 needs attention** |
| `jan_2026` (existing) | 3,272 | 1,782 | 45.5% | 10.5% | 2.04 | 17.8% | 30 / 29.6 / 13.6 / 20 | **93 good** |

Amounts in EUR per month.

**What this shows**
- Each of the four components reaches 0 and full marks in at least one set, so every branch of the formula was exercised.
- Ordering is sensible: the best cases score 100, the worst 24, and the single-factor failures (no cushion, heavy debt, heavy discretionary spend) land between.
- Subscription detection found all 5 recurring services in `subscription_creep_q1_2026`, each seen in 3 months, largest first. No other set reports subscriptions, which is correct: they are single-month statements.
- The debt plan is `None` with no debts, and uses the avalanche order (highest APR first) with two: the credit card at 19.9% comes before the 7.9% loan.
- Ingestion warnings fired where expected: closing-balance mismatch, "Amounts have no sign" for the CSV, and "Overlaps ... ignored" when a CSV and PDF cover the same month (`jan_2026`).

## 4. Automated tests

| File | Tests | Covers |
| --- | --- | --- |
| `test_rag.py` | 44 | Ask WealthWise |
| `test_data_scenarios.py` | 19 | **New.** Score bands, component extremes, debt plan, subscriptions, warnings |
| `test_dashboard.py` | 15 | Report view |
| `test_detect.py` | 10 | Document type detection |
| `test_app.py`, `test_data_jan.py` | 8, 7 | App shell and chat, January set |
| `test_agents.py`, `test_categorise.py`, `test_plans.py`, `test_samples.py`, `test_payslip_pdf.py`, `test_bank_pdf.py`, `test_load_profile.py`, `test_acceptance.py` | 4 to 5 each | Parsers, categoriser, plans, end-to-end acceptance |
| the rest (CSV, loan, metrics, score, subscriptions, demo check) | 2 to 3 each | Unit checks |

The slowest test takes 1.4 s. No test is skipped.

## 5. Findings

### Bug
1. **Lender name casing in the loan PDF parser.** `BANK OF IRELAND PERSONAL LOAN` becomes `Bank OF Ireland Personal Loan` (seen in `average_mixed_may_2026`). The `title()` helper in `wealthwise/ingestion/loan_pdf.py` keeps every all-caps word of 3 letters or fewer as an acronym, so "OF" survives. The name is shown on the dashboard and in the payoff order. Low severity, easy fix (a small list of stop words such as "of").

### Weaknesses in the advice (the numbers are right, the text is not)
2. **Nonsense debt advice with no surplus.** For `worst_overspender_jun_2026`, the one case that most needs help, the debt card reads "Adding EUR 0.00/month makes you debt-free 0 months earlier and saves EUR 0.00 in interest", and the savings plan has no target date. When the surplus is negative, the app should say so and point at cutting spending, not present an empty plan.
3. **Only takeaways are ever flagged for cutting.** In the worst case, shopping (305), entertainment (240) and 3 subscriptions (75) are untouched. And "Review your takeaway spending" appears even for EUR 20 a month (`high_debt_burden_jul_2026`) and for EUR 45 for someone saving 62% of income.
4. **Wrong emergency-fund wording for the best case.** `best_saver_mar_2026` has 10 months of cover, yet the card is titled "Build a 3-month emergency fund".
5. **Subscriptions in a single month are invisible.** The detector needs 2 or more months, so the three subscriptions in the worst case (Netflix, Disney, gym) are not listed. This is by design (`wealthwise/analysis/subscriptions.py`) but a one-month upload gets no subscription view.

### Silent assumptions (no warning shown to the user)
6. **A CSV with no balance column gives a zero cushion.** In `messy_csv_only_nov_2026` the emergency-fund score is 0 and the cushion 0.00 months only because the file carries no balance, which costs up to 20 points. The user is not told.
7. **Unrecognised merchants are quietly "other".** In the same set, "Joe's Hardware", "ACME Dental" and "Mystery Transfer" make EUR 508.40, or 28% of spending, uncategorised, with no warning.
8. **Debt repayments count as spending.** In `high_debt_burden_jul_2026`, 2,200 of the 2,550 monthly spending is loan and card payments, so the discretionary share is 0.8% and that component scores full marks even though the person is overextended. The debt component already catches it (0 of 30), so the score is still correct, but "spending" is not what most people mean by the word.

## 6. Not covered, and how to cover it

- **LLM path.** Everything here ran with template text. With an `OPENROUTER_API_KEY`, check that explanations quote only numbers from the report (ADR-0001).
- **Ask WealthWise on the new sets.** Only the existing chat tests were run.
- **Browser walk-through.** Upload each folder in the app and compare the screen to the table in section 3.
- **Layouts beyond text lines.** The new PDFs reuse the January text-line layout. The table layout is covered only by `samples/`.
- **Large inputs.** The biggest new statement is 30 transactions over 3 months.

## 7. How to reproduce

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/generate_test_data.py     # rebuilds test_data/ scenario folders
pytest                                   # 158 passed
streamlit run app.py                     # upload a whole test_data/<folder>/
```
