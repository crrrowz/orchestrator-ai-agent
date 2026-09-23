"""Domain models for the rate limiter.

These are pure data entities — they carry no behavioural logic and have no
dependencies on frameworks or I/O. The `TokenStore` protocol defines the
port that external storage implementations must satisfy, keeping the
domain free of infrastructure concerns.
"""

import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Protocol

from pydantic import Field


# --------------------------------------------------------------------------- #
# Port (Protocol) — owned by domain, implemented by adapters
# --------------------------------------------------------------------------- #

class TokenStore(Protocol):
    """Port defining the storage contract for request records.

    Any class implementing these methods can be injected as the backing
    store for :class:`SlidingWindowRateLimiter`.
    """

    def add_record(self, key: str, record: "RequestRecord", now: float) -> None:
        """Append a request record for the given key at ``now``."""
        ...

    def get_records(self, key: str) -> list["RequestRecord"]:
        """Return all stored records for the given key."""
        ...

    def prune(self, key: str, cutoff: float) -> int:
        """Remove records older than ``cutoff`` and return count removed."""
        ...

    def remove(self, key: str) -> None:
        """Remove all records for the given key."""
        ...


# --------------------------------------------------------------------------- #
# Value objects
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class WindowConfig:
    """Immutable configuration for a sliding window.

    Attributes
    ----------
    max_requests : int
        Maximum number of requests permitted within a single window.
    window_seconds : float
        Duration of the sliding window in seconds.
    """

    max_requests: int = Field(gt=0)
    window_seconds: float = Field(gt=0.0)

    def __post_init__(self) -> None:
        """Validate field constraints that pydantic Field would enforce."""
        if self.max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if self.window_seconds <= 0.0:
            raise ValueError("window_seconds must be positive")


@dataclass(frozen=True, slots=True)
class RequestRecord:
    """A single request timestamp entry, optionally carrying metadata."""

    timestamp: float
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    """Result returned by every check / allow operation."""

    allowed: bool
    current_count: int
    max_requests: int
    retry_after: float = 0.0

    @property
    def exhausted(self) -> bool:
        """Whether the limit was reached on this check."""
        return not self.allowed


# --------------------------------------------------------------------------- #
# Concrete adapter (lives in domain module for convenience, but
# is genuinely an infrastructure concern)
# --------------------------------------------------------------------------- #

class InMemoryStore:
    """Thread-safe in-memory store implementing :class:`TokenStore`."""

    _data: dict[str, Deque[RequestRecord]]
    _lock: threading.Lock

    def __init__(self) -> None:
        self._data: dict[str, Deque[RequestRecord]] = defaultdict(deque)
        self._lock = threading.Lock()

    def add_record(self, key: str, record: RequestRecord, now: float) -> None:
        with self._lock:
            self._data[key].append(record)

    def get_records(self, key: str) -> list[RequestRecord]:
        with self._lock:
            return list(self._data.get(key, ()))

    def prune(self, key: str, cutoff: float) -> int:
        with self._lock:
            dq = self._data.get(key)
            if dq is None:
                return 0
            removed = 0
            while dq and dq[0].timestamp < cutoff:
                dq.popleft()
                removed += 1
            if not dq:
                del self._data[key]
            return removed

    def remove(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def total_keys(self) -> int:
        """Return number of distinct keys currently stored."""
        with self._lock:
            return len(self._data)
