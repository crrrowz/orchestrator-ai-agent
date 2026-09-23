"""Test configuration and shared fixtures."""
import pytest

from rate_limiter.domain.models import WindowConfig
from rate_limiter.service.sliding_window import SlidingWindowRateLimiter


class JumpClock:
    """Deterministic clock that starts at 0 and supports arbitrary jumps."""

    def __init__(self) -> None:
        self._time = 0.0

    def __call__(self) -> float:
        return self._time

    def jump(self, new_time: float) -> None:
        self._time = new_time


@pytest.fixture
def default_config() -> WindowConfig:
    return WindowConfig(max_requests=5, window_seconds=10.0)


@pytest.fixture
def limiter(default_config) -> SlidingWindowRateLimiter:
    return SlidingWindowRateLimiter(config=default_config)


@pytest.fixture
def clock_limiter(default_config) -> SlidingWindowRateLimiter:
    """Rate limiter with a deterministic mock clock advancing 1s per call."""
    call_times: list[float] = [0.0]

    def advance() -> float:
        t = call_times[-1]
        call_times.append(t + 1.0)
        return t

    return SlidingWindowRateLimiter(config=default_config, clock=advance)


@pytest.fixture
def single_request_limiter(default_config) -> SlidingWindowRateLimiter:
    """Rate limiter allowing exactly 1 request per window."""
    config = WindowConfig(max_requests=1, window_seconds=60.0)
    call_times: list[float] = [0.0]

    def advance() -> float:
        t = call_times[-1]
        call_times.append(t + 1.0)
        return t

    return SlidingWindowRateLimiter(config=config, clock=advance)


@pytest.fixture
def tiny_window_limiter() -> SlidingWindowRateLimiter:
    """Rate limiter with a very small window (0.01s)."""
    config = WindowConfig(max_requests=100, window_seconds=0.01)
    call_times: list[float] = [0.0]

    def advance() -> float:
        t = call_times[-1]
        call_times.append(t + 0.01)
        return t

    return SlidingWindowRateLimiter(config=config, clock=advance)


@pytest.fixture
def large_scale_limiter() -> SlidingWindowRateLimiter:
    """Rate limiter with large numbers to test boundary behaviour."""
    config = WindowConfig(max_requests=1_000_000, window_seconds=3600.0)
    return SlidingWindowRateLimiter(config=config)


@pytest.fixture
def jump_clock() -> JumpClock:
    """Deterministic clock that can jump to arbitrary values."""
    return JumpClock()


@pytest.fixture
def store_only_limiter() -> SlidingWindowRateLimiter:
    """Limiter using an explicit store with a clock."""
    from rate_limiter.domain.models import InMemoryStore

    config = WindowConfig(max_requests=5, window_seconds=10.0)
    store = InMemoryStore()
    call_times: list[float] = [0.0]

    def advance() -> float:
        t = call_times[-1]
        call_times.append(t + 1.0)
        return t

    return SlidingWindowRateLimiter(config=config, store=store, clock=advance)