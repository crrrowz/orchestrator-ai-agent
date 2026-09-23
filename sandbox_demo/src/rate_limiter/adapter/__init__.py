"""Adapter layer — I/O implementations.

Currently re-exports :class:`InMemoryStore` from the domain layer,
where it lives alongside the :class:`TokenStore` protocol it
implements.
"""

from rate_limiter.domain.models import InMemoryStore

__all__ = ["InMemoryStore"]
