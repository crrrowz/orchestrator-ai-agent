"""Guarded Finite State Machine and Lifecycle Orchestration Subpackage.

Implements event-driven lifecycle management, pure semantic query guards (P2.1),
deterministic transition rules, lifecycle profiles, cryptographic checkpoints,
and bounded ephemeral OpenHands session execution.
"""

from orchestrator.pipeline.fsm.checkpoint import (
    FSMCheckpoint,
    FSMCheckpointManager,
    MilestoneStateSnapshot,
)
from orchestrator.pipeline.fsm.engine import FSMContext, GuardedFSMEngine
from orchestrator.pipeline.fsm.events import (
    AgentExecutionOutcome,
    EventType,
    PipelineEvent,
)
from orchestrator.pipeline.fsm.guards import (
    CompletionDecision,
    CompletionStatus,
    FSMGuards,
    ImplementationState,
    RequirementStatus,
    TaskTruthSemanticQueries,
    VerificationState,
    evaluate_task_completion,
)
from orchestrator.pipeline.fsm.profiles import (
    PROFILES,
    LifecycleProfile,
    PipelineMode,
    get_profile,
)
from orchestrator.pipeline.fsm.states import FSMState
from orchestrator.pipeline.fsm.transitions import (
    TransitionMatrix,
    TransitionResult,
    TransitionRule,
)

__all__ = [
    "FSMState",
    "EventType",
    "AgentExecutionOutcome",
    "PipelineEvent",
    "ImplementationState",
    "VerificationState",
    "RequirementStatus",
    "CompletionStatus",
    "CompletionDecision",
    "evaluate_task_completion",
    "TaskTruthSemanticQueries",
    "FSMGuards",
    "PipelineMode",
    "LifecycleProfile",
    "PROFILES",
    "get_profile",
    "TransitionRule",
    "TransitionResult",
    "TransitionMatrix",
    "MilestoneStateSnapshot",
    "FSMCheckpoint",
    "FSMCheckpointManager",
    "FSMContext",
    "GuardedFSMEngine",
]
