"""Cached Materials Project entry retrieval without Qt state."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from pymatgen.core import Element

from pourbaix_core import FetchResult, fetch_pourbaix_entries


class EntryProvider(Protocol):
    def fetch(self, elements: Sequence[str], api_key: str) -> FetchResult: ...


@dataclass(frozen=True)
class CacheDiagnostics:
    cache_items: int
    last_entries_count: int
    last_used_sanitation_retry: bool
    last_fetch_seconds: float
    oldest_cache_age_seconds: float | None


@dataclass(frozen=True)
class _CacheItem:
    result: FetchResult
    stored_at: float


class MPResterEntryProvider:
    """Call mp-api and delegate the known-ion retry to the proven R3 helper."""

    def __init__(self, mpr_factory: Callable[[str], Any] | None = None):
        self._mpr_factory = mpr_factory

    def fetch(self, elements: Sequence[str], api_key: str) -> FetchResult:
        factory = self._mpr_factory
        if factory is None:
            from mp_api.client import MPRester

            factory = MPRester
        with factory(api_key) as mpr:
            return fetch_pourbaix_entries(mpr, list(elements))


class CachedEntryService:
    """Five-minute entry cache keyed only by canonical chemical system."""

    def __init__(
        self,
        provider: EntryProvider,
        *,
        clock: Callable[[], float] = time.monotonic,
        ttl_seconds: float = 300.0,
    ):
        self._provider = provider
        self._clock = clock
        self._ttl_seconds = ttl_seconds
        self._cache: dict[tuple[str, ...], _CacheItem] = {}
        self._last_entries_count = 0
        self._last_used_sanitation_retry = False
        self._last_fetch_seconds = 0.0

    @staticmethod
    def _cache_key(elements: Sequence[str]) -> tuple[str, ...]:
        return tuple(sorted(Element(str(element).strip().capitalize()).symbol for element in elements))

    def fetch(self, elements: Sequence[str], api_key: str) -> FetchResult:
        key = self._cache_key(elements)
        now = self._clock()
        cached = self._cache.get(key)
        if cached is not None and now - cached.stored_at <= self._ttl_seconds:
            self._last_entries_count = len(cached.result.entries)
            self._last_used_sanitation_retry = cached.result.used_sanitation_retry
            self._last_fetch_seconds = 0.0
            return cached.result

        started = now
        result = self._provider.fetch(key, api_key)
        finished = self._clock()
        self._cache[key] = _CacheItem(result=result, stored_at=finished)
        self._last_entries_count = len(result.entries)
        self._last_used_sanitation_retry = result.used_sanitation_retry
        self._last_fetch_seconds = max(0.0, finished - started)
        return result

    def clear(self) -> None:
        self._cache.clear()
        self._last_entries_count = 0
        self._last_used_sanitation_retry = False
        self._last_fetch_seconds = 0.0

    def diagnostics(self) -> CacheDiagnostics:
        now = self._clock()
        ages = [max(0.0, now - item.stored_at) for item in self._cache.values()]
        return CacheDiagnostics(
            cache_items=len(self._cache),
            last_entries_count=self._last_entries_count,
            last_used_sanitation_retry=self._last_used_sanitation_retry,
            last_fetch_seconds=self._last_fetch_seconds,
            oldest_cache_age_seconds=max(ages) if ages else None,
        )
