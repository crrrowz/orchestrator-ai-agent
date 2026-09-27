"""FSM States and Transitions for ORAGAI Governance Control Plane.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from orchestrator.pipeline.fsm.states import FSMState
from orchestrator.pipeline.fsm.events import EventType, PipelineEvent
from orchestrator.pipeline.fsm.transitions import (
    TransitionMatrix,
    TransitionResult,
    TransitionRule,
)

StateTransition = TransitionRule
TransitionEvent = EventType

__all__ = [
    "FSMState",
    "EventType",
    "TransitionEvent",
    "PipelineEvent",
    "TransitionRule",
    "StateTransition",
    "TransitionResult",
    "TransitionMatrix",
]
