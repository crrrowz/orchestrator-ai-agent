"""Pipeline Finite State Machine (FSM) for dynamic stage orchestration."""

from enum import Enum
from typing import Set, Dict, List


class PipelinePhase(str, Enum):
    """Enumeration of all discrete pipeline lifecycle phases."""

    INIT = "init"
    ARCHITECT = "architect"
    DEVELOP = "develop"
    PREFLIGHT = "preflight"
    TEST = "test"
    FIX = "fix"
    REVIEW = "review"
    HUMAN_GATE = "human_gate"
    COMMIT = "commit"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class PipelineStateMachine:
    """Non-linear, extensible state machine orchestrating agent transitions and checkpoints."""

    # Explicit allowed transitions graph
    ALLOWED_TRANSITIONS: Dict[PipelinePhase, Set[PipelinePhase]] = {
        PipelinePhase.INIT: {
            PipelinePhase.ARCHITECT,
            PipelinePhase.DEVELOP,
            PipelinePhase.ABORTED,
            PipelinePhase.FAILED,
        },
        PipelinePhase.ARCHITECT: {
            PipelinePhase.HUMAN_GATE,
            PipelinePhase.DEVELOP,
            PipelinePhase.FAILED,
            PipelinePhase.ABORTED,
        },
        PipelinePhase.DEVELOP: {
            PipelinePhase.PREFLIGHT,
            PipelinePhase.HUMAN_GATE,
            PipelinePhase.TEST,
            PipelinePhase.FAILED,
            PipelinePhase.ABORTED,
        },
        PipelinePhase.PREFLIGHT: {
            PipelinePhase.DEVELOP,
            PipelinePhase.TEST,
            PipelinePhase.FAILED,
            PipelinePhase.ABORTED,
        },
        PipelinePhase.TEST: {
            PipelinePhase.FIX,
            PipelinePhase.REVIEW,
            PipelinePhase.COMMIT,
            PipelinePhase.COMPLETED,
            PipelinePhase.FAILED,
            PipelinePhase.ABORTED,
        },
        PipelinePhase.FIX: {
            PipelinePhase.PREFLIGHT,
            PipelinePhase.TEST,
            PipelinePhase.FAILED,
            PipelinePhase.ABORTED,
        },
        PipelinePhase.REVIEW: {
            PipelinePhase.DEVELOP,
            PipelinePhase.COMMIT,
            PipelinePhase.COMPLETED,
            PipelinePhase.FAILED,
            PipelinePhase.ABORTED,
        },
        PipelinePhase.HUMAN_GATE: {
            PipelinePhase.DEVELOP,
            PipelinePhase.TEST,
            PipelinePhase.COMMIT,
            PipelinePhase.COMPLETED,
            PipelinePhase.ABORTED,
            PipelinePhase.FAILED,
        },
        PipelinePhase.COMMIT: {
            PipelinePhase.COMPLETED,
            PipelinePhase.FAILED,
            PipelinePhase.ABORTED,
        },
        PipelinePhase.COMPLETED: set(),
        PipelinePhase.FAILED: set(),
        PipelinePhase.ABORTED: set(),
    }

    def __init__(self, initial_phase: PipelinePhase = PipelinePhase.INIT):
        self._current_phase = initial_phase
        self._history: List[PipelinePhase] = [initial_phase]

    @property
    def current_phase(self) -> PipelinePhase:
        """Active phase of the pipeline."""
        return self._current_phase

    @property
    def history(self) -> List[PipelinePhase]:
        """Chronological record of visited phases."""
        return list(self._history)

    def can_transition(self, target: PipelinePhase) -> bool:
        """Validate whether a transition to target phase is permissible."""
        valid_next = self.ALLOWED_TRANSITIONS.get(self._current_phase, set())
        return target in valid_next

    def transition_to(self, target: PipelinePhase) -> PipelinePhase:
        """Advance the state machine to target phase, raising ValueError on illegal transition."""
        if not self.can_transition(target):
            raise ValueError(
                f"Illegal state transition from '{self._current_phase.value}' to '{target.value}'."
            )
        self._current_phase = target
        self._history.append(target)
        return self._current_phase

    def is_terminal(self) -> bool:
        """Check if pipeline has reached a concluding terminal state."""
        return self._current_phase in (
            PipelinePhase.COMPLETED,
            PipelinePhase.FAILED,
            PipelinePhase.ABORTED,
        )
