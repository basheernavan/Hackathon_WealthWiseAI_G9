# WealthWise Hackathon Handover

## Delivered

- Ask WealthWise answers supported merchant, category, income, debt and subscription questions from the active financial profile and validated report. Merchant/category amounts and transaction evidence are calculated in Python; ChromaDB retrieval and OpenRouter remain available for open-ended explanations.
- The chat keeps bounded conversation context and respects stated preferences when suggesting alternatives. Without an OpenRouter key, deterministic report answers and a limited, grounded fallback remain available.
- The dashboard presents the overview, recommendation scenarios and source evidence. Recommendation amounts are explicitly optional; debt and savings plans are alternative destinations for the same allocation.
- Savings allocation now handles cases where proposed cuts do not cover the full monthly shortfall. Debt payoff projections do not claim results beyond the supported simulation horizon.
- The README documents setup, demo, data handling and limitations. `wealthwise/contracts.py` was not changed.

## Review ownership

Review changes with the relevant stream owners and follow [COLLABORATION.md](./COLLABORATION.md):

| Area | Files to review |
| --- | --- |
| C1 app and chat integration | `app.py`, `tests/test_app.py` |
| C2 dashboard | `wealthwise/dashboard.py`, `tests/test_dashboard.py` |
| C3 Ask WealthWise | `wealthwise/rag/__init__.py`, `tests/test_rag.py` |
| Analysis and financial scenarios | `wealthwise/analysis/agents.py`, `wealthwise/analysis/plans.py`, `tests/test_agents.py`, `tests/test_plans.py` |
| Project guidance and evidence | `README.md`, `evidence/` |

Review the financial assumptions and scenario wording with the analysis owner, and the prompt, retrieved context and provider data flow with the C3 owner. When OpenRouter is enabled, the question, bounded conversation, report context and relevant retrieved financial rows are sent to the configured provider. Do not use real financial documents for a demo.

## Launch and demonstration

From the repository root, activate the project virtual environment, then run:

```bash
streamlit run app.py
```

Choose **Use sample documents**, inspect the overview and recommendation evidence, then ask:

1. `any money on delivereoo?`
2. `I love takeaway. I don't want to stop.`
3. `What else could I change?`

The first question uses deterministic transaction matching. The last demonstrates an OpenRouter-backed, report-grounded alternative when a key and network access are configured. Keep `.env` local; the app remains usable without a key, but open-ended model answers are unavailable.

## Verification and evidence

- Focused Ask WealthWise tests: **42 passed** (`.venv/bin/pytest tests/test_rag.py`).
- Full regression suite: **134 passed**, with **5 third-party SWIG deprecation warnings** (`.venv/bin/pytest`).
- Python syntax compilation: passed (`.venv/bin/python -m compileall -q app.py wealthwise tests`).
- `git diff --check`: passed.
- Browser verification used the fictional sample documents at `http://localhost:8510/`. The live typo-tolerant merchant answer was **€287.31 at DELIVEROO across 7 transactions**, dated 2026-07-18, 2026-07-28, 2026-08-12, 2026-08-28, 2026-09-03, 2026-09-05 and 2026-09-08. The OpenRouter follow-up was also exercised. Responsive layouts were checked at narrow and desktop widths.
- Screenshots: [overview](../evidence/wealthwise-final-overview-verified-20261011.png), [recommendations](../evidence/wealthwise-final-recommendations-verified-20261011.png), and [merchant chat](../evidence/wealthwise-final-chat-verified-20261011.png).

## Remaining limitations and integration

- This is a local hackathon pilot, not a deployed or production banking service. Deployment availability was not verified in this handover.
- Open-ended answers depend on network access and the configured model, and still require user verification. The app's Altair chart emitted a browser console warning for the `Monthly amount_start` and `Monthly amount_end` fields during earlier verification; the charts rendered, but that warning has not been investigated.
- A pre-existing `evidence/wealthwise-final-overview-20261011.png` may have been overwritten during earlier work; its original was not present in the checked session backups. The separately named verified screenshots above were captured for this handover.
- No changes were pushed, merged or committed. The work remains on `15-ask-wealthwise`; review and integrate it using the team's issue ownership and pull-request process. No remote update was performed as part of this handover.
