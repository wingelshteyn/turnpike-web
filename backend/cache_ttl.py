"""Простой async TTL-кэш для справочников (снижает число повторных запросов к внешнему API)."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


class AsyncTTLCache:
    """Кэш с TTL и защитой от гонок при одновременных запросах к одному ключу."""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock_for(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def get_or_fetch(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        now = time.time()
        if key in self._store and now - self._store[key][0] < self._ttl:
            return self._store[key][1]
        async with self._lock_for(key):
            now = time.time()
            if key in self._store and now - self._store[key][0] < self._ttl:
                return self._store[key][1]
            value = await factory()
            self._store[key] = (time.time(), value)
            return value

    def invalidate_prefix(self, prefix: str) -> None:
        """Удалить все ключи, начинающиеся с prefix (после изменения справочника)."""
        to_del = [k for k in self._store if k.startswith(prefix)]
        for k in to_del:
            self._store.pop(k, None)
