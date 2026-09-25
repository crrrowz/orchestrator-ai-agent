"""Adaptive Circuit Breaker for ORAGAI (P8).

Implements 4-tier state machine transitions:
CLOSED -> DEGRADED -> STRATEGY_MUTATING -> TRIPPED_ESCALATING.

Operational Semantics:
1. CLOSED:
   - System operating efficiently (ProgressHealth.THRIVING or MAKING_PROGRESS).
   - Resets failure / cycle counters to zero.
2. DEGRADED:
   - Triggered on 1 stagnant turn or marginal churn.
   - Tightens budgets via stagnation penalty.
3. STRATEGY_MUTATING:
   - Triggered on 2 consecutive stagnant turns, detection of cycle (p >= 2), or test regression.
   - Invokes StrategyMutator according to 4-tier taxonomy.
4. TRIPPED_ESCALATING:
   - Triggered when all 4 mutation levels have been attempted without positive verification progress.
   - Quarantines milestone / escalates to HITL.
"""

from __future__ import annotations

from .models import (
    BreakerState,
    CyclePattern,
    ProgressHealth,
    ProgressVelocityMetrics,
)


class AdaptiveCircuitBreaker:
    """
    4-Tier Adaptive Circuit Breaker managing transitions:
    CLOSED -> DEGRADED -> STRATEGY_MUTATING -> TRIPPED_ESCALATING.
    """

    def __init__(self, max_mutation_tiers: int = 4):
        self.state: BreakerState = BreakerState.CLOSED
        self.stagnation_counter: int = 0
        self.mutation_tier_level: int = 0
        self.max_mutation_tiers: int = max_mutation_tiers

    def evaluate_state_transition(
        self,
        metrics: ProgressVelocityMetrics,
        cycle_pattern: CyclePattern,
    ) -> BreakerState:
        """
        Evaluate progress metrics and cycle detection to transition breaker state.
        """
        # Positive verification progress resets or relaxes breaker
        if metrics.health in (ProgressHealth.THRIVING, ProgressHealth.MAKING_PROGRESS) and metrics.v_verif >= 0:
            self.stagnation_counter = max(0, self.stagnation_counter - 1)
            if self.stagnation_counter == 0:
                self.state = BreakerState.CLOSED
                self.mutation_tier_level = 0
            return self.state

        # Immediate escalation on detected cyclic oscillation (p >= 2)
        if cycle_pattern in (CyclePattern.FLIP_FLOP_P2, CyclePattern.PERIODIC_PN):
            self.stagnation_counter += 2
            if self.mutation_tier_level >= self.max_mutation_tiers:
                self.state = BreakerState.TRIPPED_ESCALATING
            else:
                self.state = BreakerState.STRATEGY_MUTATING
                self.mutation_tier_level = min(self.max_mutation_tiers, self.mutation_tier_level + 1)
            return self.state

        # Stagnant, Regressing, or Marginal Churn turn
        if metrics.health in (
            ProgressHealth.STAGNANT,
            ProgressHealth.REGRESSING,
            ProgressHealth.MARGINAL_CHURN,
        ):
            self.stagnation_counter += 1

            if self.stagnation_counter == 1:
                self.state = BreakerState.DEGRADED
            elif self.stagnation_counter >= 2:
                if self.mutation_tier_level >= self.max_mutation_tiers:
                    self.state = BreakerState.TRIPPED_ESCALATING
                else:
                    self.state = BreakerState.STRATEGY_MUTATING
                    self.mutation_tier_level = min(self.max_mutation_tiers, self.mutation_tier_level + 1)

        return self.state

    def reset(self) -> None:
        """Fully reset breaker state to initial CLOSED."""
        self.state = BreakerState.CLOSED
        self.stagnation_counter = 0
        self.mutation_tier_level = 0
