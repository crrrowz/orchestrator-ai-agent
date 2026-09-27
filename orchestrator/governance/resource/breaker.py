"""Monetary and Resource Breaker for ORAGAI Governance Resource Layer.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from orchestrator.control.adaptive.circuit_breaker import MonetaryCircuitBreaker
from orchestrator.control.adaptive.models import (
    CircuitBreakerStatus,
    CircuitState,
    ResourceExhaustionReason,
)

AdaptiveCircuitBreaker = MonetaryCircuitBreaker
CircuitBreakerDecision = CircuitBreakerStatus

__all__ = [
    "MonetaryCircuitBreaker",
    "AdaptiveCircuitBreaker",
    "CircuitBreakerStatus",
    "CircuitBreakerDecision",
    "CircuitState",
    "ResourceExhaustionReason",
]
