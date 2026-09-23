"""Test configuration and shared fixtures."""

import pytest

from rate_limiter.domain.models import WindowConfig
from rate_limiter.service.sliding_window import SlidingWindowRateLimiter


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
