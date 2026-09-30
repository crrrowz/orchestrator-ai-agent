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


def test_fsm_engine_multi_milestone_progression_loop(tmp_path: Path):
    """Verify sequential execution across multiple milestones in milestone_dag."""
    src_file = tmp_path / "app.py"
    src_file.write_text("x = 1\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    # 3 Milestones
    engine.context.milestone_dag = [
        SubtaskMilestone(index=1, title="Milestone 1: Interface", content="Define interface"),
        SubtaskMilestone(index=2, title="Milestone 2: Implementation", content="Implement logic"),
        SubtaskMilestone(index=3, title="Milestone 3: Tests", content="Add tests"),
    ]

    executed_milestone_indices = []

    def mock_execute_turn(**kwargs):
        executed_milestone_indices.append(engine.context.active_milestone_index)
        return BridgeAgentOutcome(
            role="developer",
            exit_reason=AgentExitReason.NATURAL_COMPLETION,
            completed_naturally=True,
            iterations_executed=1,
            max_iterations_allocated=5,
            prompt_tokens=50,
            completion_tokens=20,
            total_tokens=70,
            cost_usd=0.0,
            error_message=None,
            mutated_files=tuple(),
            final_thought="Done milestone",
        )

    engine.runtime_bridge = MagicMock()
    engine.runtime_bridge.execute_bounded_turn.side_effect = mock_execute_turn

    # Mock tests passing
    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, summary="All passed")
    engine.context.adapter = mock_adapter

    result = engine.run("Build feature with 3 milestones")
    assert result["success"] is True
    assert result["status"] == "COMPLETED"
    # Should execute milestones 0, 1, 2 in order
    assert executed_milestone_indices == [0, 1, 2]
    # All milestones should be marked completed
    assert all(m.is_completed for m in engine.context.milestone_dag)


def test_fsm_engine_milestone_failure_retries_same_milestone(tmp_path: Path):
    """Verify milestone verification failure stays on same milestone until fixed."""
    src_file = tmp_path / "app.py"
    src_file.write_text("x = 1\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=5)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    engine.context.milestone_dag = [
        SubtaskMilestone(index=1, title="Milestone 1", content="Step 1"),
        SubtaskMilestone(index=2, title="Milestone 2", content="Step 2"),
    ]

    executed_indices = []

    def mock_execute_turn(**kwargs):
        executed_indices.append(engine.context.active_milestone_index)
        return BridgeAgentOutcome(
            role="developer",
            exit_reason=AgentExitReason.NATURAL_COMPLETION,
            completed_naturally=True,
            iterations_executed=1,
            max_iterations_allocated=5,
            prompt_tokens=50,
            completion_tokens=20,
            total_tokens=70,
            cost_usd=0.0,
            error_message=None,
            mutated_files=tuple(),
            final_thought="Iter done",
        )

    engine.runtime_bridge = MagicMock()
    engine.runtime_bridge.execute_bounded_turn.side_effect = mock_execute_turn

    # Milestone 1: first fails, second passes. Milestone 2: passes
    fail_res = MagicMock(passed=False, summary="Syntax/test failed")
    pass_res = MagicMock(passed=True, summary="Passed")
    mock_adapter = MagicMock()
    mock_adapter.run_tests.side_effect = [fail_res, pass_res, pass_res]
    engine.context.adapter = mock_adapter

    result = engine.run("Build with retry")
    assert result["success"] is True
    assert result["status"] == "COMPLETED"
    # Executed milestone 0 twice (due to retry), then milestone 1 once
    assert executed_indices == [0, 0, 1]
    assert all(m.is_completed for m in engine.context.milestone_dag)


def test_fsm_guard_prevents_premature_completion(tmp_path: Path):
    """Verify guard_can_complete rejects completion while milestones are pending."""
    ctx = FSMContext(
        workspace_path=tmp_path,
        config=OrchestratorConfig(workspace_path=tmp_path),
        profile=get_profile(PipelineMode.DEV_TEST),
        milestone_dag=[
            SubtaskMilestone(index=1, title="M1", content=""),
            SubtaskMilestone(index=2, title="M2", content=""),
        ],
        active_milestone_index=0,
        last_verification_decision=CompletionDecision(
            status=CompletionStatus.COMPLETE,
            satisfied_requirements=["Clean"],
        ),
    )
    ev = PipelineEvent(
        event_type=EventType.VERIFICATION_COMPLETED,
        source_phase=FSMState.VERIFICATION,
    )

    assert FSMGuards.guard_can_complete(ctx, ev) is False
    assert FSMGuards.guard_can_enter_review(ctx, ev) is False

    # When on final milestone (index 1)
    ctx.active_milestone_index = 1
    assert FSMGuards.guard_can_complete(ctx, ev) is True
    assert FSMGuards.guard_can_enter_review(ctx, ev) is True


def test_fsm_fails_when_llm_manager_missing_during_implementation(tmp_path: Path):
    """TASK-001: Verify FSM emits CRITICAL_ERROR and reaches FAILED when LLMManager is absent."""
    config = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        workspace_path=tmp_path,
        config=config,
        profile=get_profile(PipelineMode.DEV_TEST),
    )
    engine.llm_manager = None
    engine.context.llm_manager = None
    engine.runtime_bridge = None

    # Force starting state to IMPLEMENTATION
    engine.context.current_state = FSMState.IMPLEMENTATION

    ev = engine._handle_implementation()
    assert ev.event_type == EventType.CRITICAL_ERROR
    assert "LLMManager or RuntimeBridge unavailable" in (ev.error_message or "")

    # Processing this event should transition directly to FAILED
    res = engine.process_event(ev)
    assert res.success is True
    assert res.current_state == FSMState.FAILED


def test_fsm_fails_when_bridge_returns_fatal_error(tmp_path: Path):
    """TASK-001: Verify FSM emits CRITICAL_ERROR when SDK runtime bridge returns FATAL_ERROR."""
    config = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        workspace_path=tmp_path,
        config=config,
        profile=get_profile(PipelineMode.DEV_TEST),
    )
    engine.llm_manager = MagicMock()
    mock_bridge = MagicMock()
    mock_bridge.execute_bounded_turn.return_value = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.FATAL_ERROR,
        completed_naturally=False,
        iterations_executed=0,
        max_iterations_allocated=15,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        cost_usd=0.0,
        error_message="Fatal unrecoverable LLM crash: ConnectionRefused",
        mutated_files=tuple(),
        final_thought=None,
    )
    engine.runtime_bridge = mock_bridge
    engine.context.current_state = FSMState.IMPLEMENTATION

    ev = engine._handle_implementation()
    assert ev.event_type == EventType.CRITICAL_ERROR
    assert "Fatal unrecoverable LLM crash" in (ev.error_message or "")

    res = engine.process_event(ev)
    assert res.success is True
    assert res.current_state == FSMState.FAILED


def test_guard_can_enter_verification_validates_outcomes(tmp_path: Path):
    """TASK-002: Verify guard_can_enter_verification allows valid yields and rejects fatal/empty/aborted ones."""
    ctx = FSMContext(
        workspace_path=tmp_path,
        config=OrchestratorConfig(workspace_path=tmp_path),
        profile=get_profile(PipelineMode.DEV_TEST),
        current_state=FSMState.IMPLEMENTATION,
    )

    # 1. Invalid event type
    wrong_ev = PipelineEvent(
        event_type=EventType.PREFLIGHT_PASSED,
        source_phase=FSMState.IMPLEMENTATION,
        execution_outcome=AgentExecutionOutcome.NATURAL_COMPLETION,
    )
    assert FSMGuards.guard_can_enter_verification(ctx, wrong_ev) is False

    # 2. None execution outcome
    none_outcome_ev = PipelineEvent(
        event_type=EventType.AGENT_YIELDED,
        source_phase=FSMState.IMPLEMENTATION,
        execution_outcome=None,
    )
    assert FSMGuards.guard_can_enter_verification(ctx, none_outcome_ev) is False

    # 3. FATAL_ERROR outcome
    fatal_ev = PipelineEvent(
        event_type=EventType.AGENT_YIELDED,
        source_phase=FSMState.IMPLEMENTATION,
        execution_outcome=AgentExecutionOutcome.FATAL_ERROR,
    )
    assert FSMGuards.guard_can_enter_verification(ctx, fatal_ev) is False

    # 4. ABORTED outcome
    aborted_ev = PipelineEvent(
        event_type=EventType.AGENT_YIELDED,
        source_phase=FSMState.IMPLEMENTATION,
        execution_outcome=AgentExecutionOutcome.ABORTED,
    )
    assert FSMGuards.guard_can_enter_verification(ctx, aborted_ev) is False

    # 5. Valid outcomes
    for valid_outcome in (
        AgentExecutionOutcome.NATURAL_COMPLETION,
        AgentExecutionOutcome.STEP_LIMIT_REACHED,
        AgentExecutionOutcome.TOKEN_LIMIT_REACHED,
        AgentExecutionOutcome.TOOL_ERROR,
        AgentExecutionOutcome.STAGNANT_DIFF,
        AgentExecutionOutcome.TOOL_REJECTION,
        AgentExecutionOutcome.AGENT_STUCK,
    ):
        valid_ev = PipelineEvent(
            event_type=EventType.AGENT_YIELDED,
            source_phase=FSMState.IMPLEMENTATION,
            execution_outcome=valid_outcome,
        )
        assert FSMGuards.guard_can_enter_verification(ctx, valid_ev) is True


def test_verification_rejects_completion_when_test_res_is_none(tmp_path: Path):
    """TASK-003: Verify _handle_verification yields INCOMPLETE (not COMPLETE) when test_res is None."""
    src_file = tmp_path / "main.py"
    src_file.write_text("print('hello world')\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )
    engine.context.current_state = FSMState.VERIFICATION
    engine.context.adapter = None  # No test adapter -> test_res is None
    engine.context.task_truth_graph = None

    ev = engine._handle_verification()
    assert ev.event_type == EventType.VERIFICATION_COMPLETED
    assert engine.context.last_verification_decision is not None
    assert engine.context.last_verification_decision.status == CompletionStatus.INCOMPLETE
    assert engine.context.last_verification_decision.is_complete is False
    assert "No test results or verification evidence" in engine.context.last_verification_decision.blocking_reasons[0]

    # Guard check for completion should strictly fail
    assert FSMGuards.guard_can_complete(engine.context, ev) is False


def test_terminal_state_handlers_do_not_emit_start_task(tmp_path: Path):
    """TASK-004: Verify terminal state handlers emit terminal events, not START_TASK."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    completed_ev = engine._handle_completed()
    assert completed_ev.event_type != EventType.START_TASK
    assert completed_ev.source_phase == FSMState.COMPLETED

    failed_ev = engine._handle_failed()
    assert failed_ev.event_type != EventType.START_TASK
    assert failed_ev.source_phase == FSMState.FAILED


def test_headless_blocked_state_finalizes_cleanly(tmp_path: Path):
    """TASK-004: Verify entering BLOCKED without interactive human channel finalizes with blocked=True."""
    src_file = tmp_path / "main.py"
    src_file.write_text("print('test')\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )
    # Directly transition to BLOCKED
    engine.context.current_state = FSMState.BLOCKED
    engine.context.metadata["blocking_reason"] = "Missing required API credentials."

    result = engine.run("Task that blocks")
    assert result["success"] is False
    assert result["blocked"] is True
    assert result["status"] == "BLOCKED"
    assert "Missing required API credentials." in result["error_message"]


def test_global_iteration_budget_exhaustion(tmp_path: Path):
    """TASK-005: Verify global iteration budget ceiling stops execution across milestones."""
    src_file = tmp_path / "main.py"
    src_file.write_text("print('test')\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    profile = get_profile(PipelineMode.DEV_TEST)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=profile,
        workspace_path=tmp_path,
    )
    # Set context on resolution state with total_iterations hitting max_total_iterations
    engine.context.current_state = FSMState.RESOLUTION
    engine.context.iteration_count = 0  # Per-milestone count is fresh
    engine.context.total_iterations = profile.max_total_iterations  # Global exhausted

    ev = engine._handle_resolution()
    assert ev.event_type == EventType.RETRIES_EXHAUSTED
    assert "Global iteration ceiling" in (ev.error_message or "")

    res = engine.process_event(ev)
    assert res.success is True
    assert res.current_state == FSMState.FAILED


def test_workspace_hash_ignores_runtime_artifacts(tmp_path: Path):
    """TASK-006: Verify compute_workspace_hash ignores logs, diagnostic db, and cache directories."""
    src_file = tmp_path / "app.py"
    src_file.write_text("print('core app')\n", encoding="utf-8")

    initial_hash = FSMCheckpointManager.compute_workspace_hash(tmp_path)

    # Create logs and diagnostic db
    (tmp_path / "app.log").write_text("2026-09-30 INFO test log\n", encoding="utf-8")
    (tmp_path / "diagnostics.db").write_bytes(b"\x00\x01\x02\x03sqlite header fake")
    (tmp_path / ".coverage").write_text("coverage metadata", encoding="utf-8")
    cache_dir = tmp_path / ".pytest_cache"
    cache_dir.mkdir()
    (cache_dir / "cache.json").write_text("{}", encoding="utf-8")

    after_hash = FSMCheckpointManager.compute_workspace_hash(tmp_path)
    assert initial_hash == after_hash


def test_stagnation_counter_increments_without_test_adapter(tmp_path: Path):
    """TASK-006: Verify stagnation counter increments when workspace hash is unchanged even if test_res is None."""
    src_file = tmp_path / "app.py"
    src_file.write_text("print('core app')\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )
    engine.context.adapter = None  # No test adapter
    engine.context.task_truth_graph = None

    # First verification
    ev1 = engine._handle_verification()
    assert engine.context.stagnation_counter == 0

    # Second verification without code changes
    ev2 = engine._handle_verification()
    assert engine.context.stagnation_counter == 1

    # Third verification without code changes
    ev3 = engine._handle_verification()
    assert engine.context.stagnation_counter == 2


def test_fsm_engine_wall_clock_timeout(tmp_path: Path):
    """TASK-007: Verify GuardedFSMEngine halts when wall-clock timeout is exceeded."""
    import time

    src_file = tmp_path / "app.py"
    src_file.write_text("print('app')\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    def slow_implementation():
        time.sleep(0.05)
        return PipelineEvent(
            event_type=EventType.AGENT_YIELDED,
            source_phase=FSMState.IMPLEMENTATION,
            execution_outcome=AgentExecutionOutcome.NATURAL_COMPLETION,
        )

    engine._handle_implementation = slow_implementation

    result = engine.run("Hanging task", timeout_seconds=0.01)
    assert result["success"] is False
    assert result["timed_out"] is True
    assert result["status"] == "FAILED"
    assert "wall-clock timeout" in (result["error_message"] or "")


def test_resume_from_failed_checkpoint_allows_recovery(tmp_path: Path):
    """TASK-009: Verify resuming from a FAILED checkpoint resets state to PREFLIGHT/IMPLEMENTATION and executes."""
    src_file = tmp_path / "app.py"
    src_file.write_text("print('app')\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )
    # Save a FAILED checkpoint
    engine.context.current_state = FSMState.FAILED
    engine.context.state_history = [FSMState.INIT, FSMState.PREFLIGHT, FSMState.IMPLEMENTATION, FSMState.FAILED]
    engine.context.task_description = "Recovery Task"
    FSMCheckpointManager.save_checkpoint(engine.context)

    # Setup mocked successful engine for resume run
    resume_engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )
    mock_outcome = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=1,
        max_iterations_allocated=8,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=tuple(),
        final_thought="Success",
    )
    resume_engine.runtime_bridge = MagicMock()
    resume_engine.runtime_bridge.execute_bounded_turn.return_value = mock_outcome

    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, stdout="1 passed")
    resume_engine.context.adapter = mock_adapter

    # Run with resume=True
    res = resume_engine.run("Recovery Task", resume=True)
    assert res["success"] is True
    assert res["status"] == "COMPLETED"
    assert FSMState.PREFLIGHT.value in res["state_history"]








