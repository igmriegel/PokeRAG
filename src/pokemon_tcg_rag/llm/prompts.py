"""
Prompt templates for the certified judge persona.
"""

from __future__ import annotations

from collections.abc import Sequence

from pokemon_tcg_rag.domain.models import RetrievedChunk


class PromptTemplateManager:
    """Build grounded prompts for the Pokemon TCG judge persona."""

    SYSTEM_PROMPT_A = """Você é um Juiz Certificado Oficial do Pokémon Trading Card Game (TCG).
Responda apenas usando o contexto fornecido.
Não invente regras, não suponha intenções e não use conhecimento externo.
Sempre cite as fontes numeradas presentes no contexto.
Se o contexto não for suficiente, responda exatamente: "I don't know."

Contexto:
{context}

Pergunta:
{query}
"""

    SYSTEM_PROMPT_B = """Você é um árbitro experiente de Pokémon TCG.
Seu trabalho é responder com precisão, baseando-se somente nas evidências fornecidas.
Toda afirmação relevante deve ser sustentada por uma citação do contexto.
Se faltar evidência, diga "I don't know."

Contexto:
{context}

Pergunta:
{query}
"""

    def __init__(self, variant: str = "A", max_context_chars: int = 6000) -> None:
        self.variant = variant.upper()
        self.max_context_chars = max_context_chars

    def format_context(self, chunks: Sequence[RetrievedChunk]) -> str:
        """Number chunks and include citation-friendly source metadata."""
        blocks: list[str] = []
        for index, item in enumerate(chunks, start=1):
            meta = item.chunk.metadata
            source_line = f"[{index}] {meta.document_title}"
            details: list[str] = []
            if meta.source_url:
                details.append(meta.source_url)
            if meta.page_number is not None:
                details.append(f"p. {meta.page_number}")
            if meta.card_name:
                details.append(f"carta: {meta.card_name}")
            if meta.publication_date:
                details.append(f"data: {meta.publication_date}")
            if details:
                source_line += " — " + " | ".join(details)
            blocks.append(f"{source_line}\n{item.chunk.text.strip()}")

        context = "\n\n".join(blocks)
        return self._truncate_context(context)

    def build_prompt(self, query: str, chunks: Sequence[RetrievedChunk]) -> str:
        """Build the final prompt using the selected judge variant."""
        context = self.format_context(chunks)
        template = self._template_for_variant()
        return template.format(context=context, query=query.strip())

    def _template_for_variant(self) -> str:
        return self.SYSTEM_PROMPT_B if self.variant == "B" else self.SYSTEM_PROMPT_A

    def _truncate_context(self, context: str) -> str:
        if len(context) <= self.max_context_chars:
            return context
        return context[: self.max_context_chars].rstrip() + "..."
