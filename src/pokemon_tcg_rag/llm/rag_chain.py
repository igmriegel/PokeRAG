"""
End-to-End RAG Chain execution engine.
"""

import time
from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import AnswerResponse, DocumentMetadata
from pokemon_tcg_rag.llm.client import LLMClient
from pokemon_tcg_rag.llm.prompts import PromptTemplateManager
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline


class RAGChain:
    """Executes full RAG workflow: Retrieve -> Build Prompt -> Call LLM -> Format Response."""

    def __init__(self, retrieval_pipeline: RetrievalPipeline) -> None:
        self.retrieval_pipeline = retrieval_pipeline
        self.llm_client = LLMClient()
        self.prompt_manager = PromptTemplateManager()
        self.settings = get_settings()

    def query(self, raw_query: str) -> AnswerResponse:
        """Process user query through RAG pipeline and return structured AnswerResponse."""
        start_time = time.time()

        # Step 1: Execute multi-stage retrieval
        rewritten_query, chunks = self.retrieval_pipeline.execute_retrieval(
            raw_query=raw_query,
            top_k=self.settings.RETRIEVAL_FINAL_TOP_K
        )

        # Step 2: Build formatted prompt
        prompt = self.prompt_manager.build_prompt(query=raw_query, chunks=chunks)

        # Step 3: LLM Generation
        answer_text = self.llm_client.generate_answer(prompt)

        latency = time.time() - start_time
        citations: list[DocumentMetadata] = [item.chunk.metadata for item in chunks]

        return AnswerResponse(
            query=raw_query,
            rewritten_query=rewritten_query,
            answer=answer_text,
            citations=citations,
            retrieved_chunks=chunks,
            model_name=self.llm_client.model_name,
            latency_seconds=round(latency, 3),
        )
