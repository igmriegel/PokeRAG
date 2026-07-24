"""
Pydantic wire schemas for the public API.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pokemon_tcg_rag.domain.models import AnswerResponse, DocumentMetadata, RetrievedChunk


class QueryRequest(BaseModel):
    """Payload for the query endpoint."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        ...,
        min_length=1,
        max_length=512,
        examples=["Posso usar Rare Candy no primeiro turno?"],
    )
    top_k: int = Field(default=5, ge=1, le=10)
    metadata_filters: dict[str, str] | None = Field(default=None)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be empty")
        return value.strip()

    @field_validator("metadata_filters")
    @classmethod
    def metadata_filters_must_be_allowlisted(
        cls, value: dict[str, str] | None
    ) -> dict[str, str] | None:
        if value is None:
            return None
        allowed_keys = {"source", "rule_type", "document_title", "card_name", "page_number"}
        cleaned: dict[str, str] = {}
        for key, item in value.items():
            cleaned_key = key.strip()
            cleaned_value = str(item).strip()
            if cleaned_key in allowed_keys and cleaned_value:
                cleaned[cleaned_key] = cleaned_value
        return cleaned or None


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
    def from_metadata(cls, metadata: DocumentMetadata) -> CitationSchema:
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
            text=_truncate_text(item.chunk.text),
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


def _truncate_text(text: str, limit: int = 320) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


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
    def from_answer_response(
        cls, response: AnswerResponse, query_id: str | None = None
    ) -> QueryResponse:
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

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    rating: int = Field(..., description="1 for thumbs up, -1 for thumbs down")
    comment: str | None = Field(default=None, max_length=1000)
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
