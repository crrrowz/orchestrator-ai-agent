"""Completion Gate (can_complete, must_block, must_clarify) for Control Plane.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant 2: False Completion Rate Barrier (FCR == 0.000).
Invariant 3: Zero Agent Self-Certification.
"""

from __future__ import annotations

from typing import Any, Optional
from pathlib import Path
from orchestrator.pipeline.fsm.guards import (
    CompletionDecision,
    CompletionStatus,
    TaskTruthSemanticQueries,
    evaluate_task_completion,
)
from orchestrator.governance.gates.rules import verify_mandatory_criteria_satisfied


class CompletionGate:
    """Evaluates task truth completion strictly through cryptographic evidence."""

    @staticmethod
    def can_complete(graph: Optional[Any], workspace: Path) -> bool:
        ok, _ = verify_mandatory_criteria_satisfied(graph)
        if not ok:
            return False
        return TaskTruthSemanticQueries.can_complete(graph, workspace)

    @staticmethod
    def must_block(graph: Optional[Any], workspace: Path) -> bool:
        return TaskTruthSemanticQueries.must_block(graph, workspace)

    @staticmethod
    def must_clarify(graph: Optional[Any], workspace: Path) -> bool:
        return TaskTruthSemanticQueries.must_clarify(graph, workspace)

    @staticmethod
    def evaluate(graph: Optional[Any], workspace: Path) -> CompletionDecision:
        return evaluate_task_completion(graph, workspace)
