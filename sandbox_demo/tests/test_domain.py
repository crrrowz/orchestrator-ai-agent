"""Tests for domain models."""
import pytest
from rate_limiter.domain.models import (
    InMemoryStore, RateLimitResult, RequestRecord, TokenStore, WindowConfig,
)


class TestWindowConfig:
    def test_valid_config(self) -> None:
        cfg = WindowConfig(max_requests=10, window_seconds=60.0)
        assert cfg.max_requests == 10
        assert cfg.window_seconds == 60.0

    def test_zero_max_requests_raises(self) -> None:
        with pytest.raises(ValueError, match="max_requests must be at least 1"):
            WindowConfig(max_requests=0, window_seconds=60.0)

    def test_negative_max_requests_raises(self) -> None:
        with pytest.raises(ValueError, match="max_requests must be at least 1"):
            WindowConfig(max_requests=-1, window_seconds=60.0)

    def test_zero_window_raises(self) -> None:
        with pytest.raises(ValueError, match="window_seconds must be positive"):
            WindowConfig(max_requests=10, window_seconds=0.0)

    def test_negative_window_raises(self) -> None:
        with pytest.raises(ValueError, match="window_seconds must be positive"):
            WindowConfig(max_requests=10, window_seconds=-5.0)

    def test_very_large_values(self) -> None:
        cfg = WindowConfig(max_requests=2**31-1, window_seconds=1e9)
        assert cfg.max_requests == 2**31-1

    def test_fractional_window(self) -> None:
        cfg = WindowConfig(max_requests=5, window_seconds=0.001)
        assert cfg.window_seconds == 0.001

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

    def test_equality(self) -> None:
        c1 = WindowConfig(max_requests=5, window_seconds=30.0)
        c2 = WindowConfig(max_requests=5, window_seconds=30.0)
        assert c1 == c2

    def test_different_not_equal(self) -> None:
        c1 = WindowConfig(max_requests=5, window_seconds=30.0)
        c2 = WindowConfig(max_requests=10, window_seconds=30.0)
        assert c1 != c2


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

    def test_slots_no_dict(self) -> None:
        rec = RequestRecord(timestamp=100.0)
        assert not hasattr(rec, "__dict__")

    def test_not_hashable_due_to_metadata(self) -> None:
        rec = RequestRecord(timestamp=100.0)
        import pytest
        with pytest.raises(TypeError):
            hash(rec)


class TestRateLimitResult:
    def test_allowed_result(self) -> None:
        result = RateLimitResult(allowed=True, current_count=3, max_requests=10)
        assert result.allowed is True
        assert result.exhausted is False
        assert result.retry_after == 0.0

    def test_rejected_result(self) -> None:
        result = RateLimitResult(allowed=False, current_count=10, max_requests=10, retry_after=1.5)
        assert result.allowed is False
        assert result.exhausted is True
        assert result.retry_after == 1.5

    def test_immutable(self) -> None:
        result = RateLimitResult(allowed=True, current_count=1, max_requests=10)
        with pytest.raises(AttributeError):
            result.allowed = False  # type: ignore[attr-defined]

    def test_slots_no_dict(self) -> None:
        result = RateLimitResult(allowed=True, current_count=1, max_requests=10)
        assert not hasattr(result, "__dict__")

    def test_equality(self) -> None:
        r1 = RateLimitResult(allowed=True, current_count=1, max_requests=5)
        r2 = RateLimitResult(allowed=True, current_count=1, max_requests=5)
        assert r1 == r2


class TestInMemoryStore:
    def test_add_and_get(self) -> None:
        store = InMemoryStore()
        store.add_record("k1", RequestRecord(timestamp=100.0), 100.0)
        records = store.get_records("k1")
        assert len(records) == 1
        assert records[0].timestamp == 100.0

    def test_prune_removes_old(self) -> None:
        store = InMemoryStore()
        store.add_record("k1", RequestRecord(timestamp=1.0), 1.0)
        store.add_record("k1", RequestRecord(timestamp=2.0), 2.0)
        removed = store.prune("k1", cutoff=1.5)
        assert removed == 1
        assert len(store.get_records("k1")) == 1

    def test_prune_returns_zero_for_empty_key(self) -> None:
        store = InMemoryStore()
        assert store.prune("unknown", cutoff=0.0) == 0

    def test_prune_boundary_exact_match(self) -> None:
        store = InMemoryStore()
        store.add_record("k1", RequestRecord(timestamp=5.0), 5.0)
        assert store.prune("k1", cutoff=5.0) == 0
        assert len(store.get_records("k1")) == 1

    def test_prune_all_records(self) -> None:
        store = InMemoryStore()
        store.add_record("k1", RequestRecord(timestamp=10.0), 10.0)
        assert store.prune("k1", cutoff=100.0) == 1
        assert store.get_records("k1") == []

    def test_remove_clears_key(self) -> None:
        store = InMemoryStore()
        store.add_record("k1", RequestRecord(timestamp=1.0), 1.0)
        store.remove("k1")
        assert store.get_records("k1") == []

    def test_remove_nonexistent_key(self) -> None:
        store = InMemoryStore()
        store.remove("unknown")
        assert store.get_records("unknown") == []

    def test_total_keys(self) -> None:
        store = InMemoryStore()
        store.add_record("k1", RequestRecord(timestamp=1.0), 1.0)
        store.add_record("k2", RequestRecord(timestamp=1.0), 1.0)
        assert store.total_keys() == 2

    def test_total_keys_empty(self) -> None:
        store = InMemoryStore()
        assert store.total_keys() == 0

    def test_get_records_returns_copy(self) -> None:
        store = InMemoryStore()
        store.add_record("k1", RequestRecord(timestamp=1.0), 1.0)
        records = store.get_records("k1")
        records.append(RequestRecord(timestamp=999.0))
        assert len(store.get_records("k1")) == 1

    def test_token_store_protocol(self) -> None:
        store: TokenStore = InMemoryStore()
        store.add_record("k", RequestRecord(timestamp=1.0), 1.0)
        assert len(store.get_records("k")) == 1
        store.prune("k", 0.5)
        store.remove("k")

    def test_prune_return_count_accuracy(self) -> None:
        store = InMemoryStore()
        for ts in [1.0, 2.0, 3.0, 4.0, 5.0]:
            store.add_record("k1", RequestRecord(timestamp=ts), ts)
        removed = store.prune("k1", cutoff=3.0)
        assert removed == 2
        assert len(store.get_records("k1")) == 3
