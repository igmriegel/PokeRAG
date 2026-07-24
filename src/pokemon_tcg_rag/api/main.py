"""
FastAPI application entrypoint.
"""

from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from pokemon_tcg_rag.api.routes import dependency_status, router
from pokemon_tcg_rag.api.schemas import HealthResponse
from pokemon_tcg_rag.monitoring.logger import setup_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()
    app = FastAPI(
        title="Pokemon TCG Rules RAG Expert API",
        description="REST API for querying Pokemon TCG official rules and rulings",
        version="0.1.0",
    )
    app.mount("/metrics", make_asgi_app())
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()


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
