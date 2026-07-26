"""
API request guardrails for payload, rate and concurrency control.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, Request, status

from pokemon_tcg_rag.api.auth import Principal
from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.monitoring.metrics_collector import DEFAULT_METRICS_COLLECTOR


class APIRequestGuard:
    """In-memory guardrail state for API admission control."""

    def __init__(
        self,
        rate_limit_per_minute: int,
        max_concurrent_requests: int,
        max_body_bytes: int,
    ) -> None:
        self.rate_limit_per_minute = rate_limit_per_minute
        self.max_body_bytes = max_body_bytes
        self._inflight = threading.BoundedSemaphore(max(1, max_concurrent_requests))
        self._recent_requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def enforce_request_size(self, request: Request) -> None:
        """Reject oversized request bodies before downstream processing."""
        if request.method not in {"POST", "PUT", "PATCH"}:
            return

        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_body_bytes:
                    self._record_rejection("body_too_large")
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Request body too large",
                    )
            except ValueError:
                self._record_rejection("bad_content_length")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Content-Length header",
                ) from None

    @contextmanager
    def admit(
        self, principal: Principal, request: Request | None, operation: str
    ) -> Iterator[None]:
        """Enforce rate and concurrency limits around an API operation."""
        self._enforce_rate(principal, request, operation)
        acquired = self._inflight.acquire(blocking=False)
        if not acquired:
            self._record_rejection("concurrency_limit")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many concurrent requests",
            )
        try:
            yield
        finally:
            self._inflight.release()

    def _enforce_rate(self, principal: Principal, request: Request | None, operation: str) -> None:
        key = self._principal_key(principal, request, operation)
        now = time.monotonic()
        with self._lock:
            window = self._recent_requests[key]
            while window and now - window[0] > 60.0:
                window.popleft()
            if len(window) >= self.rate_limit_per_minute:
                self._record_rejection("rate_limit")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                )
            window.append(now)

    def _principal_key(self, principal: Principal, request: Request | None, operation: str) -> str:
        client_host = request.client.host if request and request.client else "local"
        return f"{principal.subject}:{client_host}:{operation}"

    def _record_rejection(self, reason: str) -> None:
        DEFAULT_METRICS_COLLECTOR.record_guardrail_rejection(reason)


def build_request_guard() -> APIRequestGuard:
    """Build a request guard from application settings."""
    settings = get_settings()
    return APIRequestGuard(
        rate_limit_per_minute=settings.API_RATE_LIMIT_PER_MINUTE,
        max_concurrent_requests=settings.API_MAX_CONCURRENT_REQUESTS,
        max_body_bytes=settings.API_MAX_BODY_BYTES,
    )


DEFAULT_REQUEST_GUARD = build_request_guard()
