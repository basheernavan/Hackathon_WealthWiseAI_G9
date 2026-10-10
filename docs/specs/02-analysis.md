# Stream B: Analysis + agents

**Entry point:** `wealthwise.analysis.build_report(profile: FinancialProfile) -> Report`, already wired in [`wealthwise/analysis/__init__.py`](../../wealthwise/analysis/__init__.py): categorise → metrics → plans → agents, plus score and subscriptions. Each step is one task below.

Each task is independent: its stub file already exists with the exact signature, and it tests against the answer key, never against another task's code. Fixtures in [`tests/conftest.py`](../../tests/conftest.py): `expected` (`samples/expected.json`), `sample_profile`, `categorised_profile` (categories already filled from the answer key), `expected_metrics`, and `assert_matches(actual, expected)` for deep comparison with 0.01 tolerance.

Every formula below is mirrored in `scripts/generate_samples.py`, which produced `samples/expected.json`. If your answer differs, re-read this spec, then compare with the generator. Rounding follows ADR-0004: full precision inside, round only when building the output model.

| Task | File | Function | Test file | Test input |
| --- | --- | --- | --- | --- |
| B1 | `wealthwise/analysis/categorise.py` | `categorise` | `tests/test_categorise.py` | `sample_profile` |
| B2 | `wealthwise/analysis/metrics.py` | `compute_metrics` | `tests/test_metrics.py` | `categorised_profile` |
| B3 | `wealthwise/analysis/score.py` | `score_health` | `tests/test_score.py` | `expected_metrics` |
| B4 | `wealthwise/analysis/subscriptions.py` | `find_subscriptions` | `tests/test_subscriptions.py` | `categorised_profile` |
| B5 | `wealthwise/analysis/plans.py` | `build_plans` | `tests/test_plans.py` | `expected_metrics`, `sample_profile.debts` |
| B6 | `wealthwise/analysis/agents.py` | `run_agents` | `tests/test_agents.py` | `categorised_profile`, `expected` |

Write the unit tests test-first (`/mattpocock-skills:tdd`).

## B1. Categorise

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

No match means `other`. Return copies (`model_copy(update=...)`); don't mutate the input.

**Done when:** the categories of `categorise(sample_profile.transactions)` equal `expected["transaction_categories"]`; "UBER EATS" is takeaway and "UBER" is transport.

## B2. Metrics

- `months_covered` = number of distinct (year, month) values in the transactions.
- `monthly_income` = sum of income amounts / months.
- `monthly_spending` = −(sum of negative amounts) / months.
- `spending_by_category` = the same per category, for categories with at least one outflow.
- `monthly_surplus` = income − spending.
- `savings_rate` = surplus / income.
- `debt_to_income` = Σ `debt.monthly_payment` / income.
- `total_debt` = Σ `debt.balance`.
- `current_balance` = balance of the last transaction (0 if none).
- `emergency_fund_months` = current_balance / spending.
- `discretionary_share` = Σ discretionary categories (`DISCRETIONARY_CATEGORIES`) / spending.
- Guard against division by zero by returning 0.

**Done when:** `compute_metrics(categorised_profile)` matches `expected["metrics"]`; an empty profile gives all zeros without crashing.

## B3. Health score

`clamp(x) = min(1, max(0, x))`

| Component | Points |
| --- | --- |
| savings_rate | 30 × clamp(savings_rate / 0.20) |
| debt_to_income | 30 × clamp((0.50 − dti) / 0.40) |
| emergency_fund | 20 × clamp(months / 3) |
| discretionary_share | 20 × clamp((0.50 − share) / 0.30) |

`score = floor(sum of unrounded points + 0.5)`. Band: ≥ 75 good, ≥ 50 fair, otherwise needs attention. Component `value` is rounded to 4 dp and `points` to 2 dp. Components appear in the order above.

**Done when:** `score_health(expected_metrics)` matches `expected["health_score"]` (**67, fair**); all-zero metrics give a valid score without crashing.

## B4. Subscriptions

Take subscriptions-category transactions and group them by exact description. Keep groups seen in 2 or more distinct months. `monthly_amount` = mean outflow (positive). Sort by amount, largest first.

**Done when:** `find_subscriptions(categorised_profile.transactions)` matches `expected["subscriptions"]`.

## B5. Plans

- `identified_cuts` = 0.5 × monthly takeaway spending (`metrics.spending_by_category`, 0 if absent).
- `freed` = max(surplus, 0) + identified_cuts.
- With debts: `extra_monthly_payment` = round(freed / 2, 2), and the savings `monthly_amount` = round(freed − extra, 2). With no debts, savings gets everything and the debt plan is `None`.
- **Avalanche simulation** (run once with `extra` = 0 for "current", once with `extra_monthly_payment`):
  - Avalanche order: APR descending, then balance ascending. This is also `payoff_order` (debt names).
  - Budget = Σ monthly_payment + extra.
  - Each month: add interest `balance × APR/100/12` to every debt. Pay each debt `min(monthly_payment, balance)`. Then pour the rest of the budget into debts in avalanche order.
  - Stop when every balance ≤ 0.005. Cap at 600 months.
  - Record months and total interest. `months_saved` = current − extra months. `interest_saved` = current interest − extra interest. Don't round inside the loop.
- **Savings:** `target_amount` = round(3 × monthly_spending, 2). `months_to_target` = ceil(max(target − current_balance, 0) / monthly_amount), or `None` if monthly_amount is 0.

**Done when:** `build_plans(expected_metrics, sample_profile.debts)` matches `expected["identified_cuts"]`, `expected["debt_plan"]` and `expected["savings_plan"]` (cuts €107.56, 8 months earlier, €513.39 interest saved); `debts=[]` gives `None` and savings gets all the freed money.

## B6. Agents (LangGraph)

`run_agents` gets the already computed figures and only turns them into words. Build a `StateGraph`: START → (`spending_agent`, `debt_agent`, `savings_agent` in parallel) → `compose` → END. The `recommendations` state key uses an `Annotated[list, operator.add]` reducer; `compose` sorts them spending, debt, savings.

- Each agent builds one `Recommendation`. **Code** fills `agent`, `monthly_impact` and `evidence`; only `title` and `detail` come from the LLM (ADR-0001).
- The LLM call: `get_chat_model()` from `wealthwise/llm.py`, then `.with_structured_output(...)` on a small `{title, detail}` model. The prompt carries the computed figures only. Ask for titles of 12 words or fewer and at most 2 sentences that quote the given figures.
- If `get_chat_model()` returns `None` or the call raises, use template text like `samples/mock_report.json`, and `llm_used` is `False`. `llm_used` is `True` only if all three LLM calls succeeded.

| Agent | Evidence | monthly_impact |
| --- | --- | --- |
| spending | Top 5 takeaway outflows by size | identified_cuts |
| debt | debt_repayment transactions | debt_plan.extra_monthly_payment (None if no plan) |
| savings | None | savings_plan.monthly_amount |

**Done when** (with no `OPENROUTER_API_KEY`: in tests, `monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)`):
- [ ] With the figures from `expected`, it returns 3 recommendations in order, `llm_used == False`, and the monthly impacts 107.56, 160.98, 160.98.
- [ ] Spending evidence is the 5 largest takeaway outflows.
- [ ] `debt_plan=None` still gives 3 recommendations without crashing.

## Stream acceptance (runs automatically)

[`tests/test_acceptance.py`](../../tests/test_acceptance.py) skips until B1-B6 are all merged, then checks that every number in `build_report(sample profile)` matches `samples/expected.json`.
