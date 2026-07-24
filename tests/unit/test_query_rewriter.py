"""
TASK-022 — TEST-070, TEST-071, TEST-072

Unit tests for the query rewriter.
"""

from __future__ import annotations

import pytest

from pokemon_tcg_rag.retrieval.query_rewriter import QueryRewriter


class FakeLLMClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def generate_answer(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


@pytest.mark.unit
def test_rewrite_expands_vague_query() -> None:
    """TEST-070: vague queries must be rewritten with Pokemon TCG domain terms."""
    client = FakeLLMClient("Pokemon TCG card legality ruling for Rare Candy")
    rewriter = QueryRewriter(client=client)

    rewritten = rewriter.rewrite_query("Can I use this card?")

    assert "Pokemon TCG" in rewritten
    assert client.prompts[0].startswith(
        "You rewrite user questions for Pokemon TCG rules retrieval."
    )


@pytest.mark.unit
def test_fallback_to_original_on_empty() -> None:
    """TEST-071: empty or degenerate rewrites must fall back to the original query."""
    rewriter = QueryRewriter(client=FakeLLMClient("   "))

    assert rewriter.rewrite_query("Can I use this card?") == "Can I use this card?"


@pytest.mark.unit
def test_rewrite_prompt_contains_domain_hint() -> None:
    """TEST-072: the prompt must mention the Pokemon TCG domain explicitly."""
    client = FakeLLMClient("Pokemon TCG legality check")
    rewriter = QueryRewriter(client=client)

    rewriter.rewrite_query("How does this work?")

    assert "Pokemon TCG" in client.prompts[0]
