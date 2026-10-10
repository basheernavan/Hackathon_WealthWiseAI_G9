# ADR-0003: No database; ChromaDB only for "Ask WealthWise"

**Status:** accepted, 2026-10-10

## Context
The original plan listed SQLite and ChromaDB. The pilot has one user per session and nothing needs to survive a restart.

## Decision
- No SQLite. Keep the profile and report in `st.session_state`.
- Recommendation evidence is selected deterministically by filtering transactions by category, not by vector search (ADR-0001).
- ChromaDB, as an in-memory `EphemeralClient`, is used only by the "Ask WealthWise" question box. It indexes one text row per transaction, payslip line and debt, and the top matches go to the LLM as context.

## Consequences
There's less infrastructure to build, and the pitch's tabular-RAG story still stands. Chroma's default embedding model downloads about 80 MB on first use, so run it once before the demo.
