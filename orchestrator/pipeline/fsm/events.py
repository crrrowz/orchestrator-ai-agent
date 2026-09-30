"""Pipeline Event schemas and Agent Execution outcome models for Guarded FSM."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple
import uuid

from orchestrator.pipeline.fsm.states import FSMState


class EventType(str, Enum):
    """Discrete event types triggering state transitions in the Guarded FSM Engine."""

    # Initialization & Preflight
    START_TASK = "START_TASK"
    PREFLIGHT_PASSED = "PREFLIGHT_PASSED"
    PREFLIGHT_FAILED = "PREFLIGHT_FAILED"

    # Planning
    PLAN_GENERATED = "PLAN_GENERATED"
    PLAN_REJECTED = "PLAN_REJECTED"
    REPLAN_TRIGGERED = "REPLAN_TRIGGERED"

    # Implementation
    MILESTONE_STARTED = "MILESTONE_STARTED"
    AGENT_YIELDED = "AGENT_YIELDED"

    # Verification
    VERIFICATION_REQUESTED = "VERIFICATION_REQUESTED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"

    # Resolution & Recovery
    REMEDIATION_ROUTED = "REMEDIATION_ROUTED"
    STAGNATION_DETECTED = "STAGNATION_DETECTED"
    RETRIES_EXHAUSTED = "RETRIES_EXHAUSTED"

    # Review
    REVIEW_REQUESTED = "REVIEW_REQUESTED"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    REVIEW_REJECTED = "REVIEW_REJECTED"

    # Edge & Terminal
    HUMAN_INTERVENTION_REQUIRED = "HUMAN_INTERVENTION_REQUIRED"
    HUMAN_INPUT_RECEIVED = "HUMAN_INPUT_RECEIVED"
    CRITICAL_ERROR = "CRITICAL_ERROR"
    ABORT_REQUESTED = "ABORT_REQUESTED"


class AgentExecutionOutcome(str, Enum):
    """Detailed outcome classification from an OpenHands ephemeral agent turn yield."""

    NATURAL_COMPLETION = "NATURAL_COMPLETION"
    STEP_LIMIT_REACHED = "STEP_LIMIT_REACHED"
    TOKEN_LIMIT_REACHED = "TOKEN_LIMIT_REACHED"
    TOOL_ERROR = "TOOL_ERROR"
    STAGNANT_DIFF = "STAGNANT_DIFF"
    INTERRUPTED = "INTERRUPTED"
    FATAL_ERROR = "FATAL_ERROR"
    TOOL_REJECTION = "TOOL_REJECTION"
    AGENT_STUCK = "AGENT_STUCK"
    ABORTED = "ABORTED"


@dataclass(frozen=True)
class PipelineEvent:
    """Immutable event payload processed by the GuardedFSMEngine."""

    event_type: EventType
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    source_phase: FSMState = FSMState.INIT
    active_milestone_id: Optional[str] = None
    execution_outcome: Optional[AgentExecutionOutcome] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
