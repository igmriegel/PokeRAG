"""
Prometheus metrics collector for monitoring the API and feedback flow.
"""

from __future__ import annotations

from collections.abc import Iterable

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Histogram

QUERY_COUNTER_NAME = "pokemon_rag_queries_total"
QUERY_LATENCY_NAME = "pokemon_rag_query_latency_seconds"
RETRIEVED_DOCS_NAME = "pokemon_rag_retrieved_docs_count"
FEEDBACK_COUNTER_NAME = "pokemon_rag_feedback_total"
SOURCE_COUNTER_NAME = "pokemon_rag_query_sources_total"
GUARDRAIL_REJECTION_COUNTER_NAME = "pokemon_rag_guardrail_rejections_total"
PROVIDER_TOKEN_COUNTER_NAME = "pokemon_rag_provider_tokens_total"
PROVIDER_COST_COUNTER_NAME = "pokemon_rag_provider_cost_usd_total"


class MetricsCollector:
    """Encapsulates the Prometheus metrics used by the API."""

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry or CollectorRegistry()
        self.query_counter = Counter(
            QUERY_COUNTER_NAME,
            "Total number of RAG queries processed",
            labelnames=("model", "status"),
            registry=self.registry,
        )
        self.query_latency = Histogram(
            QUERY_LATENCY_NAME,
            "Latency of query execution in seconds",
            buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
            registry=self.registry,
        )
        self.retrieved_docs = Histogram(
            RETRIEVED_DOCS_NAME,
            "Number of context documents retrieved per query",
            buckets=(0, 1, 2, 3, 5, 10, 20),
            registry=self.registry,
        )
        self.feedback_counter = Counter(
            FEEDBACK_COUNTER_NAME,
            "User feedback count by rating type",
            labelnames=("rating",),
            registry=self.registry,
        )
        self.source_counter = Counter(
            SOURCE_COUNTER_NAME,
            "Distribution of sources seen in queried answers",
            labelnames=("source",),
            registry=self.registry,
        )
        self.guardrail_rejections = Counter(
            GUARDRAIL_REJECTION_COUNTER_NAME,
            "API guardrail rejections by low-cardinality reason",
            labelnames=("reason",),
            registry=self.registry,
        )
        self.provider_tokens = Counter(
            PROVIDER_TOKEN_COUNTER_NAME,
            "LLM provider tokens observed by model and stage",
            labelnames=("model", "stage"),
            registry=self.registry,
        )
        self.provider_cost = Counter(
            PROVIDER_COST_COUNTER_NAME,
            "Estimated LLM provider cost in USD by model and stage",
            labelnames=("model", "stage"),
            registry=self.registry,
        )

    def record_query(
        self,
        model: str,
        latency: float,
        num_docs: int,
        status: str = "success",
        sources: Iterable[str] | None = None,
    ) -> None:
        """Record a query observation."""
        self.query_counter.labels(model=model, status=status).inc()
        self.query_latency.observe(max(0.0, latency))
        self.retrieved_docs.observe(max(0, num_docs))
        if sources:
            for source in sources:
                cleaned = source.strip()
                if cleaned:
                    self.source_counter.labels(source=cleaned).inc()

    def record_feedback(self, rating: int) -> None:
        """Record a user feedback observation."""
        label = "positive" if rating > 0 else "negative"
        self.feedback_counter.labels(rating=label).inc()

    def record_guardrail_rejection(self, reason: str) -> None:
        """Record a rejected request without logging sensitive payload details."""
        self.guardrail_rejections.labels(reason=reason).inc()

    def record_provider_usage(
        self,
        *,
        model: str,
        stage: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
    ) -> None:
        """Record model token and cost usage with bounded labels."""
        total_tokens = max(0, prompt_tokens) + max(0, completion_tokens)
        self.provider_tokens.labels(model=model, stage=stage).inc(total_tokens)
        self.provider_cost.labels(model=model, stage=stage).inc(max(0.0, cost_usd))


DEFAULT_METRICS_COLLECTOR = MetricsCollector(registry=REGISTRY)
