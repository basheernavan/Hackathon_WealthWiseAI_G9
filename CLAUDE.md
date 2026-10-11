# WealthWise

Hackathon pilot: upload a bank statement, payslip and loan statement, and get a Financial Health Score plus spending, debt and savings advice. Deadline **2026-10-11 12:00**. Work is split into independent tasks (one GitHub issue each) that anyone can pick up or hand over.

Read first: [CONTEXT.md](CONTEXT.md) (glossary and rules), [docs/specs/00-overview.md](docs/specs/00-overview.md) (tasks, ground rules, milestones), then the spec section your issue links. Claiming, branching, handing over and merging: follow [docs/COLLABORATION.md](docs/COLLABORATION.md).

## Commands (Windows PowerShell)

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env            # then add OPENROUTER_API_KEY
streamlit run app.py
pytest
python scripts/generate_samples.py   # only if the generator changes
```

## Layout

- `wealthwise/contracts.py`: the shared data contract. Frozen; changes need a PR approved by two other developers.
- `wealthwise/ingestion/`: Stream A, files to `FinancialProfile`. One module per parser.
- `wealthwise/analysis/`: Stream B, `FinancialProfile` to `Report`. `build_report` is wired; one module per step.
- `app.py`, `wealthwise/dashboard.py`, `wealthwise/rag/`: Stream C, the Streamlit app, report view and Ask WealthWise.
- `wealthwise/llm.py`: the only place that creates the LLM client (OpenRouter).
- `tests/conftest.py`: fixtures from `samples/` so each task tests in isolation. `tests/test_acceptance.py` skips until a stream is complete.
- `samples/`: fictional documents and answer keys. Generated; never hand-edit.
- `test_data/`: hand-made fictional documents in other layouts (text-line PDFs, loan PDF, unsigned CSV), one folder per set. See its README.
- `docs/adr/`: decisions. Respect them, or flag a conflict explicitly.
- `documents/`: pitch and background from an earlier plan; the repo wins where they disagree.

## Rules

- Numbers come from code; the LLM only writes explanation text (ADR-0001). The app must work with no API key.
- Edit only the files your issue names, and keep the stub's signature. Shared files change via a small separate PR.
- Write the spec's "Done when" items as tests, test-first. Run `pytest` before every PR.
- Commit and push at least every 30 minutes, so the task can be handed over.
- Keep `.env`, `uploads/` and real financial documents out of git.
- Branch per issue: `<issue#>-<short-name>`, PR into `main` with `Closes #<issue#>`.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `basheernavan/Hackathon_WealthWiseAI_G9`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
