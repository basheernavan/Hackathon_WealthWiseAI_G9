"""The one place that knows how to reach the LLM (OpenRouter, ADR-0002)."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-haiku-5.5"


def get_chat_model() -> ChatOpenAI | None:
    """Return a chat model, or None when no key is set so callers fall back to templates."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        model=os.getenv("WEALTHWISE_MODEL", DEFAULT_MODEL),
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        temperature=0,
        timeout=30,
        max_retries=2,
    )
