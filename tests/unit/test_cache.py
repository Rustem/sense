"""Tests for InMemoryCache."""

import time

from sense.core.cache import InMemoryCache


def test_cache_set_and_get() -> None:
    """Test basic cache set and get."""
    cache = InMemoryCache(ttl_seconds=60)
    cache.set("key1", "value1")

    assert cache.get("key1") == "value1"
    assert cache.get("nonexistent") is None


def test_cache_expiration() -> None:
    """Test cache entry expires after TTL."""
    cache = InMemoryCache(ttl_seconds=1)
    cache.set("key1", "value1")

    assert cache.get("key1") == "value1"

    time.sleep(1.1)
    assert cache.get("key1") is None


def test_cache_clear() -> None:
    """Test cache clear removes all entries."""
    cache = InMemoryCache(ttl_seconds=60)
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    cache.clear()

    assert cache.get("key1") is None
    assert cache.get("key2") is None
