"""
Safe retrieval result cache.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass

from pokemon_tcg_rag.domain.models import RetrievedChunk


@dataclass(slots=True)
class CacheEntry:
    value: list[RetrievedChunk]
    expires_at: float


class RetrievalCache:
    """TTL-bound cache with content-addressed keys and bounded capacity."""

    def __init__(self, max_items: int, ttl_seconds: int) -> None:
        self.max_items = max(1, max_items)
        self.ttl_seconds = max(1, ttl_seconds)
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()

    def make_key(self, **parts: object) -> str:
        payload = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> list[RetrievedChunk] | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.time():
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return [item.model_copy(deep=True) for item in entry.value]

    def set(self, key: str, value: list[RetrievedChunk]) -> None:
        self._entries[key] = CacheEntry(
            value=[item.model_copy(deep=True) for item in value],
            expires_at=time.time() + self.ttl_seconds,
        )
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_items:
            self._entries.popitem(last=False)
