"""Pipeline package containing execution flows."""

from .audit_fix_pipeline import AuditFixPipeline
from .audit_pipeline import AuditPipeline
from .audit_report_io import locate_and_normalize_report, read_report
from .base_pipeline import BasePipeline
from .checkpoint import PipelineCheckpoint, PipelineCheckpointManager
from .dev_test_loop import DevTestLoop
from .documentation_pipeline import DocumentationPipeline
from .full_pipeline import FullPipeline
from .milestone_dag import MilestoneParser, SubtaskMilestone
from .reviewer_parser import ReviewerVerdict
from .state_machine import PipelinePhase, PipelineStateMachine
from .dispatcher import OrchestratorDispatcher, StranglerPipelineDispatcher
from .migration_guard import (
    CircuitBreakerStatus,
    ExecutionPlane,
    MigrationGuard,
    MigrationRoutingConfig,
)
from .fsm import (
    CompletionDecision,
    CompletionStatus,
    EventType,
    FSMCheckpoint,
    FSMCheckpointManager,
    FSMGuards,
    FSMState,
    GuardedFSMEngine,
    LifecycleProfile,
    PipelineMode,
    PipelineEvent,
    TaskTruthSemanticQueries,
    evaluate_task_completion,
    get_profile,
)

__all__ = [
    "BasePipeline",
    "DevTestLoop",
    "FullPipeline",
    "AuditPipeline",
    "AuditFixPipeline",
    "DocumentationPipeline",
    "PipelineStateMachine",
    "PipelinePhase",
    "MilestoneParser",
    "SubtaskMilestone",
    "PipelineCheckpointManager",
    "PipelineCheckpoint",
    "ReviewerVerdict",
    "locate_and_normalize_report",
    "read_report",
    "FSMState",
    "EventType",
    "PipelineEvent",
    "GuardedFSMEngine",
    "LifecycleProfile",
    "PipelineMode",
    "get_profile",
    "FSMCheckpoint",
    "FSMCheckpointManager",
    "FSMGuards",
    "TaskTruthSemanticQueries",
    "CompletionDecision",
    "CompletionStatus",
    "evaluate_task_completion",
    "OrchestratorDispatcher",
    "StranglerPipelineDispatcher",
    "MigrationGuard",
    "ExecutionPlane",
    "CircuitBreakerStatus",
    "MigrationRoutingConfig",
]
