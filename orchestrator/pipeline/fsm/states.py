"""FSMState taxonomy and lifecycle phase definitions for Guarded FSM Engine."""

from enum import Enum
from typing import Set


class FSMState(str, Enum):
    """Discrete lifecycle states of the Guarded FSM Engine.

    Replaces passive dictionary routing with 11 mathematically defined,
    evidence-gated states.
    """

    INIT = "INIT"
    """Workspace initialization, configuration loading, and environment discovery."""

    PREFLIGHT = "PREFLIGHT"
    """Zero-token static validation (syntax check, adapter detection, baseline importability)."""

    PLANNING = "PLANNING"
    """Architect agent generates requirement decomposition, acceptance criteria, and Milestone DAG."""

    IMPLEMENTATION = "IMPLEMENTATION"
    """Developer / Fixer agent authors or modifies source code for active milestone."""

    VERIFICATION = "VERIFICATION"
    """Deterministic static checks, pytest runs, and P2.1 evidence gate evaluation."""

    RESOLUTION = "RESOLUTION"
    """Intelligent failure triage, remediation routing, and progress stagnation analysis."""

    REVIEW = "REVIEW"
    """Independent architectural and security assessment by Reviewer / Auditor agent."""

    BLOCKED = "BLOCKED"
    """Execution halted due to environmental failure, missing credentials, or human intervention requirement."""

    AMBIGUOUS = "AMBIGUOUS"
    """Execution halted due to conflicting requirements or impossible acceptance criteria."""

    COMPLETED = "COMPLETED"
    """Terminal state: Task verified complete by CompletionGate; atomic Git commit executed."""

    FAILED = "FAILED"
    """Terminal state: Unrecoverable error, invariant violation, or retry limit exhaustion."""

    ABORTED = "ABORTED"
    """Terminal state: User cancellation or external controller abort signal."""

    @property
    def is_terminal(self) -> bool:
        """Return True if state represents a concluding terminal state."""
        return self in (FSMState.COMPLETED, FSMState.FAILED, FSMState.ABORTED)

    @property
    def is_active(self) -> bool:
        """Return True if state represents an ongoing active execution phase."""
        return not self.is_terminal

    @classmethod
    def terminal_states(cls) -> Set["FSMState"]:
        """Set of all terminal states."""
        return {cls.COMPLETED, cls.FAILED, cls.ABORTED}

    @classmethod
    def recoverable_states(cls) -> Set["FSMState"]:
        """Set of non-terminal states that can participate in recovery loops."""
        return {
            cls.INIT,
            cls.PREFLIGHT,
            cls.PLANNING,
            cls.IMPLEMENTATION,
            cls.VERIFICATION,
            cls.RESOLUTION,
            cls.REVIEW,
            cls.BLOCKED,
            cls.AMBIGUOUS,
        }
