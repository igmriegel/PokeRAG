"""
End-to-end RAG chain.
"""

from __future__ import annotations

import re
import time
from typing import Any

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import AnswerResponse, DocumentMetadata
from pokemon_tcg_rag.llm.client import LLMClient, SupportsGeneration
from pokemon_tcg_rag.llm.prompts import PromptTemplateManager
from pokemon_tcg_rag.monitoring.tracing import traced_span
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline


class RAGChain:
    """Execute retrieval, prompt construction, and answer generation."""

    def __init__(
        self,
        retrieval_pipeline: RetrievalPipeline,
        llm_client: SupportsGeneration | None = None,
        prompt_manager: PromptTemplateManager | None = None,
    ) -> None:
        self.retrieval_pipeline = retrieval_pipeline
        self.llm_client = llm_client or LLMClient()
        self.prompt_manager = prompt_manager or PromptTemplateManager()
        self.settings = get_settings()

    def query(
        self,
        raw_query: str,
        top_k: int | None = None,
        metadata_filters: dict[str, str] | None = None,
    ) -> AnswerResponse:
        """Return a cited answer response for the given query."""
        start = time.time()
        effective_top_k = top_k or self.settings.RETRIEVAL_FINAL_TOP_K
        with traced_span(
            "rag.query",
            attributes={
                "query.length": len(raw_query.strip()),
                "query.top_k": effective_top_k,
            },
        ):
            rewritten_query, chunks = self._execute_retrieval(
                raw_query=raw_query,
                top_k=effective_top_k,
                metadata_filters=metadata_filters,
            )

            if not chunks:
                latency = time.time() - start
                return AnswerResponse(
                    query=raw_query,
                    rewritten_query=rewritten_query,
                    answer="I don't know.",
                    citations=[],
                    retrieved_chunks=[],
                    model_name=self.llm_client.model_name,
                    latency_seconds=round(latency, 3),
                )

            prompt = self.prompt_manager.build_prompt(query=raw_query, chunks=chunks)
            with traced_span(
                "rag.prompt",
                attributes={"retrieval.chunk_count": len(chunks)},
            ):
                answer = self.llm_client.generate_answer(prompt).strip() or "I don't know."
            if self._contains_invalid_citations(answer, len(chunks)):
                answer = "I don't know."
            latency = time.time() - start
            citations: list[DocumentMetadata] = [item.chunk.metadata for item in chunks]

            return AnswerResponse(
                query=raw_query,
                rewritten_query=rewritten_query,
                answer=answer,
                citations=citations,
                retrieved_chunks=chunks,
                model_name=self.llm_client.model_name,
                latency_seconds=round(latency, 3),
            )

    def _contains_invalid_citations(self, answer: str, max_index: int) -> bool:
        citation_indexes = [int(match) for match in re.findall(r"\[(\d+)\]", answer)]
        if not citation_indexes:
            return False
        return any(index < 1 or index > max_index for index in citation_indexes)

    def _execute_retrieval(
        self,
        raw_query: str,
        top_k: int,
        metadata_filters: dict[str, str] | None,
    ) -> tuple[str, list[Any]]:
        """Call the retrieval pipeline with compatibility for older test doubles."""
        try:
            return self.retrieval_pipeline.execute_retrieval(
                raw_query=raw_query,
                top_k=top_k,
                metadata_filters=metadata_filters,
            )
        except TypeError as exc:
            if "unexpected keyword argument 'metadata_filters'" not in str(exc):
                raise
            return self.retrieval_pipeline.execute_retrieval(
                raw_query=raw_query,
                top_k=top_k,
            )
