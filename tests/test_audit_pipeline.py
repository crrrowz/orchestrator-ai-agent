"""Unit tests for Deep Code Analysis Pipeline (--mode audit)."""

from pathlib import Path
from unittest.mock import MagicMock, patch


from orchestrator.config import OrchestratorConfig, SkillManager, ORCHESTRATOR_ROOT
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
    """Auditor agent file tool must deny writing to source files and allow docs/AUDIT_REPORT.md."""
    # Auditor file tool allows only docs/AUDIT_REPORT.md and related report paths
    allowed_prefixes = [
        "docs/AUDIT_REPORT.md",
        "docs/audit_report.md",
        "docs/",
        "AUDIT_REPORT.md",
        "audit_report.md",
    ]

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

    # 2. Attempt writing to docs/AUDIT_REPORT.md -> should succeed
    action_report = WorkspaceFileAction(
        operation="write",
        path="docs/AUDIT_REPORT.md",
        content="# Codebase Audit Report\n\nAll clear.\n",
    )
    obs_report = execute_file_action(
        action_report,
        base_dir=tmp_path,
        allowed_write_prefixes=allowed_prefixes,
    )
    assert obs_report.success is True
    assert (tmp_path / "docs" / "AUDIT_REPORT.md").exists()
    assert "All clear" in (tmp_path / "docs" / "AUDIT_REPORT.md").read_text(
        encoding="utf-8"
    )


def test_audit_pipeline_run_generates_report(tmp_path: Path):
    """AuditPipeline.run should produce docs/AUDIT_REPORT.md and record audit telemetry."""
    # Create sample code in workspace
    (tmp_path / "app.py").write_text("def run():\n    print('ok')\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditPipeline(cfg, sm, tmp_path)

    with (
        patch("orchestrator.pipeline.audit_pipeline.Conversation") as mock_conv_cls,
        patch("orchestrator.pipeline.audit_pipeline.get_llm_usage") as mock_usage,
    ):
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
        report_file = tmp_path / "docs" / "AUDIT_REPORT.md"
        assert report_file.exists()
        content = report_file.read_text(encoding="utf-8")
        assert "Codebase Architecture & Security Audit Report" in content
        assert "Executive Summary & Code Metrics" in content


def test_orchestrator_mode_audit_dispatch(tmp_path: Path):
    """Orchestrator.run_task with mode='audit' should invoke AuditPipeline."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    orch = Orchestrator(cfg)

    with patch.object(
        AuditPipeline, "run", return_value={"status": "AUDIT_COMPLETED"}
    ) as mock_run:
        result = orch.run_task(
            "Audit security", mode="audit", workspace_override=tmp_path
        )
        assert result["status"] == "AUDIT_COMPLETED"
        mock_run.assert_called_once_with("Audit security")


def test_audit_report_io_normalization_and_reading(tmp_path: Path):
    """Test locate_and_normalize_report migrates root report to docs/ and read_report extracts text."""
    from orchestrator.pipeline import locate_and_normalize_report, read_report

    # Initially empty
    assert locate_and_normalize_report(tmp_path, "AUDIT_REPORT.md") is None
    assert read_report(tmp_path, "AUDIT_REPORT.md") == ""

    # Create root level report
    root_report = tmp_path / "AUDIT_REPORT.md"
    root_report.write_text("# Root Audit\nSample body.", encoding="utf-8")

    # Locate and normalize should migrate to docs/
    normalized_path = locate_and_normalize_report(tmp_path, "AUDIT_REPORT.md")
    assert normalized_path == tmp_path / "docs" / "AUDIT_REPORT.md"
    assert normalized_path.exists()
    assert not root_report.exists()

    # read_report should return content
    content = read_report(tmp_path, "AUDIT_REPORT.md")
    assert "Root Audit" in content


def test_audit_result_contract_serialization_and_markdown(tmp_path: Path):
    """Test structured AuditResult JSON serialization and markdown rendering."""
    from orchestrator.analysis.schemas import AuditFinding, AuditResult, AuditState

    target_file = tmp_path / "src" / "service.py"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text("def process(): pass\n", encoding="utf-8")

    finding = AuditFinding(
        id="AUD-001",
        severity="HIGH",
        type="BUG",
        file="src/service.py",
        line=1,
        evidence="def process(): pass",
        problem="Empty stub function",
        recommended_fix="Implement logic",
        actionable=True,
    )

    result = AuditResult(
        status=AuditState.AUDIT_COMPLETED,
        summary="Found 1 defect",
        findings=[finding],
        total_files_scanned=10,
        total_loc=500,
        clean_static=True,
    )

    json_path = tmp_path / "docs" / "audit_findings.json"
    result.save_json(json_path)
    assert json_path.exists()

    loaded = AuditResult.load_json(json_path)
    assert loaded is not None
    assert loaded.status == AuditState.AUDIT_COMPLETED
    assert len(loaded.findings) == 1
    assert loaded.findings[0].id == "AUD-001"

    md = loaded.to_markdown()
    assert "AUD-001" in md
    assert "src/service.py" in md
    assert "Empty stub function" in md


def test_finding_validator_evidence_integrity(tmp_path: Path):
    """Test FindingValidator rejects non-existent files, generic advice, and non-actionable findings."""
    from orchestrator.analysis.schemas import AuditFinding, FindingValidator

    real_file = tmp_path / "app.py"
    real_file.write_text("x = 1\n", encoding="utf-8")

    # 1. Valid finding
    valid = AuditFinding(
        id="AUD-001",
        severity="HIGH",
        type="BUG",
        file="app.py",
        line=1,
        evidence="x = 1",
        problem="Hardcoded variable",
        recommended_fix="Use config setting",
        actionable=True,
    )
    ok, reason = FindingValidator.validate(valid, tmp_path)
    assert ok is True
    assert reason is None

    # 2. Non-existent file
    ghost_file = AuditFinding(
        id="AUD-002",
        severity="HIGH",
        type="BUG",
        file="nonexistent.py",
        evidence="some code",
        problem="Ghost problem",
        recommended_fix="Fix it",
        actionable=True,
    )
    ok, reason = FindingValidator.validate(ghost_file, tmp_path)
    assert ok is False
    assert "does not exist on disk" in reason

    # 3. Generic informational advisory
    generic = AuditFinding(
        id="AUD-003",
        severity="HIGH",
        type="BUG",
        file="app.py",
        line=None,
        evidence="hotspot advisory",
        problem="Review file size hotspots exceeding 300 LOC",
        recommended_fix="Decompose files",
        actionable=True,
    )
    ok, reason = FindingValidator.validate(generic, tmp_path)
    assert ok is False
    assert "generic informational advisory" in reason

    # 4. Non-actionable flag
    non_actionable = AuditFinding(
        id="AUD-004",
        severity="LOW",
        type="CONVENTION",
        file="app.py",
        evidence="x = 1",
        problem="Style note",
        recommended_fix="Refactor",
        actionable=False,
    )
    ok, reason = FindingValidator.validate(non_actionable, tmp_path)
    assert ok is False
    assert "non-actionable" in reason


def test_audit_fix_pipeline_halts_on_incomplete_audit_state(tmp_path: Path):
    """When audit findings state is AUDIT_INCOMPLETE, audit-fix must halt immediately."""
    from orchestrator.analysis.schemas import AuditResult, AuditState
    from orchestrator.pipeline import AuditFixPipeline

    (tmp_path / "main.py").write_text("print('test')\n", encoding="utf-8")

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    incomplete_result = AuditResult(
        status=AuditState.AUDIT_INCOMPLETE,
        summary="Audit failed or was incomplete",
        findings=[],
        total_files_scanned=1,
        total_loc=1,
        clean_static=True,
    )
    incomplete_result.save_json(docs_dir / "audit_findings.json")

    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=4)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, tmp_path)

    with patch("orchestrator.pipeline.audit_fix_pipeline.Conversation") as mock_conv:
        res = pipeline.run("Audit and fix")
        assert res["status"] == "AUDIT_INCOMPLETE"
        assert res["converged"] is False
        # Developer agent conversation must never be instantiated
        mock_conv.assert_not_called()


def test_audit_fix_pipeline_fast_converges_on_clean_contract(tmp_path: Path):
    """When audit contract is AUDIT_CLEAN, audit-fix must converge in iteration 1 without dev steps."""
    from orchestrator.analysis.schemas import AuditResult, AuditState
    from orchestrator.pipeline import AuditFixPipeline

    (tmp_path / "main.py").write_text("print('test')\n", encoding="utf-8")

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    clean_result = AuditResult(
        status=AuditState.AUDIT_CLEAN,
        summary="Workspace clean",
        findings=[],
        total_files_scanned=1,
        total_loc=1,
        clean_static=True,
    )
    clean_result.save_json(docs_dir / "audit_findings.json")

    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=4)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, tmp_path)

    with patch("orchestrator.pipeline.audit_fix_pipeline.Conversation") as mock_conv:
        res = pipeline.run("Audit and fix")
        assert res["status"] == "CONVERGED_CLEAN"
        assert res["iterations"] == 1
        mock_conv.assert_not_called()


def test_audit_pipeline_handles_token_budget_interruption_as_incomplete(tmp_path: Path):
    """When the auditor conversation is interrupted by token ceiling, status must be AUDIT_INCOMPLETE."""
    from orchestrator.pipeline.base_pipeline import ConvRunResult
    from orchestrator.analysis.schemas import AuditState

    (tmp_path / "app.py").write_text("def hello(): return 1\n", encoding="utf-8")
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditPipeline(cfg, sm, tmp_path)

    interrupted_result = ConvRunResult(
        completed=False,
        interrupted_by_tokens=True,
        tokens_consumed=104506,
    )

    with (
        patch("orchestrator.pipeline.audit_pipeline.Conversation"),
        patch.object(pipeline, "_run_conv", return_value=interrupted_result),
    ):
        res = pipeline.run("Deep audit")
        assert res["audit_state"] == AuditState.AUDIT_INCOMPLETE.value
        assert "token budget ceiling" in res["result"].summary
        report_file = tmp_path / "docs" / "AUDIT_REPORT.md"
        assert report_file.exists()
        assert "AUDIT_INCOMPLETE" in report_file.read_text(encoding="utf-8")


def test_audit_pipeline_ignores_tool_exit_code_errors_for_agent_status(tmp_path: Path):
    """Tool observation failures (like dir or grep returning 1) must not trigger AUDIT_FAILED."""
    from orchestrator.pipeline.base_pipeline import ConvRunResult
    from orchestrator.analysis.schemas import AuditState

    (tmp_path / "app.py").write_text("def hello(): return 1\n", encoding="utf-8")
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditPipeline(cfg, sm, tmp_path)

    completed_result = ConvRunResult(completed=True)

    with (
        patch("orchestrator.pipeline.audit_pipeline.Conversation"),
        patch.object(pipeline, "_run_conv", return_value=completed_result),
    ):
        res = pipeline.run("Deep audit")
        # Since static analysis is clean and agent completed without crash, workspace is AUDIT_CLEAN
        assert res["audit_state"] == AuditState.AUDIT_CLEAN.value
