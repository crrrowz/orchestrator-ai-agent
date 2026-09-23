# Rate Limiter (Sliding Window)

A high-performance Sliding Window Rate Limiter Python library built with Clean Hexagonal Architecture.

---

## Architecture Overview

```
src/rate_limiter/
├── domain/
│   └── models.py       # WindowConfig, RateLimitResult, RequestRecord, TokenStore (Protocol)
├── service/
│   └── sliding_window.py # SlidingWindowRateLimiter business logic
└── adapter/
    └── memory_store.py # Thread-safe InMemoryStore
```

---

## How to Run

### 1. Run the Live Demo
```bash
uv run python demo.py
# or with standard python:
python demo.py
```

### 2. Run Test Suite
```bash
uv run pytest
# or:
python -m pytest tests/ -v
```

---

## Quickstart (Code Example)

```python
from rate_limiter import SlidingWindowRateLimiter, WindowConfig

# Configure: 5 requests per 60-second sliding window
config = WindowConfig(max_requests=5, window_seconds=60.0)
limiter = SlidingWindowRateLimiter(config=config)

# Check and consume a slot for a client
result = limiter.allow("client_ip_or_id")

if result.allowed:
    print(f"Request allowed! ({result.current_count}/{result.max_requests})")
else:
    print(f"Rate limited! Retry after {result.retry_after:.2f} seconds")

# Preview without consuming
preview = limiter.check("client_ip_or_id")

# Fetch current metrics
metrics = limiter.metrics("client_ip_or_id")
print(f"Remaining capacity: {metrics.remaining}")
```
