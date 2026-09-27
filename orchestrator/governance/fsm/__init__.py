"""FSM Package for ORAGAI Governance Control Plane.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from orchestrator.governance.fsm.engine import GuardedFSMEngine, FSMContext
from orchestrator.governance.fsm.states import (
    FSMState,
    EventType,
    TransitionEvent,
    PipelineEvent,
    TransitionRule,
    StateTransition,
    TransitionResult,
    TransitionMatrix,
)
from orchestrator.governance.fsm.guards import (
    CompletionDecision,
    CompletionStatus,
    FSMGuards,
    TaskTruthSemanticQueries,
    evaluate_task_completion,
)

__all__ = [
    "GuardedFSMEngine",
    "FSMContext",
    "FSMState",
    "EventType",
    "TransitionEvent",
    "PipelineEvent",
    "TransitionRule",
    "StateTransition",
    "TransitionResult",
    "TransitionMatrix",
    "CompletionDecision",
    "CompletionStatus",
    "FSMGuards",
    "TaskTruthSemanticQueries",
    "evaluate_task_completion",
]
