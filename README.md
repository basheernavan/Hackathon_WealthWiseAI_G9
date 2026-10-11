# WealthWise

WealthWise is a hackathon pilot for understanding personal finances from a bank statement, payslip and loan statement. It calculates a Financial Health Score and presents spending, debt and savings information with evidence-based scenarios. It is not financial advice.

## What it does

- Reads supported PDF, CSV and XLSX financial documents and builds a financial profile.
- Calculates income, spending, surplus, category totals, recurring payments, debt and savings metrics in Python.
- Shows a financial overview, income-versus-spending and category charts, three recommendation themes, and supporting evidence.
- Answers supported questions about merchants, categories, income, debt, subscriptions and savings from the uploaded profile and report.
- Uses ChromaDB for relevant document retrieval and OpenRouter for open-ended conversational explanations when configured.
- Runs without an OpenRouter key: deterministic report questions and the dashboard remain available; open-ended suggestions are limited.

## Technology and analysis

The application uses Python, Streamlit, Pydantic, LangGraph, LangChain, ChromaDB, Altair, PyMuPDF and openpyxl.

The report's LangGraph contains three recommendation agents:

- **Spending** — identifies category evidence and an explicitly optional spending scenario.
- **Debt** — models an avalanche repayment plan from reported balances, rates and payments.
- **Savings** — estimates progress toward an emergency-fund target.

Python supplies the financial values. The optional LLM can rewrite recommendation wording, but it does not calculate those values. Monthly surplus and the optional spending-cut scenario are kept distinct; debt and savings are destinations that split an allocation rather than extra sources of money.

Ask WealthWise calculates exact merchant and category totals from transactions instead of relying on semantic search. It uses ChromaDB's in-memory collection for relevant supporting document rows and sends a structured report context, selected retrieved rows, recent conversation and current preferences to the configured OpenRouter chat model for open-ended questions. The runtime prompt instructs the model to keep answers grounded, respect preferences and distinguish historical figures from hypothetical scenarios. The chat history is bounded and associated with the current profile.

## Run locally

Python 3.11 or newer is recommended. From the repository root:

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install the pinned dependencies and create a local environment file:

```bash
pip install -r requirements.txt
cp .env.example .env          # macOS/Linux
# PowerShell: Copy-Item .env.example .env
```

Edit `.env` locally if you want OpenRouter-backed wording and open-ended chat:

```dotenv
OPENROUTER_API_KEY=           # optional; never commit a real key
WEALTHWISE_MODEL=anthropic/claude-haiku-5.5
```

`WEALTHWISE_MODEL` is optional; the configured default is `anthropic/claude-haiku-5.5`. The selected OpenRouter model must support the chat operations used by the application. Keep `.env`, uploads and real financial documents out of Git.

Start the app and run tests:

```bash
streamlit run app.py
pytest
```

## Tracing, evals and guardrails

Ask WealthWise has guardrails: prompt-injection attempts are refused without calling the model, and a model answer with a figure that is not in the report data is replaced with a "couldn't verify that" reply.

To trace runs in [LangSmith](https://smith.langchain.com), add a LangSmith API key to `.env` and set `LANGSMITH_TRACING=true`. Each question shows up as an "Ask WealthWise" run in the `wealthwise` project, including the ones a guardrail declined. The run's input is just the question, but the traced model call includes the report data, so tracing is for local use and eval runs only: do not add LangSmith keys to Streamlit Cloud Secrets.

The eval set in [wealthwise/evals.py](wealthwise/evals.py) lists questions on the sample documents, each with the expected outcome (answered or declined) and, where there is one, the figure from the answer key. `pytest` runs the cases that need no model. To run every case through the live model and record it as a LangSmith experiment (needs `OPENROUTER_API_KEY` and `LANGSMITH_API_KEY`):

```bash
python scripts/run_evals.py
```

## Hackathon demo

1. Start the app and choose **Use sample documents** to load fictional data, or upload your own supported documents.
2. Review the Financial Health Score, overview cards and charts.
3. Compare the Spending, Debt and Savings recommendations; use **View supporting evidence** to inspect the source records and assumptions.
4. Ask a specific question such as `How much did I spend on Deliveroo?`, then try a follow-up such as `And Tesco?` or `Which was higher?`.
5. To demonstrate open-ended coaching, configure OpenRouter locally and try a savings question followed by a preference or alternative. Without a key, use deterministic questions and note the open-ended limitation.

The files under [samples/](samples/) are fictional and intended for demos and tests. [test_data/](test_data/) contains additional fictional layouts.

## Limitations and privacy

- This is a hackathon pilot, not a production banking service or regulated financial adviser. Check all extracted figures against the source documents before acting.
- Averages describe the dates available in the uploaded data. Optional spending cuts and debt/savings projections depend on reported assumptions and are not guarantees.
- Recurring-payment detection does not establish whether a payment is necessary or safe to cancel. The app should not infer a user's priorities from a category label.
- Open-ended language generation requires an OpenRouter key, network access and a compatible model. Model responses can still be incomplete or wrong; verify factual claims against the dashboard and uploaded records.
- When OpenRouter is enabled, the question, bounded recent conversation, structured report data and relevant retrieved financial rows may be sent to the selected provider. Do not upload real financial records unless you understand and accept that processing.
- ChromaDB uses an ephemeral in-memory collection for the active profile; this is not a durable or multi-user data store. No production deployment or data-retention guarantees are claimed.

## Team review

Follow [docs/COLLABORATION.md](docs/COLLABORATION.md) for task ownership, branch, review and merge conventions. Read [CONTEXT.md](CONTEXT.md), [docs/specs/00-overview.md](docs/specs/00-overview.md) and the relevant [ADRs](docs/adr/) before changing domain behavior. In particular, review financial assumptions, OpenRouter data handling, and changes to shared dashboard or chat integration before merging. `wealthwise/contracts.py` is frozen under the team rules and was not changed for this work.

Earlier pitch and background material is in [documents/](documents/); the current code and specifications take precedence.
