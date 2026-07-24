"""
FastAPI Main Application Entrypoint.
"""

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from pokemon_tcg_rag.api.routes import router
from pokemon_tcg_rag.api.schemas import HealthResponse
from pokemon_tcg_rag.monitoring.logger import setup_logging

setup_logging()

app = FastAPI(
    title="Pokemon TCG Rules RAG Expert API",
    description="REST API for querying Pokemon TCG Official Rules, Errata, and Pokegym Compendium Rulings",
    version="0.1.0"
)

# Prometheus metrics endpoint at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Service liveness probe endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")
