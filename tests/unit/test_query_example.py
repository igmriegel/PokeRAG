"""
TASK-031 — TEST-100, TEST-101

Unit tests for the programmatic RAG query example.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from pokemon_tcg_rag.domain.models import (
    AnswerResponse,
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)

EXAMPLE_PATH = Path(__file__).parents[2] / "examples" / "query_example.py"


def _load_example_module():
    spec = importlib.util.spec_from_file_location("query_example", EXAMPLE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _response() -> AnswerResponse:
    metadata = DocumentMetadata(
        source=DocumentSource.RULEBOOK_PDF,
        document_title="Official Rulebook",
        page_number=12,
        rule_type=RuleType.GENERAL_RULE,
        source_url="https://example.com/rulebook.pdf",
    )
    chunk = Chunk(
        chunk_id="chunk-1",
        doc_id="doc-1",
        text="Rare Candy text",
        token_count=3,
        metadata=metadata,
    )
    retrieved = RetrievedChunk(chunk=chunk, score=0.9, retrieval_method="dense")
    return AnswerResponse(
        query="Can I use Rare Candy?",
        rewritten_query="Pokemon TCG Rare Candy legality",
        answer="Yes.",
        citations=[metadata],
        retrieved_chunks=[retrieved],
        model_name="gpt-4o-mini",
        latency_seconds=0.42,
    )


class FakeChain:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def query(self, question: str, top_k: int | None = None) -> AnswerResponse:
        self.calls.append(question)
        return _response()


def test_example_runs_with_mocked_chain(capsys: pytest.CaptureFixture[str]) -> None:
    """TEST-100: example must run with a mocked chain."""
    query_example = _load_example_module()
    chain = FakeChain()
    exit_code = query_example.main(["--question", "Can I use Rare Candy?"], rag_chain=chain)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Resposta do Juiz" in captured.out
    assert chain.calls == ["Can I use Rare Candy?"]


def test_example_prints_citations(capsys: pytest.CaptureFixture[str]) -> None:
    """TEST-101: example output must include citations."""
    query_example = _load_example_module()
    chain = FakeChain()
    query_example.main(["--question", "Can I use Rare Candy?"], rag_chain=chain)

    captured = capsys.readouterr()
    assert "Citações:" in captured.out
    assert "Official Rulebook" in captured.out
