"""
User Query Rewriting Engine for domain-specific Pokemon TCG terminology expansion.
"""

import logging
from openai import OpenAI
from pokemon_tcg_rag.config.settings import get_settings

logger = logging.getLogger(__name__)


class QueryRewriter:
    """Transforms ambiguous user questions into structured Pokemon TCG domain queries."""

    REWRITE_PROMPT_TEMPLATE = """You are an expert Pokemon TCG Rules Judge assistant.
Your job is to rewrite user questions to optimize information retrieval against official Pokemon TCG rules, errata, tournament handbooks, and Pokegym compendium rulings.

User Question: "{query}"

Rules for rewriting:
1. Preserve all card names, mechanic keywords (e.g. Mega Evolution, Rare Candy, Bench, Active, VSTAR, EX).
2. Expand ambiguous terminology (e.g. "Posso usar essa carta?" -> "Pokemon TCG card legality status and format legality rules").
3. Make the query formal, concise, and targeted for semantic vector search.
4. Output ONLY the rewritten query string. No preamble or explanation.
"""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_name = settings.OPENAI_MODEL_NAME

    def rewrite_query(self, original_query: str) -> str:
        """Rewrite raw user query into domain-optimized search phrase."""
        if not original_query.strip():
            return original_query

        try:
            prompt = self.REWRITE_PROMPT_TEMPLATE.format(query=original_query)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=100,
            )
            rewritten = response.choices[0].message.content.strip()
            logger.info("Original query: '%s' -> Rewritten query: '%s'", original_query, rewritten)
            return rewritten
        except Exception as exc:
            logger.warning("Query rewriting failed: %s. Using original query.", exc)
            return original_query
