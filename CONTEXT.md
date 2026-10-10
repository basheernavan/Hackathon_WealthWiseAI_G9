# WealthWise: domain context

WealthWise turns a person's own financial documents (bank statement, payslip, loan statement) into a Financial Health Score and three kinds of advice: spending, debt and savings. It's a hackathon pilot: one user, one session, no accounts. Advice is guidance, not regulated financial advice.

## Glossary

Use these terms exactly in code, issues and UI. The code names live in `wealthwise/contracts.py`.

| Term | Meaning | Avoid |
| --- | --- | --- |
| **Document** | One uploaded file, of type `bank_statement`, `payslip` or `loan_statement`. | "file" in domain code |
| **Transaction** | One bank-statement line. `amount` is signed: negative means money out, positive means money in. | "expense"/"payment" as type names |
| **Category** | One of the fixed `Category` values. Analysis assigns it with keyword rules; ingestion leaves it `None`. | "tag", "type" |
| **Discretionary** | The takeaway, shopping, entertainment and subscriptions categories. | "wants", "non-essential" |
| **Subscription** | A subscriptions-category outflow with the same description in 2 or more distinct months. | "recurring payment" |
| **Debt** | A loan or credit card from the loan statement. `annual_interest_rate` is APR in percent (8.9 = 8.9%). | "liability", "loan" for both kinds |
| **FinancialProfile** | Everything ingestion extracted: transactions, payslips, debts, sources. | "user data" |
| **Metrics** | Monthly averages and ratios computed by Pandas from the profile. | "stats" |
| **Financial Health Score** | 0–100, from 4 fixed components ([spec](docs/specs/02-analysis.md#health-score)). Band: good ≥ 75, fair ≥ 50, otherwise needs attention. | "credit score" |
| **Identified cuts** | EUR/month the spending agent finds to free up (50% of takeaway). | "savings" (that's a different concept) |
| **Freed money** | Positive monthly surplus plus identified cuts, split between the debt plan and the savings plan. | |
| **Avalanche** | Debt strategy: extra money goes to the highest-APR debt first. | |
| **Agent** | One LangGraph node (`spending`, `debt` or `savings`) that turns computed figures into a recommendation. | "bot" |
| **Recommendation** | An agent's output: a title, a detail, its monthly impact and evidence transactions. | "insight", "tip" |
| **Report** | The full analysis result rendered by the dashboard. | |

## Rules that hold everywhere

- **Numbers come from code, words come from the LLM.** The LLM never calculates or invents a figure ([ADR-0001](docs/adr/0001-deterministic-numbers-llm-explains.md)).
- **The app works without an LLM key**, falling back to template text.
- **Money is EUR as a float**, rounded to 2 dp only at output ([ADR-0004](docs/adr/0004-money-as-rounded-float-eur.md)).
- **No real financial documents in git.** Use `samples/` (fictional) only.
