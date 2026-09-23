"""Unit tests verifying Phase 2: Context, Token Optimization & Sandbox Security."""

import os
from pathlib import Path
import pytest

from orchestrator.guards import PreFlightGuard
from orchestrator.utils import (
    PytestOutputParser,
    GraftContextProvider,
    CompactSkillInjector,
)
from orchestrator.tools.workspace_tools import (
    WorkspaceFileAction,
    execute_file_action,
    WorkspaceTerminalAction,
    execute_terminal_action,
)
from openhands.sdk.skills import Skill


def test_preflight_guard_detects_syntax_errors(tmp_path: Path):
    """PreFlightGuard should accurately flag syntax errors offline in <50ms without invoking LLMs."""
    # Valid file
    valid_file = tmp_path / "valid.py"
    valid_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    ok, err = PreFlightGuard.check_syntax(tmp_path)
    assert ok is True
    assert err == ""

    # Broken syntax file
    broken_file = tmp_path / "broken.py"
    broken_file.write_text("def hello(\n    return 'missing paren'\n", encoding="utf-8")
    ok, err = PreFlightGuard.check_syntax(tmp_path)
    assert ok is False
    assert "Syntax error in 'broken.py'" in err or "broken.py" in err


def test_pytest_output_parser_compacts_failures():
    """PytestOutputParser should strip passing test noise and format minimal actionable failure traces."""
    verbose_stdout = """
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-8.0.0
rootdir: /workspace
collected 4 items

tests/test_app.py::test_pass1 PASSED                                    [ 25%]
tests/test_app.py::test_pass2 PASSED                                    [ 50%]
tests/test_app.py::test_fail FAILED                                     [ 75%]
tests/test_app.py::test_pass3 PASSED                                    [100%]

================================== FAILURES ===================================
__________________________________ test_fail __________________________________

    def test_fail():
        result = compute(10)
>       assert result == 42
E       AssertionError: assert 10 == 42

tests/test_app.py:15: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_app.py::test_fail - AssertionError: assert 10 == 42
========================= 1 failed, 3 passed in 0.12s =========================
"""
    compact = PytestOutputParser.extract_compact_failures(verbose_stdout, "")
    assert "test_fail" in compact
    assert "assert 10 == 42" in compact
    assert "test_pass1 PASSED" not in compact
    assert "test_pass2 PASSED" not in compact


def test_compact_skill_injector():
    """CompactSkillInjector should compress skill content by removing code blocks and trimming."""
    long_content = """# Header
Here are the principles:
- Rule 1: Always type hint.
- Rule 2: Never use stubs.

```python
def example():
    pass
```

Additional details:
- Rule 3: Fast test suites.
"""
    skill = Skill(name="sample-skill", content=long_content)
    compact_skill = CompactSkillInjector.create_compact_skill(skill, max_chars=300)

    assert compact_skill.name == "sample-skill"
    assert "def example():" not in compact_skill.content
    assert "Rule 1: Always type hint" in compact_skill.content


def test_rbac_file_restrictions(tmp_path: Path):
    """File tool must enforce RBAC: read-only, allowed prefixes, and blocked prefixes."""
    # 1. Read-only restriction (Reviewer)
    action_write = WorkspaceFileAction(operation="write", path="src/main.py", content="print('hello')")
    obs_ro = execute_file_action(action_write, base_dir=tmp_path, read_only=True)
    assert obs_ro.is_error is True
    assert "read-only access" in obs_ro.message

    # Read should still be allowed under read_only
    test_file = tmp_path / "src" / "main.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("x = 1\n", encoding="utf-8")
    action_read = WorkspaceFileAction(operation="read", path="src/main.py")
    obs_read = execute_file_action(action_read, base_dir=tmp_path, read_only=True)
    assert obs_read.is_error is False
    assert "x = 1" in (obs_read.file_content or "")

    # 2. Blocked write prefixes (Developer blocked from tests/)
    action_dev_test = WorkspaceFileAction(operation="write", path="tests/test_hacked.py", content="# hack")
    obs_dev = execute_file_action(action_dev_test, base_dir=tmp_path, blocked_write_prefixes=["tests/"])
    assert obs_dev.is_error is True
    assert "restricted" in obs_dev.message

    # Developer allowed to write outside tests/
    action_dev_ok = WorkspaceFileAction(operation="write", path="src/feature.py", content="# feature")
    obs_dev_ok = execute_file_action(action_dev_ok, base_dir=tmp_path, blocked_write_prefixes=["tests/"])
    assert obs_dev_ok.is_error is False

    # 3. Allowed write prefixes (Architect allowed only PLAN.md)
    action_arch_plan = WorkspaceFileAction(operation="write", path="PLAN.md", content="# Architecture Plan")
    obs_arch_ok = execute_file_action(action_arch_plan, base_dir=tmp_path, allowed_write_prefixes=["PLAN.md"])
    assert obs_arch_ok.is_error is False

    action_arch_code = WorkspaceFileAction(operation="write", path="src/impl.py", content="# Should be blocked")
    obs_arch_blocked = execute_file_action(action_arch_code, base_dir=tmp_path, allowed_write_prefixes=["PLAN.md"])
    assert obs_arch_blocked.is_error is True
    assert "outside permitted role scope" in obs_arch_blocked.message


def test_terminal_environment_credential_sanitization(tmp_path: Path):
    """Terminal tool must strip sensitive keys (OPENROUTER_API_KEY, SECRET, etc.) before spawning processes."""
    # Set a sensitive dummy variable in environment
    os.environ["MOCK_SECRET_KEY"] = "super_secret_value_12345"
    os.environ["MOCK_TOKEN"] = "bearer_secret_abc"
    try:
        # Run a python command that checks if MOCK_SECRET_KEY is visible
        cmd = 'python -c "import os; print(\'VISIBLE\' if \'MOCK_SECRET_KEY\' in os.environ or \'MOCK_TOKEN\' in os.environ else \'STRIPPED\')"'
        obs = execute_terminal_action(WorkspaceTerminalAction(command=cmd), base_dir=tmp_path)
        assert obs.is_error is False
        assert "STRIPPED" in obs.stdout
    finally:
        os.environ.pop("MOCK_SECRET_KEY", None)
        os.environ.pop("MOCK_TOKEN", None)


def test_graft_context_provider_fallback(tmp_path: Path):
    """GraftContextProvider should gracefully handle systems without graft CLI installed."""
    # Should not raise exception even if graft is absent
    map_res = GraftContextProvider.get_compact_map(tmp_path)
    skeleton_res = GraftContextProvider.get_skeleton(tmp_path, "any_file.py")
    assert map_res is None or isinstance(map_res, str)
    assert skeleton_res is None or isinstance(skeleton_res, str)
