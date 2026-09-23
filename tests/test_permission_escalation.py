"""Tests for Dynamic Human-in-the-Loop Permission Escalation and Path Normalization."""

import pytest
from pathlib import Path
from orchestrator.control.human_channel import (
    HumanInterventionChannel,
    set_active_channel,
)
from orchestrator.tools.workspace_tools import (
    WorkspaceFileAction,
    RequestPermissionAction,
    RequestPermissionExecutor,
    execute_file_action,
)


@pytest.fixture(autouse=True)
def reset_active_channel():
    """Ensure active channel is reset after each test."""
    yield
    set_active_channel(None)


def test_path_normalization_strips_virtual_workspace_prefix(tmp_path: Path):
    """Paths starting with /workspace or workspace/ should resolve to workspace_root directly."""
    # Write a file using /workspace prefix
    action_write = WorkspaceFileAction(
        operation="write", path="/workspace/nested/example.py", content="x = 42\n"
    )
    obs = execute_file_action(action_write, base_dir=tmp_path)
    assert obs.success is True
    assert (tmp_path / "nested" / "example.py").exists()
    assert (tmp_path / "nested" / "example.py").read_text() == "x = 42\n"

    # Read using relative workspace/ prefix
    action_read = WorkspaceFileAction(
        operation="read", path="workspace/nested/example.py"
    )
    obs_read = execute_file_action(action_read, base_dir=tmp_path)
    assert obs_read.success is True
    assert "x = 42" in obs_read.file_content


def test_file_write_rbac_escalation_approved(tmp_path: Path):
    """When an agent attempts a restricted write, developer can grant permission."""
    channel = HumanInterventionChannel(enabled=True)
    set_active_channel(channel)

    # Simulate developer pressing 'y'
    def mock_input(prompt: str) -> str:
        assert "DEVELOPER PERMISSION REQUEST" in prompt
        return "y"

    action = WorkspaceFileAction(
        operation="write", path="src/protected.py", content="# privileged content\n"
    )

    # Tester agent has write scope restricted to 'tests/'
    execute_file_action(
        action,
        base_dir=tmp_path,
        allowed_write_prefixes=["tests/"],
    )

    # Since there's no interactive tty by default, let's call request_permission with mock_input
    # Now let's test request_permission directly on channel
    granted, msg = channel.request_permission(
        role="tester",
        action_type="file_write",
        target="src/protected.py",
        reason="Role outside allowed scope",
        input_fn=mock_input,
    )
    assert granted is True
    assert channel.is_path_approved("src/protected.py")

    # Now that it's authorized in session, execute_file_action succeeds!
    obs2 = execute_file_action(
        action,
        base_dir=tmp_path,
        allowed_write_prefixes=["tests/"],
    )
    assert obs2.success is True
    assert (tmp_path / "src" / "protected.py").exists()


def test_file_write_rbac_escalation_denied(tmp_path: Path):
    """When developer denies permission, the restricted action is blocked."""
    channel = HumanInterventionChannel(enabled=True)
    set_active_channel(channel)

    def mock_input(prompt: str) -> str:
        return "n"

    granted, msg = channel.request_permission(
        role="developer",
        action_type="file_write",
        target="tests/hacked.py",
        reason="Blocked write prefix",
        input_fn=mock_input,
    )
    assert granted is False
    assert not channel.is_path_approved("tests/hacked.py")


def test_terminal_restricted_command_escalation():
    """Terminal commands outside allowlist can be approved by developer."""
    channel = HumanInterventionChannel(enabled=True)
    set_active_channel(channel)

    def mock_input(prompt: str) -> str:
        return "y"

    granted, msg = channel.request_permission(
        role="developer",
        action_type="terminal_command",
        target="echo dynamic_allowed",
        reason="Testing dynamic escalation",
        input_fn=mock_input,
    )
    assert granted is True
    assert channel.is_command_approved("echo dynamic_allowed")


def test_request_permission_tool(tmp_path: Path):
    """Agent can explicitly use RequestPermissionAction to request developer approval."""
    channel = HumanInterventionChannel(enabled=True)
    set_active_channel(channel)

    # Mock conversation with human_channel
    class MockConv:
        def __init__(self, ch):
            self.human_channel = ch

    conv = MockConv(channel)
    executor = RequestPermissionExecutor()

    # Developer inputs 'y'
    def mock_input(prompt: str) -> str:
        assert "Agent request: Need to install requests for API testing" in prompt
        return "y"

    action = RequestPermissionAction(
        action_type="dependency_install",
        target="pip install requests",
        justification="Need to install requests for API testing",
    )

    # Patch input inside channel
    original_req = channel.request_permission

    def patched_req(*args, **kwargs):
        kwargs["input_fn"] = mock_input
        return original_req(*args, **kwargs)

    channel.request_permission = patched_req

    obs = executor(action, conversation=conv)
    assert obs.granted is True
    assert obs.is_error is False
    assert "Permission GRANTED" in obs.message
    assert channel.is_command_approved("pip install requests")
