"""Unified Adaptive Resource Governor façade.

Orchestrates pre-dispatch turn budgeting, context clamping, monetary circuit breakers,
and post-yield telemetry accounting across lifecycle phases.
"""

from __future__ import annotations

from typing import Dict, Optional, Set

from orchestrator.control.adaptive.allocator import AdaptiveBudgetAllocator
from orchestrator.control.adaptive.circuit_breaker import (
    MonetaryCircuitBreaker,
    ProviderQuotaProtector,
)
from orchestrator.control.adaptive.clamper import ASTAwareContextClamper
from orchestrator.control.adaptive.models import (
    CircuitBreakerStatus,
    ResourceGovernorConfig,
    ResourcePhase,
    TurnBudgetResult,
)


class AdaptiveResourceGovernor:
    """Unified façade consumed by GuardedFSMEngine and Strangler routing."""

    def __init__(self, config: Optional[ResourceGovernorConfig] = None) -> None:
        self.config = config or ResourceGovernorConfig()
        self.allocator = AdaptiveBudgetAllocator(self.config)
        self.clamper = ASTAwareContextClamper()
        self.circuit_breaker = MonetaryCircuitBreaker(self.config)
        self.provider_protector = ProviderQuotaProtector()
        self._stagnation_counter: int = 0

    @property
    def stagnation_counter(self) -> int:
        """Return the current consecutive stagnation count."""
        return self._stagnation_counter

    @stagnation_counter.setter
    def stagnation_counter(self, value: int) -> None:
        self._stagnation_counter = max(0, value)

    @property
    def is_tripped(self) -> bool:
        """Return True if any circuit breaker has tripped."""
        return self.circuit_breaker.is_tripped

    @property
    def remaining_budget_usd(self) -> float:
        """Return remaining monetary budget."""
        return self.circuit_breaker.remaining_budget_usd

    @property
    def status(self) -> CircuitBreakerStatus:
        """Return snapshot of circuit breaker status."""
        return self.circuit_breaker.status

    def pre_dispatch_allocate(
        self,
        phase: ResourcePhase,
        acceptance_criteria_count: int = 1,
        dag_depth: int = 1,
        target_files_count: int = 1,
        symbol_count: int = 10,
    ) -> TurnBudgetResult:
        """Called before dispatching an agent turn to calculate dynamic turn limits."""
        if self.circuit_breaker.is_tripped:
            return TurnBudgetResult(
                phase=phase,
                allocated_turns=0,
                allocated_output_tokens=0,
                complexity_score=0.0,
                stagnation_penalty=0,
                reasoning=f"Circuit breaker tripped: {self.circuit_breaker.trip_reason}",
            )

        return self.allocator.allocate_turn_budget(
            phase=phase,
            acceptance_criteria_count=acceptance_criteria_count,
            dag_depth=dag_depth,
            target_files_count=target_files_count,
            symbol_count=symbol_count,
            stagnation_count=self._stagnation_counter,
        )

    def post_yield_record(
        self,
        phase: ResourcePhase,
        cost_usd: float,
        tokens_consumed: int,
        turns_used: int,
        made_meaningful_progress: bool,
    ) -> None:
        """Called when an agent session yields to record spend and update stagnation."""
        self.circuit_breaker.record_consumption(
            cost_usd=cost_usd,
            tokens=tokens_consumed,
            phase=phase,
            turns=turns_used,
        )

        if made_meaningful_progress:
            self._stagnation_counter = 0
            self.provider_protector.record_success()
        else:
            self._stagnation_counter += 1

    def assemble_prompt_context(
        self,
        tier0_intent: str,
        tier1_diagnostics: str = "",
        tier2_files: Optional[Dict[str, str]] = None,
        tier3_architecture: str = "",
        target_symbols_per_file: Optional[Dict[str, Set[str]]] = None,
        max_context_chars: int = 120_000,
        reserved_headroom_chars: int = 16_000,
    ) -> str:
        """Assemble priority-tiered prompt context preserving guaranteed headroom."""
        return self.clamper.assemble_clamped_context(
            tier0_intent=tier0_intent,
            tier1_diagnostics=tier1_diagnostics,
            tier2_files=tier2_files or {},
            tier3_architecture=tier3_architecture,
            target_symbols_per_file=target_symbols_per_file,
            max_context_chars=max_context_chars,
            reserved_headroom_chars=reserved_headroom_chars,
        )
