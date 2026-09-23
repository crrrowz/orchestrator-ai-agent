"""Unit tests validating Phase 1 optimizations: skill isolation, budget guards, and token tracking."""

from pathlib import Path
from orchestrator.config import SkillManager
from orchestrator.telemetry import TelemetryRecorder
from orchestrator.evolution import SystemAuditor


def test_skill_isolation_no_project_leak():
    """Verify that build_agent_context sets load_project_skills=False to prevent prompt bloat."""
    manager = SkillManager(Path.cwd())
    context = manager.build_agent_context(["pytest-rigorous-testing"])
    assert context.load_project_skills is False
    assert len(context.skills) == 1
    assert context.skills[0].name == "pytest-rigorous-testing"


def test_telemetry_recorder_token_tracking_and_budget_guard(tmp_path: Path):
    """Verify recorder logs tokens, computes costs, and triggers budget guard."""
    recorder = TelemetryRecorder(
        task_description="Test Budget Task",
        pipeline_mode="dev-test",
        reports_dir=tmp_path / "reports",
        max_budget_usd=0.25,
    )

    # Record normal step
    recorder.record_step(
        agent_role="developer",
        action_type="initial_implementation",
        iteration=1,
        duration_seconds=5.0,
        success=True,
        prompt_tokens=1500,
        completion_tokens=500,
        total_tokens=2000,
        estimated_cost_usd=0.10,
    )

    assert len(recorder.metrics) == 1
    m = recorder.metrics[0]
    assert m.total_tokens == 2000
    assert m.estimated_cost_usd == 0.10

    # Under budget
    assert recorder.check_budget(0.10) is False
    assert recorder.budget_exhausted is False

    # Exceed budget
    assert recorder.check_budget(0.26) is True
    assert recorder.budget_exhausted is True
    assert any(inc.incident_type == "budget_exceeded" for inc in recorder.incidents)

    # Finalize report
    report = recorder.finalize(completed_successfully=False)
    assert report.budget_exhausted is True
    assert report.total_tokens == 2000
    assert report.total_cost_usd == 0.10
    assert (tmp_path / "reports" / f"{recorder.report_id}.json").exists()


def test_auditor_fallback_recovery(tmp_path: Path):
    """Verify auditor recovers reports from session log when reports dir is empty."""
    reports_dir = tmp_path / "diagnostics" / "reports"
    logs_dir = tmp_path / "diagnostics" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    fake_session = {
        "session_start": 1000.0,
        "steps": [
            {
                "index": 1,
                "role": "Developer",
                "phase": "Implementation",
                "summary": "Step 1",
                "action_type": "WorkspaceFileAction",
                "duration_s": 10.0,
                "is_error": False,
            },
            {
                "index": 2,
                "role": "Tester",
                "phase": "Verification",
                "summary": "Session interrupted by user (KeyboardInterrupt).",
                "action_type": None,
                "duration_s": 25.0,
                "is_error": True,
            },
        ],
    }
    import json

    (logs_dir / "latest_session.json").write_text(
        json.dumps(fake_session), encoding="utf-8"
    )

    auditor = SystemAuditor(reports_dir=reports_dir)
    reports = auditor.load_reports()
    assert len(reports) == 1
    assert reports[0].report_id == "run_recovered_from_session"
    assert any(inc.incident_type == "user_interruption" for inc in reports[0].incidents)
