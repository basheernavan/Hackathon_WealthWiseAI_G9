# Stream C: Dashboard + Ask WealthWise

Each task is independent: its stub already exists, and it builds against `samples/mock_report.json` (load it with `Report.model_validate_json(Path("samples/mock_report.json").read_text(encoding="utf-8"))`) and `samples/expected_profile.json`, never against unfinished A or B code.

| Task | File | What | Test file |
| --- | --- | --- | --- |
| C1 | `app.py` | Page shell: upload, pipeline, fallback, documents read, Ask box | manual check (below) |
| C2 | `wealthwise/dashboard.py` | `render_report(report)`, `format_eur`, `format_pct` | `tests/test_dashboard.py` (formatters) |
| C3 | `wealthwise/rag/__init__.py` | `answer_question(profile, report, question)` | `tests/test_rag.py` |

Check the UI by running `streamlit run app.py` and clicking through. It must be usable at 1280 px width with no horizontal scroll on the main column.

## C1. App shell (`app.py`)

1. **Header.** "WealthWise" plus the caption "Not financial advice."
2. **Upload.** `st.file_uploader(..., type=["pdf","csv","xlsx"], accept_multiple_files=True)`. Wrap each file as `UploadedDocument(filename=f.name, content=f.getvalue())`. Add an "Analyse" button and a "Use sample documents" button that loads the bank statement PDF, payslip PDF and loan XLSX from `samples/`.
3. **Pipeline.** `load_profile` then `build_report`, run inside `st.spinner`. Store both in `st.session_state`. If either raises `NotImplementedError`, use `samples/expected_profile.json` and `samples/mock_report.json` instead and show a small "demo data" badge. Any other error shows `st.error` with the message, not a traceback.
4. **Documents read.** For each source: filename, type and any warnings (`st.warning`).
5. **Report.** Call `wealthwise.dashboard.render_report(report)`. Don't draw the report sections in `app.py`; that's C2.
6. **Ask WealthWise.** A text input that calls `answer_question` and shows the answer. If it raises `NotImplementedError`, show "Ask WealthWise is coming soon".

**Done when:** with today's stubs, "Use sample documents" shows the demo-data badge and C2's placeholder; a `.txt` upload shows a warning or error message, not a traceback.

## C2. Report view (`wealthwise/dashboard.py`)

`render_report(report)` draws, top to bottom:

1. **Health score.** A large `st.metric` with the score and band, plus the 4 components as progress bars (points / max_points).
2. **Key metrics row.** Monthly income, spending, surplus, total debt and emergency fund months.
3. **Recommendations.** Three cards (spending, debt, savings): title, detail and `monthly_impact` as "€X/month". An expander lists the evidence transactions as a table.
4. **Spending by category.** A bar chart of `spending_by_category`, plus a subscriptions table.
5. **Debt plan** (skip if `None`). Payoff order, "debt-free in N months (M months earlier)" and interest saved.

Format money with `format_eur` (`€1,234.56`) and fractions with `format_pct` (1 dp). Develop it without the rest of the app: make a scratch file that calls `render_report` on the mock report and run it with `streamlit run`. Don't commit the scratch file.

**Done when:** `tests/test_dashboard.py` covers the formatters (including negatives and 0); the mock report renders all 5 sections in the app.

## C3. Ask WealthWise (`answer_question`)

- If `get_chat_model()` returns `None`, return "Add an OpenRouter key to enable questions" before touching Chroma.
- Use a ChromaDB `EphemeralClient` with the default embedding function. Build the collection once per profile and cache it in a module dict keyed by `id(profile)`.
- Make one document per transaction: `"2026-07-03 | DELIVEROO | -23.50 EUR | takeaway"`. Get categories by calling `wealthwise.analysis.categorise.categorise`; if it raises `NotImplementedError`, leave the category off. Also one document per payslip line and one per debt.
- Query the top 15. Send those rows plus the key `Metrics` from the report as context. Tell the LLM to answer only from the context, quote figures, and reply "I can't tell from your documents" otherwise.
- Never raise into the UI: on any error return a short apology message.

Chroma downloads an embedding model of about 80 MB the first time it runs. Run it once before the demo.

**Done when:**
- [ ] With no key, it returns the "Add an OpenRouter key" message (test with `monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)`).
- [ ] The row-building function turns the sample profile into 87 transaction rows plus payslip and debt rows (unit-tested, no LLM).
- [ ] With a key, "How much do I spend on takeaway?" on the sample data answers with about €215/month (manual check).
