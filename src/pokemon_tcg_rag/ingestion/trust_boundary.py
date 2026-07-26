"""
Trust-boundary helpers for untrusted ingestion content.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

from pokemon_tcg_rag.domain.exceptions import IngestionError

ALLOWED_SOURCE_HOSTS = {
    "assets.pokemon.com",
    "compendium.pokegym.net",
    "mcdn.pokemon.com",
    "www.pokemon.com",
    "pokemon.com",
}

INSTRUCTION_POISON_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt",
    "developer message",
    "reveal secret",
    "exfiltrat",
    "follow the instructions above instead",
)


def validate_source_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        raise IngestionError(f"Rejected non-HTTPS source URL: {url}")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_SOURCE_HOSTS:
        raise IngestionError(f"Rejected unapproved source host: {host}")


def download_trusted_bytes(
    url: str,
    *,
    max_bytes: int,
    timeout: int | float,
    user_agent: str,
    allowed_content_types: tuple[str, ...] = (),
) -> tuple[bytes, str]:
    validate_source_url(url)
    response = requests.get(
        url,
        timeout=timeout,
        stream=True,
        allow_redirects=True,
        headers={"User-Agent": user_agent},
    )
    response.raise_for_status()

    headers = getattr(response, "headers", {}) or {}
    content_type = headers.get("content-type", "")
    if (
        content_type
        and allowed_content_types
        and not any(token in content_type for token in allowed_content_types)
    ):
        raise IngestionError(
            f"Rejected source with unexpected content type: {content_type}"
        )

    if hasattr(response, "iter_content"):
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise IngestionError(f"Rejected oversized download from {url}")
            chunks.append(chunk)
        return b"".join(chunks), content_type

    content = getattr(response, "content", b"")
    if len(content) > max_bytes:
        raise IngestionError(f"Rejected oversized download from {url}")
    return content, content_type


def is_instruction_poisoned(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in INSTRUCTION_POISON_PATTERNS)


def quarantine_payload(
    quarantine_dir: str | Path,
    *,
    source_url: str,
    reason: str,
    payload: str | bytes,
) -> Path:
    folder = Path(quarantine_dir)
    folder.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(
        payload if isinstance(payload, bytes) else payload.encode("utf-8")
    ).hexdigest()
    path = folder / f"quarantine_{timestamp}_{digest[:12]}.txt"
    body = (
        payload.decode("utf-8", errors="ignore")
        if isinstance(payload, bytes)
        else payload
    )
    path.write_text(
        "\n".join(
            [
                f"source_url={source_url}",
                f"reason={reason}",
                f"captured_at={timestamp}",
                "",
                body,
            ]
        ),
        encoding="utf-8",
    )
    return path
