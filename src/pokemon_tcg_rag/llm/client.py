"""
LLM provider abstraction client.
"""

from __future__ import annotations

import random
import time
from typing import Protocol

from openai import OpenAI

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import LLMError, LLMQuotaError
from pokemon_tcg_rag.monitoring.metrics_collector import DEFAULT_METRICS_COLLECTOR
from pokemon_tcg_rag.monitoring.tracing import traced_span


class LLMClient:
    """Wrapper around an OpenAI-compatible chat completions endpoint."""

    def __init__(
        self, client: OpenAI | None = None, retries: int = 3, retry_delay: float = 0.5
    ) -> None:
        settings = get_settings()
        self.request_timeout_seconds = settings.API_PROVIDER_TIMEOUT_SECONDS
        self.max_retries = settings.API_PROVIDER_MAX_RETRIES
        self.circuit_breaker_threshold = settings.API_PROVIDER_CIRCUIT_BREAKER_THRESHOLD
        self.circuit_breaker_reset_seconds = (
            settings.API_PROVIDER_CIRCUIT_BREAKER_RESET_SECONDS
        )
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
        with traced_span(
            "llm.generate",
            attributes={
                "llm.model_name": self.model_name,
                "llm.temperature": self.temperature,
                "llm.prompt_length": len(prompt),
            },
        ):
            for attempt in range(self.retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.temperature,
                        timeout=self.request_timeout_seconds,
                    )
                    content = (
                        response.choices[0].message.content
                        if response.choices
                        else None
                    )
                    if not content or not content.strip():
                        raise LLMError("LLM returned an empty response")
                    usage = getattr(response, "usage", None)
                    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
                    cost_usd = 0.0
                    DEFAULT_METRICS_COLLECTOR.record_provider_usage(
                        model=self.model_name,
                        stage="answer",
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost_usd=cost_usd,
                    )
                    self._record_success()
                    return content.strip()
                except (
                    Exception
                ) as exc:  # pragma: no cover - network / provider boundary
                    last_error = exc
                    self._record_failure()
                    if _is_insufficient_quota(exc):
                        raise LLMQuotaError(
                            "OpenAI API quota is unavailable; review API billing and credits"
                        ) from exc
                    if attempt < self.retries - 1:
                        time.sleep(
                            (self.retry_delay * (attempt + 1))
                            + random.uniform(0.0, 0.05)
                        )
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
            self._circuit_open_until = (
                time.monotonic() + self.circuit_breaker_reset_seconds
            )
            self._failure_count = 0


class SupportsGeneration(Protocol):
    """Minimal contract for prompt-rewriting and answer-generation clients."""

    model_name: str

    def generate_answer(self, prompt: str) -> str: ...


def _is_insufficient_quota(exc: Exception) -> bool:
    """Recognize OpenAI billing quota failures without exposing provider payloads."""
    if getattr(exc, "code", None) == "insufficient_quota":
        return True
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error", body)
        if isinstance(error, dict) and error.get("code") == "insufficient_quota":
            return True
    return "insufficient_quota" in str(exc).lower()
