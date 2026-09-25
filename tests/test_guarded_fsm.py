"""Comprehensive unit and integration test suite for GuardedFSMEngine (Phase 4).

Validates FSMState taxonomy, strongly typed PipelineEvents, pure TaskTruthSemanticQueries,
FSMGuards, TransitionMatrix, LifecycleProfiles, cryptographic FSMCheckpointManager,
and end-to-end event-driven orchestration loops.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.control.pipeline_controller import PipelineController
from orchestrator.engine.openhands_bridge import (
    AgentExecutionOutcome as BridgeAgentOutcome,
    AgentExitReason,
    OpenHandsRuntimeBridge,
    PromptView,
    TurnEnvelope,
)
from orchestrator.pipeline.fsm import (
    CompletionDecision,
    CompletionStatus,
    EventType,
    FSMCheckpoint,
    FSMCheckpointManager,
    FSMContext,
    FSMGuards,
    FSMState,
    GuardedFSMEngine,
    ImplementationState,
    LifecycleProfile,
    MilestoneStateSnapshot,
    PipelineEvent,
    PipelineMode,
    RequirementStatus,
    TaskTruthSemanticQueries,
    TransitionMatrix,
    TransitionResult,
    TransitionRule,
    VerificationState,
    evaluate_task_completion,
    get_profile,
)
from orchestrator.pipeline.fsm.events import AgentExecutionOutcome
from orchestrator.pipeline.milestone_dag import SubtaskMilestone


# =============================================================================
# Helper Models for Task Truth Mocking
# =============================================================================


class MockCriterion(BaseModel):
    id: str
    description: str = "Test criterion"
    is_mandatory: bool = True
    status: VerificationState = VerificationState.UNVERIFIED
    verification_state: VerificationState = VerificationState.UNVERIFIED


class MockRequirement(BaseModel):
    id: str
    title: str = "Requirement"
    is_mandatory: bool = True
    implementation_state: ImplementationState = ImplementationState.NOT_STARTED
    verification_state: VerificationState = VerificationState.UNVERIFIED
    status: RequirementStatus = RequirementStatus.DRAFT
    dependencies: List[str] = Field(default_factory=list)
    acceptance_criteria: List[MockCriterion] = Field(default_factory=list)


class MockTaskTruthGraph(BaseModel):
    task_id: str = "TASK-001"
    requirements: List[MockRequirement] = Field(default_factory=list)
    external_dependency_blocked: bool = False
    blocker_reason: Optional[str] = None
    has_unresolved_mutations: bool = False
    has_conflicting_requirements: bool = False

    def get_requirement(self, req_id: str) -> Optional[MockRequirement]:
        for r in self.requirements:
            if r.id == req_id:
                return r
        return None


# =============================================================================
# 1. State Taxonomy & Properties Tests
# =============================================================================


def test_fsm_state_taxonomy():
    """Verify 11 discrete states and their lifecycle properties."""
    expected_states = {
        "INIT",
        "PREFLIGHT",
        "PLANNING",
        "IMPLEMENTATION",
        "VERIFICATION",
        "RESOLUTION",
        "REVIEW",
        "BLOCKED",
        "AMBIGUOUS",
        "COMPLETED",
        "FAILED",
        "ABORTED",
    }
    actual_states = {s.value for s in FSMState}
    assert expected_states.issubset(actual_states)

    # Test is_terminal property
    assert FSMState.COMPLETED.is_terminal is True
    assert FSMState.FAILED.is_terminal is True
    assert FSMState.ABORTED.is_terminal is True
    assert FSMState.INIT.is_terminal is False
    assert FSMState.IMPLEMENTATION.is_terminal is False
    assert FSMState.VERIFICATION.is_terminal is False

    # Test is_active property
    assert FSMState.PLANNING.is_active is True
    assert FSMState.COMPLETED.is_active is False

    # Test collections
    assert FSMState.COMPLETED in FSMState.terminal_states()
    assert FSMState.IMPLEMENTATION in FSMState.recoverable_states()


# =============================================================================
# 2. Pipeline Event & Outcome Schema Tests
# =============================================================================


def test_pipeline_event_and_outcome_schemas():
    """Verify strongly typed PipelineEvent and AgentExecutionOutcome models."""
    event = PipelineEvent(
        event_type=EventType.AGENT_YIELDED,
        source_phase=FSMState.IMPLEMENTATION,
        active_milestone_id="MS-01",
        execution_outcome=AgentExecutionOutcome.NATURAL_COMPLETION,
        payload={"mutated_files": ["src/main.py"]},
    )
    assert event.event_type == EventType.AGENT_YIELDED
    assert event.source_phase == FSMState.IMPLEMENTATION
    assert event.active_milestone_id == "MS-01"
    assert event.execution_outcome == AgentExecutionOutcome.NATURAL_COMPLETION
    assert event.payload["mutated_files"] == ["src/main.py"]
    assert event.event_id is not None
    assert event.timestamp is not None

    # Verify AgentExecutionOutcome enum variants
    assert AgentExecutionOutcome.NATURAL_COMPLETION.value == "NATURAL_COMPLETION"
    assert AgentExecutionOutcome.STEP_LIMIT_REACHED.value == "STEP_LIMIT_REACHED"
    assert AgentExecutionOutcome.TOKEN_LIMIT_REACHED.value == "TOKEN_LIMIT_REACHED"
    assert AgentExecutionOutcome.TOOL_ERROR.value == "TOOL_ERROR"
    assert AgentExecutionOutcome.STAGNANT_DIFF.value == "STAGNANT_DIFF"


# =============================================================================
# 3. Pure Boolean Guards & Task Truth Semantic Queries Tests
# =============================================================================


def test_evaluate_task_completion_nonexistent_workspace(tmp_path: Path):
    """Completion evaluation on non-existent workspace returns BLOCKED."""
    fake_path = tmp_path / "non_existent_dir_12345"
    decision = evaluate_task_completion(None, fake_path)
    assert decision.status == CompletionStatus.BLOCKED
    assert decision.is_complete is False


def test_evaluate_task_completion_syntax_error(tmp_path: Path):
    """Syntax error in workspace results in FAILED decision."""
    broken_py = tmp_path / "broken.py"
    broken_py.write_text("def invalid_syntax(: pass\n", encoding="utf-8")
    decision = evaluate_task_completion(None, tmp_path)
    assert decision.status == CompletionStatus.FAILED
    assert len(decision.violated_invariants) > 0


def test_evaluate_task_completion_empty_requirements(tmp_path: Path):
    """TaskTruthGraph with no mandatory requirements returns INCOMPLETE."""
    clean_py = tmp_path / "clean.py"
    clean_py.write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
    graph = MockTaskTruthGraph(requirements=[])
    decision = evaluate_task_completion(graph, tmp_path)
    assert decision.status == CompletionStatus.INCOMPLETE
    assert "No mandatory requirements" in decision.blocking_reasons[0]


def test_evaluate_task_completion_mandatory_implemented_and_passed(tmp_path: Path):
    """Satisfied requirements with passing criteria evaluate to COMPLETE."""
    clean_py = tmp_path / "calc.py"
    clean_py.write_text("def mul(a: int, b: int) -> int:\n    return a * b\n", encoding="utf-8")

    crit1 = MockCriterion(
        id="AC-01", status=VerificationState.PASSED, verification_state=VerificationState.PASSED
    )
    req1 = MockRequirement(
        id="REQ-01",
        implementation_state=ImplementationState.IMPLEMENTED,
        verification_state=VerificationState.PASSED,
        status=RequirementStatus.VERIFIED,
        acceptance_criteria=[crit1],
    )
    graph = MockTaskTruthGraph(requirements=[req1])

    decision = evaluate_task_completion(graph, tmp_path)
    assert decision.status == CompletionStatus.COMPLETE
    assert decision.is_complete is True
    assert "REQ-01" in decision.satisfied_requirements


def test_evaluate_task_completion_failed_criteria(tmp_path: Path):
    """Failing acceptance criteria results in FAILED decision."""
    clean_py = tmp_path / "calc.py"
    clean_py.write_text("x = 1\n", encoding="utf-8")

    crit1 = MockCriterion(
        id="AC-01", status=VerificationState.FAILED, verification_state=VerificationState.FAILED
    )
    req1 = MockRequirement(
        id="REQ-01",
        implementation_state=ImplementationState.IMPLEMENTED,
        acceptance_criteria=[crit1],
    )
    graph = MockTaskTruthGraph(requirements=[req1])

    decision = evaluate_task_completion(graph, tmp_path)
    assert decision.status == CompletionStatus.FAILED
    assert "AC-01" in decision.failed_criteria


def test_evaluate_task_completion_blocked_dependency(tmp_path: Path):
    """Unverified dependency blocks downstream requirement."""
    clean_py = tmp_path / "calc.py"
    clean_py.write_text("x = 1\n", encoding="utf-8")

    req_dep = MockRequirement(
        id="REQ-00",
        implementation_state=ImplementationState.NOT_STARTED,
        verification_state=VerificationState.UNVERIFIED,
    )
    req_main = MockRequirement(
        id="REQ-01",
        implementation_state=ImplementationState.IMPLEMENTED,
        dependencies=["REQ-00"],
    )
    graph = MockTaskTruthGraph(requirements=[req_dep, req_main])

    decision = evaluate_task_completion(graph, tmp_path)
    assert decision.status == CompletionStatus.BLOCKED
    assert any("blocked by unverified dependency" in r for r in decision.blocking_reasons)


def test_semantic_queries_interface(tmp_path: Path):
    """Verify TaskTruthSemanticQueries read-only interface."""
    clean_py = tmp_path / "app.py"
    clean_py.write_text("class App:\n    pass\n", encoding="utf-8")

    req1 = MockRequirement(
        id="REQ-01",
        implementation_state=ImplementationState.IMPLEMENTED,
        verification_state=VerificationState.PASSED,
        status=RequirementStatus.VERIFIED,
        acceptance_criteria=[
            MockCriterion(
                id="AC-01",
                status=VerificationState.PASSED,
                verification_state=VerificationState.PASSED,
            )
        ],
    )
    graph = MockTaskTruthGraph(requirements=[req1])

    assert TaskTruthSemanticQueries.can_enter_testing(graph) is True
    assert TaskTruthSemanticQueries.can_enter_review(graph, tmp_path) is True
    assert TaskTruthSemanticQueries.can_complete(graph, tmp_path) is True
    assert TaskTruthSemanticQueries.must_block(graph, tmp_path) is False
    assert TaskTruthSemanticQueries.must_clarify(graph, tmp_path) is False


# =============================================================================
# 4. Lifecycle Profiles Tests
# =============================================================================


def test_lifecycle_profiles():
    """Verify canonical profiles and profile factory helper."""
    dev_test = get_profile(PipelineMode.DEV_TEST)
    assert dev_test.mode == PipelineMode.DEV_TEST
    assert dev_test.enable_planning is False
    assert dev_test.enable_review is False
    assert FSMState.PLANNING not in dev_test.allowed_states
    assert FSMState.IMPLEMENTATION in dev_test.allowed_states

    full = get_profile("full")
    assert full.mode == PipelineMode.FULL
    assert full.enable_planning is True
    assert full.enable_review is True
    assert FSMState.PLANNING in full.allowed_states
    assert FSMState.REVIEW in full.allowed_states

    audit = get_profile("audit")
    assert audit.mode == PipelineMode.AUDIT
    assert audit.enable_planning is False
    assert audit.enable_git_commit is False

    audit_fix = get_profile("audit-fix")
    assert audit_fix.mode == PipelineMode.AUDIT_FIX
    assert audit_fix.enable_planning is True


# =============================================================================
# 5. Transition Matrix & Guard Verification Tests
# =============================================================================


def test_transition_matrix_default_rules(tmp_path: Path):
    """Verify TransitionMatrix evaluation and guard rejection behavior."""
    matrix = TransitionMatrix.build_default()
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    profile = get_profile(PipelineMode.FULL)

    clean_file = tmp_path / "main.py"
    clean_file.write_text("x = 42\n", encoding="utf-8")

    ctx = FSMContext(
        workspace_path=tmp_path,
        config=cfg,
        profile=profile,
        current_state=FSMState.INIT,
    )

    # 1. INIT -> PREFLIGHT on START_TASK
    ev_start = PipelineEvent(
        event_type=EventType.START_TASK, source_phase=FSMState.INIT
    )
    rule = matrix.get_matching_rule(FSMState.INIT, ev_start, ctx)
    assert rule is not None
    assert rule.target_state == FSMState.PREFLIGHT

    # 2. PREFLIGHT -> PLANNING on PREFLIGHT_PASSED
    ctx.current_state = FSMState.PREFLIGHT
    ev_passed = PipelineEvent(
        event_type=EventType.PREFLIGHT_PASSED, source_phase=FSMState.PREFLIGHT
    )
    rule_prep = matrix.get_matching_rule(FSMState.PREFLIGHT, ev_passed, ctx)
    assert rule_prep is not None
    assert rule_prep.target_state == FSMState.PLANNING

    # 3. Universal Abort from any state
    ctx.current_state = FSMState.IMPLEMENTATION
    ev_abort = PipelineEvent(
        event_type=EventType.ABORT_REQUESTED,
        source_phase=FSMState.IMPLEMENTATION,
    )
    rule_abort = matrix.get_matching_rule(FSMState.IMPLEMENTATION, ev_abort, ctx)
    assert rule_abort is not None
    assert rule_abort.target_state == FSMState.ABORTED


def test_transition_rejection_disallowed_profile_state(tmp_path: Path):
    """GuardedFSMEngine rejects transitions to states disallowed by profile."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    # DEV_TEST profile disallows PLANNING state
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )
    engine.context.current_state = FSMState.PREFLIGHT

    # Attempt to transition into PLANNING
    rule_illegal = TransitionRule(
        source_state=FSMState.PREFLIGHT,
        trigger_event=EventType.PLAN_GENERATED,
        target_state=FSMState.PLANNING,
    )
    engine.transition_matrix.add_rule(rule_illegal)

    res = engine.process_event(
        PipelineEvent(
            event_type=EventType.PLAN_GENERATED,
            source_phase=FSMState.PREFLIGHT,
        )
    )
    assert res.success is False
    assert "disallowed under profile" in res.rejection_reason


# =============================================================================
# 6. Checkpoint Persistence & Safe Resume Tests
# =============================================================================


def test_checkpoint_save_and_load(tmp_path: Path):
    """Verify FSMCheckpointManager serialization, hash verification, and clear."""
    src_file = tmp_path / "module.py"
    src_file.write_text("def hello(): return 'world'\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    ctx = FSMContext(
        workspace_path=tmp_path,
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        task_description="Implement hello world module",
        current_state=FSMState.IMPLEMENTATION,
        iteration_count=2,
        total_tokens_consumed=12500,
        total_cost_usd=0.035,
        milestone_dag=[
            SubtaskMilestone(
                index=1,
                title="Create module",
                content="Create module.py",
            )
        ],
    )

    path = FSMCheckpointManager.save_checkpoint(ctx)
    assert path.exists()

    loaded = FSMCheckpointManager.load_checkpoint(tmp_path)
    assert loaded is not None
    assert loaded.current_state == "IMPLEMENTATION"
    assert loaded.task_description == "Implement hello world module"
    assert loaded.iteration_count == 2
    assert loaded.total_tokens_consumed == 12500
    assert len(loaded.milestones) == 1
    assert len(loaded.workspace_root_hash) == 64

    # Clear checkpoint
    cleared = FSMCheckpointManager.clear_checkpoint(tmp_path)
    assert cleared is True
    assert not path.exists()


# =============================================================================
# 7. End-to-End Orchestration Loop & Recovery Tests
# =============================================================================


def test_fsm_engine_dev_test_clean_run(tmp_path: Path):
    """End-to-end dev-test run with clean syntax and mock test pass."""
    app_py = tmp_path / "app.py"
    app_py.write_text("def run():\n    return 0\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    # Mock runtime bridge and adapter
    mock_outcome = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=2,
        max_iterations_allocated=8,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=tuple(),
        final_thought="Completed",
    )
    engine.runtime_bridge = MagicMock()
    engine.runtime_bridge.execute_bounded_turn.return_value = mock_outcome

    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, stdout="1 passed")
    engine.context.adapter = mock_adapter

    result = engine.run("Implement run function")
    assert result["success"] is True
    assert result["status"] == "COMPLETED"
    assert FSMState.INIT.value in result["state_history"]
    assert FSMState.PREFLIGHT.value in result["state_history"]
    assert FSMState.IMPLEMENTATION.value in result["state_history"]
    assert FSMState.VERIFICATION.value in result["state_history"]
    assert FSMState.COMPLETED.value in result["state_history"]


def test_fsm_engine_remediation_recovery_loop(tmp_path: Path):
    """Verify failure triage and retry loop: VERIFICATION -> RESOLUTION -> IMPLEMENTATION."""
    src_file = tmp_path / "service.py"
    src_file.write_text("x = 10\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=3)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    mock_outcome = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=2,
        max_iterations_allocated=8,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=tuple(),
        final_thought="Fixed",
    )
    engine.runtime_bridge = MagicMock()
    engine.runtime_bridge.execute_bounded_turn.return_value = mock_outcome

    # First verification run fails, second verification passes
    mock_adapter = MagicMock()
    fail_res = MagicMock(passed=False, stdout="FAILED test_service.py", stderr="AssertionError")
    pass_res = MagicMock(passed=True, stdout="1 passed", stderr="")
    mock_adapter.run_tests.side_effect = [fail_res, pass_res]
    engine.context.adapter = mock_adapter

    result = engine.run("Fix service bug")
    assert result["success"] is True
    assert result["status"] == "COMPLETED"
    assert FSMState.RESOLUTION.value in result["state_history"]
    assert engine.context.iteration_count == 1


def test_fsm_engine_stagnation_circuit_breaker(tmp_path: Path):
    """Verify stagnation circuit breaker trips when diff hash remains unchanged across retries."""
    src_file = tmp_path / "stagnant.py"
    src_file.write_text("val = 1\n", encoding="utf-8")

    cfg = OrchestratorConfig(
        workspace_path=tmp_path,
        circuit_breaker_threshold=2,
        max_iterations=5,
    )
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    mock_outcome = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=2,
        max_iterations_allocated=8,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=tuple(),
        final_thought="Still stagnant",
    )
    engine.runtime_bridge = MagicMock()
    engine.runtime_bridge.execute_bounded_turn.return_value = mock_outcome

    # Continuous failing tests with unchanged workspace
    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(
        passed=False, stdout="AssertionError", stderr="Test failed repeatedly"
    )
    engine.context.adapter = mock_adapter

    result = engine.run("Stagnant task")
    assert result["success"] is False
    assert result["status"] == "FAILED"
    assert FSMState.RESOLUTION.value in result["state_history"]


def test_fsm_engine_full_profile_review_approved(tmp_path: Path):
    """End-to-end FULL profile lifecycle: INIT -> PREFLIGHT -> PLANNING -> IMPLEMENTATION -> VERIFICATION -> REVIEW -> COMPLETED."""
    app_py = tmp_path / "core.py"
    app_py.write_text("def core_logic(): return True\n", encoding="utf-8")

    plan_md = tmp_path / "PLAN.md"
    plan_md.write_text("## Milestone 1: Core\nImplement core_logic\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.FULL),
        workspace_path=tmp_path,
    )

    mock_outcome = BridgeAgentOutcome(
        role="reviewer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=1,
        max_iterations_allocated=5,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=tuple(),
        final_thought="```json\n{\n  \"verdict\": \"APPROVED\"\n}\n```",
    )
    engine.runtime_bridge = MagicMock()
    engine.runtime_bridge.execute_bounded_turn.return_value = mock_outcome

    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, stdout="All tests passed")
    engine.context.adapter = mock_adapter

    result = engine.run("Implement core logic feature")
    assert result["success"] is True
    assert result["status"] == "COMPLETED"
    assert FSMState.PLANNING.value in result["state_history"]
    assert FSMState.REVIEW.value in result["state_history"]


def test_fsm_engine_resume_from_checkpoint(tmp_path: Path):
    """Verify GuardedFSMEngine resumes accurately from a persisted checkpoint."""
    src_file = tmp_path / "resumed.py"
    src_file.write_text("state = 'active'\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    ctx = FSMContext(
        workspace_path=tmp_path,
        config=cfg,
        profile=get_profile(PipelineMode.FULL),
        task_description="Resume task",
        current_state=FSMState.IMPLEMENTATION,
        state_history=[FSMState.INIT, FSMState.PREFLIGHT, FSMState.PLANNING, FSMState.IMPLEMENTATION],
        iteration_count=1,
    )
    FSMCheckpointManager.save_checkpoint(ctx)

    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.FULL),
        workspace_path=tmp_path,
    )

    mock_outcome = BridgeAgentOutcome(
        role="reviewer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=1,
        max_iterations_allocated=5,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=tuple(),
        final_thought="APPROVED",
    )
    engine.runtime_bridge = MagicMock()
    engine.runtime_bridge.execute_bounded_turn.return_value = mock_outcome

    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, stdout="Passed")
    engine.context.adapter = mock_adapter

    result = engine.run("Resume task", resume=True)
    assert result["success"] is True
    assert result["status"] == "COMPLETED"
    assert FSMState.PLANNING.value in result["state_history"]


def test_fsm_engine_preflight_syntax_failure(tmp_path: Path):
    """Verify PREFLIGHT failure halts pipeline and transitions to FAILED."""
    broken_py = tmp_path / "syntax_error.py"
    broken_py.write_text("def broken_syntax(:\n    pass\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    result = engine.run("Run with syntax error")
    assert result["success"] is False
    assert result["status"] == "FAILED"
    assert FSMState.PREFLIGHT.value in result["state_history"]


def test_fsm_engine_reviewer_rejection_and_fix(tmp_path: Path):
    """Verify Reviewer rejection routes to RESOLUTION, then re-implements and succeeds."""
    app_py = tmp_path / "app.py"
    app_py.write_text("def feature(): return 1\n", encoding="utf-8")

    plan_md = tmp_path / "PLAN.md"
    plan_md.write_text("## Milestone 1: App\nImplement feature\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.FULL),
        workspace_path=tmp_path,
    )

    mock_dev = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=2,
        max_iterations_allocated=8,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=tuple(),
        final_thought="Feature written",
    )

    mock_reject = BridgeAgentOutcome(
        role="reviewer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=1,
        max_iterations_allocated=5,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=tuple(),
        final_thought="```json\n{\n  \"verdict\": \"REJECTED\",\n  \"required_fixes\": [\"Add docstring\"]\n}\n```",
    )

    mock_approve = BridgeAgentOutcome(
        role="reviewer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=1,
        max_iterations_allocated=5,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=tuple(),
        final_thought="```json\n{\n  \"verdict\": \"APPROVED\"\n}\n```",
    )

    engine.runtime_bridge = MagicMock()
    # 1. Dev Turn -> 2. Review (Reject) -> 3. Dev (Fix) -> 4. Review (Approve)
    engine.runtime_bridge.execute_bounded_turn.side_effect = [
        mock_dev,
        mock_reject,
        mock_dev,
        mock_approve,
    ]

    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, stdout="Passed")
    engine.context.adapter = mock_adapter

    result = engine.run("Review with revisions")
    assert result["success"] is True
    assert result["status"] == "COMPLETED"
    assert FSMState.RESOLUTION.value in result["state_history"]
    assert FSMState.REVIEW.value in result["state_history"]


def test_transition_hooks_execution(tmp_path: Path):
    """Verify on_entry and on_exit transition hooks are executed."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    clean_file = tmp_path / "valid.py"
    clean_file.write_text("x = 1\n", encoding="utf-8")

    entry_called = []
    exit_called = []

    custom_rule = TransitionRule(
        source_state=FSMState.INIT,
        trigger_event=EventType.START_TASK,
        target_state=FSMState.PREFLIGHT,
        on_exit=lambda ctx, ev: exit_called.append("INIT_EXIT"),
        on_entry=lambda ctx, ev: entry_called.append("PREFLIGHT_ENTRY"),
    )
    engine.transition_matrix = TransitionMatrix([custom_rule])

    res = engine.process_event(
        PipelineEvent(
            event_type=EventType.START_TASK, source_phase=FSMState.INIT
        )
    )
    assert res.success is True
    assert exit_called == ["INIT_EXIT"]
    assert entry_called == ["PREFLIGHT_ENTRY"]


def test_fsm_checkpoint_drift_detection(tmp_path: Path):
    """Verify workspace hash changes when new files are added."""
    file_a = tmp_path / "a.py"
    file_a.write_text("a = 1\n", encoding="utf-8")

    hash1 = FSMCheckpointManager.compute_workspace_hash(tmp_path)

    # Modify file
    file_a.write_text("a = 2\n", encoding="utf-8")
    hash2 = FSMCheckpointManager.compute_workspace_hash(tmp_path)

    assert hash1 != hash2


def test_controller_abort_signal(tmp_path: Path):
    """Verify pipeline halts immediately when PipelineController requests abort."""
    app_py = tmp_path / "app.py"
    app_py.write_text("x = 1\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    controller = PipelineController()
    controller.request_abort()

    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
        controller=controller,
    )

    result = engine.run("Aborted task")
    assert result["success"] is False
    assert result["status"] == "ABORTED"
