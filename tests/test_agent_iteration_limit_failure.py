"""Regression tests for Developer Agent iteration limit exhaustion failure propagation.

Verifies that when a Developer Agent reaches maximum iterations or fails to complete naturally:
1. The FSM / Pipeline fails and propagates status=FAILED with success=False.
2. Passing pytest results in the workspace do NOT falsely mask developer turn iteration limit exhaustion.
3. MigrationTelemetry records plane failure with Success=False.
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
from orchestrator.orchestrator import Orchestrator
from orchestrator.pipeline import (
    ExecutionPlane,
    GuardedFSMEngine,
    MigrationGuard,
    OrchestratorDispatcher,
    PipelineMode,
    get_profile,
)
from orchestrator.pipeline.fsm.events import AgentExecutionOutcome, EventType


def test_fsm_fails_when_developer_hits_step_limit_even_if_pytest_passes(tmp_path: Path):
    """Verify FSM produces FAILED and success=False when agent reaches step limit despite passing tests."""
    (tmp_path / "app.py").write_text("def run(): pass\n", encoding="utf-8")
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    # Mock developer turn yielding with STEP_LIMIT_REACHED (Agent reached maximum iterations limit)
    mock_outcome = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.STEP_LIMIT_REACHED,
        completed_naturally=False,
        iterations_executed=11,
        max_iterations_allocated=11,
        prompt_tokens=5000,
        completion_tokens=2000,
        total_tokens=7000,
        cost_usd=0.05,
        error_message="Turn step limit reached (11 turns). Agent reached maximum iterations limit.",
        mutated_files=tuple(),
        final_thought=None,
    )
    mock_bridge = MagicMock()
    mock_bridge.execute_bounded_turn.return_value = mock_outcome
    engine.runtime_bridge = mock_bridge
    engine.llm_manager = MagicMock()

    # Pre-existing workspace tests pass
    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, stdout="10 passed")
    engine.context.adapter = mock_adapter

    result = engine.run("Implement feature")

    assert result["success"] is False
    assert result["status"] == "FAILED"
    assert "Agent reached maximum iterations limit" in (result["error_message"] or "")


def test_migration_guard_telemetry_records_failure_on_step_limit(tmp_path: Path):
    """Verify MigrationGuard records Success=False in telemetry when agent reaches step limit."""
    guard = MigrationGuard()
    guard.config.use_guarded_fsm = True
    guard.config.canary_percentage = 100

    dispatcher = OrchestratorDispatcher(migration_guard=guard)
    cfg = OrchestratorConfig(workspace_path=tmp_path)

    # Mock GuardedFSMEngine to return failed result from step limit
    with MagicMock() as MockEngineClass:
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            "success": False,
            "status": "FAILED",
            "run_id": "RUN-FAIL-001",
            "error_message": "Agent reached maximum iterations limit (11)",
            "state_history": ["INIT", "PREFLIGHT", "IMPLEMENTATION", "VERIFICATION", "RESOLUTION", "FAILED"],
        }
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("orchestrator.pipeline.dispatcher.GuardedFSMEngine", lambda **kwargs: mock_instance)
            res = dispatcher.dispatch(
                task="Implement complex algorithm",
                mode="dev-test",
                config=cfg,
                workspace=tmp_path,
            )

    assert res["success"] is False
    assert res["status"] == "FAILED"

    # Verify MigrationGuard recorded failure, NOT success
    summary = guard.get_telemetry_summary()
    assert summary["modern_failures"] == 1
    assert summary["modern_successes"] == 0
    assert len(guard.telemetry_records) == 1
    assert guard.telemetry_records[0].success is False
    assert guard.telemetry_records[0].plane == ExecutionPlane.MODERN_GUARDED_FSM
    assert "Agent reached maximum iterations limit" in (guard.telemetry_records[0].error_message or "")
