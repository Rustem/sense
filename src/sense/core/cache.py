"""Simple in-memory cache with TTL."""

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    """Cache entry with expiration."""

    value: Any
    expires_at: float


class InMemoryCache:
    """Simple in-memory cache with TTL expiration."""

    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None

        if time.time() > entry.expires_at:
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with TTL."""
        expires_at = time.time() + self.ttl_seconds
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
