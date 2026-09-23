"""Unit tests validating Report Retention Policy and Project-Partitioned Session Logs."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestrator.config import OrchestratorConfig
from orchestrator.telemetry import TelemetryRecorder
from orchestrator.utils import SessionLogStore


def test_telemetry_recorder_auto_pruning(tmp_path: Path):
    """Verify TelemetryRecorder prunes oldest report files when exceeding max_retained_reports."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    # Pre-create 5 dummy report files with synthetic timestamps
    for i in range(5):
        dummy_file = reports_dir / f"run_20260101_00000{i}_abcdef.json"
        dummy_file.write_text("{}", encoding="utf-8")
        # Ensure distinct modification times
        time.sleep(0.01)

    assert len(list(reports_dir.glob("run_*.json"))) == 5

    # Run TelemetryRecorder with max_retained_reports = 3
    rec = TelemetryRecorder(
        task_description="Test pruning",
        reports_dir=reports_dir,
        max_retained_reports=3,
    )
    rec.finalize(completed_successfully=True)

    # After finalizing: total files should not exceed 3
    remaining = list(reports_dir.glob("run_*.json"))
    assert len(remaining) <= 3
    # The newly created report should definitely exist
    assert (reports_dir / f"{rec.report_id}.json").exists()


def test_session_log_store_project_partitioning(tmp_path: Path):
    """Verify SessionLogStore partitions logs by project slug and maintains latest pointers."""
    logs_dir = tmp_path / "logs"

    # Workspace A
    ws_a = tmp_path / "ProjectAlpha"
    store_a = SessionLogStore(workspace_path=ws_a, max_retained_sessions=2)
    store_a.add_step("Step in Project A")
    saved_a = store_a.save_to_file(target_dir=logs_dir)

    # Verify Project A directory and file
    assert saved_a.exists()
    assert "projectalpha" in saved_a.parent.name
    assert (logs_dir / "projectalpha" / "latest_session.json").exists()
    assert (logs_dir / "latest_session.json").exists()

    # Workspace B
    ws_b = tmp_path / "ProjectBeta"
    store_b = SessionLogStore(workspace_path=ws_b, max_retained_sessions=2)
    store_b.add_step("Step in Project B")
    saved_b = store_b.save_to_file(target_dir=logs_dir)

    # Verify Project B does NOT overwrite Project A's directory or session log
    assert saved_b.exists()
    assert "projectbeta" in saved_b.parent.name
    assert (logs_dir / "projectbeta" / "latest_session.json").exists()
    assert (logs_dir / "projectalpha" / "latest_session.json").exists()
    assert saved_a.exists()  # Project A session file still intact!

    # Global latest points to the latest run (Project B)
    import json
    global_data = json.loads((logs_dir / "latest_session.json").read_text(encoding="utf-8"))
    assert global_data["project"] == "projectbeta"

    # Project A latest still points to Project A
    alpha_data = json.loads((logs_dir / "projectalpha" / "latest_session.json").read_text(encoding="utf-8"))
    assert alpha_data["project"] == "projectalpha"


def test_session_log_pruning_per_project(tmp_path: Path):
    """Verify SessionLogStore prunes old sessions inside its project directory."""
    logs_dir = tmp_path / "logs"
    ws = tmp_path / "DemoApp"

    # Run 4 sessions for DemoApp with max_retained_sessions = 2
    for i in range(4):
        store = SessionLogStore(workspace_path=ws, max_retained_sessions=2)
        store._session_file_name = f"session_20260101_00000{i}.json"
        store.add_step(f"Step {i}")
        store.save_to_file(target_dir=logs_dir)
        time.sleep(0.01)

    project_dir = logs_dir / "demoapp"
    session_files = list(project_dir.glob("session_*.json"))
    assert len(session_files) == 2
