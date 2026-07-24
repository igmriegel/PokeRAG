"""
LLM provider abstraction client.
"""

from __future__ import annotations

import time

from openai import OpenAI

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import LLMError


class LLMClient:
    """Wrapper around an OpenAI-compatible chat completions endpoint."""

    def __init__(self, client: OpenAI | None = None, retries: int = 3, retry_delay: float = 0.5) -> None:
        settings = get_settings()
        self.client = client or OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_name = settings.OPENAI_MODEL_NAME
        self.temperature = settings.OPENAI_TEMPERATURE
        self.retries = retries
        self.retry_delay = retry_delay

    def generate_answer(self, prompt: str) -> str:
        """Generate a text response using the configured chat model."""
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                )
                content = response.choices[0].message.content if response.choices else None
                if not content or not content.strip():
                    raise LLMError("LLM returned an empty response")
                return content.strip()
            except Exception as exc:  # pragma: no cover - network / provider boundary
                last_error = exc
                if attempt < self.retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise LLMError(f"LLM generation failed: {exc}") from exc

        raise LLMError(f"LLM generation failed: {last_error}")
