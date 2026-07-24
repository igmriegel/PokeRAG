"""
Prometheus Metrics Collector for Grafana Dashboard integration.
"""

from prometheus_client import Counter, Histogram

# Metric Definitions
QUERY_COUNTER = Counter(
    "pokemon_rag_queries_total",
    "Total number of RAG queries processed",
    ["model", "status"]
)

LATENCY_HISTOGRAM = Histogram(
    "pokemon_rag_query_latency_seconds",
    "Latency of query execution in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

FEEDBACK_COUNTER = Counter(
    "pokemon_rag_user_feedback_total",
    "User feedback count by rating type",
    ["rating_type"]  # 'positive' or 'negative'
)

RETRIEVED_DOCS_HISTOGRAM = Histogram(
    "pokemon_rag_retrieved_docs_count",
    "Number of context documents retrieved per query",
    buckets=[1, 3, 5, 10, 20]
)


class MetricsCollector:
    """Helper class to update Prometheus metrics."""

    @staticmethod
    def record_query(model: str, latency: float, num_docs: int, status: str = "success") -> None:
        QUERY_COUNTER.labels(model=model, status=status).inc()
        LATENCY_HISTOGRAM.observe(latency)
        RETRIEVED_DOCS_HISTOGRAM.observe(num_docs)

    @staticmethod
    def record_feedback(rating: int) -> None:
        rating_type = "positive" if rating > 0 else "negative"
        FEEDBACK_COUNTER.labels(rating_type=rating_type).inc()
