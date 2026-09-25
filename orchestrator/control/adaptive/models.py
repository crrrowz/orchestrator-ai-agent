"""Models, enums, and configuration for adaptive resource governance.

Defines phase classifications, circuit breaker states, exhaustion reasons,
and budget profiles for OpenHands and FSM runtime boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class ResourcePhase(str, Enum):
    """Execution phase matching FSM States for resource budgeting."""

    PREFLIGHT = "PREFLIGHT"
    PLANNING = "PLANNING"
    IMPLEMENTATION = "IMPLEMENTATION"
    VERIFICATION = "VERIFICATION"
    RESOLUTION = "RESOLUTION"
    REVIEW = "REVIEW"
    AUDIT = "AUDIT"


class CircuitState(str, Enum):
    """Operational state of the monetary and quota circuit breakers."""

    CLOSED = "CLOSED"        # Normal operation
    HALF_OPEN = "HALF_OPEN"  # Testing recovery after transient failure
    OPEN = "OPEN"            # Tripped; blocking execution


class ResourceExhaustionReason(str, Enum):
    """Formal taxonomy of resource termination conditions."""

    NONE = "NONE"
    MAX_TURNS_REACHED = "MAX_TURNS_REACHED"
    MONETARY_BUDGET_EXHAUSTED = "MONETARY_BUDGET_EXHAUSTED"
    TOKEN_CEILING_EXCEEDED = "TOKEN_CEILING_EXCEEDED"
    PROVIDER_RATE_LIMIT = "PROVIDER_RATE_LIMIT"
    STAGNATION_LIMIT_EXCEEDED = "STAGNATION_LIMIT_EXCEEDED"


@dataclass(frozen=True)
class PhaseBudgetProfile:
    """Resource constraints for a specific FSM execution phase."""

    phase: ResourcePhase
    base_turns: int
    min_turns: int
    max_turns: int
    output_headroom_tokens: int
    investigation_token_ratio: float  # 1.0 = 100% investigation permitted


@dataclass(frozen=True)
class ResourceGovernorConfig:
    """Master configuration for the adaptive resource governance engine."""

    max_budget_usd: float = 5.00
    warning_budget_usd: float = 4.00
    max_task_tokens: int = 1_000_000
    default_model_context_window: int = 200_000
    default_max_output_tokens: int = 8_192
    max_stagnation_turns: int = 4
    enable_ast_folding: bool = True


@dataclass
class TurnBudgetResult:
    """Computed turn budget and configuration for an agent execution session."""

    phase: ResourcePhase
    allocated_turns: int
    allocated_output_tokens: int
    complexity_score: float
    stagnation_penalty: int
    reasoning: str


@dataclass
class ResourceUsageSnapshot:
    """Cumulative resource consumption telemetry."""

    total_cost_usd: float = 0.0
    total_tokens_consumed: int = 0
    turns_executed: int = 0
    phase_spend_usd: Dict[ResourcePhase, float] = field(default_factory=dict)
    phase_tokens: Dict[ResourcePhase, int] = field(default_factory=dict)


@dataclass
class CircuitBreakerStatus:
    """Snapshot of circuit breaker status and spend thresholds."""

    total_cost_usd: float
    max_budget_usd: float
    is_tripped: bool
    state: CircuitState = CircuitState.CLOSED
    trip_reason: Optional[ResourceExhaustionReason] = None
