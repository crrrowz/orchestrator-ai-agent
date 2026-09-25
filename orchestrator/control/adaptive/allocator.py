"""Adaptive budget allocator for dynamic turn and token allocation per lifecycle phase.

Implements continuous task complexity scoring and phase-aware turn budgeting.
"""

from __future__ import annotations

import math
from typing import Dict, Optional

from orchestrator.control.adaptive.models import (
    PhaseBudgetProfile,
    ResourceGovernorConfig,
    ResourcePhase,
    TurnBudgetResult,
)


class AdaptiveBudgetAllocator:
    """Computes dynamic, complexity-scored turn and token budgets per FSM state."""

    PHASE_PROFILES: Dict[ResourcePhase, PhaseBudgetProfile] = {
        ResourcePhase.PREFLIGHT: PhaseBudgetProfile(
            phase=ResourcePhase.PREFLIGHT,
            base_turns=0,
            min_turns=0,
            max_turns=0,
            output_headroom_tokens=0,
            investigation_token_ratio=1.0,
        ),
        ResourcePhase.PLANNING: PhaseBudgetProfile(
            phase=ResourcePhase.PLANNING,
            base_turns=15,
            min_turns=8,
            max_turns=25,
            output_headroom_tokens=8192,
            investigation_token_ratio=1.0,
        ),
        ResourcePhase.IMPLEMENTATION: PhaseBudgetProfile(
            phase=ResourcePhase.IMPLEMENTATION,
            base_turns=10,
            min_turns=5,
            max_turns=20,
            output_headroom_tokens=4096,
            investigation_token_ratio=0.50,
        ),
        ResourcePhase.VERIFICATION: PhaseBudgetProfile(
            phase=ResourcePhase.VERIFICATION,
            base_turns=0,
            min_turns=0,
            max_turns=0,
            output_headroom_tokens=0,
            investigation_token_ratio=1.0,
        ),
        ResourcePhase.RESOLUTION: PhaseBudgetProfile(
            phase=ResourcePhase.RESOLUTION,
            base_turns=5,
            min_turns=3,
            max_turns=10,
            output_headroom_tokens=4096,
            investigation_token_ratio=0.70,
        ),
        ResourcePhase.REVIEW: PhaseBudgetProfile(
            phase=ResourcePhase.REVIEW,
            base_turns=8,
            min_turns=4,
            max_turns=12,
            output_headroom_tokens=4096,
            investigation_token_ratio=1.0,
        ),
        ResourcePhase.AUDIT: PhaseBudgetProfile(
            phase=ResourcePhase.AUDIT,
            base_turns=20,
            min_turns=10,
            max_turns=30,
            output_headroom_tokens=8192,
            investigation_token_ratio=1.0,
        ),
    }

    def __init__(self, config: Optional[ResourceGovernorConfig] = None) -> None:
        self.config = config or ResourceGovernorConfig()

    def compute_complexity_score(
        self,
        acceptance_criteria_count: int,
        dag_depth: int = 1,
        target_files_count: int = 1,
        symbol_count: int = 10,
    ) -> float:
        """Calculates a normalized task complexity score in [0.0, 1.0]."""
        c_ac = min(1.0, max(0.0, acceptance_criteria_count / 8.0))
        c_dag = min(1.0, max(0.0, dag_depth / 5.0))
        c_files = min(1.0, max(0.0, target_files_count / 6.0))
        c_symbols = min(1.0, max(0.0, symbol_count / 50.0))

        score = (0.35 * c_ac) + (0.25 * c_dag) + (0.20 * c_files) + (0.20 * c_symbols)
        return round(min(1.0, max(0.0, score)), 4)

    def allocate_turn_budget(
        self,
        phase: ResourcePhase,
        acceptance_criteria_count: int = 1,
        dag_depth: int = 1,
        target_files_count: int = 1,
        symbol_count: int = 10,
        stagnation_count: int = 0,
    ) -> TurnBudgetResult:
        """Computes the bounded turn budget for an upcoming agent session."""
        profile = self.PHASE_PROFILES.get(phase, self.PHASE_PROFILES[ResourcePhase.IMPLEMENTATION])

        if profile.base_turns == 0:
            return TurnBudgetResult(
                phase=phase,
                allocated_turns=0,
                allocated_output_tokens=0,
                complexity_score=0.0,
                stagnation_penalty=0,
                reasoning=f"Phase {phase.value} is deterministic zero-token.",
            )

        comp_score = self.compute_complexity_score(
            acceptance_criteria_count=acceptance_criteria_count,
            dag_depth=dag_depth,
            target_files_count=target_files_count,
            symbol_count=symbol_count,
        )

        stagnation_penalty = min(6, stagnation_count * 2)
        raw_turns = (profile.base_turns * (1.0 + 0.8 * comp_score)) - stagnation_penalty
        allocated_turns = max(profile.min_turns, min(int(math.floor(raw_turns)), profile.max_turns))

        reasoning = (
            f"Phase {phase.value}: base={profile.base_turns}, comp_score={comp_score:.2f}, "
            f"stagnation_penalty={stagnation_penalty} -> allocated={allocated_turns}"
        )

        return TurnBudgetResult(
            phase=phase,
            allocated_turns=allocated_turns,
            allocated_output_tokens=profile.output_headroom_tokens,
            complexity_score=comp_score,
            stagnation_penalty=stagnation_penalty,
            reasoning=reasoning,
        )
