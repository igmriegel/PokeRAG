"""
Unit tests for PromptTemplateManager.

NOTE: PromptTemplateManager is implemented in Sprint 2 (TASK-014).
These tests are placeholders that will be activated once the llm.prompts
module is fully implemented.
"""

import pytest

pytest.importorskip(
    "pokemon_tcg_rag.llm.prompts",
    reason="PromptTemplateManager not yet implemented (Sprint 2 / TASK-014)",
)

from pokemon_tcg_rag.domain.models import Chunk, RetrievedChunk  # noqa: E402
from pokemon_tcg_rag.llm.prompts import PromptTemplateManager  # noqa: E402


@pytest.mark.unit
def test_prompt_template_formatting(sample_chunk: Chunk) -> None:
    manager = PromptTemplateManager()
    chunk_item = RetrievedChunk(chunk=sample_chunk, score=0.95, retrieval_method="dense")
    prompt = manager.build_prompt("Rare Candy question?", [chunk_item])
    assert "Juiz Certificado Oficial" in prompt
    assert "Rare Candy" in prompt
    assert "Official Rulebook" in prompt
