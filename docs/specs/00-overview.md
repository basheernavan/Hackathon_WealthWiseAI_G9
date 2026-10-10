# WealthWise: build overview

**Deadline:** Sunday 2026-10-11, 12:00 noon. **Team:** anyone can pick up any task; people may hand over mid-task. How to work together: [docs/COLLABORATION.md](../COLLABORATION.md).

## Team

All three developers are collaborators on the GitHub repo and can push branches and merge PRs.

| GitHub | Role |
| --- | --- |
| [basheernavan](https://github.com/basheernavan) | Repo owner, D1 pitch deck |
| [dilipmath](https://github.com/dilipmath) | Developer |
| [kmrsdrm-arch](https://github.com/kmrsdrm-arch) | Developer |

## Pipeline

```
uploads (PDF/CSV/XLSX)
  -> Stream A  wealthwise.ingestion.load_profile(list[UploadedDocument]) -> FinancialProfile
  -> Stream B  wealthwise.analysis.build_report(FinancialProfile)        -> Report
  -> Stream C  app.py renders Report;  wealthwise.rag.answer_question(...) -> str
```

The interfaces between streams are those functions and the models in [`wealthwise/contracts.py`](../../wealthwise/contracts.py).

## Tasks

Every task has its own file (a stub with the exact signature is already on `main`), its own test file, and test data in `samples/`. **No task waits for another.** The GitHub issue for each task is linked from the [issue list](https://github.com/basheernavan/Hackathon_WealthWiseAI_G9/issues).

| Stream | Spec | Tasks |
| --- | --- | --- |
| A: Ingestion | [01-ingestion.md](01-ingestion.md) | ~~A1 detect type #1~~ ✅ · ~~A2 bank CSV #2~~ ✅ · A3 bank PDF #3 · A4 payslip PDF #4 · ~~A5 loan XLSX #5~~ ✅ · ~~A6 `load_profile` #6~~ ✅ |
| B: Analysis + agents | [02-analysis.md](02-analysis.md) | ~~B1 categorise #7~~ ✅ · ~~B2 metrics #8~~ ✅ · ~~B3 score #9~~ ✅ · ~~B4 subscriptions #10~~ ✅ · ~~B5 plans #11~~ ✅ · B6 agents #12 |
| C: Dashboard + Ask | [03-dashboard-and-rag.md](03-dashboard-and-rag.md) | ~~C1 app shell #13~~ ✅ · C2 report view #14 · C3 Ask WealthWise #15 |
| D: Demo + pitch | this file | ~~D1 align pitch deck with the ADRs (Basheer) #16~~ ✅ · D2 demo rehearsal #17 |

When the last task of a stream is merged, [`tests/test_acceptance.py`](../../tests/test_acceptance.py) stops skipping and checks that stream end to end.

## Ground rules

1. **The contract is frozen.** To change `contracts.py`, open a PR and get a 👍 from two other active developers before merging. Never change it silently inside a task PR.
2. **Stay in your task's files**: the file and test file named in your task. This is what keeps merges conflict-free.
3. **Shared files** (`contracts.py`, `llm.py`, `requirements.txt`, `samples/`, `tests/conftest.py`, the specs) change only via a small separate PR.
4. **Never commit real financial documents or `.env`.**
5. **Regenerate samples** only with `python scripts/generate_samples.py`, and only when the generator changed. It rewrites the PDF/XLSX files even when their content is the same, so discard those with `git checkout -- samples/` unless you meant to change them. Never hand-edit the JSON files.

## Milestones

Merge each task as soon as it's done. These times say what should be on `main` by then.

| When | On `main` |
| --- | --- |
| 20:00 Sat | A2, A5, B1, B2, B3, C1 |
| 23:59 Sat | Everything else in A, B and C, at least with template text |
| 08:00 Sun | Full demo script passes on `main`. **Bug fixes only from here.** |
| 10:30 Sun | **Code freeze.** Rehearse the demo twice (D2). |
| 12:00 Sun | Submit. |

## Demo script (acceptance test for the whole app)

1. `streamlit run app.py`, then upload the bank statement PDF, the payslip PDF and the loan XLSX from `samples/`.
2. See "3 documents read" with no errors.
3. See Health Score **67 (fair)** with its 4 components.
4. See three recommendations (spending, debt, savings) with the figures from `expected.json`: cuts €107.56/month, debt-free 8 months earlier, saves €513.39 interest.
5. Ask "How much do I spend on takeaway?" and get an answer citing about €215/month.
6. Repeat with the CSV bank statement instead of the PDF and get identical numbers.
