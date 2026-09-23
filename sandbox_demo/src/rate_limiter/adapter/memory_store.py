"""In-memory token store adapter.

Re-exports :class:`InMemoryStore` from the domain module where it
lives alongside the :class:`TokenStore` protocol it implements.
"""

from rate_limiter.domain.models import InMemoryStore

__all__ = ["InMemoryStore"]
