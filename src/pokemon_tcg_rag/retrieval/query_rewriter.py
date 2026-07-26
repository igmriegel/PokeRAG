"""
Query rewriting helper for retrieval-optimized Pokemon TCG searches.
"""

from __future__ import annotations

from pokemon_tcg_rag.llm.client import LLMClient, SupportsGeneration
from pokemon_tcg_rag.monitoring.tracing import traced_span


class QueryRewriter:
    """Rewrite vague user questions into domain-specific retrieval queries."""

    def __init__(self, client: SupportsGeneration | None = None) -> None:
        self.client = client or LLMClient()

    def rewrite_query(self, original_query: str) -> str:
        """Rewrite a vague query or safely fall back to the original."""
        with traced_span(
            "retrieval.query_rewrite",
            attributes={"query.length": len(original_query.strip())},
        ):
            prompt = self._build_prompt(original_query)
            rewrite = self.client.generate_answer(prompt).strip()
            rewrite = self._sanitize(rewrite)
            if not rewrite or self._normalized(rewrite) == self._normalized(original_query):
                return original_query
            return rewrite

    def _build_prompt(self, original_query: str) -> str:
        return (
            "You rewrite user questions for Pokemon TCG rules retrieval.\n"
            "Return a concise search query that includes Pokemon TCG domain terms.\n"
            "If the original question is vague, infer the likely card/gameplay context.\n"
            f"Original question: {original_query}\n"
            "Rewritten query:"
        )

    def _sanitize(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```") and cleaned.endswith("```"):
            cleaned = cleaned.strip("`").strip()
        cleaned = cleaned.strip('"').strip("'")
        if cleaned.lower().startswith("rewritten query:"):
            cleaned = cleaned.split(":", 1)[1].strip()
        return cleaned

    def _normalized(self, text: str) -> str:
        return " ".join(text.lower().split())
