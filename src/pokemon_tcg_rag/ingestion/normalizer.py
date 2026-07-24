"""
Document Normalization Engine.
"""

import re
from pokemon_tcg_rag.domain.models import Document


class DocumentNormalizer:
    """Normalizes extracted text, removes extra whitespace, standardizes terminology."""

    def normalize(self, document: Document) -> Document:
        """Clean and normalize document content while preserving metadata."""
        text = document.content
        # Remove repeated newlines and whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        # Standardize card terms
        text = text.replace("Pokémon", "Pokemon")
        text = text.strip()

        document.content = text
        return document
