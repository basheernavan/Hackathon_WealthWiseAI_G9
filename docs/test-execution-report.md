# WealthWise test execution report

**Run:** 2026-10-11 · `pytest -q --junitxml` on Python 3.12.10, Windows 11 · offline (no API key) · repo at 4743b51 plus the uncommitted test work below
**Companion:** findings and analysis are in [test-report.md](test-report.md). This file is the execution record.

## 1. Result

| | Count |
| --- | --- |
| **Total executed** | **414** |
| Passed | **408** |
| Failed | **0** |
| Errors | **0** |
| Expected failures (XFAIL, known defects) | **6** |
| Skipped | 0 |
| Duration | 26.5 s |

**New in this round: 256 tests in [tests/test_combinations.py](../tests/test_combinations.py), 250 passed and 6 XFAIL.** The other 158 are the earlier suite (139 original, 19 scenario tests) and all still pass.

**Overall status: PASS.** The 6 XFAIL results are real defects on purpose, described in section 4. They are strict, so each one turns into a red XPASS failure the moment someone fixes it, which is the cue to remove its marker.

## 2. New tests by group (256)

| Group | What varies | Cases | Passed | Failed | XFAIL |
| --- | --- | --- | --- | --- | --- |
| A. Report invariants | 12 test_data folders x 12 checks | 144 | 144 | 0 | 0 |
| B. Score table | 20 hand-worked metric combinations incl. band edges 49/50 and 74/75, clamping and rounding | 20 | 20 | 0 | 0 |
| C. Categoriser | 43 descriptions (every category and keyword, case, near-miss words) + 5 money-in cases | 48 | 48 | 0 | 0 |
| D. Parsers and loader | 8 CSV cases (signed, unsigned, BOM, 4 bad rows, empty), 15 file-type detections, 4 mixed/duplicate/unsupported uploads | 27 | 27 | 0 | 0 |
| E. Plans and metrics | payoff months, extra payment (4 sizes), interest, avalanche order, empty, income-only and zero-surplus profiles, takeaway cut | 11 | 11 | 0 | 0 |
| F. Known defects | 6 reproduced defects | 6 | 0 | 0 | 6 |
| **Total** | | **256** | **250** | **0** | **6** |

### Group A checks (each run on all 12 folders)

| Check | Result |
| --- | --- |
| Score 0 to 100 and band matches the score | 12/12 pass |
| Four named components, max points sum to 100, points within range | 12/12 pass |
| Score equals the rounded sum of component points | 12/12 pass |
| Surplus = income - spending | 12/12 pass |
| Category spending adds up to total spending | 12/12 pass |
| Every transaction gets a category | 12/12 pass |
| Report survives a JSON round trip | 12/12 pass |
| Spending, debt and savings agents each answer | 12/12 pass |
| Savings target = 3 x monthly spending | 12/12 pass |
| `months_to_target` is None only with no savings | 12/12 pass |
| Debt plan exists exactly when debts exist, extra payment never slows payoff, avalanche order first | 12/12 pass |
| Offline run reports `llm_used = False` | 12/12 pass |

The 12 folders are the 11 new scenario sets plus `jan_2026`.

## 3. Status of the full suite by file

| File | Tests | Passed | XFAIL | Time (s) |
| --- | --- | --- | --- | --- |
| test_combinations.py (new) | 256 | 250 | 6 | 1.8 |
| test_rag.py | 44 | 44 | 0 | 0.1 |
| test_data_scenarios.py (new) | 19 | 19 | 0 | 0.9 |
| test_dashboard.py | 15 | 15 | 0 | 4.5 |
| test_detect.py | 10 | 10 | 0 | 0.0 |
| test_app.py | 8 | 8 | 0 | 8.5 |
| test_data_jan.py | 7 | 7 | 0 | 0.1 |
| test_agents.py, test_categorise.py, test_plans.py, test_samples.py | 5 each | 20 | 0 | 0.1 |
| test_bank_pdf.py, test_acceptance.py, test_payslip_pdf.py | 4 each | 12 | 0 | 2.5 |
| test_load_profile.py, test_loan_xlsx.py, test_score.py, test_subscriptions.py, test_demo_check.py, test_bank_csv.py | 3 each | 18 | 0 | 2.2 |
| test_loan_pdf.py, test_metrics.py | 2 each | 4 | 0 | 0.0 |
| **Total** | **414** | **408** | **6** | **26.5** |

## 4. The six XFAIL results (defects, not test failures)

| Test | Defect | Severity |
| --- | --- | --- |
| `test_lender_name_casing_in_loan_pdf` | BUG-1: "BANK OF IRELAND" is shown as "Bank OF Ireland" | Low |
| `test_debt_advice_does_not_promise_nothing` | WEAK-2: with no surplus the debt card says "Adding EUR 0.00/month ..." | Medium |
| `test_worst_case_advice_mentions_more_than_takeaways` | WEAK-3: only takeaways are ever flagged for cutting | Medium |
| `test_best_saver_is_not_told_to_build_an_emergency_fund` | WEAK-4: 10 months of cover, still told to "Build a 3-month emergency fund" | Low |
| `test_csv_without_balance_warns_about_the_emergency_fund` | WEAK-6: a CSV with no balance silently scores 0 on the cushion (up to 20 points) | Medium |
| `test_large_uncategorised_spending_is_reported` | WEAK-7: 28% of spending falls in "other" with no warning | Medium |

WEAK-5 (subscriptions need 2 or more months) and WEAK-8 (debt repayments count as spending) are design choices rather than defects, so they have no test.

## 5. Coverage of the product

| Pipeline step | Covered by | Status |
| --- | --- | --- |
| Detect file type | 4 junk-file cases, 11 folders, plus `test_detect.py` | Pass |
| Bank CSV / PDF parsing | 8 CSV cases here, folders A, `test_bank_*` | Pass |
| Payslip and loan parsing | every folder (payslips in 9, loan PDF or XLSX in 5) | Pass |
| Load and combine uploads | mixed, duplicate and unsupported uploads | Pass |
| Categorise | 48 cases | Pass |
| Metrics | 12 folders, empty and income-only profiles | Pass |
| Health score | 20 hand-worked cases + 12 folders | Pass |
| Subscriptions | `subscription_creep_q1_2026` (5 found) and 11 folders (none) | Pass |
| Debt and savings plans | 11 cases + 12 folders | Pass |
| Recommendations text | structure checked; wording has 4 XFAIL defects | Pass with defects |
| LLM text, Ask WealthWise on new data, browser UI | not run in this round | Not covered |

## 6. Reproduce

```powershell
.\.venv\Scripts\Activate.ps1
pytest                                           # 408 passed, 6 xfailed
pytest tests/test_combinations.py -v             # the 256 new cases, one line each
pytest -q --junitxml=test-results.xml            # machine-readable record
pytest tests/test_combinations.py -rx            # list the six XFAIL reasons
```
