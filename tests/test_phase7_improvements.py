"""Unit tests validating Phase 7: Dead Code Wiring, Path Isolation, and Runtime Safety."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestrator.config import (
    DEFAULT_DIAGNOSTICS_DIR,
    ORCHESTRATOR_ROOT,
    OrchestratorConfig,
    SkillManager,
)
from orchestrator.control import PipelineController
from orchestrator.pipeline import DevTestLoop
from orchestrator.pipeline.checkpoint import PipelineCheckpoint
from orchestrator.pipeline.state_machine import PipelinePhase
from orchestrator.telemetry import TelemetryRecorder


def test_path_isolation_and_skill_manager_root():
    """Verify ORCHESTRATOR_ROOT and DEFAULT_DIAGNOSTICS_DIR prevent CWD path pollution."""
    assert ORCHESTRATOR_ROOT.exists()
    assert (ORCHESTRATOR_ROOT / "orchestrator").exists()
    assert DEFAULT_DIAGNOSTICS_DIR == ORCHESTRATOR_ROOT / "diagnostics"

    # SkillManager defaults to ORCHESTRATOR_ROOT, not arbitrary CWD
    sm = SkillManager()
    assert sm.project_root == ORCHESTRATOR_ROOT


def test_telemetry_recorder_integrates_budget_guard(tmp_path: Path):
    """Verify TelemetryRecorder uses BudgetGuard internally and exposes remaining_budget."""
    rec = TelemetryRecorder(
        task_description="Test BudgetGuard integration",
        pipeline_mode="dev-test",
        reports_dir=tmp_path / "reports",
        max_budget_usd=1.00,
    )
    assert hasattr(rec, "budget_guard")
    assert rec.remaining_budget == 1.00

    # Under budget
    assert rec.check_budget(0.40) is False
    assert rec.remaining_budget == 0.60
    assert rec.budget_exhausted is False

    # Exceed budget
    assert rec.check_budget(1.05) is True
    assert rec.remaining_budget == 0.0
    assert rec.budget_exhausted is True


def test_pipeline_controller_halts_pipeline_execution(tmp_path: Path):
    """PipelineController check_should_continue() should abort pipeline gracefully when requested."""
    config = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    controller = PipelineController()
    controller.request_stop_after_current()

    pipeline = DevTestLoop(
        config=config,
        skill_manager=sm,
        workspace_path=tmp_path,
        controller=controller,
    )
    res = pipeline.run("Test stopped task")
    assert res["status"] == "STOPPED"
    assert pipeline.state_machine.current_phase == PipelinePhase.INIT


def test_checkpoint_phase_skipping_developer(tmp_path: Path):
    """When a checkpoint indicates developer phase is completed, initial implementation is skipped."""
    config = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    cp = PipelineCheckpoint(
        run_id="run_test_cp",
        task="Test checkpoint skip",
        mode="dev-test",
        current_phase="after_developer",
        completed_phases=["developer"],
    )

    pipeline = DevTestLoop(
        config=config,
        skill_manager=sm,
        workspace_path=tmp_path,
        checkpoint=cp,
    )

    # Mock terminal execution so tests pass immediately
    mock_agent = MagicMock()
    mock_agent.llm.metrics = None

    with (
        patch(
            "orchestrator.pipeline.dev_test_loop.execute_terminal_action"
        ) as mock_exec,
        patch(
            "orchestrator.pipeline.dev_test_loop.create_developer_agent",
            return_value=mock_agent,
        ),
        patch(
            "orchestrator.pipeline.dev_test_loop.create_tester_agent",
            return_value=mock_agent,
        ),
        patch("orchestrator.pipeline.dev_test_loop.Conversation"),
    ):
        mock_exec.return_value = MagicMock(exit_code=0, stdout="81 passed", stderr="")
        res = pipeline.run("Test checkpoint skip")

        assert res["status"] == "SUCCESS"
        assert pipeline.state_machine.current_phase == PipelinePhase.COMPLETED
