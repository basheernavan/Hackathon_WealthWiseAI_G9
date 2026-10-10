# WealthWise: build overview

**Deadline:** Sunday 2026-10-11, 12:00 noon. **Developers:** Sundar, Dilip, Lea, one stream each.

## Pipeline

```
uploads (PDF/CSV/XLSX)
  -> Stream A  wealthwise.ingestion.load_profile(list[UploadedDocument]) -> FinancialProfile
  -> Stream B  wealthwise.analysis.build_report(FinancialProfile)        -> Report
  -> Stream C  app.py renders Report;  wealthwise.rag.answer_question(...) -> str
```

The only interfaces between streams are those two functions and the models in [`wealthwise/contracts.py`](../../wealthwise/contracts.py). Each stream can start now without waiting for the others:

| Stream | Spec | Builds against | Done when |
| --- | --- | --- | --- |
| A: Ingestion | [01-ingestion.md](01-ingestion.md) | `samples/*.pdf/.csv/.xlsx` | Output equals `samples/expected_profile.json` |
| B: Analysis + agents | [02-analysis.md](02-analysis.md) | `samples/expected_profile.json` | Output matches `samples/expected.json` |
| C: Dashboard + Ask | [03-dashboard-and-rag.md](03-dashboard-and-rag.md) | `samples/mock_report.json` | Demo script runs end to end |

## Ground rules

1. **The contract is frozen.** To change `contracts.py`, open a PR and get a 👍 from both other developers before merging. Never change it silently on your own branch.
2. **Stay in your folder.** A: `wealthwise/ingestion/`. B: `wealthwise/analysis/`. C: `app.py`, `wealthwise/rag/`. Tests go in `tests/test_<stream>.py`. This avoids merge conflicts.
3. **Shared files** (`contracts.py`, `llm.py`, `requirements.txt`, `samples/`) change only via a small separate PR.
4. **Never commit real financial documents or `.env`.**
5. **Regenerate samples** only with `python scripts/generate_samples.py`. Never hand-edit the JSON files.

## Merge checkpoints

Merging only at the end is the biggest risk. Merge your branch into `main` (PR with `pytest` green) at each checkpoint, even if your stream is unfinished. The stubs keep `main` runnable.

| When (Sat/Sun) | Goal |
| --- | --- |
| 20:00 Sat | A: CSV + XLSX parsing. B: metrics + score. C: dashboard on mock report. |
| 23:59 Sat | A: both PDFs. B: debt/savings plans + LangGraph agents with fallback text. C: real pipeline wired in behind a try/except. |
| 08:00 Sun | Full flow on the sample files; Ask WealthWise. Bug-fix only from here. |
| 10:30 Sun | Code freeze. Rehearse the demo twice. |
| 12:00 Sun | Submit. |

## Demo script (acceptance test for the whole app)

1. `streamlit run app.py`, then upload the bank statement PDF, the payslip PDF and the loan XLSX from `samples/`.
2. See "3 documents read" with no errors.
3. See Health Score **67 (fair)** with its 4 components.
4. See three recommendations (spending, debt, savings) with the figures from `expected.json`: cuts €107.56/month, debt-free 8 months earlier, saves €513.39 interest.
5. Ask "How much do I spend on takeaway?" and get an answer citing about €215/month.
6. Repeat with the CSV bank statement instead of the PDF and get identical numbers.
