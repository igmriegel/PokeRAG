"""
Monitoring package for Prometheus metrics export, structured logging, and feedback persistence.
"""

from pokemon_tcg_rag.monitoring.logger import get_logger, setup_logging

__all__ = ["setup_logging", "get_logger"]

# MetricsCollector and FeedbackStore are imported lazily to avoid requiring
# prometheus_client and sqlalchemy at import time in environments where
# those optional dependencies are not installed.
