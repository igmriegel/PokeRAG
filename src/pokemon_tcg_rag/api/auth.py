"""
Bearer-token authentication and authorization helpers.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from pokemon_tcg_rag.config.settings import Settings, get_settings

_ALLOWED_ALGORITHMS = {"HS256"}
_CURRENT_PRINCIPAL: Principal | None = None
_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated caller identity and authorization scopes."""

    subject: str
    issuer: str
    audience: str
    scopes: frozenset[str]
    token_id: str | None = None

    def has_scopes(self, required_scopes: tuple[str, ...]) -> bool:
        return all(scope in self.scopes for scope in required_scopes)


def create_access_token(
    subject: str,
    *,
    secret: str,
    issuer: str,
    audience: str,
    scopes: tuple[str, ...],
    lifetime_seconds: int = 3600,
    algorithm: str = "HS256",
) -> str:
    """Create a signed JWT for tests and local development."""
    if algorithm not in _ALLOWED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    header = {"alg": algorithm, "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": subject,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + lifetime_seconds,
        "scope": " ".join(scopes),
    }
    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_segment}.{payload_segment}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"


def authorize_request(*required_scopes: str) -> Callable[[Request], Principal]:
    """Return a FastAPI dependency enforcing bearer auth and scope checks."""

    def dependency(request: Request) -> Principal:
        global _CURRENT_PRINCIPAL
        settings = get_settings()
        if not settings.API_AUTH_SECRET.strip() and settings.ENVIRONMENT != "production":
            principal = Principal(
                subject="anonymous",
                issuer=settings.API_AUTH_ISSUER,
                audience=settings.API_AUTH_AUDIENCE,
                scopes=frozenset({"rag:query", "rag:feedback", "rag:metrics", "rag:diagnostics"}),
            )
            request.state.principal = principal
            _CURRENT_PRINCIPAL = principal
            return principal

        token_value = _extract_bearer_token(request.headers.get("authorization"))
        if token_value is None:
            _raise_unauthorized("Missing bearer token")
        token_value = cast(str, token_value)

        principal = decode_access_token(
            token_value,
            settings=settings,
            required_algorithms={settings.API_AUTH_ALGORITHM},
        )
        if not principal.has_scopes(required_scopes):
            _raise_forbidden("Insufficient scope")
        request.state.principal = principal
        _CURRENT_PRINCIPAL = principal
        return principal

    return dependency


def decode_access_token(
    token: str,
    *,
    settings: Settings | None = None,
    required_algorithms: set[str] | None = None,
) -> Principal:
    """Decode and validate a signed JWT bearer token."""
    active_settings = settings or get_settings()
    if not active_settings.API_AUTH_SECRET.strip() and active_settings.ENVIRONMENT != "production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    parts = token.split(".")
    if len(parts) != 3:
        _raise_unauthorized("Malformed bearer token")

    header = _decode_json_segment(parts[0], "header")
    payload = _decode_json_segment(parts[1], "payload")

    algorithm = str(header.get("alg", "")).strip()
    if not algorithm or algorithm not in (required_algorithms or _ALLOWED_ALGORITHMS):
        _raise_unauthorized("Unsupported token algorithm")
    if algorithm not in _ALLOWED_ALGORITHMS:
        _raise_unauthorized("Unsupported token algorithm")

    expected_signature = _sign_token(parts[0], parts[1], active_settings.API_AUTH_SECRET)
    provided_signature = _b64url_decode(parts[2])
    if not hmac.compare_digest(expected_signature, provided_signature):
        _raise_unauthorized("Invalid bearer token signature")

    issuer = str(payload.get("iss", "")).strip()
    audience = str(payload.get("aud", "")).strip()
    subject = str(payload.get("sub", "")).strip()
    if issuer != active_settings.API_AUTH_ISSUER:
        _raise_forbidden("Invalid token issuer")
    if audience != active_settings.API_AUTH_AUDIENCE:
        _raise_forbidden("Invalid token audience")
    if not subject:
        _raise_unauthorized("Missing subject claim")

    expires_at = int(payload.get("exp", 0))
    issued_at = int(payload.get("iat", 0))
    now = int(time.time())
    if issued_at and issued_at > now + 30:
        _raise_unauthorized("Token not yet valid")
    if expires_at <= now:
        _raise_unauthorized("Token expired")

    scopes = _normalize_scopes(payload.get("scope"))
    return Principal(
        subject=subject,
        issuer=issuer,
        audience=audience,
        scopes=frozenset(scopes),
        token_id=str(payload.get("jti")) if payload.get("jti") else None,
    )


def _normalize_scopes(raw_scopes: Any) -> tuple[str, ...]:
    if raw_scopes is None:
        return ()
    if isinstance(raw_scopes, str):
        return tuple(scope for scope in raw_scopes.split() if scope)
    if isinstance(raw_scopes, list):
        return tuple(str(scope).strip() for scope in raw_scopes if str(scope).strip())
    return ()


def _decode_json_segment(segment: str, name: str) -> dict[str, Any]:
    try:
        payload = _b64url_decode(segment)
        return cast(dict[str, Any], json.loads(payload.decode("utf-8")))
    except Exception as exc:  # pragma: no cover - decoding boundary
        _raise_unauthorized(f"Invalid JWT {name}")
        raise exc


def _sign_token(header_segment: str, payload_segment: str, secret: str) -> bytes:
    signing_input = f"{header_segment}.{payload_segment}".encode()
    return hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _raise_unauthorized(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _raise_forbidden(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def get_current_principal() -> Principal | None:
    """Return the principal associated with the active request, if any."""
    return _CURRENT_PRINCIPAL


def bearer_scheme() -> HTTPBearer:
    """Expose the bearer scheme for OpenAPI security declarations."""
    return _bearer_scheme


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return None
    cleaned = token.strip()
    return cleaned or None
