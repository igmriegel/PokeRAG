# Monitoring Module (`monitoring/`)

This directory contains observability, logging, and metrics exporter code:
- `logger.py`: Structured JSON log configuration using structlog.
- `metrics_collector.py`: Prometheus metrics counters and latency histograms.
- `feedback_store.py`: Feedback collector persisting user ratings to Postgres and updating metrics.
