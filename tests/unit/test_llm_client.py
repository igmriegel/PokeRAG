"""
TASK-021 — TEST-067, TEST-068, TEST-069

Unit tests for the OpenAI-compatible LLM client.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from pokemon_tcg_rag.domain.exceptions import LLMError
from pokemon_tcg_rag.llm.client import LLMClient


class FakeCompletions:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, completions: FakeCompletions) -> None:
        self.chat = SimpleNamespace(completions=completions)


def _completion(text: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


@pytest.mark.unit
def test_generate_answer_returns_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-067: client must return the text from the completion response."""
    completions = FakeCompletions(response=_completion("yes"))
    client = LLMClient(client=FakeClient(completions))

    assert client.generate_answer("prompt") == "yes"


@pytest.mark.unit
def test_temperature_and_model_from_settings() -> None:
    """TEST-068: model and temperature must come from settings."""
    client = LLMClient(client=FakeClient(FakeCompletions(response=_completion("ok"))))

    assert client.model_name == "gpt-4o-mini"
    assert client.temperature == 0.0


@pytest.mark.unit
def test_api_error_raises_llm_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-069: provider failures must raise LLMError after retries."""
    completions = FakeCompletions(error=RuntimeError("boom"))
    client = LLMClient(client=FakeClient(completions), retries=1, retry_delay=0.0)

    with pytest.raises(LLMError):
        client.generate_answer("prompt")
