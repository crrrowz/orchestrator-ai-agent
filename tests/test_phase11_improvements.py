"""Unit tests validating Phase 11: Architectural Consolidation, BasePipeline, and ReviewerVerdict."""

from pathlib import Path

from orchestrator.config import ORCHESTRATOR_ROOT, OrchestratorConfig, SkillManager
from orchestrator.pipeline import (
    BasePipeline,
    DevTestLoop,
    FullPipeline,
    ReviewerVerdict,
)
from orchestrator.tools.workspace_tools import (
    WorkspaceTerminalAction,
    _matches_path_scope,
    execute_terminal_action,
    is_command_allowed,
)


def test_reviewer_verdict_json_parsing():
    """Verify ReviewerVerdict parses structured JSON code blocks correctly."""
    text_approved = """
I have audited the implementation.
```json
{
  "verdict": "APPROVED",
  "reasoning": ["Adheres to clean architecture", "100% test coverage"],
  "required_fixes": []
}
```
Good work.
"""
    v_app = ReviewerVerdict.parse(text_approved)
    assert v_app.approved is True
    assert v_app.verdict == "APPROVED"
    assert len(v_app.reasoning) == 2

    text_rejected = """
Found critical security flaw.
```json
{
  "verdict": "REJECTED",
  "reasoning": ["Input not sanitized"],
  "required_fixes": ["Add input validation regex in models.py"]
}
```
"""
    v_rej = ReviewerVerdict.parse(text_rejected)
    assert v_rej.approved is False
    assert v_rej.verdict == "REJECTED"
    assert len(v_rej.required_fixes) == 1


def test_reviewer_verdict_legacy_fallback():
    """Verify ReviewerVerdict falls back to legacy string patterns if no JSON is present."""
    text_legacy_app = "Audit complete. VERDICT: APPROVED without comments."
    v_legacy_app = ReviewerVerdict.parse(text_legacy_app)
    assert v_legacy_app.approved is True

    text_legacy_rej = "VERDICT: REJECTED\nREASONING:\n- Broken test"
    v_legacy_rej = ReviewerVerdict.parse(text_legacy_rej)
    assert v_legacy_rej.approved is False


def test_terminal_tool_command_allowlist(tmp_path: Path):
    """Verify terminal tool blocks unpermitted binaries and allows permitted ones."""
    assert is_command_allowed("python -c 'print(1)'") is True
    assert is_command_allowed("pytest tests/ -v") is True
    assert is_command_allowed("git status") is True
    assert is_command_allowed("curl http://example.com") is False
    assert is_command_allowed("powershell -Command Get-Process") is False

    # Blocked execution returns security violation
    act = WorkspaceTerminalAction(command="curl http://malicious.example")
    res = execute_terminal_action(act, base_dir=tmp_path)
    assert res.is_error is True
    assert res.exit_code == 126
    assert "Security policy violation" in res.stderr


def test_rbac_matches_path_scope():
    """Verify exact file matching prevents prefix bleeding into extensions or backup files."""
    assert _matches_path_scope("PLAN.md", "PLAN.md") is True
    # Crucial security fix: PLAN.md must not match PLAN.md.bak
    assert _matches_path_scope("PLAN.md.bak", "PLAN.md") is False
    assert _matches_path_scope("PLAN.md2", "PLAN.md") is False

    # Directory scope
    assert _matches_path_scope("docs/arch.md", "docs/") is True
    assert _matches_path_scope("docs/arch.md", "docs") is True
    assert _matches_path_scope("src/module.py", "docs") is False


def test_base_pipeline_subclasses():
    """Verify DevTestLoop and FullPipeline inherit from BasePipeline and share common lifecycle."""
    assert issubclass(DevTestLoop, BasePipeline)
    assert issubclass(FullPipeline, BasePipeline)

    config = OrchestratorConfig()
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = DevTestLoop(config=config, skill_manager=sm)

    assert hasattr(pipeline, "_setup_run")
    assert hasattr(pipeline, "_run_conv")
    assert hasattr(pipeline, "_run_preflight")
    assert hasattr(pipeline, "_execute_pytest")
    assert hasattr(pipeline, "_finalize_pipeline")
    assert hasattr(pipeline, "controller")
    assert hasattr(pipeline, "budget_guard")
    assert hasattr(pipeline, "state_machine")
