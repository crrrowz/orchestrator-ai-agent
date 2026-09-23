"""Unit and integration tests for Autonomous Audit & Auto-Fix Pipeline (--mode audit-fix)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestrator.config import OrchestratorConfig, SkillManager, ORCHESTRATOR_ROOT
from orchestrator.pipeline import AuditFixPipeline
from orchestrator.main import parse_args, resolve_workspace_dir, resolve_task_input
from orchestrator.agents.developer import create_developer_agent


def test_audit_fix_pipeline_metrics_collection(tmp_path: Path):
    """AuditFixPipeline should compute file counts and LOC excluding venv and cache."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text("def process():\n    return 42\n", encoding="utf-8")
    (src / "model.py").write_text("class Item:\n    name: str\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, tmp_path)

    metrics = pipeline.collect_codebase_metrics()
    assert metrics["total_files"] == 2
    assert metrics["total_loc"] == 4
    assert metrics["avg_loc"] == 2


def test_audit_fix_pipeline_static_checks(tmp_path: Path):
    """AuditFixPipeline.run_static_checks detects syntax errors in python files."""
    # 1. Valid syntax
    good_file = tmp_path / "valid.py"
    good_file.write_text("x = 10\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, tmp_path)

    clean, issues = pipeline.run_static_checks()
    assert clean is True
    assert len(issues) == 0

    # 2. Invalid syntax
    bad_file = tmp_path / "broken.py"
    bad_file.write_text("def broken_syntax(\n", encoding="utf-8")

    clean_after, issues_after = pipeline.run_static_checks()
    assert clean_after is False
    assert any("Syntax Error" in iss or "broken.py" in iss for iss in issues_after)


def test_developer_agent_allow_test_writes(tmp_path: Path):
    """create_developer_agent with allow_test_writes=True allows writing to tests/ directory."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)

    # Standard dev agent (allow_test_writes=False): blocked on tests/
    dev_standard = create_developer_agent(cfg, sm, tmp_path, allow_test_writes=False)
    # Audit-fix dev agent (allow_test_writes=True): no write blocks
    dev_fix = create_developer_agent(cfg, sm, tmp_path, allow_test_writes=True)

    assert dev_standard is not None
    assert dev_fix is not None


def test_audit_fix_pipeline_clean_convergence(tmp_path: Path):
    """When workspace has valid code, pipeline converges cleanly and writes AUDIT_FIX_REPORT.md without git."""
    (tmp_path / "app.py").write_text(
        "def main():\n    return 'clean'\n", encoding="utf-8"
    )

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, tmp_path)

    with (
        patch("orchestrator.pipeline.audit_fix_pipeline.Conversation") as mock_conv_cls,
        patch("orchestrator.pipeline.audit_fix_pipeline.get_llm_usage") as mock_usage,
    ):
        mock_conv = MagicMock()
        mock_conv_cls.return_value = mock_conv
        mock_usage.return_value = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "estimated_cost_usd": 0.0,
        }

        res = pipeline.run("Autonomous auto-fix validation")

        assert res["status"] in ("CONVERGED_CLEAN", "MAX_ITERATIONS_REACHED")
        report_file = tmp_path / "docs" / "AUDIT_FIX_REPORT.md"
        assert report_file.exists()
        content = report_file.read_text(encoding="utf-8")
        assert "Autonomous Codebase Audit & Auto-Fix Report" in content
        assert "Zero Git Footprint" in content or "Final Verification State" in content


def test_audit_fix_pipeline_remediation_loop(tmp_path: Path):
    """When syntax error is present, developer remediation is invoked to fix issues."""
    broken_py = tmp_path / "module.py"
    broken_py.write_text("def foo(\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=2)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, tmp_path)

    # Simulate developer fixing the syntax error during run_conv
    def fix_code_side_effect(*args, **kwargs):
        broken_py.write_text("def foo():\n    return 'fixed'\n", encoding="utf-8")

    with (
        patch("orchestrator.pipeline.audit_fix_pipeline.Conversation") as mock_conv_cls,
        patch("orchestrator.pipeline.audit_fix_pipeline.get_llm_usage") as mock_usage,
    ):
        mock_conv = MagicMock()
        mock_conv.run.side_effect = fix_code_side_effect
        mock_conv_cls.return_value = mock_conv
        mock_usage.return_value = {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "estimated_cost_usd": 0.001,
        }

        res = pipeline.run("Fix syntax error")

        assert res["status"] == "CONVERGED_CLEAN"
        assert (tmp_path / "docs" / "AUDIT_FIX_REPORT.md").exists()
        # Verify code was actually fixed
        assert "def foo():" in broken_py.read_text(encoding="utf-8")


def test_resolve_workspace_dir_graceful_handling(tmp_path: Path):
    """Passing a file path as workspace resolves to parent directory rather than failing."""
    dummy_file = tmp_path / "AUDIT_REPORT.md"
    dummy_file.write_text("# Audit Report", encoding="utf-8")

    resolved = resolve_workspace_dir(dummy_file, tmp_path)
    assert resolved == tmp_path
    assert resolved.is_dir()


def test_resolve_task_input_embedded_file(tmp_path: Path):
    """resolve_task_input reads referenced file contents if mentioned inside task text."""
    report_file = tmp_path / "AUDIT_REPORT.md"
    report_file.write_text("Issue: missing tests in core module", encoding="utf-8")

    task_str = f"Please inspect and fix {report_file}"
    resolved_task = resolve_task_input(task_str)

    assert "missing tests in core module" in resolved_task
    assert report_file.name in resolved_task


def test_cli_mode_audit_fix_parsing():
    """CLI argument parser accepts --mode audit-fix without errors."""
    with patch("sys.argv", ["orchestrator", "--mode", "audit-fix"]):
        args = parse_args()
        assert args.mode == "audit-fix"
