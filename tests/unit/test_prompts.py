"""
TASK-024 — TEST-076, TEST-077, TEST-078, TEST-079

Unit tests for prompt templates and judge persona.
"""

from __future__ import annotations

import pytest

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.llm.prompts import PromptTemplateManager


def _make_retrieved(chunk_id: str, text: str, page_number: int = 1) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id=chunk_id,
        doc_id=f"doc-{chunk_id}",
        text=text,
        token_count=len(text.split()),
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Official Rulebook",
            page_number=page_number,
            card_name="Rare Candy",
            rule_type=RuleType.GENERAL_RULE,
            publication_date="2026-07-24",
            source_url="https://example.com/rulebook.pdf",
        ),
    )
    return RetrievedChunk(chunk=chunk, score=0.9, retrieval_method="dense")


@pytest.mark.unit
def test_context_ordering_and_numbering() -> None:
    """TEST-076: context must preserve order and number each source."""
    manager = PromptTemplateManager()
    context = manager.format_context(
        [
            _make_retrieved("c1", "First chunk"),
            _make_retrieved("c2", "Second chunk", page_number=2),
        ]
    )

    assert context.startswith("[1] Official Rulebook")
    assert "\n\n[2] Official Rulebook" in context
    assert "First chunk" in context
    assert "Second chunk" in context


@pytest.mark.unit
def test_prompt_contains_citation_instruction() -> None:
    """TEST-077: prompt must instruct the model to cite sources."""
    manager = PromptTemplateManager()
    prompt = manager.build_prompt(
        "Can I use Rare Candy?", [_make_retrieved("c1", "Rare Candy rule")]
    )

    assert "cite" in prompt.lower()
    assert "[1]" in prompt


@pytest.mark.unit
def test_idk_instruction_present() -> None:
    """TEST-078: prompt must contain the no-hallucination fallback instruction."""
    manager = PromptTemplateManager(variant="B")
    prompt = manager.build_prompt("Unknown question", [])

    assert "I don't know." in prompt
    assert "não invente" not in prompt.lower() or "Não invente".lower() in prompt.lower()


@pytest.mark.unit
def test_context_length_bounded() -> None:
    """TEST-079: formatted context must be truncated to the configured bound."""
    manager = PromptTemplateManager(max_context_chars=80)
    context = manager.format_context([_make_retrieved("c1", "x" * 500)])

    assert len(context) <= 83
    assert context.endswith("...")
