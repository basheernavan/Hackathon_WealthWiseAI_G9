# Stream C: Dashboard + Ask WealthWise

**Files:** `app.py`, `wealthwise/rag/`. **Tests:** `tests/test_rag.py`. Load the mock with `Report.model_validate_json(Path("samples/mock_report.json").read_text())`. Don't wait for Streams A or B.

## Dashboard (Streamlit)
1. **Header.** "WealthWise" plus the caption "Not financial advice."
2. **Upload.** `st.file_uploader(..., type=["pdf","csv","xlsx"], accept_multiple_files=True)`. Wrap each file as `UploadedDocument(filename=f.name, content=f.getvalue())`. Add an "Analyse" button and a "Use sample documents" button that loads the three files from `samples/` for the demo.
3. **Pipeline.** `load_profile` then `build_report`, run inside `st.spinner`. Store both in `st.session_state`. If either raises `NotImplementedError`, fall back to `mock_report.json` and show a small "demo data" badge. Any other error shows `st.error` with the message, not a traceback.
4. **Documents read.** For each source: filename, type and any warnings (`st.warning`).
5. **Health score.** A large `st.metric` with the score and band, plus the 4 components as progress bars (points / max_points).
6. **Key metrics row.** Monthly income, spending, surplus, total debt and emergency fund months.
7. **Recommendations.** Three cards (spending, debt, savings): title, detail and `monthly_impact` as "€X/month". An expander lists the evidence transactions as a table.
8. **Spending by category.** A bar chart of `spending_by_category`, plus a subscriptions table.
9. **Debt plan.** Payoff order, "debt-free in N months (M months earlier)" and interest saved.
10. **Ask WealthWise.** A text input that calls `answer_question`. Show the answer, or "Add an OpenRouter key to enable questions" when there's no key.

Format money as `€1,234.56`. Format fractions as percentages with 1 dp.

## Ask WealthWise: `answer_question(profile, report, question) -> str`
- Use a ChromaDB `EphemeralClient` with the default embedding function. Build the collection once per profile and cache it in `st.session_state` or a module dict keyed by `id(profile)`.
- Make one document per transaction: `"2026-07-03 | DELIVEROO | -23.50 EUR | takeaway"`. Until Stream B merges, leave the category off; afterwards, import B's categoriser. Also one per payslip line and one per debt.
- Query the top 15. Send those rows plus the key `Metrics` as context, and tell the LLM to answer only from the context, quote figures, and reply "I can't tell from your documents" otherwise.
- No key gives the message above. Never raise into the UI.

## Acceptance criteria
- [ ] Before A and B merge, the whole dashboard renders from `mock_report.json`.
- [ ] After the merge, "Use sample documents" shows score 67 and the figures in `docs/specs/00-overview.md` → Demo script.
- [ ] A bad file shows a warning and the rest still renders.
- [ ] Ask WealthWise answers "How much do I spend on takeaway?" with about €215/month.
- [ ] Usable at 1280 px width. No horizontal scroll on the main column.
