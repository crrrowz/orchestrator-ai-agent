"""Adaptive resource governance subpackage.

Provides phase-aware turn budgeting, AST-aware context clamping,
and non-intrusive monetary and provider circuit breakers.
"""

from orchestrator.control.adaptive.allocator import AdaptiveBudgetAllocator
from orchestrator.control.adaptive.circuit_breaker import (
    MonetaryCircuitBreaker,
    ProviderQuotaProtector,
)
from orchestrator.control.adaptive.clamper import ASTAwareContextClamper
from orchestrator.control.adaptive.governor import AdaptiveResourceGovernor
from orchestrator.control.adaptive.models import (
    CircuitBreakerStatus,
    CircuitState,
    PhaseBudgetProfile,
    ResourceExhaustionReason,
    ResourceGovernorConfig,
    ResourcePhase,
    ResourceUsageSnapshot,
    TurnBudgetResult,
)

__all__ = [
    "AdaptiveBudgetAllocator",
    "ASTAwareContextClamper",
    "MonetaryCircuitBreaker",
    "ProviderQuotaProtector",
    "AdaptiveResourceGovernor",
    "CircuitBreakerStatus",
    "CircuitState",
    "PhaseBudgetProfile",
    "ResourceExhaustionReason",
    "ResourceGovernorConfig",
    "ResourcePhase",
    "ResourceUsageSnapshot",
    "TurnBudgetResult",
]
