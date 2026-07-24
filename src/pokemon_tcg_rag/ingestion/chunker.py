"""
Text Chunking Engine (Fixed & Semantic Chunking).
"""

import hashlib
from pokemon_tcg_rag.domain.models import Chunk, Document


class DocumentChunker:
    """Splits normalized documents into chunks with rich metadata propagation."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Document) -> list[Chunk]:
        """Chunk a document into segments of fixed token/word length with overlap."""
        chunks: list[Chunk] = []
        words = document.content.split()
        if not words:
            return chunks

        start = 0
        chunk_idx = 0
        while start < len(words):
            end = start + self.chunk_size
            segment_words = words[start:end]
            segment_text = " ".join(segment_words)
            
            chunk_hash = hashlib.md5(f"{document.doc_id}_{chunk_idx}_{segment_text[:50]}".encode()).hexdigest()
            
            chunk = Chunk(
                chunk_id=f"{document.doc_id}_chunk_{chunk_hash[:8]}",
                doc_id=document.doc_id,
                text=segment_text,
                token_count=len(segment_words),
                metadata=document.metadata
            )
            chunks.append(chunk)
            
            chunk_idx += 1
            start += (self.chunk_size - self.chunk_overlap)
            if start >= len(words):
                break

        return chunks
