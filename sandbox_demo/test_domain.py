"""Tests for domain models and TokenStore protocol."""

import pytest

from rate_limiter.domain.models import (
    InMemoryStore,
    RateLimitResult,
    RequestRecord,
    TokenStore,
    WindowConfig,
)


class TestWindowConfig:
    def test_valid_config(self) -> None:
        cfg = WindowConfig(max_requests=10, window_seconds=60.0)
        assert cfg.max_requests == 10
        assert cfg.window_seconds == 60.0

    def test_zero_max_requests_raises(self) -> None:
        with pytest.raises(ValueError):
            WindowConfig(max_requests=0, window_seconds=60.0)

    def test_negative_max_requests_raises(self) -> None:
        with pytest.raises(ValueError):
            WindowConfig(max_requests=-1, window_seconds=60.0)

    def test_zero_window_raises(self) -> None:
        with pytest.raises(ValueError):
            WindowConfig(max_requests=10, window_seconds=0.0)

    def test_negative_window_raises(self) -> None:
        with pytest.raises(ValueError):
            WindowConfig(max_requests=10, window_seconds=-5.0)

    def test_immutable(self) -> None:
        cfg = WindowConfig(max_requests=5, window_seconds=30.0)
        with pytest.raises(AttributeError):
            cfg.max_requests = 99  # type: ignore[attr-defined]

    def test_slots_no_dict(self) -> None:
        cfg = WindowConfig(max_requests=5, window_seconds=30.0)
        assert not hasattr(cfg, "__dict__")

    def test_hashable(self) -> None:
        cfg = WindowConfig(max_requests=5, window_seconds=30.0)
        assert isinstance(hash(cfg), int)


class TestRequestRecord:
    def test_default_metadata(self) -> None:
        rec = RequestRecord(timestamp=123.45)
        assert rec.timestamp == 123.45
        assert rec.metadata == {}

    def test_custom_metadata(self) -> None:
        rec = RequestRecord(timestamp=100.0, metadata={"user": "alice"})
        assert rec.metadata == {"user": "alice"}

    def test_immutable(self) -> None:
        rec = RequestRecord(timestamp=100.0)
        with pytest.raises(AttributeError):
            rec.timestamp = 200.0  # type: ignore[attr-defined]


class TestRateLimitResult:
    def test_allowed_result(self) -> None:
        result = RateLimitResult(allowed=True, current_count=3, max_requests=10, retry_after=0.0)
        assert result.allowed is True
        assert result.current_count == 3
        assert result.exhausted is False

    def test_rejected_result(self) -> None:
        result = RateLimitResult(allowed=False, current_count=10, max_requests=10, retry_after=1.5)
        assert result.allowed is False
        assert result.exhausted is True
        assert result.retry_after == 1.5

    def test_retry_after_zero_when_allowed(self) -> None:
        result = RateLimitResult(allowed=True, current_count=5, max_requests=10)
        assert result.retry_after == 0.0

    def test_immutable(self) -> None:
        result = RateLimitResult(allowed=True, current_count=1, max_requests=10)
        with pytest.raises(AttributeError):
            result.allowed = False  # type: ignore[attr-defined]


class TestInMemoryStore:
    def test_add_and_get_records(self) -> None:
        store = InMemoryStore()
        store.add_record("key1", RequestRecord(timestamp=100.0), 100.0)
        records = store.get_records("key1")
        assert len(records) == 1
        assert records[0].timestamp == 100.0

    def test_prune_removes_old(self) -> None:
        store = InMemoryStore()
        store.add_record("key1", RequestRecord(timestamp=1.0), 1.0)
        store.add_record("key1", RequestRecord(timestamp=2.0), 2.0)
        removed = store.prune("key1", cutoff=1.5)
        assert removed == 1
        assert len(store.get_records("key1")) == 1

    def test_remove_clears_key(self) -> None:
        store = InMemoryStore()
        store.add_record("key1", RequestRecord(timestamp=1.0), 1.0)
        store.remove("key1")
        assert store.get_records("key1") == []

    def test_total_keys(self) -> None:
        store = InMemoryStore()
        store.add_record("key1", RequestRecord(timestamp=1.0), 1.0)
        store.add_record("key2", RequestRecord(timestamp=1.0), 1.0)
        assert store.total_keys() == 2

    def test_token_store_protocol(self) -> None:
        """Verify InMemoryStore satisfies TokenStore protocol at runtime."""
        store: TokenStore = InMemoryStore()
        store.add_record("k", RequestRecord(timestamp=1.0), 1.0)
        assert len(store.get_records("k")) == 1
        store.prune("k", 0.5)
        store.remove("k")
