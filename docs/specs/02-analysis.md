# Stream B: Analysis + agents

**Entry point:** `wealthwise.analysis.build_report(profile: FinancialProfile) -> Report`
**Folder:** `wealthwise/analysis/`. **Tests:** `tests/test_analysis.py`. Load the input with `FinancialProfile.model_validate_json(Path("samples/expected_profile.json").read_text())`. Don't wait for Stream A.

Every formula below is mirrored in `scripts/generate_samples.py`, which produced `samples/expected.json`. If your answer differs, re-read this spec first. Rounding follows ADR-0004.

## 1. Categorise (keyword rules)
Use the first rule that matches. A positive amount is always `income`. Otherwise match whole-word, case-insensitive (`\bKEYWORD\b`) against the description, in this order:

| Category | Keywords |
| --- | --- |
| debt_repayment | LOAN REPAYMENT, CREDIT CARD PAYMENT |
| housing | RENT, MORTGAGE |
| groceries | TESCO, LIDL, ALDI, SUPERVALU, DUNNES |
| takeaway | DELIVEROO, JUST EAT, UBER EATS |
| transport | LEAP CARD, CIRCLE K, IRISH RAIL, UBER |
| utilities | ELECTRIC IRELAND, BORD GAIS, EIR, THREE MOBILE, VODAFONE |
| subscriptions | NETFLIX, SPOTIFY, DISNEY, FLYEFIT, GYM |
| shopping | AMAZON, ZARA, PENNEYS, IKEA |
| entertainment | CINEWORLD, TICKETMASTER, PUB, BRAZEN HEAD |

No match means `other`. Check: the results equal `expected.json["transaction_categories"]`.

## 2. Metrics
- `months_covered` = number of distinct (year, month) values in the transactions.
- `monthly_income` = sum of income amounts / months.
- `monthly_spending` = −(sum of negative amounts) / months.
- `spending_by_category` = the same per category, for categories with at least one outflow.
- `monthly_surplus` = income − spending.
- `savings_rate` = surplus / income.
- `debt_to_income` = Σ `debt.monthly_payment` / income.
- `total_debt` = Σ `debt.balance`.
- `current_balance` = balance of the last transaction.
- `emergency_fund_months` = current_balance / spending.
- `discretionary_share` = Σ discretionary categories / spending.
- Guard against division by zero by returning 0.

## 3. Health score
`clamp(x) = min(1, max(0, x))`

| Component | Points |
| --- | --- |
| savings_rate | 30 × clamp(savings_rate / 0.20) |
| debt_to_income | 30 × clamp((0.50 − dti) / 0.40) |
| emergency_fund | 20 × clamp(months / 3) |
| discretionary_share | 20 × clamp((0.50 − share) / 0.30) |

`score = floor(sum of unrounded points + 0.5)`. Band: ≥ 75 good, ≥ 50 fair, otherwise needs attention. Component `value` is rounded to 4 dp and `points` to 2 dp. The sample gives **67, fair**.

## 4. Subscriptions
Take subscriptions-category transactions and group them by exact description. Keep groups seen in 2 or more distinct months. `monthly_amount` = mean outflow. Sort by amount, largest first.

## 5. Plans
- `identified_cuts` = 0.5 × monthly takeaway spending.
- `freed` = max(surplus, 0) + identified_cuts.
- With debts: `extra_monthly_payment` = round(freed / 2, 2), and the savings `monthly_amount` = round(freed − extra, 2). With no debts, savings gets everything and `debt_plan = None`.
- **Avalanche simulation** (`extra` = 0 for "current", then `extra_monthly_payment`):
  - Avalanche order: APR descending, then balance ascending.
  - Budget = Σ monthly_payment + extra.
  - Each month: add interest `balance × APR/100/12` to every debt. Pay each debt `min(monthly_payment, balance)`. Then pour the rest of the budget into debts in avalanche order.
  - Stop when every balance ≤ 0.005. Cap at 600 months.
  - Record months and total interest. `interest_saved` = current interest − extra interest. Don't round inside the loop.
- **Savings:** `target_amount` = round(3 × monthly_spending, 2). `months_to_target` = ceil(max(target − current_balance, 0) / monthly_amount), or `None` if monthly_amount is 0.

## 6. Agents (LangGraph)
Use `StateGraph`: START → `compute` → (`spending_agent`, `debt_agent` and `savings_agent` in parallel) → `compose` → END. The `recommendations` state key uses an `Annotated[list, operator.add]` reducer.

- `compute` runs steps 1–5.
- Each agent builds one `Recommendation`. **Code** fills `agent`, `monthly_impact` and `evidence`; only `title` and `detail` come from the LLM.
- The LLM call: `get_chat_model()` from `wealthwise/llm.py`, then `.with_structured_output(...)` on a small `{title, detail}` model. The prompt carries the computed figures only. Ask for ≤ 12-word titles and ≤ 2 sentences that must quote the given figures.
- If `get_chat_model()` returns `None` or the call raises, use template text like `samples/mock_report.json` and set `llm_used = False`.

| Agent | Evidence | monthly_impact |
| --- | --- | --- |
| spending | Top 5 takeaway outflows by size | identified_cuts |
| debt | debt_repayment transactions | extra_monthly_payment |
| savings | None | savings monthly_amount |

## Acceptance criteria
- [ ] Every number in `build_report(sample profile)` matches `samples/expected.json` (abs 0.01).
- [ ] With no `OPENROUTER_API_KEY`, `build_report` succeeds with `llm_used == False`.
- [ ] A profile with no debts gives `debt_plan is None`, and savings gets all freed money.
- [ ] A profile with no transactions doesn't crash: all metrics are 0, and the score uses the same formulas.
- [ ] Unit tests for the categoriser, score and simulation are written test-first (`/mattpocock-skills:tdd`).
