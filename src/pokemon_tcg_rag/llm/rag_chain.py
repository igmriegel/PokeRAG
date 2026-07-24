"""
End-to-end RAG chain.
"""

from __future__ import annotations

import time

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import AnswerResponse, DocumentMetadata
from pokemon_tcg_rag.llm.client import LLMClient
from pokemon_tcg_rag.llm.prompts import PromptTemplateManager
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline


class RAGChain:
    """Execute retrieval, prompt construction, and answer generation."""

    def __init__(
        self,
        retrieval_pipeline: RetrievalPipeline,
        llm_client: LLMClient | None = None,
        prompt_manager: PromptTemplateManager | None = None,
    ) -> None:
        self.retrieval_pipeline = retrieval_pipeline
        self.llm_client = llm_client or LLMClient()
        self.prompt_manager = prompt_manager or PromptTemplateManager()
        self.settings = get_settings()

    def query(self, raw_query: str, top_k: int | None = None) -> AnswerResponse:
        """Return a cited answer response for the given query."""
        start = time.time()
        effective_top_k = top_k or self.settings.RETRIEVAL_FINAL_TOP_K
        rewritten_query, chunks = self.retrieval_pipeline.execute_retrieval(
            raw_query=raw_query,
            top_k=effective_top_k,
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
        answer = self.llm_client.generate_answer(prompt).strip() or "I don't know."
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
