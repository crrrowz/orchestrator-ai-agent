"""Milestone DAG Dispatcher for Autonomous Workstream Execution.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Section 4 Step 2: Kahn's Topological Execution.
"""

from __future__ import annotations

from typing import List, Optional
from orchestrator.pipeline.milestone_dag import MilestoneParser, SubtaskMilestone
from orchestrator.workstreams.milestone_dag.resolver import MilestoneDependencyResolver


class MilestoneDAGDispatcher:
    """Dispatches milestones in strict topological order."""

    def __init__(self, milestones: List[SubtaskMilestone]):
        self.milestones = milestones
        self.resolver = MilestoneDependencyResolver()

    def get_execution_order(self) -> List[SubtaskMilestone]:
        return self.resolver.resolve_topological_order(self.milestones)

    def validate_dag(self) -> bool:
        cycles = self.resolver.detect_cycles(self.milestones)
        return len(cycles) == 0
