"""Unit and regression tests for Cross-Platform Subprocess Execution & Ghost-Defect Isolation."""

from pathlib import Path
from unittest.mock import patch

from orchestrator.adapters.python_adapter import PythonAdapter
from orchestrator.analysis.pytest_parser import PytestOutputParser
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.core.constants import ORCHESTRATOR_ROOT
from orchestrator.pipeline.audit_fix_pipeline import AuditFixPipeline
from orchestrator.sentinel.command_interceptor import TerminalCommandTranslator
from orchestrator.tools.workspace_tools import (
    WorkspaceTerminalAction,
    WorkspaceTerminalObservation,
    execute_terminal_action,
)


def test_pytest_parser_detects_uv_trampoline_crash():
    """Verify is_runner_crash accurately identifies uv trampoline crashes on Windows."""
    stdout = ""
    stderr = "error: uv trampoline failed to canonicalize script path"
    is_crash, reason = PytestOutputParser.is_runner_crash(stdout, stderr)
    assert is_crash is True
    assert "trampoline" in reason.lower()

    # Verify compact summary informs the agent not to modify code logic
    compact = PytestOutputParser.extract_compact_failures(stdout, stderr)
    assert "ENVIRONMENT RUNNER LAUNCHER CRASH" in compact
    assert "DO NOT MODIFY CODE LOGIC" in compact


def test_pytest_parser_detects_missing_module_crash():
    """Verify is_runner_crash detects missing pytest interpreter errors."""
    stdout = ""
    stderr = "/usr/bin/python: No module named pytest"
    is_crash, reason = PytestOutputParser.is_runner_crash(stdout, stderr)
    assert is_crash is True
    assert "pytest not installed" in reason


def test_pytest_parser_passes_legitimate_assertion_failures():
    """Verify is_runner_crash returns False for actual code logic / test assertion failures."""
    stdout = """
============================= test session starts =============================
collected 2 items

tests/test_math.py .F                                                    [100%]

================================== FAILURES ===================================
__________________________________ test_add ___________________________________

    def test_add():
>       assert add(2, 2) == 5
E       assert 4 == 5

tests/test_math.py:4: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_math.py::test_add - assert 4 == 5
========================= 1 failed, 1 passed in 0.12s =========================
"""
    stderr = ""
    is_crash, reason = PytestOutputParser.is_runner_crash(stdout, stderr)
    assert is_crash is False
    assert reason == ""

    compact = PytestOutputParser.extract_compact_failures(stdout, stderr)
    assert "FAILED tests/test_math.py::test_add" in compact
    assert "AssertionError" in compact
    assert "ENVIRONMENT RUNNER" not in compact


def test_terminal_command_translator_windows_python_module_translation():
    """Verify TerminalCommandTranslator rewrites launcher executables on Windows to interpreter modules."""
    # 1. Bare pytest
    ok, translated, _ = TerminalCommandTranslator.intercept_and_translate(
        "pytest tests/ -v", os_name="nt"
    )
    assert ok is True
    assert translated == "python -m pytest tests/ -v"

    # 2. uv run pytest
    ok, translated, _ = TerminalCommandTranslator.intercept_and_translate(
        "uv run pytest tests/ -v", os_name="nt"
    )
    assert ok is True
    assert translated == "uv run python -m pytest tests/ -v"

    # 3. ruff check
    ok, translated, _ = TerminalCommandTranslator.intercept_and_translate(
        "ruff check .", os_name="nt"
    )
    assert ok is True
    assert translated == "python -m ruff check ."

    # 4. uv run ruff
    ok, translated, _ = TerminalCommandTranslator.intercept_and_translate(
        "uv run ruff check .", os_name="nt"
    )
    assert ok is True
    assert translated == "uv run python -m ruff check ."


def test_python_adapter_resolves_module_based_test_command(tmp_path: Path):
    """Verify PythonAdapter generates module-based pytest commands."""
    adapter = PythonAdapter()
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    # With pyproject.toml and uv
    (tmp_path / "pyproject.toml").write_text("[project]\nname='app'\n", encoding="utf-8")
    with patch("shutil.which", return_value="C:\\bin\\uv.exe"):
        cmd = adapter.get_test_command(tmp_path)
        assert cmd == "uv run python -m pytest tests/ -v"

    # Without uv
    with patch("shutil.which", return_value=None):
        cmd = adapter.get_test_command(tmp_path)
        assert cmd == "python -m pytest tests/ -v"


def test_workspace_terminal_execution_in_path_with_spaces(tmp_path: Path):
    """Verify terminal action execution works seamlessly in paths containing spaces."""
    spaced_dir = tmp_path / "workspace with multiple spaces"
    spaced_dir.mkdir()
    sample_file = spaced_dir / "test_file.py"
    sample_file.write_text("print('hello from spaced path')", encoding="utf-8")

    action = WorkspaceTerminalAction(command='python -c "import sys; print(sys.version_info.major)"')
    obs = execute_terminal_action(action, base_dir=spaced_dir)
    assert obs.is_error is False
    assert obs.exit_code == 0
    assert "3" in obs.stdout


def test_audit_fix_pipeline_auto_heals_trampoline_launcher_failure(tmp_path: Path):
    """Verify audit fix pipeline auto-heals runner crash without failing the iteration."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='app'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_dummy.py").write_text("def test_dummy(): pass\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, workspace_path=tmp_path)

    # Mock first execution returning uv trampoline failure, and second returning success
    first_obs = WorkspaceTerminalObservation(
        content=[],
        is_error=True,
        exit_code=1,
        stdout="",
        stderr="error: uv trampoline failed to canonicalize script path",
    )
    second_obs = WorkspaceTerminalObservation(
        content=[],
        is_error=False,
        exit_code=0,
        stdout="1 passed in 0.01s",
        stderr="",
    )

    with patch(
        "orchestrator.pipeline.audit_fix_pipeline.execute_terminal_action",
        side_effect=[first_obs, second_obs],
    ) as mock_exec:
        passed, msg = pipeline.run_test_suite()
        assert passed is True
        assert "passed successfully" in msg
        assert mock_exec.call_count == 2
