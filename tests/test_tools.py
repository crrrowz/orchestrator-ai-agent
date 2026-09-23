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
    write_act = WorkspaceFileAction(operation="write", path="test.py", content="print('hello')")
    res_w = execute_file_action(write_act, base_dir=tmp_path)
    assert res_w.success is True
    assert (tmp_path / "test.py").exists()

    # Read
    read_act = WorkspaceFileAction(operation="read", path="test.py")
    res_r = execute_file_action(read_act, base_dir=tmp_path)
    assert res_r.success is True
    assert res_r.content == "print('hello')"


def test_file_tool_edit(tmp_path: Path):
    # Write initial
    write_act = WorkspaceFileAction(operation="write", path="mod.py", content="def foo(): return 1\n")
    execute_file_action(write_act, base_dir=tmp_path)

    # Edit
    edit_act = WorkspaceFileAction(
        operation="edit",
        path="mod.py",
        target_text="return 1",
        replacement_text="return 42"
    )
    res_e = execute_file_action(edit_act, base_dir=tmp_path)
    assert res_e.success is True

    # Verify content
    read_act = WorkspaceFileAction(operation="read", path="mod.py")
    res_r = execute_file_action(read_act, base_dir=tmp_path)
    assert "return 42" in (res_r.content or "")


def test_file_tool_path_traversal_blocked(tmp_path: Path):
    act = WorkspaceFileAction(operation="write", path="../../secret.txt", content="hack")
    res = execute_file_action(act, base_dir=tmp_path)
    assert res.success is False
    assert "Access denied" in res.message


def test_terminal_tool_execution(tmp_path: Path):
    act = WorkspaceTerminalAction(command="python -c \"print('executed')\"")
    res = execute_terminal_action(act, base_dir=tmp_path)
    assert res.exit_code == 0
    assert "executed" in res.stdout
