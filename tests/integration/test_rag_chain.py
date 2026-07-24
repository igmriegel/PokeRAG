"""
TASK-025 — TEST-080, TEST-081, TEST-082, TEST-083

Integration tests for the end-to-end RAG chain.
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
from pokemon_tcg_rag.llm.rag_chain import RAGChain


def _make_chunk(chunk_id: str, text: str) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id=chunk_id,
        doc_id=f"doc-{chunk_id}",
        text=text,
        token_count=len(text.split()),
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Official Rulebook",
            page_number=12,
            rule_type=RuleType.GENERAL_RULE,
            source_url="https://example.com/rulebook.pdf",
        ),
    )
    return RetrievedChunk(chunk=chunk, score=0.9, retrieval_method="hybrid_rrf")


class FakeRetrievalPipeline:
    def __init__(self, rewritten_query: str, chunks: list[RetrievedChunk]) -> None:
        self.rewritten_query = rewritten_query
        self.chunks = chunks
        self.calls: list[str] = []

    def execute_retrieval(self, raw_query: str, top_k: int = 5):
        self.calls.append(raw_query)
        return self.rewritten_query, self.chunks[:top_k]


class FakeLLMClient:
    def __init__(self, response: str = "Answer text") -> None:
        self.response = response
        self.calls: list[str] = []
        self.model_name = "gpt-4o-mini"

    def generate_answer(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.response


@pytest.mark.integration
def test_query_returns_answer_response() -> None:
    """TEST-080: query must return a valid AnswerResponse."""
    chunks = [_make_chunk("c1", "Rare Candy rule")]
    retrieval_pipeline = FakeRetrievalPipeline("rewritten query", chunks)
    llm = FakeLLMClient("Grounded answer.")
    chain = RAGChain(retrieval_pipeline=retrieval_pipeline, llm_client=llm)

    response = chain.query("Can I use Rare Candy?")

    assert response.answer == "Grounded answer."
    assert response.rewritten_query == "rewritten query"
    assert response.query == "Can I use Rare Candy?"


@pytest.mark.integration
def test_answer_includes_citations() -> None:
    """TEST-081: citations must be attached from the retrieved chunks."""
    chunks = [_make_chunk("c1", "Rare Candy rule")]
    chain = RAGChain(
        retrieval_pipeline=FakeRetrievalPipeline("rewritten query", chunks),
        llm_client=FakeLLMClient("Grounded answer."),
    )

    response = chain.query("Can I use Rare Candy?")

    assert len(response.citations) == 1
    assert response.citations[0].document_title == "Official Rulebook"


@pytest.mark.integration
def test_latency_and_model_recorded() -> None:
    """TEST-082: latency and model name must be recorded."""
    chunks = [_make_chunk("c1", "Rare Candy rule")]
    llm = FakeLLMClient("Grounded answer.")
    chain = RAGChain(
        retrieval_pipeline=FakeRetrievalPipeline("rewritten query", chunks),
        llm_client=llm,
    )

    response = chain.query("Can I use Rare Candy?")

    assert response.model_name == "gpt-4o-mini"
    assert response.latency_seconds >= 0


@pytest.mark.integration
def test_no_context_returns_idk() -> None:
    """TEST-083: empty retrieval results must return the grounded fallback answer."""
    llm = FakeLLMClient("This should not be used")
    chain = RAGChain(
        retrieval_pipeline=FakeRetrievalPipeline("rewritten query", []),
        llm_client=llm,
    )

    response = chain.query("Can I use Rare Candy?")

    assert response.answer == "I don't know."
    assert response.citations == []
    assert llm.calls == []
