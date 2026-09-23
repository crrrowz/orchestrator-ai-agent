"""Tests for SlidingWindowRateLimiter service."""
import pytest
from rate_limiter.domain.models import WindowConfig
from rate_limiter.service.sliding_window import SlidingWindowRateLimiter


@pytest.fixture
def jump_limiter(default_config, jump_clock) -> SlidingWindowRateLimiter:
    """Limiter that uses the jump_clock for precise time control."""
    return SlidingWindowRateLimiter(config=default_config, clock=jump_clock)


class TestAllow:
    def test_first_request_allowed(self, clock_limiter) -> None:
        result = clock_limiter.allow("user1")
        assert result.allowed is True
        assert result.current_count == 1
        assert result.max_requests == 5
        assert result.retry_after == 0.0

    def test_within_limit_allows(self, clock_limiter) -> None:
        for _ in range(4):
            result = clock_limiter.allow("user1")
            assert result.allowed is True

    def test_rejects_after_max_requests(self, clock_limiter) -> None:
        max_req = clock_limiter._config.max_requests
        for _ in range(max_req):
            assert clock_limiter.allow("user1").allowed is True
        result = clock_limiter.allow("user1")
        assert result.allowed is False
        assert result.current_count == max_req
        assert result.exhausted is True

    def test_different_keys_independent(self, clock_limiter) -> None:
        for _ in range(6):
            clock_limiter.allow("user1")
        assert clock_limiter.allow("user1").allowed is False
        for _ in range(5):
            assert clock_limiter.allow("user2").allowed is True
        assert clock_limiter.allow("user2").allowed is False

    def test_returns_current_count(self, clock_limiter) -> None:
        clock_limiter.allow("user1")
        result = clock_limiter.allow("user1")
        assert result.current_count == 2

    def test_uses_real_clock_by_default(self) -> None:
        limiter = SlidingWindowRateLimiter(config=WindowConfig(max_requests=100, window_seconds=60.0))
        result = limiter.allow("user1")
        assert result.allowed is True
        assert result.current_count == 1

    def test_empty_key(self, clock_limiter) -> None:
        result = clock_limiter.allow("")
        assert result.allowed is True
        assert result.current_count == 1

    def test_single_request_limit(self) -> None:
        config = WindowConfig(max_requests=1, window_seconds=60.0)
        call_times = [0.0]
        def advance() -> float:
            t = call_times[-1]
            call_times.append(t + 1.0)
            return t
        limiter = SlidingWindowRateLimiter(config=config, clock=advance)
        assert limiter.allow("user1").allowed is True
        assert limiter.allow("user1").allowed is False

    def test_boundary_max_requests_exactly_one_less(self, clock_limiter) -> None:
        max_req = clock_limiter._config.max_requests
        for _ in range(max_req - 1):
            assert clock_limiter.allow("user1").allowed is True
        result = clock_limiter.allow("user1")
        assert result.allowed is True
        assert result.current_count == max_req

    def test_multiple_keys_do_not_share_slots(self, clock_limiter) -> None:
        for _ in range(5):
            clock_limiter.allow("user1")
        for key in ["user2", "user3", "user4", "user5"]:
            assert clock_limiter.allow(key).allowed is True
        assert clock_limiter.allow("user1").allowed is False


class TestCheck:
    def test_check_shows_available(self, clock_limiter) -> None:
        result = clock_limiter.check("user1")
        assert result.allowed is True
        assert result.current_count == 0

    def test_check_does_not_consume(self, clock_limiter) -> None:
        clock_limiter.check("user1")
        result = clock_limiter.check("user1")
        assert result.current_count == 0

    def test_check_rejects_when_full(self, clock_limiter) -> None:
        max_req = clock_limiter._config.max_requests
        for _ in range(max_req):
            clock_limiter.allow("user1")
        result = clock_limiter.check("user1")
        assert result.allowed is False
        assert result.exhausted is True

    def test_check_current_count_reflects_existing(self, clock_limiter) -> None:
        clock_limiter.allow("user1")
        result = clock_limiter.check("user1")
        assert result.current_count == 1

    def test_check_empty_key(self, clock_limiter) -> None:
        result = clock_limiter.check("")
        assert result.allowed is True
        assert result.current_count == 0

    def test_check_empty_key_after_allow(self, clock_limiter) -> None:
        clock_limiter.allow("")
        result = clock_limiter.check("")
        assert result.allowed is True
        assert result.current_count == 1

    def test_check_after_window_expiry(self, jump_limiter, jump_clock) -> None:
        for _ in range(5):
            jump_limiter.allow("user1")
        jump_clock.jump(20.0)
        result = jump_limiter.check("user1")
        assert result.allowed is True
        assert result.current_count == 0


class TestAllowBatch:
    def test_batch_returns_all_results(self, clock_limiter) -> None:
        results = clock_limiter.allow_batch(["a", "b", "c"])
        assert set(results.keys()) == {"a", "b", "c"}
        for result in results.values():
            assert result.allowed is True

    def test_batch_respects_limit_per_key(self, clock_limiter) -> None:
        max_req = clock_limiter._config.max_requests
        for _ in range(max_req):
            clock_limiter.allow("user1")
        results = clock_limiter.allow_batch(["user1", "user2"])
        assert results["user1"].allowed is False
        assert results["user2"].allowed is True

    def test_batch_empty_list(self, clock_limiter) -> None:
        results = clock_limiter.allow_batch([])
        assert results == {}

    def test_batch_duplicate_keys(self, clock_limiter) -> None:
        results = clock_limiter.allow_batch(["a", "a", "b"])
        assert len(results) == 2
        assert results["a"].allowed is True
        assert results["b"].allowed is True


class TestReset:
    def test_reset_allows_again(self, clock_limiter) -> None:
        max_req = clock_limiter._config.max_requests
        for _ in range(max_req):
            clock_limiter.allow("user1")
        assert clock_limiter.allow("user1").allowed is False
        clock_limiter.reset("user1")
        assert clock_limiter.allow("user1").allowed is True

    def test_reset_other_keys_unaffected(self, clock_limiter) -> None:
        max_req = clock_limiter._config.max_requests
        for _ in range(max_req):
            clock_limiter.allow("user1")
        for _ in range(max_req):
            clock_limiter.allow("user2")
        clock_limiter.reset("user1")
        assert clock_limiter.allow("user1").allowed is True
        assert clock_limiter.allow("user2").allowed is False

    def test_reset_nonexistent_key(self, clock_limiter) -> None:
        clock_limiter.reset("nonexistent")
        assert clock_limiter.check("nonexistent").allowed is True

    def test_reset_empty_key(self, clock_limiter) -> None:
        clock_limiter.reset("")
        assert clock_limiter.check("").allowed is True


class TestMetrics:
    def test_metrics_after_requests(self, clock_limiter) -> None:
        clock_limiter.allow("user1")
        clock_limiter.allow("user1")
        metrics = clock_limiter.metrics("user1")
        assert metrics.count_in_window == 2
        assert metrics.remaining == 3
        assert metrics.oldest_timestamp is not None

    def test_metrics_empty_key(self, clock_limiter) -> None:
        metrics = clock_limiter.metrics("unknown")
        assert metrics.count_in_window == 0
        assert metrics.remaining == 5
        assert metrics.oldest_timestamp is None

    def test_metrics_does_not_consume(self, clock_limiter) -> None:
        clock_limiter.allow("user1")
        clock_limiter.metrics("user1")
        result = clock_limiter.allow("user1")
        assert result.current_count == 2

    def test_metrics_after_window_expiry(self, jump_limiter, jump_clock) -> None:
        for _ in range(5):
            jump_limiter.allow("user1")
        jump_clock.jump(20.0)
        metrics = jump_limiter.metrics("user1")
        assert metrics.count_in_window == 0
        assert metrics.remaining == 5
        assert metrics.oldest_timestamp is None

    def test_metrics_max_requests_boundary(self) -> None:
        config = WindowConfig(max_requests=1, window_seconds=60.0)
        call_times = [0.0]
        def advance() -> float:
            t = call_times[-1]
            call_times.append(t + 1.0)
            return t
        limiter = SlidingWindowRateLimiter(config=config, clock=advance)
        limiter.allow("user1")
        metrics = limiter.metrics("user1")
        assert metrics.count_in_window == 1
        assert metrics.remaining == 0


class TestEdgeCases:
    def test_empty_key_operations(self, clock_limiter) -> None:
        assert clock_limiter.allow("").allowed is True
        assert clock_limiter.check("").allowed is True
        clock_limiter.reset("")
        assert clock_limiter.check("").allowed is True

    def test_none_key_does_not_raise(self, clock_limiter) -> None:
        result = clock_limiter.allow(None)  # type: ignore[arg-type]
        assert result.allowed is True

    def test_custom_store(self) -> None:
        from rate_limiter.domain.models import InMemoryStore
        store = InMemoryStore()
        config = WindowConfig(max_requests=3, window_seconds=60.0)
        limiter = SlidingWindowRateLimiter(config=config, store=store)
        assert limiter.allow("user1").allowed is True
        assert store.total_keys() == 1

    def test_custom_store_persists_across_resets(self) -> None:
        from rate_limiter.domain.models import InMemoryStore
        store = InMemoryStore()
        config = WindowConfig(max_requests=2, window_seconds=60.0)
        limiter = SlidingWindowRateLimiter(config=config, store=store)
        limiter.allow("user1")
        limiter.reset("user1")
        assert store.get_records("user1") == []

    def test_check_after_reset(self, clock_limiter) -> None:
        for _ in range(5):
            clock_limiter.allow("user1")
        clock_limiter.reset("user1")
        result = clock_limiter.check("user1")
        assert result.allowed is True
        assert result.current_count == 0

    def test_batch_empty(self, clock_limiter) -> None:
        results = clock_limiter.allow_batch([])
        assert results == {}

    def test_batch_mixed_keys(self, clock_limiter) -> None:
        config = WindowConfig(max_requests=2, window_seconds=60.0)
        call_times = [0.0]
        def advance() -> float:
            t = call_times[-1]
            call_times.append(t + 1.0)
            return t
        limiter = SlidingWindowRateLimiter(config=config, clock=advance)
        limiter.allow("a")
        limiter.allow("a")
        results = limiter.allow_batch(["a", "b"])
        assert results["a"].allowed is False
        assert results["b"].allowed is True

    def test_very_small_window_expiry(self, jump_clock) -> None:
        config = WindowConfig(max_requests=100, window_seconds=0.01)
        limiter = SlidingWindowRateLimiter(config=config)
        limiter.allow("user1")
        jump_clock.jump(0.1)
        result = limiter.allow("user1")
        assert result.allowed is True

    def test_reset_preserves_other_keys(self, store_only_limiter) -> None:
        store_only_limiter.allow("user1")
        store_only_limiter.allow("user2")
        store_only_limiter.reset("user1")
        assert store_only_limiter.check("user1").allowed is True
        assert store_only_limiter.check("user2").allowed is True
        assert store_only_limiter.allow("user2").current_count == 2

    def test_metrics_remaining_zero_when_full(self, clock_limiter) -> None:
        for _ in range(5):
            clock_limiter.allow("user1")
        metrics = clock_limiter.metrics("user1")
        assert metrics.remaining == 0
        assert metrics.count_in_window == 5

    def test_check_does_not_affect_subsequent_allow(self, clock_limiter) -> None:
        clock_limiter.check("user1")
        result = clock_limiter.allow("user1")
        assert result.current_count == 1

    def test_retry_after_computation(self, clock_limiter) -> None:
        max_req = clock_limiter._config.max_requests
        for _ in range(max_req):
            clock_limiter.allow("user1")
        result = clock_limiter.allow("user1")
        assert result.retry_after > 0.0
        assert result.allowed is False

    def test_window_expiry_allows_new_requests(self, jump_limiter, jump_clock) -> None:
        for _ in range(5):
            jump_limiter.allow("user1")
        jump_clock.jump(20.0)
        result = jump_limiter.allow("user1")
        assert result.allowed is True
        assert result.current_count == 1

    def test_custom_store_isolation(self) -> None:
        from rate_limiter.domain.models import InMemoryStore
        store1 = InMemoryStore()
        store2 = InMemoryStore()
        config = WindowConfig(max_requests=5, window_seconds=10.0)
        limiter1 = SlidingWindowRateLimiter(config=config, store=store1)
        limiter2 = SlidingWindowRateLimiter(config=config, store=store2)
        for _ in range(5):
            limiter1.allow("user1")
        for _ in range(5):
            limiter2.allow("user1")
        assert limiter1.check("user1").allowed is False
        assert limiter2.check("user1").allowed is False
        assert store1.total_keys() == 1
        assert store2.total_keys() == 1

    def test_different_configs_different_limits(self) -> None:
        config1 = WindowConfig(max_requests=2, window_seconds=60.0)
        config2 = WindowConfig(max_requests=10, window_seconds=60.0)
        limiter1 = SlidingWindowRateLimiter(config=config1)
        limiter2 = SlidingWindowRateLimiter(config=config2)
        for _ in range(2):
            assert limiter1.allow("user1").allowed is True
        assert limiter1.allow("user1").allowed is False
        for _ in range(10):
            assert limiter2.allow("user1").allowed is True
        assert limiter2.allow("user1").allowed is False

    def test_large_number_of_keys(self, clock_limiter) -> None:
        for i in range(100):
            result = clock_limiter.allow(f"user{i}")
            assert result.allowed is True

    def test_concurrent_same_key(self, clock_limiter) -> None:
        import threading
        results: list = []
        def make_request() -> None:
            results.append(clock_limiter.allow("shared"))
        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        allowed_count = sum(1 for r in results if r.allowed)
        assert allowed_count <= 5
