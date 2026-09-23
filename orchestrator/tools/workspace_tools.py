"""In-process native tools for workspace file operations and terminal execution."""

import os
import subprocess
from pathlib import Path
from typing import Literal, Optional, Sequence, Any
from openhands.sdk.tool import Tool, ToolDefinition, register_tool, Action, Observation, ToolExecutor


# ==========================================
# 1. Workspace File Tool
# ==========================================

class WorkspaceFileAction(Action):
    """File manipulation action within the workspace sandbox."""
    operation: Literal["read", "write", "edit", "list", "delete"]
    path: str
    content: Optional[str] = None
    target_text: Optional[str] = None
    replacement_text: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class WorkspaceFileObservation(Observation):
    """Observation resulting from workspace file manipulation."""
    success: bool
    message: str
    content: Optional[str] = None
    files: Optional[list[str]] = None


def execute_file_action(
    action: WorkspaceFileAction,
    conversation=None,
    base_dir: Optional[Path] = None
) -> WorkspaceFileObservation:
    """Safely execute file operation within workspace."""
    workspace_root = base_dir or Path(os.environ.get("WORKSPACE_PATH", "./workspace")).resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)

    target_path = (workspace_root / action.path).resolve()

    # Sandboxing check
    if not str(target_path).startswith(str(workspace_root)):
        return WorkspaceFileObservation(
            success=False,
            message=f"Access denied: path '{action.path}' escapes workspace directory."
        )

    try:
        if action.operation == "read":
            if not target_path.exists():
                return WorkspaceFileObservation(
                    success=False,
                    message=f"File '{action.path}' does not exist."
                )
            lines = target_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            start = (action.start_line - 1) if action.start_line and action.start_line > 0 else 0
            end = action.end_line if action.end_line and action.end_line <= len(lines) else len(lines)
            selected_content = "".join(lines[start:end])
            return WorkspaceFileObservation(
                success=True,
                message=f"Read {len(lines[start:end])} lines from '{action.path}'.",
                content=selected_content
            )

        elif action.operation == "write":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(action.content or "", encoding="utf-8")
            return WorkspaceFileObservation(
                success=True,
                message=f"File '{action.path}' written successfully ({len(action.content or '')} chars)."
            )

        elif action.operation == "edit":
            if not target_path.exists():
                return WorkspaceFileObservation(
                    success=False,
                    message=f"File '{action.path}' not found for editing."
                )
            existing = target_path.read_text(encoding="utf-8", errors="replace")
            if not action.target_text:
                return WorkspaceFileObservation(
                    success=False,
                    message="Missing 'target_text' required for editing."
                )
            if action.target_text not in existing:
                return WorkspaceFileObservation(
                    success=False,
                    message=f"Target text was not found in '{action.path}'."
                )
            new_content = existing.replace(action.target_text, action.replacement_text or "", 1)
            target_path.write_text(new_content, encoding="utf-8")
            return WorkspaceFileObservation(
                success=True,
                message=f"Successfully edited '{action.path}'."
            )

        elif action.operation == "list":
            search_dir = target_path if target_path.is_dir() else workspace_root
            if not search_dir.exists():
                return WorkspaceFileObservation(
                    success=False,
                    message=f"Directory '{search_dir}' does not exist."
                )
            file_list = [
                str(p.relative_to(workspace_root))
                for p in search_dir.rglob("*")
                if p.is_file() and not any(part.startswith(".") for part in p.parts)
            ]
            return WorkspaceFileObservation(
                success=True,
                message=f"Found {len(file_list)} files.",
                files=file_list
            )

        elif action.operation == "delete":
            if target_path.exists():
                if target_path.is_file():
                    target_path.unlink()
                else:
                    import shutil
                    shutil.rmtree(target_path)
                return WorkspaceFileObservation(
                    success=True,
                    message=f"Deleted '{action.path}'."
                )
            return WorkspaceFileObservation(
                success=False,
                message=f"File '{action.path}' does not exist."
            )

        return WorkspaceFileObservation(
            success=False,
            message=f"Unknown operation: {action.operation}"
        )

    except Exception as e:
        return WorkspaceFileObservation(
            success=False,
            message=f"Error performing '{action.operation}' on '{action.path}': {str(e)}"
        )


class WorkspaceFileExecutor(ToolExecutor[WorkspaceFileAction, WorkspaceFileObservation]):
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path

    def __call__(
        self,
        action: WorkspaceFileAction,
        conversation: Any = None,
    ) -> WorkspaceFileObservation:
        return execute_file_action(action, conversation, self.workspace_path)


class WorkspaceFileTool(ToolDefinition[WorkspaceFileAction, WorkspaceFileObservation]):
    """Tool for reading, writing, editing, listing, and deleting files inside the project workspace."""

    @classmethod
    def create(
        cls,
        conv_state: Optional[Any] = None,
        workspace_path: Optional[str] = None,
        **params,
    ) -> Sequence["WorkspaceFileTool"]:
        target_path: Optional[Path] = None
        if workspace_path:
            target_path = Path(workspace_path)
        elif conv_state and hasattr(conv_state, "workspace"):
            ws = conv_state.workspace
            if hasattr(ws, "working_dir"):
                target_path = Path(ws.working_dir)
            elif isinstance(ws, (str, Path)):
                target_path = Path(ws)

        return [
            cls(
                description="Read, write, edit, list, and delete files inside the project workspace.",
                action_type=WorkspaceFileAction,
                observation_type=WorkspaceFileObservation,
                executor=WorkspaceFileExecutor(target_path),
            )
        ]


# ==========================================
# 2. Workspace Terminal Tool
# ==========================================

class WorkspaceTerminalAction(Action):
    """Terminal execution action within the workspace environment."""
    command: str
    timeout_seconds: int = 30


class WorkspaceTerminalObservation(Observation):
    """Observation resulting from terminal command execution."""
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


def execute_terminal_action(
    action: WorkspaceTerminalAction,
    conversation=None,
    base_dir: Optional[Path] = None
) -> WorkspaceTerminalObservation:
    """Execute terminal command safely inside workspace directory."""
    workspace_root = base_dir or Path(os.environ.get("WORKSPACE_PATH", "./workspace")).resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        proc = subprocess.run(
            action.command,
            shell=True,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            timeout=action.timeout_seconds,
            env=env
        )
        return WorkspaceTerminalObservation(
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            timed_out=False
        )
    except subprocess.TimeoutExpired as te:
        return WorkspaceTerminalObservation(
            exit_code=-1,
            stdout=te.stdout.decode() if te.stdout else "",
            stderr="Command timed out after specified seconds.",
            timed_out=True
        )
    except Exception as e:
        return WorkspaceTerminalObservation(
            exit_code=-1,
            stdout="",
            stderr=f"Execution error: {str(e)}",
            timed_out=False
        )


class WorkspaceTerminalExecutor(ToolExecutor[WorkspaceTerminalAction, WorkspaceTerminalObservation]):
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path

    def __call__(
        self,
        action: WorkspaceTerminalAction,
        conversation: Any = None,
    ) -> WorkspaceTerminalObservation:
        return execute_terminal_action(action, conversation, self.workspace_path)


class WorkspaceTerminalTool(ToolDefinition[WorkspaceTerminalAction, WorkspaceTerminalObservation]):
    """Tool for running terminal commands (tests, python, git, build) inside the workspace."""

    @classmethod
    def create(
        cls,
        conv_state: Optional[Any] = None,
        workspace_path: Optional[str] = None,
        **params,
    ) -> Sequence["WorkspaceTerminalTool"]:
        target_path: Optional[Path] = None
        if workspace_path:
            target_path = Path(workspace_path)
        elif conv_state and hasattr(conv_state, "workspace"):
            ws = conv_state.workspace
            if hasattr(ws, "working_dir"):
                target_path = Path(ws.working_dir)
            elif isinstance(ws, (str, Path)):
                target_path = Path(ws)

        return [
            cls(
                description="Run terminal commands (tests, python, git, build) inside the workspace.",
                action_type=WorkspaceTerminalAction,
                observation_type=WorkspaceTerminalObservation,
                executor=WorkspaceTerminalExecutor(target_path),
            )
        ]


# Register both tools in OpenHands global tool registry
register_tool("WorkspaceFileTool", WorkspaceFileTool)
register_tool("WorkspaceTerminalTool", WorkspaceTerminalTool)


# Factory functions to build tool specifications for Agents
def create_workspace_file_tool(workspace_path: Optional[Path] = None) -> Tool:
    params = {}
    if workspace_path:
        params["workspace_path"] = str(Path(workspace_path).resolve())
    return Tool(name="WorkspaceFileTool", params=params)


def create_workspace_terminal_tool(workspace_path: Optional[Path] = None) -> Tool:
    params = {}
    if workspace_path:
        params["workspace_path"] = str(Path(workspace_path).resolve())
    return Tool(name="WorkspaceTerminalTool", params=params)
