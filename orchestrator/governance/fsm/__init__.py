"""FSM Package for ORAGAI Governance Control Plane.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
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

def __getattr__(name: str):
    if name in ("GuardedFSMEngine", "FSMContext"):
        import orchestrator.governance.fsm.engine as _e
        return getattr(_e, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
