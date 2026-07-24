"""
API OpenAPI Request & Response Schemas.
"""

from typing import Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Payload for RAG question query endpoint."""
    question: str = Field(..., example="Posso usar a carta Rare Candy no primeiro turno do jogo?")
    top_k: int = Field(default=5, ge=1, le=20)


class CitationSchema(BaseModel):
    """Source document citation metadata schema."""
    source: str
    document_title: str
    page_number: int | None = None
    rule_type: str
    card_name: str | None = None


class ChunkSnippetSchema(BaseModel):
    """Snippet of retrieved chunk content."""
    chunk_id: str
    text: str
    score: float
    retrieval_method: str


class QueryResponse(BaseModel):
    """Full RAG answer response API schema."""
    query: str
    rewritten_query: str | None = None
    answer: str
    citations: list[CitationSchema]
    retrieved_chunks: list[ChunkSnippetSchema]
    model_name: str
    latency_seconds: float


class FeedbackRequest(BaseModel):
    """User feedback submission payload."""
    query: str
    answer: str
    rating: int = Field(..., description="1 for thumbs up, -1 for thumbs down")
    comment: str | None = None
    model_name: str
    latency_seconds: float


class HealthResponse(BaseModel):
    """API health status response."""
    status: str
    version: str
