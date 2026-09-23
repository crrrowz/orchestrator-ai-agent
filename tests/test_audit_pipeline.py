"""Unit tests for Deep Code Analysis Pipeline (--mode audit)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.config import OrchestratorConfig, SkillManager, ORCHESTRATOR_ROOT
from orchestrator.agents import create_auditor_agent
from orchestrator.pipeline import AuditPipeline
from orchestrator.orchestrator import Orchestrator
from orchestrator.tools.workspace_tools import WorkspaceFileAction, execute_file_action


def test_audit_pipeline_metrics_collection(tmp_path: Path):
    """AuditPipeline should compute file counts and LOC excluding venv and cache."""
    # Create sample codebase
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    (src / "auth.py").write_text("class Auth:\n    pass\n", encoding="utf-8")

    # Excluded directory
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "site.py").write_text("x = 1\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditPipeline(cfg, sm, tmp_path)

    metrics = pipeline.collect_codebase_metrics()
    assert metrics["total_files"] == 2
    assert metrics["total_loc"] == 4
    assert metrics["avg_loc"] == 2


def test_auditor_agent_rbac_write_restriction(tmp_path: Path):
    """Auditor agent file tool must deny writing to source files and allow AUDIT_REPORT.md."""
    # Auditor file tool allows only AUDIT_REPORT.md / audit_report.md
    allowed_prefixes = ["AUDIT_REPORT.md", "audit_report.md"]

    # 1. Attempt writing to source file -> should be denied
    action_source = WorkspaceFileAction(
        operation="write",
        path="src/service.py",
        content="# malicious or unintended edit",
    )
    obs_source = execute_file_action(
        action_source,
        base_dir=tmp_path,
        allowed_write_prefixes=allowed_prefixes,
    )
    assert obs_source.success is False
    assert "Permission denied" in obs_source.message
    assert not (tmp_path / "src" / "service.py").exists()

    # 2. Attempt writing to AUDIT_REPORT.md -> should succeed
    action_report = WorkspaceFileAction(
        operation="write",
        path="AUDIT_REPORT.md",
        content="# Codebase Audit Report\n\nAll clear.\n",
    )
    obs_report = execute_file_action(
        action_report,
        base_dir=tmp_path,
        allowed_write_prefixes=allowed_prefixes,
    )
    assert obs_report.success is True
    assert (tmp_path / "AUDIT_REPORT.md").exists()
    assert "All clear" in (tmp_path / "AUDIT_REPORT.md").read_text(encoding="utf-8")


def test_audit_pipeline_run_generates_report(tmp_path: Path):
    """AuditPipeline.run should produce AUDIT_REPORT.md and record audit telemetry."""
    # Create sample code in workspace
    (tmp_path / "app.py").write_text("def run():\n    print('ok')\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditPipeline(cfg, sm, tmp_path)

    with patch("orchestrator.pipeline.audit_pipeline.Conversation") as mock_conv_cls, \
         patch("orchestrator.pipeline.audit_pipeline.get_llm_usage") as mock_usage:

        mock_conv = MagicMock()
        mock_conv_cls.return_value = mock_conv
        mock_usage.return_value = {
            "prompt_tokens": 1200,
            "completion_tokens": 400,
            "total_tokens": 1600,
            "estimated_cost_usd": 0.0,
        }

        # Simulate agent execution
        res = pipeline.run("Comprehensive security and architecture audit")

        assert res["status"] == "AUDIT_COMPLETED"
        report_file = tmp_path / "AUDIT_REPORT.md"
        assert report_file.exists()
        content = report_file.read_text(encoding="utf-8")
        assert "Codebase Architecture & Security Audit Report" in content
        assert "Executive Summary & Code Metrics" in content


def test_orchestrator_mode_audit_dispatch(tmp_path: Path):
    """Orchestrator.run_task with mode='audit' should invoke AuditPipeline."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    orch = Orchestrator(cfg)

    with patch.object(AuditPipeline, "run", return_value={"status": "AUDIT_COMPLETED"}) as mock_run:
        result = orch.run_task("Audit security", mode="audit", workspace_override=tmp_path)
        assert result["status"] == "AUDIT_COMPLETED"
        mock_run.assert_called_once_with("Audit security")
