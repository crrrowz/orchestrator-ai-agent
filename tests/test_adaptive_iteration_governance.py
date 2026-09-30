"""Comprehensive test suite for the Adaptive Iteration Governance Layer.

Verifies:
1. Task-aware dynamic budget allocation across categories.
2. Real-time step telemetry and progress metrics calculation.
3. Chaos and error-burst detection.
4. Stagnation and exploration-exhaustion detection.
5. Evidence-based budget extensions.
6. GuardedFSMEngine integration and directive injection.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from orchestrator.config import OrchestratorConfig
from orchestrator.engine.openhands_bridge import (
    AgentExecutionOutcome as BridgeAgentOutcome,
    AgentExitReason,
)
from orchestrator.governance import (
    AdaptiveTaskBudgetAllocator,
    ChaosDetector,
    CheckpointEvaluator,
    DEFAULT_TASK_PROFILES,
    ExecutionHealth,
    GovernanceAction,
    IterationGovernor,
    ProgressMetricsCalculator,
    ProgressMonitor,
    StagnationDetector,
    StepRecord,
    TaskBudgetProfile,
    TaskCategory,
)
from orchestrator.pipeline.fsm.engine import GuardedFSMEngine
from orchestrator.pipeline.fsm.profiles import PipelineMode, get_profile


def test_task_aware_category_inference():
    """Verify accurate domain classification for different engineering task descriptions."""
    alloc = AdaptiveTaskBudgetAllocator

    assert alloc.infer_category("Design system architecture", role="architect") == TaskCategory.ARCHITECTURE
    assert alloc.infer_category("Fix null pointer exception in auth service") == TaskCategory.DEBUGGING
    assert alloc.infer_category("Add unit tests for payment processor") == TaskCategory.TESTING
    assert alloc.infer_category("Conduct comprehensive security audit", mode="audit") == TaskCategory.AUDIT
    assert alloc.infer_category("Update README and API reference docs", mode="docs") == TaskCategory.DOCUMENTATION
    assert alloc.infer_category("Refactor database queries for performance") == TaskCategory.REFACTORING
    assert alloc.infer_category("Scan for CVE vulnerabilities in dependencies") == TaskCategory.SECURITY
    assert alloc.infer_category("Implement sliding window rate limiter") == TaskCategory.IMPLEMENTATION


def test_task_budget_allocation_scaling():
    """Verify budget limits are customized per category and scale with complexity."""
    alloc = AdaptiveTaskBudgetAllocator

    impl_turns_low = alloc.calculate_initial_budget("Implement feature", complexity_hint=0.1)
    impl_turns_high = alloc.calculate_initial_budget("Implement feature", complexity_hint=0.9)
    audit_turns = alloc.calculate_initial_budget("Comprehensive audit", mode="audit")
    review_turns = alloc.calculate_initial_budget("PR review", role="reviewer")

    assert impl_turns_high >= impl_turns_low
    assert audit_turns >= 20
    assert review_turns <= 15


def test_progress_monitor_and_metrics():
    """Verify ProgressMonitor records action categories and computes metrics."""
    monitor = ProgressMonitor()

    # Step 1: list files
    monitor.record_step(action_type="list", tool_name="workspace_file", target_path=".")
    # Step 2: read file
    monitor.record_step(action_type="read", tool_name="workspace_file", target_path="pyproject.toml")
    # Step 3: mutate file
    monitor.record_step(action_type="write", tool_name="workspace_file", target_path="src/main.py")
    # Step 4: run terminal
    s4 = monitor.record_step(action_type="terminal", tool_name="workspace_terminal", command="pytest")
    monitor.mark_last_step_error("Test failed: AssertionError")

    assert monitor.step_count == 4
    assert "src/main.py" in monitor.mutated_files
    assert "pyproject.toml" in monitor.read_files

    metrics = monitor.get_metrics()
    assert metrics.total_steps == 4
    assert metrics.mutation_steps == 1
    assert metrics.read_steps == 2
    assert metrics.error_steps == 1
    assert metrics.error_rate == 0.25
    assert metrics.mutation_velocity == 0.25


def test_chaos_detector_error_burst():
    """Verify ChaosDetector triggers on repeated consecutive failures."""
    detector = ChaosDetector(consecutive_error_threshold=3)

    steps = [
        StepRecord(step_index=1, action_type="read", tool_name="file", target_path="a.py", is_read=True),
        StepRecord(step_index=2, action_type="terminal", tool_name="term", command="find .", is_error=True, error_message="FIND: Parameter format not correct"),
        StepRecord(step_index=3, action_type="terminal", tool_name="term", command="python -m ruff check", is_error=True, error_message="No module named ruff"),
        StepRecord(step_index=4, action_type="terminal", tool_name="term", command="pip list", is_error=True, error_message="No module named pip"),
    ]

    is_chaotic, reason = detector.check_chaos(steps)
    assert is_chaotic is True
    assert "Error burst detected" in reason


def test_stagnation_detector_exploration_exhaustion():
    """Verify StagnationDetector flags exploration churn with zero mutations."""
    detector = StagnationDetector(max_exploration_turns=5)

    steps = [
        StepRecord(step_index=i, action_type="read", tool_name="file", target_path=f"file_{i}.py", is_read=True)
        for i in range(1, 7)
    ]

    is_stagnant, reason = detector.check_stagnation(steps, has_prior_mutations=False)
    assert is_stagnant is True
    assert "Exploration exhaustion" in reason


def test_stagnation_detector_repetition_loop():
    """Verify StagnationDetector flags reading the same file repeatedly."""
    detector = StagnationDetector(max_repeated_reads=3)

    steps = [
        StepRecord(step_index=1, action_type="read", tool_name="file", target_path="main.py", is_read=True),
        StepRecord(step_index=2, action_type="read", tool_name="file", target_path="main.py", is_read=True),
        StepRecord(step_index=3, action_type="read", tool_name="file", target_path="main.py", is_read=True),
    ]

    is_stagnant, reason = detector.check_stagnation(steps)
    assert is_stagnant is True
    assert "Repetitive inspection loop" in reason


def test_budget_extension_on_active_mutations():
    """Verify governor extends budget when agent is actively making progress."""
    evaluator = CheckpointEvaluator()
    profile = DEFAULT_TASK_PROFILES[TaskCategory.IMPLEMENTATION]

    steps = [
        StepRecord(step_index=1, action_type="read", tool_name="file", target_path="app.py", is_read=True),
        StepRecord(step_index=2, action_type="write", tool_name="file", target_path="app.py", is_mutation=True),
        StepRecord(step_index=3, action_type="patch", tool_name="file", target_path="test_app.py", is_mutation=True),
    ]

    decision = evaluator.evaluate(
        steps=steps,
        profile=profile,
        turns_used=20,
        turns_allocated=20,
        agent_yielded=True,
        agent_completed_naturally=False,
    )

    assert decision.action == GovernanceAction.EXTEND_BUDGET
    assert decision.allocated_turns_extension > 0
    assert decision.health == ExecutionHealth.PROGRESSING


def test_governance_blocks_chaotic_session():
    """Verify chaotic session yields CHANGE_STRATEGY directive."""
    evaluator = CheckpointEvaluator()
    profile = DEFAULT_TASK_PROFILES[TaskCategory.IMPLEMENTATION]

    steps = [
        StepRecord(step_index=1, action_type="terminal", tool_name="term", command="cmd1", is_error=True, error_message="err1"),
        StepRecord(step_index=2, action_type="terminal", tool_name="term", command="cmd2", is_error=True, error_message="err2"),
        StepRecord(step_index=3, action_type="terminal", tool_name="term", command="cmd3", is_error=True, error_message="err3"),
    ]

    decision = evaluator.evaluate(
        steps=steps,
        profile=profile,
        turns_used=3,
        turns_allocated=15,
        agent_yielded=False,
    )

    assert decision.action == GovernanceAction.CHANGE_STRATEGY
    assert decision.health == ExecutionHealth.CHAOTIC
    assert decision.recommended_directive is not None


def test_fsm_engine_integrates_iteration_governor(tmp_path: Path):
    """Verify GuardedFSMEngine allocates initial budget via governor and tracks directives."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    assert isinstance(engine.iteration_governor, IterationGovernor)
    assert engine.iteration_governor.monitor is not None

    # Simulate governor directive in metadata
    engine.context.metadata["governance_directive"] = "Modify app.py directly"

    mock_outcome = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=2,
        max_iterations_allocated=20,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.001,
        error_message=None,
        mutated_files=("app.py",),
        final_thought="Completed",
    )
    engine.runtime_bridge = MagicMock()
    engine.runtime_bridge.execute_bounded_turn.return_value = mock_outcome

    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, stdout="1 passed")
    engine.context.adapter = mock_adapter

    res = engine.run("Implement auth token generator")
    assert res["success"] is True
    assert "governance_decision" in engine.context.metadata
