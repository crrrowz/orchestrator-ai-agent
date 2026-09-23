"""Sliding Window Rate Limiter — Clean Python Architecture.

Package layout follows strict separation of concerns:
  domain/   — pure data models, protocols, and I/O adapters
  service/  — business logic (the SlidingWindowRateLimiter)
"""

from rate_limiter.domain.models import InMemoryStore, TokenStore, WindowConfig
from rate_limiter.service.sliding_window import SlidingWindowRateLimiter

__all__ = [
    "WindowConfig",
    "SlidingWindowRateLimiter",
    "TokenStore",
    "InMemoryStore",
]
