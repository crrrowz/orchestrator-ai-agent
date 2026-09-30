"""Adaptive Iteration Governor: Authoritative lifecycle controller for agent execution streams."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set
from orchestrator.governance.budget_allocator import AdaptiveTaskBudgetAllocator
from orchestrator.governance.checkpoint_evaluator import CheckpointEvaluator
from orchestrator.governance.models import (
    ExecutionHealth,
    GovernanceAction,
    GovernanceDecision,
    ProgressMetricsSnapshot,
    StepRecord,
    TaskBudgetProfile,
)
from orchestrator.governance.progress_monitor import ProgressMonitor


class IterationGovernor:
    """Master controller of execution budgets, stagnation detection, and turn extensions."""

    def __init__(
        self,
        progress_monitor: Optional[ProgressMonitor] = None,
        evaluator: Optional[CheckpointEvaluator] = None,
    ) -> None:
        self.monitor = progress_monitor or ProgressMonitor()
        self.evaluator = evaluator or CheckpointEvaluator()
        self._history: List[GovernanceDecision] = []

    @property
    def decision_history(self) -> List[GovernanceDecision]:
        return list(self._history)

    def allocate_initial_budget(
        self,
        task_description: str,
        role: str = "developer",
        mode: Optional[str] = None,
        workspace_path: Optional[Path] = None,
        complexity_hint: float = 0.5,
    ) -> int:
        """Compute the dynamic initial turn budget tailored to the task."""
        return AdaptiveTaskBudgetAllocator.calculate_initial_budget(
            task_description=task_description,
            role=role,
            mode=mode,
            workspace_path=workspace_path,
            complexity_hint=complexity_hint,
        )

    def get_task_profile(
        self,
        task_description: str,
        role: str = "developer",
        mode: Optional[str] = None,
    ) -> TaskBudgetProfile:
        """Retrieve task budget profile and governance thresholds."""
        return AdaptiveTaskBudgetAllocator.get_profile(
            task_description=task_description, role=role, mode=mode
        )

    def evaluate_checkpoint(
        self,
        profile: TaskBudgetProfile,
        turns_used: int,
        turns_allocated: int,
        has_prior_mutations: bool = False,
    ) -> GovernanceDecision:
        """Perform a periodic or event-triggered execution check."""
        decision = self.evaluator.evaluate(
            steps=self.monitor.steps,
            profile=profile,
            turns_used=turns_used,
            turns_allocated=turns_allocated,
            agent_yielded=False,
            agent_completed_naturally=False,
            has_prior_mutations=has_prior_mutations,
        )
        self._history.append(decision)
        return decision

    def evaluate_turn_yield(
        self,
        profile: TaskBudgetProfile,
        turns_used: int,
        turns_allocated: int,
        completed_naturally: bool,
        has_prior_mutations: bool = False,
    ) -> GovernanceDecision:
        """Authoritatively evaluate the conclusion or suspension of an agent turn."""
        decision = self.evaluator.evaluate(
            steps=self.monitor.steps,
            profile=profile,
            turns_used=turns_used,
            turns_allocated=turns_allocated,
            agent_yielded=True,
            agent_completed_naturally=completed_naturally,
            has_prior_mutations=has_prior_mutations,
        )
        self._history.append(decision)
        return decision
