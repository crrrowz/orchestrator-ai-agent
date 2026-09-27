"""Hardened Terminal Adapter (Grammar Command Interceptor & Secret Redactor).

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant 5: Absolute Workspace Sandboxing & Credential Masking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple
from orchestrator.tools.hardened.manager import ToolSandboxManager
from orchestrator.tools.hardened.models import (
    AgentExecutionScope,
    TerminalActionRequest,
    ToolPermissionLevel,
)


class HardenedTerminalAdapter:
    """Provides sandboxed, grammar-checked terminal command execution."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.manager = ToolSandboxManager(workspace_path)

    def execute_command(
        self, command: str, timeout_sec: int = 60
    ) -> Tuple[int, str, str]:
        scope = AgentExecutionScope(
            persona="DEVELOPER",
            permission_level=ToolPermissionLevel.COMMAND_EXECUTION,
        )
        req = TerminalActionRequest(
            command=command,
            timeout_seconds=timeout_sec,
        )
        obs = self.manager.handle_terminal_action(req, scope)
        return obs.exit_code, obs.stdout, obs.stderr
