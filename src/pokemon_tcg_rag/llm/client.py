"""
LLM provider abstraction client.
"""

from __future__ import annotations

import random
import time
from typing import Protocol

from openai import OpenAI

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import LLMError


class LLMClient:
    """Wrapper around an OpenAI-compatible chat completions endpoint."""

    def __init__(
        self, client: OpenAI | None = None, retries: int = 3, retry_delay: float = 0.5
    ) -> None:
        settings = get_settings()
        self.request_timeout_seconds = settings.API_PROVIDER_TIMEOUT_SECONDS
        self.max_retries = settings.API_PROVIDER_MAX_RETRIES
        self.circuit_breaker_threshold = settings.API_PROVIDER_CIRCUIT_BREAKER_THRESHOLD
        self.circuit_breaker_reset_seconds = settings.API_PROVIDER_CIRCUIT_BREAKER_RESET_SECONDS
        self.client = client or OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=self.request_timeout_seconds,
        )
        self.model_name = settings.OPENAI_MODEL_NAME
        self.temperature = settings.OPENAI_TEMPERATURE
        self.retries = min(retries, self.max_retries)
        self.retry_delay = retry_delay
        self._failure_count = 0
        self._circuit_open_until = 0.0

    def generate_answer(self, prompt: str) -> str:
        """Generate a text response using the configured chat model."""
        self._ensure_circuit_closed()
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    timeout=self.request_timeout_seconds,
                )
                content = response.choices[0].message.content if response.choices else None
                if not content or not content.strip():
                    raise LLMError("LLM returned an empty response")
                self._record_success()
                return content.strip()
            except Exception as exc:  # pragma: no cover - network / provider boundary
                last_error = exc
                self._record_failure()
                if attempt < self.retries - 1:
                    time.sleep((self.retry_delay * (attempt + 1)) + random.uniform(0.0, 0.05))
                    continue
                raise LLMError(f"LLM generation failed: {exc}") from exc

        raise LLMError(f"LLM generation failed: {last_error}")

    def _ensure_circuit_closed(self) -> None:
        if time.monotonic() < self._circuit_open_until:
            raise LLMError("LLM circuit breaker is open")

    def _record_success(self) -> None:
        self._failure_count = 0
        self._circuit_open_until = 0.0

    def _record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self.circuit_breaker_threshold:
            self._circuit_open_until = time.monotonic() + self.circuit_breaker_reset_seconds
            self._failure_count = 0


class SupportsGeneration(Protocol):
    """Minimal contract for prompt-rewriting and answer-generation clients."""

    model_name: str

    def generate_answer(self, prompt: str) -> str: ...
