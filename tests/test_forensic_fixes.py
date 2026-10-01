"""Tests verifying forensic fixes for ORAGAI execution reliability."""

from pathlib import Path
from unittest.mock import MagicMock

from orchestrator.config import OrchestratorConfig
from orchestrator.domain.task_truth import TaskTruthGraph
from orchestrator.engine.openhands_bridge import (
    AgentExecutionOutcome as BridgeAgentOutcome,
    AgentExitReason,
)
from orchestrator.governance.models import (
    ExecutionHealth,
    GovernanceAction,
    GovernanceDecision,
)
from orchestrator.pipeline.fsm.checkpoint import FSMCheckpointManager
from orchestrator.pipeline.fsm.engine import GuardedFSMEngine
from orchestrator.pipeline.fsm.events import EventType, PipelineEvent
from orchestrator.pipeline.fsm.guards import CompletionDecision, CompletionStatus
from orchestrator.pipeline.fsm.profiles import PipelineMode, get_profile
from orchestrator.pipeline.fsm.states import FSMState
from orchestrator.pipeline.milestone_dag import SubtaskMilestone


def test_f001_and_f010_all_profiles_allow_blocked_state():
    """F-001 & F-010: Ensure BLOCKED state is in allowed_states across all profiles."""
    for mode in PipelineMode:
        profile = get_profile(mode)
        assert FSMState.BLOCKED in profile.allowed_states, f"Profile {mode} missing BLOCKED"
        assert FSMState.ABORTED in profile.allowed_states, f"Profile {mode} missing ABORTED"


def test_f004_checkpoint_symmetric_context_restoration(tmp_path: Path):
    """F-004: Ensure full context (DAG, TTG, mutated_files, stagnation) is restored."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )
    engine.context.task_description = "Refactor auth"
    engine.context.mutated_files = {"src/auth.py", "tests/test_auth.py"}
    engine.context.stagnation_counter = 2
    engine.context.active_milestone_id = "2"
    engine.context.active_milestone_index = 1
    engine.context.milestone_dag = [
        SubtaskMilestone(index=1, title="M1", content="Content 1", is_completed=True),
        SubtaskMilestone(index=2, title="M2", content="Content 2", is_completed=False),
    ]
    ttg = TaskTruthGraph(
        task_id="T1",
        raw_prompt="Refactor auth",
        workspace_root=str(tmp_path),
        created_at_utc="2026-10-01T00:00:00Z",
    )
    engine.context.task_truth_graph = ttg

    ckpt_path = FSMCheckpointManager.save_checkpoint(engine.context)
    assert ckpt_path.exists()

    # Load and resume in a fresh engine
    resumed_engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )
    ckpt = FSMCheckpointManager.load_checkpoint(tmp_path)
    assert ckpt is not None
    resumed_engine._resume_from_checkpoint(ckpt)

    assert resumed_engine.context.mutated_files == {"src/auth.py", "tests/test_auth.py"}
    assert resumed_engine.context.stagnation_counter == 2
    assert len(resumed_engine.context.milestone_dag) == 2
    assert resumed_engine.context.milestone_dag[0].is_completed is True
    assert resumed_engine.context.milestone_dag[1].content == "Content 2"
    assert resumed_engine.context.task_truth_graph is not None
    assert resumed_engine.context.task_truth_graph.task_id == "T1"


def test_f006_and_f003_governance_budget_extension_and_directive(tmp_path: Path):
    """F-006 & F-003: Check that budget extensions and CHANGE_STRATEGY directives are consumed."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )
    engine.context.task_description = "Fix critical bug"
    engine.context.metadata["governance_decision"] = {
        "action": "EXTEND_BUDGET",
        "allocated_turns_extension": 4,
        "health": "PROGRESSING",
    }
    engine.context.metadata["governance_directive"] = "Commit fixes directly."

    # Verify implementation builds prompt and applies extension
    mock_bridge = MagicMock()
    mock_outcome = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=1,
        max_iterations_allocated=12,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=("src/fix.py",),
        final_thought="Fixed",
    )
    mock_bridge.execute_bounded_turn.return_value = mock_outcome
    engine.runtime_bridge = mock_bridge
    engine.llm_manager = MagicMock()

    ev = engine._handle_implementation()
    assert ev.event_type == EventType.AGENT_YIELDED

    call_args = mock_bridge.execute_bounded_turn.call_args
    assert call_args is not None
    # Verify prompt received directive
    prompt = call_args.kwargs["prompt_view"].compiled_prompt
    assert "Strategic Directive from Governance Watchdog" in prompt or "MANDATORY GOVERNANCE DIRECTIVE" in prompt
    # Verify turn envelope received budget extension
    turn_env = call_args.kwargs["turn_envelope"]
    assert turn_env.max_turns >= 12  # Base 8 + extension 4


def test_f005_audit_fix_zero_mutation_rejection(tmp_path: Path):
    """F-005: Audit-fix mode does not accept passing tests if zero code mutations were made."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.AUDIT_FIX),
        workspace_path=tmp_path,
    )
    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, summary="All passed")
    engine.context.adapter = mock_adapter
    engine.context.mutated_files = set()  # Zero mutations

    ev = engine._handle_verification()
    decision: CompletionDecision = ev.payload["decision"]
    assert decision.status == CompletionStatus.INCOMPLETE
    assert "requires verified code modifications" in decision.blocking_reasons[0]


def test_f014_cost_tracking_computed_on_tokens(tmp_path: Path):
    """F-014: Check that token usage computes non-zero cost in classification."""
    from orchestrator.engine.openhands_bridge import ExitStatusClassifier

    conv_mock = MagicMock()
    conv_mock.state.execution_status.name = "FINISHED"
    conv_mock.state.events = []
    llm_metrics = MagicMock()
    llm_metrics.accumulated_token_usage.prompt_tokens = 1000
    llm_metrics.accumulated_token_usage.completion_tokens = 500
    conv_mock.agent.llm.metrics = llm_metrics

    from openhands.sdk import ConversationExecutionStatus
    outcome = ExitStatusClassifier.classify(
        conv=conv_mock,
        role="developer",
        initial_tokens=0,
        max_turns=8,
        token_ceiling=100000,
        mutated_files=[],
    )
    assert outcome.total_tokens == 1500
    assert outcome.cost_usd > 0.0
