"""ORAGAI Control Plane & Governance Package.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestrator.governance.fsm.engine import GuardedFSMEngine, FSMContext

from orchestrator.governance.fsm import (
    CompletionDecision,
    CompletionStatus,
    EventType,
    FSMGuards,
    FSMState,
    PipelineEvent,
    StateTransition,
    TaskTruthSemanticQueries,
    TransitionEvent,
    TransitionMatrix,
    TransitionResult,
    TransitionRule,
    evaluate_task_completion,
)
from orchestrator.governance.resource import (
    AdaptiveBudgetAllocator,
    AdaptiveCircuitBreaker,
    CircuitBreakerDecision,
    CircuitState,
    ComplexityEstimator,
    MonetaryCircuitBreaker,
    PhaseBudgetProfile,
    ResourceExhaustionReason,
    ResourceGovernorConfig,
    ResourcePhase,
    TurnBudgetResult,
    compute_task_complexity,
)
from orchestrator.governance.stagnation import (
    CyclePattern,
    MutationStrategyType,
    OscillationDetector,
    ProgressHealth,
    ProgressVelocityMetrics,
    RecoveryActionType,
    RecoveryDecision,
    RecoveryOrchestrator,
    SemanticProgressTracker,
    StateFingerprint,
    StrategyMutationDirective,
    StrategyMutator,
)
from orchestrator.governance.gates import (
    CompletionGate,
    verify_mandatory_criteria_satisfied,
)
from orchestrator.governance.models import (
    ExecutionHealth,
    GovernanceAction,
    GovernanceDecision,
    ProgressMetricsSnapshot,
    StepRecord,
    TaskBudgetProfile,
    TaskCategory,
)
from orchestrator.governance.progress_metrics import ProgressMetricsCalculator
from orchestrator.governance.progress_monitor import ProgressMonitor
from orchestrator.governance.chaos_detector import ChaosDetector
from orchestrator.governance.stagnation_detector import StagnationDetector
from orchestrator.governance.budget_allocator import AdaptiveTaskBudgetAllocator
from orchestrator.governance.checkpoint_evaluator import CheckpointEvaluator
from orchestrator.governance.iteration_governor import IterationGovernor
from orchestrator.governance.governance_policy import DEFAULT_TASK_PROFILES


def __getattr__(name: str):
    if name == "GuardedFSMEngine":
        from orchestrator.pipeline.fsm.engine import GuardedFSMEngine
        return GuardedFSMEngine
    if name == "FSMContext":
        from orchestrator.pipeline.fsm.context import FSMContext
        return FSMContext
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
    "ComplexityEstimator",
    "compute_task_complexity",
    "AdaptiveBudgetAllocator",
    "PhaseBudgetProfile",
    "ResourceGovernorConfig",
    "ResourcePhase",
    "TurnBudgetResult",
    "MonetaryCircuitBreaker",
    "AdaptiveCircuitBreaker",
    "CircuitBreakerDecision",
    "CircuitState",
    "ResourceExhaustionReason",
    "SemanticProgressTracker",
    "ProgressHealth",
    "ProgressVelocityMetrics",
    "StateFingerprint",
    "CyclePattern",
    "OscillationDetector",
    "RecoveryOrchestrator",
    "StrategyMutator",
    "MutationStrategyType",
    "RecoveryActionType",
    "RecoveryDecision",
    "StrategyMutationDirective",
    "CompletionGate",
    "verify_mandatory_criteria_satisfied",
    "ExecutionHealth",
    "GovernanceAction",
    "GovernanceDecision",
    "ProgressMetricsSnapshot",
    "StepRecord",
    "TaskBudgetProfile",
    "TaskCategory",
    "ProgressMetricsCalculator",
    "ProgressMonitor",
    "ChaosDetector",
    "StagnationDetector",
    "AdaptiveTaskBudgetAllocator",
    "CheckpointEvaluator",
    "IterationGovernor",
    "DEFAULT_TASK_PROFILES",
]
