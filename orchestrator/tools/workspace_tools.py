"""In-process native tools for workspace file operations and terminal execution."""

import os
import subprocess
from pathlib import Path
from typing import Literal, Optional, Sequence, Any
from openhands.sdk.tool import Tool, ToolDefinition, register_tool, Action, Observation, ToolExecutor
from openhands.sdk.tool.schema import TextContent


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
    file_content: Optional[str] = None
    files: Optional[list[str]] = None


def execute_file_action(
    action: WorkspaceFileAction,
    conversation=None,
    base_dir: Optional[Path] = None
) -> WorkspaceFileObservation:
    """Safely execute file operation within workspace."""
    workspace_root = base_dir or Path(os.environ.get("WORKSPACE_PATH", "./workspace")).resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)

    raw_path = Path(action.path)
    if raw_path.is_absolute():
        target_path = raw_path.resolve()
    else:
        target_path = (workspace_root / action.path.lstrip("/\\")).resolve()

    # Sandboxing check
    try:
        target_path.relative_to(workspace_root)
    except ValueError:
        err_msg = f"Access denied: path '{action.path}' escapes workspace directory '{workspace_root}'."
        return WorkspaceFileObservation(
            content=[TextContent(text=err_msg)],
            is_error=True,
            success=False,
            message=err_msg
        )

    try:
        if action.operation == "read":
            if not target_path.exists():
                err_msg = f"File '{action.path}' does not exist."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg
                )
            lines = target_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            start = (action.start_line - 1) if action.start_line and action.start_line > 0 else 0
            end = action.end_line if action.end_line and action.end_line <= len(lines) else len(lines)
            selected_content = "".join(lines[start:end])
            return WorkspaceFileObservation(
                content=[TextContent(text=selected_content)],
                is_error=False,
                success=True,
                message=f"Read {len(lines[start:end])} lines from '{action.path}'.",
                file_content=selected_content
            )

        elif action.operation == "write":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(action.content or "", encoding="utf-8")
            msg = f"File '{action.path}' written successfully ({len(action.content or '')} chars)."
            return WorkspaceFileObservation(
                content=[TextContent(text=msg)],
                is_error=False,
                success=True,
                message=msg
            )

        elif action.operation == "edit":
            if not target_path.exists():
                err_msg = f"File '{action.path}' not found for editing."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg
                )
            existing = target_path.read_text(encoding="utf-8", errors="replace")
            if not action.target_text:
                err_msg = "Missing 'target_text' required for editing."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg
                )
            if action.target_text not in existing:
                err_msg = f"Target text was not found in '{action.path}'."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg
                )
            new_content = existing.replace(action.target_text, action.replacement_text or "", 1)
            target_path.write_text(new_content, encoding="utf-8")
            msg = f"Successfully edited '{action.path}'."
            return WorkspaceFileObservation(
                content=[TextContent(text=msg)],
                is_error=False,
                success=True,
                message=msg
            )

        elif action.operation == "list":
            search_dir = target_path if target_path.is_dir() else workspace_root
            if not search_dir.exists():
                err_msg = f"Directory '{search_dir}' does not exist."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg
                )
            file_list = [
                str(p.relative_to(workspace_root))
                for p in search_dir.rglob("*")
                if p.is_file() and not any(part.startswith(".") for part in p.parts)
            ]
            files_str = "\n".join(file_list) if file_list else "(No files found in directory)"
            msg = f"Found {len(file_list)} files:\n{files_str}"
            return WorkspaceFileObservation(
                content=[TextContent(text=msg)],
                is_error=False,
                success=True,
                message=msg,
                files=file_list
            )

        elif action.operation == "delete":
            if target_path.exists():
                if target_path.is_file():
                    target_path.unlink()
                else:
                    import shutil
                    shutil.rmtree(target_path)
                msg = f"Deleted '{action.path}'."
                return WorkspaceFileObservation(
                    content=[TextContent(text=msg)],
                    is_error=False,
                    success=True,
                    message=msg
                )
            err_msg = f"File '{action.path}' does not exist."
            return WorkspaceFileObservation(
                content=[TextContent(text=err_msg)],
                is_error=True,
                success=False,
                message=err_msg
            )

        err_msg = f"Unknown operation: {action.operation}"
        return WorkspaceFileObservation(
            content=[TextContent(text=err_msg)],
            is_error=True,
            success=False,
            message=err_msg
        )

    except Exception as e:
        err_msg = f"Error performing '{action.operation}' on '{action.path}': {str(e)}"
        return WorkspaceFileObservation(
            content=[TextContent(text=err_msg)],
            is_error=True,
            success=False,
            message=err_msg
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
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
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
            encoding="utf-8",
            errors="replace",
            timeout=action.timeout_seconds,
            env=env
        )
        stdout_text = proc.stdout or ""
        stderr_text = proc.stderr or ""
        output_text = f"Exit code: {proc.returncode}\nStdout:\n{stdout_text}\nStderr:\n{stderr_text}"
        return WorkspaceTerminalObservation(
            content=[TextContent(text=output_text)],
            is_error=(proc.returncode != 0),
            exit_code=proc.returncode,
            stdout=stdout_text,
            stderr=stderr_text,
            timed_out=False
        )
    except subprocess.TimeoutExpired as te:
        timeout_msg = "Command timed out after specified seconds."
        stdout_str = te.stdout if isinstance(te.stdout, str) else (te.stdout.decode("utf-8", errors="replace") if te.stdout else "")
        stderr_str = te.stderr if isinstance(te.stderr, str) else (te.stderr.decode("utf-8", errors="replace") if te.stderr else timeout_msg)
        return WorkspaceTerminalObservation(
            content=[TextContent(text=timeout_msg)],
            is_error=True,
            exit_code=-1,
            stdout=stdout_str,
            stderr=stderr_str,
            timed_out=True
        )
    except Exception as e:
        err_msg = f"Execution error: {str(e)}"
        return WorkspaceTerminalObservation(
            content=[TextContent(text=err_msg)],
            is_error=True,
            exit_code=-1,
            stdout="",
            stderr=err_msg,
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
