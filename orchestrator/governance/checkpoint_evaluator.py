"""Checkpoint Evaluator: Analyzes trajectory and makes authoritative governance recommendations."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence
from orchestrator.governance.chaos_detector import ChaosDetector
from orchestrator.governance.models import (
    ExecutionHealth,
    GovernanceAction,
    GovernanceDecision,
    ProgressMetricsSnapshot,
    StepRecord,
    TaskBudgetProfile,
)
from orchestrator.governance.progress_metrics import ProgressMetricsCalculator
from orchestrator.governance.stagnation_detector import StagnationDetector


class CheckpointEvaluator:
    """Evaluates agent execution stream at periodic checkpoints and turn yields."""

    def __init__(
        self,
        chaos_detector: Optional[ChaosDetector] = None,
        stagnation_detector: Optional[StagnationDetector] = None,
    ) -> None:
        self.chaos_detector = chaos_detector or ChaosDetector()
        self.stagnation_detector = stagnation_detector or StagnationDetector()

    def evaluate(
        self,
        steps: Sequence[StepRecord],
        profile: TaskBudgetProfile,
        turns_used: int,
        turns_allocated: int,
        agent_yielded: bool = False,
        agent_completed_naturally: bool = False,
        has_prior_mutations: bool = False,
    ) -> GovernanceDecision:
        """Evaluate current step telemetry and determine the authoritative governance action."""
        metrics: ProgressMetricsSnapshot = ProgressMetricsCalculator.calculate(steps)

        # 1. Chaos evaluation
        is_chaotic, chaos_reason = self.chaos_detector.check_chaos(steps)
        if is_chaotic:
            return GovernanceDecision(
                action=GovernanceAction.CHANGE_STRATEGY,
                health=ExecutionHealth.CHAOTIC,
                reason=chaos_reason,
                recommended_directive=(
                    "Halt repeating failed commands or tool errors. Verify environment requirements, "
                    "paths, and syntax before proceeding."
                ),
                confidence=0.95,
                evidence=metrics.model_dump(),
            )

        # 2. Stagnation evaluation
        is_stagnant, stagnation_reason = self.stagnation_detector.check_stagnation(
            steps, has_prior_mutations=has_prior_mutations
        )
        if is_stagnant:
            return GovernanceDecision(
                action=GovernanceAction.CHANGE_STRATEGY,
                health=ExecutionHealth.STAGNANT,
                reason=stagnation_reason,
                recommended_directive=(
                    "Cease repetitive reading operations. Commit the required code modifications "
                    "to targeted files now."
                ),
                confidence=0.90,
                evidence=metrics.model_dump(),
            )

        # 3. Handle Natural Yield / Completion
        if agent_yielded:
            if agent_completed_naturally:
                return GovernanceDecision(
                    action=GovernanceAction.VERIFY_COMPLETION,
                    health=ExecutionHealth.HEALTHY,
                    reason="Agent completed turn naturally; proceed to independent verification gate.",
                    confidence=1.0,
                    evidence=metrics.model_dump(),
                )
            else:
                # Agent yielded due to step limit or resource boundary
                # Check if eligible for budget extension
                has_mutations = metrics.mutation_steps > 0 or has_prior_mutations
                can_extend = (
                    turns_allocated + profile.max_extension_turns <= profile.max_total_ceiling_turns
                    and has_mutations
                    and metrics.error_rate < 0.40
                )
                if can_extend:
                    extension = min(
                        profile.max_extension_turns,
                        profile.max_total_ceiling_turns - turns_allocated,
                    )
                    return GovernanceDecision(
                        action=GovernanceAction.EXTEND_BUDGET,
                        health=ExecutionHealth.PROGRESSING,
                        reason=(
                            f"Agent reached turn envelope limit ({turns_allocated} turns) but demonstrates active "
                            f"mutations ({metrics.mutation_steps} mutation steps, {metrics.unique_files_mutated} files). "
                            f"Extending budget by {extension} turns."
                        ),
                        allocated_turns_extension=extension,
                        confidence=0.88,
                        evidence=metrics.model_dump(),
                    )
                else:
                    return GovernanceDecision(
                        action=GovernanceAction.FAIL,
                        health=ExecutionHealth.EXHAUSTED,
                        reason=(
                            f"Turn budget exhausted ({turns_allocated} turns) with insufficient progress or "
                            "ceiling reached without natural completion."
                        ),
                        confidence=0.95,
                        evidence=metrics.model_dump(),
                    )

        # 4. Mid-turn execution status
        return GovernanceDecision(
            action=GovernanceAction.CONTINUE,
            health=ExecutionHealth.PROGRESSING if metrics.mutation_steps > 0 else ExecutionHealth.HEALTHY,
            reason=f"Execution proceeding nominally ({turns_used}/{turns_allocated} turns used).",
            confidence=1.0,
            evidence=metrics.model_dump(),
        )
