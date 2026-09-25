"""Circuit breaker and provider resilience mechanisms for adaptive governance.

Enforces financial limits, token ceilings, and provider exponential backoff
to protect against runaway execution loops and API exhaustion.
"""

from __future__ import annotations

import logging
import random
from typing import Optional

from orchestrator.control.adaptive.models import (
    CircuitBreakerStatus,
    CircuitState,
    ResourceExhaustionReason,
    ResourceGovernorConfig,
    ResourcePhase,
    ResourceUsageSnapshot,
)

logger = logging.getLogger(__name__)


class MonetaryCircuitBreaker:
    """Enforces non-intrusive financial ceilings and safe execution pausing."""

    def __init__(self, config: Optional[ResourceGovernorConfig] = None) -> None:
        self.config = config or ResourceGovernorConfig()
        self.usage = ResourceUsageSnapshot()
        self.state: CircuitState = CircuitState.CLOSED
        self.trip_reason: Optional[ResourceExhaustionReason] = None
        self._warning_logged: bool = False

    def record_consumption(
        self,
        cost_usd: float,
        tokens: int,
        phase: ResourcePhase,
        turns: int = 1,
    ) -> None:
        """Records telemetry and evaluates circuit state against configured thresholds."""
        c = max(0.0, cost_usd)
        tok = max(0, tokens)
        t = max(0, turns)

        self.usage.total_cost_usd += c
        self.usage.total_tokens_consumed += tok
        self.usage.turns_executed += t

        self.usage.phase_spend_usd[phase] = (
            self.usage.phase_spend_usd.get(phase, 0.0) + c
        )
        self.usage.phase_tokens[phase] = (
            self.usage.phase_tokens.get(phase, 0) + tok
        )

        self._evaluate_thresholds()

    def _evaluate_thresholds(self) -> None:
        """Evaluates whether financial or token limits have been breached."""
        if not self._warning_logged and self.usage.total_cost_usd >= self.config.warning_budget_usd:
            logger.warning(
                f"Budget warning threshold reached: ${self.usage.total_cost_usd:.2f} >= "
                f"${self.config.warning_budget_usd:.2f} (ceiling: ${self.config.max_budget_usd:.2f})"
            )
            self._warning_logged = True

        if self.usage.total_cost_usd >= self.config.max_budget_usd:
            self.state = CircuitState.OPEN
            self.trip_reason = ResourceExhaustionReason.MONETARY_BUDGET_EXHAUSTED
            logger.error(
                f"Monetary circuit breaker TRIPPED: total spend ${self.usage.total_cost_usd:.2f} "
                f"exceeds ceiling ${self.config.max_budget_usd:.2f}."
            )
        elif self.usage.total_tokens_consumed >= self.config.max_task_tokens:
            self.state = CircuitState.OPEN
            self.trip_reason = ResourceExhaustionReason.TOKEN_CEILING_EXCEEDED
            logger.error(
                f"Token circuit breaker TRIPPED: total tokens {self.usage.total_tokens_consumed} "
                f"exceeds ceiling {self.config.max_task_tokens}."
            )

    @property
    def is_tripped(self) -> bool:
        """Return True if circuit breaker has tripped OPEN."""
        return self.state == CircuitState.OPEN

    @property
    def warning_triggered(self) -> bool:
        """Return True if spending has reached or exceeded warning threshold."""
        return self.usage.total_cost_usd >= self.config.warning_budget_usd

    @property
    def remaining_budget_usd(self) -> float:
        """Return remaining spend allowance before tripping."""
        return max(0.0, round(self.config.max_budget_usd - self.usage.total_cost_usd, 4))

    @property
    def status(self) -> CircuitBreakerStatus:
        """Return detailed status snapshot."""
        return CircuitBreakerStatus(
            total_cost_usd=round(self.usage.total_cost_usd, 4),
            max_budget_usd=self.config.max_budget_usd,
            is_tripped=self.is_tripped,
            state=self.state,
            trip_reason=self.trip_reason,
        )

    def reset(self) -> None:
        """Reset breaker back to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.trip_reason = None
        self._warning_logged = False


class ProviderQuotaProtector:
    """Manages rate-limiting backoffs and tracks provider API health."""

    def __init__(self, max_retries: int = 4, base_delay_seconds: float = 2.0) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay_seconds
        self.consecutive_rate_limits = 0

    def compute_backoff_delay(self, attempt: int, jitter: bool = False) -> float:
        """Calculates exponential backoff delay with optional random jitter.

        Base formula: delay = base_delay * (2 ^ min(attempt, 5)).
        """
        scaled = self.base_delay * (2.0 ** min(attempt, 5))
        if jitter:
            scaled += random.uniform(0.1, 1.0)
        return round(scaled, 2)

    def record_rate_limit_event(self) -> bool:
        """Records a 429/529 event. Returns True if max retries exceeded (tripped)."""
        self.consecutive_rate_limits += 1
        return self.consecutive_rate_limits > self.max_retries

    def record_success(self) -> None:
        """Resets rate limit counter on clean API call."""
        self.consecutive_rate_limits = 0

    @property
    def is_tripped(self) -> bool:
        """Return True if rate limit threshold exceeded."""
        return self.consecutive_rate_limits > self.max_retries
