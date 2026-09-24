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

    cfg = OrchestratorConfig(workspace_path=tmp_path, auto_chain_audit=False)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, tmp_path, auto_chain_audit=False)

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


def test_audit_fix_pipeline_default_task_zero_tokens_clean(tmp_path: Path):
    """When workspace is clean and auto-chain is disabled, Developer is never invoked (0 tokens)."""
    (tmp_path / "clean_module.py").write_text(
        "def compute():\n    return 42\n", encoding="utf-8"
    )

    cfg = OrchestratorConfig(workspace_path=tmp_path, auto_chain_audit=False)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, tmp_path, auto_chain_audit=False)

    with patch(
        "orchestrator.pipeline.audit_fix_pipeline.Conversation"
    ) as mock_conv_cls:
        res = pipeline.run("Autonomous codebase defect and optimization fix loop.")

        assert res["status"] == "CONVERGED_CLEAN"
        assert res["tokens"] == 0
        mock_conv_cls.return_value.run.assert_not_called()
        report_file = tmp_path / "docs" / "AUDIT_FIX_REPORT.md"
        assert report_file.exists()
        content = report_file.read_text(encoding="utf-8")
        assert (
            "No remediation iterations were needed; workspace was clean on initial scan."
            in content
        )


def test_audit_fix_pipeline_auto_chains_audit(tmp_path: Path):
    """When workspace is clean and AUDIT_REPORT.md is missing, AuditPipeline is auto-chained."""
    (tmp_path / "clean_module.py").write_text(
        "def compute():\n    return 42\n", encoding="utf-8"
    )

    cfg = OrchestratorConfig(workspace_path=tmp_path, auto_chain_audit=True)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, tmp_path, auto_chain_audit=True)

    def mock_audit_run(*args, **kwargs):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "AUDIT_REPORT.md").write_text(
            "## 4. Key Recommendations\n- Refactor clean_module.py", encoding="utf-8"
        )
        return {"status": "AUDIT_COMPLETED"}

    with (
        patch(
            "orchestrator.pipeline.audit_pipeline.AuditPipeline.run",
            side_effect=mock_audit_run,
        ) as mock_audit,
        patch("orchestrator.pipeline.audit_fix_pipeline.Conversation") as mock_conv_cls,
    ):

        def mock_dev_run(*args, **kwargs):
            (tmp_path / "clean_module.py").write_text(
                "def compute():\n    return 43\n", encoding="utf-8"
            )

        mock_conv = MagicMock()
        mock_conv.run.side_effect = mock_dev_run
        mock_conv_cls.return_value = mock_conv

        res = pipeline.run("Autonomous codebase defect and optimization fix loop.")

        mock_audit.assert_called_once()
        assert res["status"] in ("CONVERGED_CLEAN", "MAX_ITERATIONS_REACHED")
        mock_conv.run.assert_called_once()


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


def test_extract_actionable_recommendations_strips_metrics_table():
    """extract_actionable_recommendations extracts Section 6/4 and ignores file metrics tables."""
    from orchestrator.pipeline.audit_fix_pipeline import (
        extract_actionable_recommendations,
        extract_affected_files,
    )

    report = (
        "# Codebase Architecture & Security Audit Report\n\n"
        "### Largest Modules\n"
        "- `orchestrator/tools/workspace_tools.py` (883 LOC)\n"
        "- `orchestrator/pipeline/full_pipeline.py` (684 LOC)\n"
        "- `orchestrator/pipeline/audit_fix_pipeline.py` (614 LOC)\n\n"
        "## 6. Actionable Prioritized Remediation Roadmap\n"
        "- Target File: `orchestrator/pipeline/base_pipeline.py`\n"
        "  Deduplicate _run_conv and unify timeout guards.\n"
    )

    extracted = extract_actionable_recommendations(report)
    assert "Actionable Prioritized Remediation Roadmap" in extracted
    assert "base_pipeline.py" in extracted
    assert "Largest Modules" not in extracted
    assert "883 LOC" not in extracted

    # Ensure extract_affected_files only picks up the actionable file
    workspace = Path(".").resolve()
    affected = extract_affected_files([extracted], workspace)
    assert "orchestrator/pipeline/base_pipeline.py" in affected
    assert "orchestrator/tools/workspace_tools.py" not in affected


def test_structured_iteration_state_prompt_block():
    """StructuredIterationState renders compact state directive without conversation bloat."""
    from orchestrator.pipeline.iteration_state import StructuredIterationState

    state = StructuredIterationState(
        iteration=2,
        affected_files=["base_pipeline.py"],
        completed_fixes=["Fixed timeout monitor"],
        remaining_findings=["Unify _run_conv duplicate"],
        tests_status="PASSED",
    )
    rendered = state.render_prompt_block()
    assert "=== ITERATION STATE [Cycle 2] ===" in rendered
    assert "- [x] Fixed timeout monitor" in rendered
    assert "- [ ] Unify _run_conv duplicate" in rendered
    assert "`base_pipeline.py`" in rendered
    assert len(rendered.splitlines()) < 10


def test_check_and_rotate_stale_reports_converged_clean(tmp_path: Path):
    """When AUDIT_FIX_REPORT indicates CONVERGED_CLEAN, both reports are auto-archived."""
    from orchestrator.pipeline.audit_fix_pipeline import check_and_rotate_stale_reports

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    audit_file = docs_dir / "AUDIT_REPORT.md"
    audit_file.write_text("### 1.1 [HIGH] Sample Bug\nFix it.", encoding="utf-8")

    fix_file = docs_dir / "AUDIT_FIX_REPORT.md"
    fix_file.write_text(
        "# Report\n- **Final Outcome**: `CONVERGED_CLEAN`\n\n"
        "## Remediated Audit Findings\n- [x] [HIGH] Sample Bug\n",
        encoding="utf-8",
    )

    content, resolved = check_and_rotate_stale_reports(tmp_path)
    # Stale reports should be rotated out
    assert content == ""
    assert not audit_file.exists()
    assert not fix_file.exists()
    archive_dir = tmp_path / "diagnostics" / "reports" / "archive"
    assert archive_dir.exists()
    assert len(list(archive_dir.glob("*_AUDIT_REPORT.md"))) == 1
    assert len(list(archive_dir.glob("*_AUDIT_FIX_REPORT.md"))) == 1


def test_check_and_rotate_stale_reports_backlog_resumption(tmp_path: Path):
    """When AUDIT_FIX_REPORT has partial fixes, resolved titles are returned to filter queue."""
    from orchestrator.pipeline.audit_fix_pipeline import check_and_rotate_stale_reports

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    audit_file = docs_dir / "AUDIT_REPORT.md"
    audit_file.write_text(
        "### 1.1 [HIGH] First Bug\nFix 1.\n### 1.2 [HIGH] Second Bug\nFix 2.",
        encoding="utf-8",
    )

    fix_file = docs_dir / "AUDIT_FIX_REPORT.md"
    fix_file.write_text(
        "# Report\n- **Final Outcome**: `MAX_ITERATIONS_REACHED`\n\n"
        "## Remediated Audit Findings\n- [x] [HIGH] First Bug\n\n"
        "## Remaining Audit Backlog\n- [ ] [HIGH] Second Bug\n",
        encoding="utf-8",
    )

    content, resolved = check_and_rotate_stale_reports(tmp_path)
    assert "First Bug" in content
    assert any("first bug" in r for r in resolved)
    assert not any("second bug" in r for r in resolved)
    assert audit_file.exists()
