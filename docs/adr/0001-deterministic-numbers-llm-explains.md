# ADR-0001: Numbers are computed in code; the LLM only explains them

**Status:** accepted, 2026-10-10

## Context
Accuracy and correctness are the top priorities. LLMs make arithmetic mistakes, and retrieval (RAG) over numeric tables is unreliable for totals.

## Decision
Pandas and plain Python calculate every figure: metrics, the Health Score, the debt plan and the savings plan. Each agent passes those figures to the LLM, which only writes the `title` and `detail` text. `monthly_impact` and `evidence` are always filled by code. If the LLM call fails or no key is set, template text is used and `Report.llm_used` is `False`.

## Consequences
The figures can be tested against `samples/expected.json`. The demo still works offline. The pitch's "grounded in your data" claim is true by construction.
