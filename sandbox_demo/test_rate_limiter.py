"""Tests for SlidingWindowRateLimiter service."""

import pytest

from rate_limiter.domain.models import WindowConfig
from rate_limiter.service.sliding_window import SlidingWindowRateLimiter


@pytest.fixture
def clock_limiter() -> SlidingWindowRateLimiter:
    config = WindowConfig(max_requests=5, window_seconds=10.0)
    call_times: list[float] = [0.0]

    def advance() -> float:
        t = call_times[-1]
        call_times.append(t + 1.0)
        return t

    return SlidingWindowRateLimiter(config=config, clock=advance)


class TestAllow:
    def test_first_request_allowed(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        result = clock_limiter.allow("user1")
        assert result.allowed is True
        assert result.current_count == 1

    def test_within_limit_allows(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        for _ in range(4):
            result = clock_limiter.allow("user1")
            assert result.allowed is True

    def test_rejects_after_max_requests(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        max_requests = clock_limiter._config.max_requests
        for _ in range(max_requests):
            result = clock_limiter.allow("user1")
            assert result.allowed is True

        result = clock_limiter.allow("user1")
        assert result.allowed is False
        assert result.current_count == max_requests

    def test_different_keys_independent(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        for _ in range(6):
            clock_limiter.allow("user1")
        assert clock_limiter.allow("user1").allowed is False
        for _ in range(5):
            assert clock_limiter.allow("user2").allowed is True
        assert clock_limiter.allow("user2").allowed is False

    def test_returns_current_count(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        clock_limiter.allow("user1")
        result = clock_limiter.allow("user1")
        assert result.current_count == 2

    def test_uses_real_clock_by_default(self) -> None:
        limiter = SlidingWindowRateLimiter(config=WindowConfig(max_requests=100, window_seconds=60.0))
        result = limiter.allow("user1")
        assert result.allowed is True
        assert result.current_count == 1


class TestCheck:
    def test_check_shows_available(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        result = clock_limiter.check("user1")
        assert result.allowed is True
        assert result.current_count == 0

    def test_check_does_not_consume(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        clock_limiter.check("user1")
        result = clock_limiter.check("user1")
        assert result.current_count == 0

    def test_check_rejects_when_full(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        max_requests = clock_limiter._config.max_requests
        for _ in range(max_requests):
            clock_limiter.allow("user1")
        result = clock_limiter.check("user1")
        assert result.allowed is False

    def test_check_current_count_reflects_existing(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        clock_limiter.allow("user1")
        result = clock_limiter.check("user1")
        assert result.current_count == 1


class TestAllowBatch:
    def test_batch_returns_all_results(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        results = clock_limiter.allow_batch(["a", "b", "c"])
        assert set(results.keys()) == {"a", "b", "c"}
        for result in results.values():
            assert result.allowed is True

    def test_batch_respects_limit_per_key(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        max_requests = clock_limiter._config.max_requests
        for _ in range(max_requests):
            clock_limiter.allow("user1")
        results = clock_limiter.allow_batch(["user1", "user2"])
        assert results["user1"].allowed is False
        assert results["user2"].allowed is True


class TestReset:
    def test_reset_allows_again(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        max_requests = clock_limiter._config.max_requests
        for _ in range(max_requests):
            clock_limiter.allow("user1")
        assert clock_limiter.allow("user1").allowed is False
        clock_limiter.reset("user1")
        assert clock_limiter.allow("user1").allowed is True

    def test_reset_other_keys_unaffected(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        max_requests = clock_limiter._config.max_requests
        for _ in range(max_requests):
            clock_limiter.allow("user1")
        for _ in range(max_requests):
            clock_limiter.allow("user2")
        clock_limiter.reset("user1")
        assert clock_limiter.allow("user1").allowed is True
        assert clock_limiter.allow("user2").allowed is False


class TestMetrics:
    def test_metrics_after_requests(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        clock_limiter.allow("user1")
        clock_limiter.allow("user1")
        metrics = clock_limiter.metrics("user1")
        assert metrics.count_in_window == 2
        assert metrics.remaining == 3

    def test_metrics_empty_key(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        metrics = clock_limiter.metrics("unknown")
        assert metrics.count_in_window == 0
        assert metrics.remaining == 5
        assert metrics.oldest_timestamp is None

    def test_metrics_does_not_consume(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        clock_limiter.allow("user1")
        clock_limiter.metrics("user1")
        result = clock_limiter.allow("user1")
        assert result.current_count == 2


class TestEdgeCases:
    def test_empty_key(self, clock_limiter: SlidingWindowRateLimiter) -> None:
        result = clock_limiter.allow("")
        assert result.allowed is True

    def test_custom_store(self) -> None:
        from rate_limiter.domain.models import InMemoryStore

        store = InMemoryStore()
        config = WindowConfig(max_requests=3, window_seconds=60.0)
        limiter = SlidingWindowRateLimiter(config=config, store=store)
        assert limiter.allow("user1").allowed is True
        assert store.total_keys() == 1
