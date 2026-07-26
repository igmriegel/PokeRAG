"""
Token-aware document chunking.
"""

from __future__ import annotations

import re

from pokemon_tcg_rag.domain.models import Chunk, Document, DocumentSource


class DocumentChunker:
    """Split normalized documents into deterministic chunks."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size and chunk_size > 1:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Document) -> list[Chunk]:
        """Chunk a document into deterministic windows of whitespace tokens."""
        tokens = self._tokenize(document.content)
        if not tokens:
            return []

        if document.metadata.source == DocumentSource.POKEGYM:
            return [
                self._build_chunk(
                    document=document,
                    index=0,
                    token_window=tokens,
                )
            ]

        chunks: list[Chunk] = []
        start = 0
        index = 0
        step = max(1, self.chunk_size - self.chunk_overlap)

        while start < len(tokens):
            token_window = tokens[start : start + self.chunk_size]
            if not token_window:
                break
            chunks.append(
                self._build_chunk(
                    document=document,
                    index=index,
                    token_window=token_window,
                )
            )
            index += 1
            if len(token_window) < self.chunk_size:
                break
            start += step

        return chunks

    def _build_chunk(
        self, document: Document, index: int, token_window: list[str]
    ) -> Chunk:
        text = " ".join(token_window).strip()
        return Chunk(
            chunk_id=f"{document.doc_id}#{index}",
            document_id=document.doc_id,
            text=text,
            token_count=len(token_window),
            metadata=document.metadata,
        )

    def _tokenize(self, text: str) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text.strip())
        return cleaned.split(" ") if cleaned else []
