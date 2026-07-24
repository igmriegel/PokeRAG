"""
Prompt Engineering System Templates.
"""

from pokemon_tcg_rag.domain.models import RetrievedChunk


class PromptTemplateManager:
    """Manages system prompts, context formatting, and citation instructions."""

    SYSTEM_PROMPT = """Você é um Juiz Certificado Oficial do Pokémon Trading Card Game (TCG).
Sua missão é responder à pergunta do usuário utilizando EXCLUSIVAMENTE a documentação oficial e rulings fornecidas no contexto abaixo.

REGRAS OBRIGATÓRIAS:
1. Responda apenas com base nas informações explicitamente presentes nos trechos fornecidos.
2. NUNCA invente ou assuma regras que não estejam comprovadas pelos documentos.
3. Se o contexto fornecido for insuficiente para responder com certeza, declare expressamente: "Não há evidência suficiente na documentação oficial para responder a esta pergunta."
4. TODA afirmação sobre regras, mecânicas, banimentos ou erratas DEVE conter uma citação clara no formato: [Fonte: <Nome do Documento / Rulings>, Página: <Págs/Link>].
5. Mantenha um tom profissional, imparcial e preciso, idêntico ao de um juiz principal de torneio oficial.

CONTEXTO RECUPERADO:
{context}

PERGUNTA DO USUÁRIO:
{query}

RESPOSTA DO JUIZ:
"""

    def format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Format list of retrieved chunks into structured context text."""
        formatted_blocks = []
        for idx, item in enumerate(chunks, start=1):
            meta = item.chunk.metadata
            source_info = f"{meta.document_title} ({meta.source.value})"
            if meta.page_number:
                source_info += f" - Pág. {meta.page_number}"
            if meta.card_name:
                source_info += f" - Carta: {meta.card_name}"
            
            formatted_blocks.append(
                f"--- DOCUMENTO [{idx}] ---\n"
                f"Fonte: {source_info}\n"
                f"Conteúdo:\n{item.chunk.text}\n"
            )
        return "\n".join(formatted_blocks)

    def build_prompt(self, query: str, chunks: list[RetrievedChunk]) -> str:
        """Construct complete prompt with formatted context."""
        context_str = self.format_context(chunks)
        return self.SYSTEM_PROMPT.format(context=context_str, query=query)
