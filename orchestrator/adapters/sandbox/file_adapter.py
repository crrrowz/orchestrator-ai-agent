"""Hardened File Adapter (Path Jailing & Anti-Stub Virtualizer).

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant 4: The Zero Stub Invariant.
Invariant 5: Absolute Workspace Sandboxing & Credential Masking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from orchestrator.tools.hardened.manager import ToolSandboxManager
from orchestrator.tools.hardened.models import (
    AgentExecutionScope,
    FileActionRequest,
    FileOperationType,
    ToolPermissionLevel,
)


class HardenedFileAdapter:
    """Provides path-jailed, AST-guarded, anti-stub file operations."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.manager = ToolSandboxManager(workspace_path)

    def read_file(self, relative_path: str) -> str:
        full_path = (self.workspace_path / relative_path).resolve()
        if not full_path.is_relative_to(self.workspace_path.resolve()):
            raise PermissionError(f"Access denied: path '{relative_path}' outside workspace.")
        return full_path.read_text(encoding="utf-8")

    def write_file_ast_guarded(self, relative_path: str, content: str) -> bool:
        scope = AgentExecutionScope(
            persona="DEVELOPER",
            permission_level=ToolPermissionLevel.WORKSPACE_WRITE,
        )
        req = FileActionRequest(
            operation=FileOperationType.WRITE,
            path=relative_path,
            content=content,
        )
        obs = self.manager.handle_file_action(req, scope)
        return obs.success
