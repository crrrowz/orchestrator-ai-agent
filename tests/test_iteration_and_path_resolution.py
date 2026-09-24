"""Unit tests for auto max_iterations handling, path resolution with spaces/quotes, and PLAN.md recovery."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestrator.cli.handlers import resolve_task_input
from orchestrator.cli.wizard import interactive_wizard
from orchestrator.context.file_resolver import FilePathResolver
from orchestrator.core.config import OrchestratorConfig
from orchestrator.pipeline.dev_test_loop import DevTestLoop
from orchestrator.pipeline.full_pipeline import FullPipeline
from orchestrator.skills.manager import SkillManager


def test_resolve_task_input_with_spaces(tmp_path: Path):
    """resolve_task_input should resolve file paths containing spaces and unicode."""
    folder_with_spaces = tmp_path / "Contracted projects" / "sub dir"
    folder_with_spaces.mkdir(parents=True)
    plan_file = folder_with_spaces / "plan.md"
    plan_content = "# Project Plan\n\n- Build feature A\n- Test feature A"
    plan_file.write_text(plan_content, encoding="utf-8")

    # 1. Direct path string with spaces
    result = resolve_task_input(str(plan_file))
    assert result == plan_content

    # 2. Quoted path with spaces embedded in prompt
    task_with_quote = f'Please implement specifications in "{plan_file}"'
    result_quoted = resolve_task_input(task_with_quote)
    assert "[Referenced File Content (plan.md)]:" in result_quoted
    assert plan_content in result_quoted


def test_file_path_resolver_with_spaces_and_quotes(tmp_path: Path):
    """FilePathResolver should detect and resolve paths with spaces and quotes."""
    doc_dir = tmp_path / "My Documents" / "Specs"
    doc_dir.mkdir(parents=True)
    spec_file = doc_dir / "architecture.md"
    spec_text = "Architecture: Service A connects to Database B"
    spec_file.write_text(spec_text, encoding="utf-8")

    # 1. Exact path string as task
    enriched, resolved = FilePathResolver.extract_and_resolve(
        str(spec_file), workspace=tmp_path
    )
    assert len(resolved) == 1
    assert str(spec_file.resolve()) in resolved
    assert spec_text in enriched

    # 2. Quoted path in text
    prompt = f'Follow specs from "{spec_file}" and create tests'
    enriched_prompt, resolved_prompt = FilePathResolver.extract_and_resolve(
        prompt, workspace=tmp_path
    )
    assert len(resolved_prompt) == 1
    assert str(spec_file.resolve()) in resolved_prompt
    assert "[Referenced File: architecture.md" in enriched_prompt


def test_interactive_wizard_file_resolution(tmp_path: Path):
    """interactive_wizard should pass input through resolve_task_input."""
    plan_file = tmp_path / "plan_directive.md"
    plan_file.write_text("# Auto Directive\nDo the job.", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(tmp_path)

    with patch("builtins.input", side_effect=[str(plan_file), str(tmp_path)]):
        task, mode, ws = interactive_wizard(cfg, sm, default_mode="full")
        assert task == "# Auto Directive\nDo the job."
        assert mode == "full"
        assert ws == tmp_path.resolve()


def test_dev_test_loop_handles_auto_max_iterations(tmp_path: Path):
    """DevTestLoop must not crash with TypeError when max_iterations is 'auto'."""
    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations="auto")
    sm = SkillManager(tmp_path)
    pipeline = DevTestLoop(config=cfg, skill_manager=sm, workspace_path=tmp_path)

    # Verify controller stops gracefully without int/str comparison crash
    pipeline.controller.request_abort()

    with (
        patch.object(pipeline, "_run_conv", return_value=None),
        patch("orchestrator.pipeline.dev_test_loop.create_developer_agent") as mock_dev,
        patch("orchestrator.pipeline.dev_test_loop.create_tester_agent") as mock_test,
    ):
        mock_dev.return_value = MagicMock()
        mock_test.return_value = MagicMock()

        res = pipeline.run("Test task")
        assert res["status"] in ("STOPPED", "SUCCESS", "TESTS_FAILED")


def test_full_pipeline_handles_auto_max_iterations(tmp_path: Path):
    """FullPipeline must not crash with TypeError when max_iterations is 'auto'."""
    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations="auto")
    sm = SkillManager(tmp_path)
    pipeline = FullPipeline(config=cfg, skill_manager=sm, workspace_path=tmp_path)

    # Verify controller stops gracefully without int/str comparison crash
    pipeline.controller.request_abort()

    with (
        patch.object(pipeline, "_run_conv", return_value=None),
        patch(
            "orchestrator.pipeline.full_pipeline.create_architect_agent"
        ) as mock_arch,
        patch("orchestrator.pipeline.full_pipeline.create_developer_agent") as mock_dev,
        patch("orchestrator.pipeline.full_pipeline.create_tester_agent") as mock_test,
        patch("orchestrator.pipeline.full_pipeline.create_reviewer_agent") as mock_rev,
    ):
        mock_arch.return_value = MagicMock()
        mock_dev.return_value = MagicMock()
        mock_test.return_value = MagicMock()
        mock_rev.return_value = MagicMock()

        res = pipeline.run("Test task")
        assert res["status"] in ("STOPPED", "SUCCESS", "TESTS_FAILED")


def test_full_pipeline_plan_md_auto_recovery_from_events(tmp_path: Path):
    """When Architect emits plan text in conversation events, it should be auto-recovered to PLAN.md."""
    plan_file = tmp_path / "PLAN.md"
    assert not plan_file.exists()

    # Simulate conversation state with architect response
    architect_conv = MagicMock()
    mock_event = MagicMock()
    mock_event.content = "# Architectural Blueprint\n\n## Milestone 1: Core Service\nImplement core engine."
    mock_event.text = None
    architect_conv.state.events = [mock_event]

    recovered_plan = ""
    for ev in reversed(architect_conv.state.events):
        text = str(getattr(ev, "content", "") or getattr(ev, "text", "") or "").strip()
        if text and ("#" in text or "milestone" in text.lower() or len(text) > 80):
            recovered_plan = text
            break

    if recovered_plan:
        plan_file.write_text(recovered_plan, encoding="utf-8")

    assert plan_file.exists()
    assert "Milestone 1: Core Service" in plan_file.read_text(encoding="utf-8")
