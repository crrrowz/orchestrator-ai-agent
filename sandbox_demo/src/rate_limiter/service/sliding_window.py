"""Sliding Window Rate Limiter service layer.

Implements the core sliding window algorithm that determines whether
incoming requests are permitted or rejected based on configured limits.
"""

import time
from dataclasses import dataclass
from typing import Callable

from rate_limiter.domain.models import (
    RateLimitResult,
    RequestRecord,
    TokenStore,
    WindowConfig,
)


@dataclass(frozen=True, slots=True)
class _WindowMetrics:
    """Immutable metrics snapshot computed after each check."""

    count_in_window: int
    oldest_timestamp: float | None
    remaining: int


class SlidingWindowRateLimiter:
    """Sliding window rate limiter.

    Parameters
    ----------
    config : WindowConfig
        Configuration defining max requests and window duration.
    store : TokenStore | None
        Optional external store conforming to the :class:`TokenStore`
        protocol. Defaults to :class:`InMemoryStore`.
    clock : Callable[[], float] | None
        Optional clock callable (used for testability). Defaults to
        ``time.time``.

    Notes
    -----
    The algorithm maintains a deque of timestamps per client key. On every
    request it prunes timestamps outside the current window and compares the
    remaining count against the configured maximum.
    """

    _store: TokenStore
    _config: WindowConfig
    _clock: Callable[[], float]

    def __init__(
        self,
        config: WindowConfig,
        store: TokenStore | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._config = config
        self._store = store if store is not None else _make_default_store()
        self._clock = clock if clock is not None else time.time

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def allow(self, key: str) -> RateLimitResult:
        """Check whether a request identified by ``key`` should be allowed."""
        now = self._clock()
        window_start = now - self._config.window_seconds

        self._store.prune(key, window_start)
        records = self._store.get_records(key)

        if len(records) >= self._config.max_requests:
            return RateLimitResult(
                allowed=False,
                current_count=len(records),
                max_requests=self._config.max_requests,
                retry_after=self._compute_retry_after(records[0], now),
            )

        record = RequestRecord(timestamp=now, metadata={})
        self._store.add_record(key, record, now)

        return RateLimitResult(
            allowed=True,
            current_count=len(records) + 1,
            max_requests=self._config.max_requests,
            retry_after=0.0,
        )

    def check(self, key: str) -> RateLimitResult:
        """Preview whether a request would be allowed without consuming a slot."""
        now = self._clock()
        window_start = now - self._config.window_seconds

        self._store.prune(key, window_start)
        records = self._store.get_records(key)

        if len(records) >= self._config.max_requests:
            return RateLimitResult(
                allowed=False,
                current_count=len(records),
                max_requests=self._config.max_requests,
                retry_after=self._compute_retry_after(records[0], now),
            )

        return RateLimitResult(
            allowed=True,
            current_count=len(records),
            max_requests=self._config.max_requests,
            retry_after=0.0,
        )

    def allow_batch(self, keys: list[str]) -> dict[str, RateLimitResult]:
        """Check a batch of keys, returning results for each."""
        return {key: self.allow(key) for key in keys}

    def reset(self, key: str) -> None:
        """Remove all tracking data for ``key``."""
        self._store.remove(key)

    def metrics(self, key: str) -> _WindowMetrics:
        """Return current window metrics for ``key`` without consuming a slot."""
        now = self._clock()
        window_start = now - self._config.window_seconds
        self._store.prune(key, window_start)
        records = self._store.get_records(key)

        return _WindowMetrics(
            count_in_window=len(records),
            oldest_timestamp=records[0].timestamp if records else None,
            remaining=max(0, self._config.max_requests - len(records)),
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _compute_retry_after(
        self, oldest: RequestRecord, now: float
    ) -> float:
        """Seconds until the oldest record exits the sliding window."""
        return max(0.0, oldest.timestamp + self._config.window_seconds - now)


def _make_default_store() -> TokenStore:
    """Lazy-import factory to create the default in-memory store."""
    from rate_limiter.adapter.memory_store import InMemoryStore

    return InMemoryStore()