"""
FastAPI application entrypoint.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from pokemon_tcg_rag.api.routes import dependency_status, router
from pokemon_tcg_rag.api.runtime import app_lifespan
from pokemon_tcg_rag.api.schemas import HealthResponse
from pokemon_tcg_rag.monitoring.logger import setup_logging
from pokemon_tcg_rag.monitoring.metrics_collector import DEFAULT_METRICS_COLLECTOR


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()
    app = FastAPI(
        title="Pokemon TCG Rules RAG Expert API",
        description="REST API for querying Pokemon TCG official rules and rulings",
        version="0.1.0",
        lifespan=app_lifespan,
    )
    app.include_router(router, prefix="/api/v1")

    @app.get("/metrics")
    def metrics() -> Response:
        """Expose Prometheus metrics for scraping."""
        payload = generate_latest(DEFAULT_METRICS_COLLECTOR.registry)
        return Response(content=payload, media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()


@app.get("/live")
def live() -> dict[str, str]:
    """Expose a liveness probe that only checks process availability."""
    return {"status": "alive", "version": "0.1.0"}


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Expose a root health check for external probes."""
    rag_ready, feedback_ready = dependency_status()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        rag_chain_ready=rag_ready,
        feedback_store_ready=feedback_ready,
    )


@app.get("/ready", response_model=HealthResponse)
def ready_check() -> HealthResponse:
    """Expose a readiness probe that reflects dependency availability."""
    rag_ready, feedback_ready = dependency_status()
    status = "healthy" if rag_ready and feedback_ready else "degraded"
    return HealthResponse(
        status=status,
        version="0.1.0",
        rag_chain_ready=rag_ready,
        feedback_store_ready=feedback_ready,
    )
