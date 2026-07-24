"""
Pydantic wire schemas for the public API.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pokemon_tcg_rag.domain.models import AnswerResponse, RetrievedChunk


class QueryRequest(BaseModel):
    """Payload for the query endpoint."""

    question: str = Field(..., min_length=1, examples=["Posso usar Rare Candy no primeiro turno?"])
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be empty")
        return value.strip()


class CitationSchema(BaseModel):
    """Citation metadata for an answer."""

    model_config = ConfigDict(from_attributes=True)

    source: str
    document_title: str
    page_number: int | None = None
    rule_type: str
    card_name: str | None = None
    publication_date: str | None = None
    source_url: str | None = None

    @classmethod
    def from_metadata(cls, metadata) -> CitationSchema:
        return cls(
            source=metadata.source.value,
            document_title=metadata.document_title,
            page_number=metadata.page_number,
            rule_type=metadata.rule_type.value,
            card_name=metadata.card_name,
            publication_date=metadata.publication_date,
            source_url=metadata.source_url,
        )


class ChunkSnippetSchema(BaseModel):
    """Short snippet of a retrieved chunk."""

    chunk_id: str
    text: str
    score: float
    retrieval_method: str
    source: str
    document_title: str
    page_number: int | None = None
    rule_type: str
    card_name: str | None = None
    publication_date: str | None = None
    source_url: str | None = None

    @classmethod
    def from_retrieved_chunk(cls, item: RetrievedChunk) -> ChunkSnippetSchema:
        metadata = item.chunk.metadata
        return cls(
            chunk_id=item.chunk.chunk_id,
            text=item.chunk.text,
            score=item.score,
            retrieval_method=item.retrieval_method,
            source=metadata.source.value,
            document_title=metadata.document_title,
            page_number=metadata.page_number,
            rule_type=metadata.rule_type.value,
            card_name=metadata.card_name,
            publication_date=metadata.publication_date,
            source_url=metadata.source_url,
        )


class QueryResponse(BaseModel):
    """Public API response for an answer."""

    query_id: str
    query: str
    rewritten_query: str | None = None
    answer: str
    citations: list[CitationSchema]
    retrieved_chunks: list[ChunkSnippetSchema]
    model_name: str
    latency_seconds: float

    @classmethod
    def from_answer_response(cls, response: AnswerResponse, query_id: str | None = None) -> QueryResponse:
        return cls(
            query_id=query_id or response.query_id or "",
            query=response.query,
            rewritten_query=response.rewritten_query,
            answer=response.answer,
            citations=[CitationSchema.from_metadata(item) for item in response.citations],
            retrieved_chunks=[
                ChunkSnippetSchema.from_retrieved_chunk(item) for item in response.retrieved_chunks
            ],
            model_name=response.model_name,
            latency_seconds=response.latency_seconds,
        )


class FeedbackRequest(BaseModel):
    """Payload submitted by the UI and client for feedback persistence."""

    query_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    rating: int = Field(..., description="1 for thumbs up, -1 for thumbs down")
    comment: str | None = None
    model_name: str = Field(..., min_length=1)
    latency_seconds: float = Field(..., ge=0)

    @field_validator("query", "answer", "model_name")
    @classmethod
    def text_fields_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value.strip()

    @field_validator("rating")
    @classmethod
    def rating_must_be_binary(cls, value: int) -> int:
        if value not in (-1, 1):
            raise ValueError("rating must be either 1 or -1")
        return value


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str
    version: str
    rag_chain_ready: bool
    feedback_store_ready: bool
