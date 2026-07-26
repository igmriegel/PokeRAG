"""
FastAPI application entrypoint.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from pokemon_tcg_rag.api.auth import authorize_request
from pokemon_tcg_rag.api.routes import dependency_status, router
from pokemon_tcg_rag.api.runtime import app_lifespan
from pokemon_tcg_rag.api.schemas import HealthResponse
from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import PokemonRAGError
from pokemon_tcg_rag.monitoring.logger import get_logger, setup_logging
from pokemon_tcg_rag.monitoring.metrics_collector import DEFAULT_METRICS_COLLECTOR
from pokemon_tcg_rag.monitoring.tracing import initialize_tracing

LOGGER = get_logger(__name__)


def live() -> dict[str, str]:
    """Expose a liveness probe that only checks process availability."""
    return {"status": "alive", "version": "0.1.0"}


def health_check() -> HealthResponse:
    """Expose a root health check for external probes."""
    rag_ready, feedback_ready = dependency_status()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        rag_chain_ready=rag_ready,
        feedback_store_ready=feedback_ready,
    )


def ready_check() -> HealthResponse:
    """Expose a readiness probe that reflects dependency availability."""
    rag_ready, feedback_ready = dependency_status()
    if not rag_ready or not feedback_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dependencies not ready",
        )
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        rag_chain_ready=rag_ready,
        feedback_store_ready=feedback_ready,
    )


def _register_root_routes(app: FastAPI) -> None:
    app.get("/live")(live)
    app.get("/health", response_model=HealthResponse)(health_check)
    app.get(
        "/ready",
        response_model=HealthResponse,
        dependencies=[Depends(authorize_request("rag:diagnostics"))],
    )(ready_check)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()
    initialize_tracing()
    settings = get_settings()
    app = FastAPI(
        title="Pokemon TCG Rules RAG Expert API",
        description="REST API for querying Pokemon TCG official rules and rulings",
        version="0.1.0",
        lifespan=app_lifespan,
    )
    allowed_origins = [
        origin.strip()
        for origin in settings.API_CORS_ALLOWED_ORIGINS.split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(router, prefix="/api/v1")
    _register_root_routes(app)

    @app.middleware("http")
    async def request_size_limiter(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Reject oversized request bodies before model validation or provider calls."""
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if (
                content_length is not None
                and content_length.isdigit()
                and int(content_length) > settings.API_MAX_BODY_BYTES
            ):
                return Response(status_code=413, content="Request body too large")
        return await call_next(request)

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Attach conservative security headers to API responses."""
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        return response

    @app.exception_handler(PokemonRAGError)
    async def pokemon_rag_error_handler(_: Request, exc: PokemonRAGError) -> Response:
        """Return a stable error envelope while keeping details server-side."""
        error_id = uuid.uuid4().hex[:8]
        LOGGER.exception(
            "domain_error",
            extra={"error_id": error_id, "error_type": exc.__class__.__name__},
        )
        return Response(
            content=f'{{"detail":"Request failed","error_id":"{error_id}"}}',
            media_type="application/json",
            status_code=500,
        )

    @app.get("/metrics", dependencies=[Depends(authorize_request("rag:metrics"))])
    def metrics() -> Response:
        """Expose Prometheus metrics for scraping."""
        payload = generate_latest(DEFAULT_METRICS_COLLECTOR.registry)
        return Response(content=payload, media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
