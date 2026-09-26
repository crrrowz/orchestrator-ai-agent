"""Runtime context definition for GuardedFSMEngine."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from orchestrator.adapters import ProjectAdapter
from orchestrator.analysis.pytest_parser import TestExecutionResult
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.control.adaptive import AdaptiveResourceGovernor
from orchestrator.control.human_channel import HumanChannel
from orchestrator.control.pipeline_controller import PipelineController
from orchestrator.engine.openhands_bridge import (
    AgentExecutionOutcome as BridgeAgentOutcome,
    OpenHandsRuntimeBridge,
)
from orchestrator.pipeline.fsm.guards import CompletionDecision
from orchestrator.pipeline.fsm.profiles import LifecycleProfile
from orchestrator.pipeline.fsm.states import FSMState
from orchestrator.pipeline.milestone_dag import SubtaskMilestone
from orchestrator.pipeline.reviewer_parser import ReviewerVerdict
from orchestrator.tools.hardened.manager import ToolSandboxManager
from orchestrator.vcs.git_ops import GitOps


@dataclass
class FSMContext:
    """Encapsulates the mutable runtime execution context for GuardedFSMEngine."""

    workspace_path: Path
    config: OrchestratorConfig
    profile: LifecycleProfile
    task_description: str = ""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    current_state: FSMState = FSMState.INIT
    state_history: List[FSMState] = field(default_factory=lambda: [FSMState.INIT])
    task_truth_graph: Optional[Any] = None
    milestone_dag: List[SubtaskMilestone] = field(default_factory=list)
    active_milestone_id: Optional[str] = None
    active_milestone_index: int = 0
    iteration_count: int = 0
    stagnation_counter: int = 0
    last_workspace_hash: Optional[str] = None
    current_workspace_hash: Optional[str] = None
    last_outcome: Optional[BridgeAgentOutcome] = None
    last_verification_decision: Optional[CompletionDecision] = None
    last_test_result: Optional[TestExecutionResult] = None
    last_audit_result: Optional[Any] = None
    review_verdict: Optional[ReviewerVerdict] = None
    total_tokens_consumed: int = 0
    total_cost_usd: float = 0.0
    mutated_files: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    controller: Optional[PipelineController] = None
    human_channel: Optional[HumanChannel] = None
    skill_manager: Optional[SkillManager] = None
    llm_manager: Optional[Any] = None
    runtime_bridge: Optional[OpenHandsRuntimeBridge] = None
    sandbox_manager: Optional[ToolSandboxManager] = None
    log_store: Optional[Any] = None
    visualizer: Optional[Any] = None
    diagnostics_db: Optional[Any] = None
    git_ops: Optional[GitOps] = None
    adapter: Optional[ProjectAdapter] = None
    governor: Optional[AdaptiveResourceGovernor] = None
