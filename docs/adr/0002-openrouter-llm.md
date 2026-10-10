# ADR-0002: Reach the LLM through OpenRouter

**Status:** accepted, 2026-10-10

## Context
The team has an OpenRouter key, not an OpenAI key. The budget is under €30.

## Decision
Use `langchain-openai`'s `ChatOpenAI` pointed at `https://openrouter.ai/api/v1`, built only in `wealthwise/llm.py`. The model is set by `WEALTHWISE_MODEL`. The default is `anthropic/claude-haiku-5.5` ($0.10 in / $0.50 out per million tokens on 2026-10-10, with structured outputs); the backup is `deepseek/deepseek-v3.2`. Structured output uses `with_structured_output(Schema)`, with `json_schema` as the default method.

## Consequences
Switching models is a one-line `.env` change. A full analysis is a few short calls, costing well under €0.01.
