# Background documents

Pitch deck, speaker notes, early setup notes and budget, kept for the presentation.

The pitch deck (`WealthWise_Heading_Robots.pptx`) and its speaker notes (`WealthWise.docx`) match the app: architecture, stack, the "numbers from code" trust story and the demo figures from `samples/expected.json`. The speaker notes follow the deck's 8 slides.

**The setup notes and the budget describe an earlier plan.** Where they disagree with the code, the repo wins:

| These files say | What we actually do |
| --- | --- |
| SQLite database; documents "stored within ChromaDB" | No database. ChromaDB only for Ask WealthWise ([ADR-0003](../docs/adr/0003-no-database-chroma-for-questions-only.md)) |
| OpenAI GPT-4o | OpenRouter, `anthropic/claude-haiku-5.5` ([ADR-0002](../docs/adr/0002-openrouter-llm.md)) |
| `agents/`, `rag/`, `database/` folders; `venv` | The layout in [CLAUDE.md](../CLAUDE.md); `.venv`. Setup: [docs/COLLABORATION.md](../docs/COLLABORATION.md) |

To build the app, use [docs/COLLABORATION.md](../docs/COLLABORATION.md), not the setup document here.
