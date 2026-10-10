# WealthWise

Hackathon pilot: upload a bank statement, payslip and loan statement, and get a Financial Health Score plus spending, debt and savings advice. Deadline **2026-10-11 12:00**. Three developers (Sundar, Dilip, Lea) each build one stream in parallel.

Read first: [CONTEXT.md](CONTEXT.md) (glossary and rules), [docs/specs/00-overview.md](docs/specs/00-overview.md) (streams, ground rules, merge checkpoints), then your stream's spec in `docs/specs/`.

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

- `wealthwise/contracts.py`: the shared data contract. Frozen; changes need a PR seen by all three developers.
- `wealthwise/ingestion/`: Stream A, files to `FinancialProfile`.
- `wealthwise/analysis/`: Stream B, `FinancialProfile` to `Report` (metrics, score, LangGraph agents).
- `app.py`, `wealthwise/rag/`: Stream C, the Streamlit dashboard and Ask WealthWise.
- `wealthwise/llm.py`: the only place that creates the LLM client (OpenRouter).
- `samples/`: fictional documents and answer keys. Generated; never hand-edit.
- `docs/adr/`: decisions. Respect them, or flag a conflict explicitly.

## Rules

- Numbers come from code; the LLM only writes explanation text (ADR-0001). The app must work with no API key.
- Stay inside your stream's folder. Shared files change only via a small separate PR.
- Write the spec's acceptance criteria as tests. Run `pytest` before every PR.
- Never commit `.env`, `uploads/` or real financial documents.
- Branches: `sundar-dev`, `dilip-dev`, `lea-dev`. PR into `main` at each merge checkpoint.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `basheernavan/Hackathon_WealthWiseAI_G9`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
