import ast
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal, Optional, Sequence, Any, Tuple
from pydantic import ConfigDict, Field
from openhands.sdk.tool import (
    Tool,
    ToolDefinition,
    register_tool,
    Action,
    Observation,
    ToolExecutor,
)
from openhands.sdk.tool.schema import TextContent
from orchestrator.config import DEFAULT_WORKSPACE_DIR
from orchestrator.control.human_channel import get_active_channel


# ==========================================
# 1. Workspace File Tool
# ==========================================


_APPEND_COUNTS: dict[str, int] = {}
MAX_APPENDS_PER_FILE: int = 5
MAX_READ_LINES: int = 250
MAX_READ_CHARS: int = 12_000  # ~3,000 tokens safe input ceiling


def reset_append_counts() -> None:
    """Reset session append counters across pipeline iterations."""
    _APPEND_COUNTS.clear()


class WorkspaceFileAction(Action):
    """File manipulation action within the workspace sandbox."""

    model_config = ConfigDict(extra="ignore")
    operation: Literal["read", "write", "edit", "list", "delete", "append", "symbol"]
    path: str
    symbol: Optional[str] = None
    content: Optional[str] = None
    target_text: Optional[str] = None
    replacement_text: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None


def extract_ast_symbol(
    file_path: Path, symbol_name: str
) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
    """Parse python file and extract exact function or class symbol with line bounds."""
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(file_path))
    except Exception as e:
        return None, None, None, f"Failed to parse '{file_path.name}' with AST: {e}"

    lines = source.splitlines(keepends=True)
    target = symbol_name.strip()

    match_node = None
    all_symbols = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            all_symbols.append(node.name)
            if node.name == target:
                match_node = node
                break

    # If qualified like ClassName.method
    if not match_node and "." in target:
        cls_name, m_name = target.split(".", 1)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == cls_name:
                for sub in node.body:
                    if (
                        isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and sub.name == m_name
                    ):
                        match_node = sub
                        break

    if match_node:
        start_ln = getattr(match_node, "lineno", 1)
        end_ln = getattr(match_node, "end_lineno", len(lines))
        extracted = "".join(lines[start_ln - 1 : end_ln])
        return extracted, start_ln, end_ln, None

    avail_str = ", ".join(all_symbols[:15]) if all_symbols else "None"
    return (
        None,
        None,
        None,
        f"Symbol '{target}' not found in '{file_path.name}'. Available symbols: {avail_str}",
    )


class WorkspaceFileObservation(Observation):
    """Observation resulting from workspace file manipulation."""

    success: bool
    message: str
    file_content: Optional[str] = None
    files: Optional[list[str]] = None


def sanitize_output_secrets(text: str) -> str:
    """Redact sensitive API keys, tokens, and credentials from terminal and file observations."""
    if not text:
        return text
    # 1. Redact values of environment variables with sensitive names
    sensitive_keys = {"KEY", "SECRET", "TOKEN", "PASSWORD", "AUTH", "CREDENTIAL"}
    for k, v in os.environ.items():
        if any(sk in k.upper() for sk in sensitive_keys) and v and len(v) >= 8:
            text = text.replace(v, f"[REDACTED_{k.upper()}]")
    # 2. Redact typical API key formats (OpenRouter, OpenAI, Anthropic, Gemini, etc.)
    text = re.sub(r"sk-or-v1-[a-f0-9]{32,}", "[REDACTED_API_KEY]", text)
    text = re.sub(r"sk-[a-zA-Z0-9_-]{20,}", "[REDACTED_API_KEY]", text)
    text = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", text)
    return text


def _matches_path_scope(rel_posix: str, scope: str) -> bool:
    """Match exact file name or directory boundary prefix, preventing PLAN.md matching PLAN.md.bak."""
    clean = scope.lstrip("/")
    if rel_posix == clean:
        return True
    if clean.endswith("/") and rel_posix.startswith(clean):
        return True
    if rel_posix.startswith(clean + "/"):
        return True
    return False


def is_sensitive_file(path: Path) -> bool:
    """Detect whether a path references sensitive credentials, tokens, or secret configs."""
    name = path.name.lower()
    if name == ".env" or name.startswith(".env.") or name.startswith(".env"):
        return True
    sensitive_substrings = (
        "id_rsa",
        "id_ed25519",
        "id_dsa",
        "id_ecdsa",
        "credentials.json",
        ".secret",
        ".token",
    )
    if any(s in name for s in sensitive_substrings):
        return True
    if path.suffix.lower() in (".pem", ".key", ".pfx", ".p12"):
        return True
    return False


def execute_file_action(
    action: WorkspaceFileAction,
    conversation=None,
    base_dir: Optional[Path] = None,
    read_only: bool = False,
    allowed_write_prefixes: Optional[Sequence[str]] = None,
    blocked_write_prefixes: Optional[Sequence[str]] = None,
) -> WorkspaceFileObservation:
    """Safely execute file operation within workspace."""
    workspace_root = (
        base_dir
        or Path(os.environ.get("WORKSPACE_PATH", str(DEFAULT_WORKSPACE_DIR))).resolve()
    )
    workspace_root.mkdir(parents=True, exist_ok=True)

    # Normalize path: strip leading virtual container /workspace or workspace prefixes
    clean_path = re.sub(r"^[/\\]*(workspace[/\\]+)?", "", action.path.strip())
    raw_path = Path(clean_path)
    if raw_path.is_absolute():
        target_path = raw_path.resolve()
    else:
        target_path = (workspace_root / clean_path.lstrip("/\\")).resolve()

    # Sandboxing check
    try:
        target_path.relative_to(workspace_root)
    except ValueError:
        err_msg = f"Access denied: path '{action.path}' escapes workspace directory '{workspace_root}'."
        return WorkspaceFileObservation(
            content=[TextContent(text=err_msg)],
            is_error=True,
            success=False,
            message=err_msg,
        )

    # Secret Protection: Block read/write/edit/delete on sensitive credential files
    if is_sensitive_file(target_path):
        channel = getattr(conversation, "human_channel", None) or get_active_channel()
        rel_posix = target_path.relative_to(workspace_root).as_posix()
        is_pre_authorized = channel.is_path_approved(rel_posix) if channel else False
        if not is_pre_authorized:
            granted = False
            feedback = ""
            if channel:
                granted, feedback = channel.request_permission(
                    role="agent",
                    action_type="sensitive_file_access",
                    target=rel_posix,
                    reason=f"Accessing sensitive credential/environment file '{target_path.name}'.",
                )
            if not granted:
                err_msg = f"Security restriction: Access to sensitive file '{action.path}' is blocked. {feedback}".strip()
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )

    # RBAC Permission Enforcement
    if action.operation in ("write", "edit", "delete", "append"):
        rel_posix = target_path.relative_to(workspace_root).as_posix()
        violation_reason = None

        channel = getattr(conversation, "human_channel", None) or get_active_channel()
        is_pre_authorized = channel.is_path_approved(rel_posix) if channel else False

        if not is_pre_authorized:
            if read_only:
                violation_reason = (
                    "Agent role has strictly read-only access to workspace files."
                )
            elif allowed_write_prefixes and not any(
                _matches_path_scope(rel_posix, p) for p in allowed_write_prefixes
            ):
                violation_reason = f"Writing to '{action.path}' is outside permitted role scope {list(allowed_write_prefixes)}."
            elif blocked_write_prefixes and any(
                _matches_path_scope(rel_posix, p) for p in blocked_write_prefixes
            ):
                violation_reason = (
                    f"Modifying '{action.path}' is restricted for this agent role."
                )

        if violation_reason:
            granted = False
            feedback = ""
            if channel:
                granted, feedback = channel.request_permission(
                    role="agent",
                    action_type="file_write",
                    target=rel_posix,
                    reason=violation_reason,
                )
            if not granted:
                err_msg = f"Permission denied: {violation_reason} {feedback}".strip()
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )

    try:
        if action.operation == "read":
            if target_path.name.startswith(".env"):
                err_msg = f"Security restriction: reading '{action.path}' is blocked."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )
            if not target_path.exists():
                err_msg = f"File '{action.path}' does not exist."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )
            lines = target_path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines(keepends=True)
            total_lines = len(lines)

            # 1. Line Constraint: window max 250 LOC
            if action.start_line is not None or action.end_line is not None:
                start = max(
                    0,
                    (action.start_line - 1)
                    if action.start_line and action.start_line > 0
                    else 0,
                )
                req_end = (
                    action.end_line
                    if action.end_line and action.end_line <= total_lines
                    else total_lines
                )
                if (req_end - start) > MAX_READ_LINES:
                    end = start + MAX_READ_LINES
                    clamped_by_lines = True
                else:
                    end = req_end
                    clamped_by_lines = False
            else:
                start = 0
                if total_lines > MAX_READ_LINES:
                    end = MAX_READ_LINES
                    clamped_by_lines = True
                else:
                    end = total_lines
                    clamped_by_lines = False

            # 2. Token / Byte Constraint: window max 12,000 chars (~3,000 tokens)
            sliced_text = "".join(lines[start:end])
            clamped_by_chars = False
            if len(sliced_text) > MAX_READ_CHARS:
                cut_point = sliced_text.rfind("\n", 0, MAX_READ_CHARS)
                if cut_point < MAX_READ_CHARS // 2:
                    cut_point = MAX_READ_CHARS
                sliced_text = sliced_text[:cut_point]
                clamped_by_chars = True

            # 3. Dynamic Governance Guidance
            if clamped_by_chars:
                notice = (
                    f"\n\n[Governance Notice: Read clamped by character budget ({MAX_READ_CHARS} chars max). "
                    f"Showing partial lines {start + 1}-{end} of {total_lines}. Specify start_line with next unread section to paginate.]"
                )
            elif clamped_by_lines:
                notice = (
                    f"\n\n[Governance Notice: Showing lines {start + 1}-{end} of {total_lines} total lines in '{action.path}'. "
                    f"To read further, specify start_line={end + 1}, end_line={min(total_lines, end + MAX_READ_LINES)} in workspace_file]"
                )
            else:
                notice = ""

            selected_content = sanitize_output_secrets(sliced_text) + notice
            return WorkspaceFileObservation(
                content=[TextContent(text=selected_content)],
                is_error=False,
                success=True,
                message=f"Read lines {start + 1}-{end} of {total_lines} from '{action.path}'.",
                file_content=selected_content,
            )

        elif action.operation == "symbol" or (
            action.operation == "read" and getattr(action, "symbol", None)
        ):
            if not target_path.exists():
                err_msg = f"File '{action.path}' does not exist."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )
            sym = (getattr(action, "symbol", None) or "").strip()
            if not sym:
                err_msg = "Missing 'symbol' parameter required for operation='symbol'."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )

            extracted, start_ln, end_ln, err = extract_ast_symbol(target_path, sym)
            if err:
                return WorkspaceFileObservation(
                    content=[TextContent(text=err)],
                    is_error=True,
                    success=False,
                    message=err,
                )

            annotated_lines = []
            for idx, line in enumerate(
                (extracted or "").splitlines(), start=start_ln or 1
            ):
                annotated_lines.append(f"{idx:4d}: {line}")
            annotated_content = "\n".join(annotated_lines)

            # Enforce governance character budget clamping (~3,000 tokens ceiling)
            if len(annotated_content) > MAX_READ_CHARS:
                cut_point = annotated_content.rfind("\n", 0, MAX_READ_CHARS)
                if cut_point < MAX_READ_CHARS // 2:
                    cut_point = MAX_READ_CHARS
                annotated_content = (
                    annotated_content[:cut_point]
                    + f"\n\n[Governance Notice: Symbol output clamped at {MAX_READ_CHARS} chars to protect token budget.]"
                )

            selected_content = sanitize_output_secrets(annotated_content)

            return WorkspaceFileObservation(
                content=[TextContent(text=selected_content)],
                is_error=False,
                success=True,
                message=f"Extracted symbol '{sym}' (lines {start_ln}-{end_ln}) from '{action.path}'.",
                file_content=selected_content,
            )

        elif action.operation == "write":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            content_to_write = action.content or ""
            if target_path.suffix == ".py":
                from orchestrator.sentinel.ast_guard import ASTGuard

                guard = ASTGuard()
                is_safe, err_msg, healed = guard.intercept_ast(
                    target_path, content_to_write
                )
                if not is_safe:
                    return WorkspaceFileObservation(
                        content=[
                            TextContent(text=f"AST Integrity Violation: {err_msg}")
                        ],
                        is_error=True,
                        success=False,
                        message=f"AST Integrity Violation: {err_msg}",
                    )
                if healed:
                    content_to_write = healed
            target_path.write_text(content_to_write, encoding="utf-8")
            msg = f"File '{action.path}' written successfully ({len(content_to_write)} chars)."
            return WorkspaceFileObservation(
                content=[TextContent(text=msg)],
                is_error=False,
                success=True,
                message=msg,
            )

        elif action.operation == "append":
            if not target_path.exists():
                err_msg = (
                    f"Append guard: Cannot append to non-existent file '{action.path}'. "
                    "Use operation='write' to initialize the file first."
                )
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )

            key = str(target_path.resolve())
            current_appends = _APPEND_COUNTS.get(key, 0)
            if current_appends >= MAX_APPENDS_PER_FILE:
                err_msg = (
                    f"Append guard: Maximum append limit ({MAX_APPENDS_PER_FILE} appends) reached for '{action.path}'. "
                    "Use operation='edit' with target_text or overwrite with 'write'."
                )
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )

            _APPEND_COUNTS[key] = current_appends + 1
            content_to_append = action.content or ""
            with target_path.open("a", encoding="utf-8") as f:
                f.write(content_to_append)
            msg = (
                f"File '{action.path}' appended successfully "
                f"({len(content_to_append)} chars added, append {current_appends + 1}/{MAX_APPENDS_PER_FILE})."
            )
            return WorkspaceFileObservation(
                content=[TextContent(text=msg)],
                is_error=False,
                success=True,
                message=msg,
            )

        elif action.operation == "edit":
            if not target_path.exists():
                err_msg = f"File '{action.path}' not found for editing."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )
            existing = target_path.read_text(encoding="utf-8", errors="replace")
            if not action.target_text:
                err_msg = "Missing 'target_text' required for editing."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )

            target = action.target_text
            replacement = action.replacement_text or ""
            new_content = None

            if target in existing:
                new_content = existing.replace(target, replacement, 1)
            elif target.replace("\r\n", "\n") in existing.replace("\r\n", "\n"):
                normalized_existing = existing.replace("\r\n", "\n")
                normalized_target = target.replace("\r\n", "\n")
                new_content = normalized_existing.replace(
                    normalized_target, replacement, 1
                )
            else:
                existing_lines = existing.splitlines(keepends=True)
                target_lines = [tl.strip() for tl in target.splitlines() if tl.strip()]
                match_start = -1
                for i in range(len(existing_lines)):
                    window = [
                        el.strip()
                        for el in existing_lines[i : i + len(target_lines)]
                        if el.strip()
                    ]
                    if window == target_lines:
                        match_start = i
                        break
                if match_start != -1:
                    first_line = existing_lines[match_start]
                    base_indent = len(first_line) - len(first_line.lstrip())
                    indent_str = " " * base_indent

                    repl_lines = replacement.splitlines(keepends=True)
                    adjusted_repl = []
                    for rline in repl_lines:
                        if rline.strip() and not rline.startswith(" "):
                            adjusted_repl.append(f"{indent_str}{rline}")
                        else:
                            adjusted_repl.append(rline)

                    if adjusted_repl and not adjusted_repl[-1].endswith("\n"):
                        adjusted_repl[-1] = adjusted_repl[-1] + "\n"

                    pre = "".join(existing_lines[:match_start])
                    post = "".join(existing_lines[match_start + len(target_lines) :])
                    new_content = pre + "".join(adjusted_repl) + post

            if new_content is None:
                try:
                    from orchestrator.sentinel import SelfHealingEngine

                    applied, fuzzy_content, note = SelfHealingEngine().fix_fuzzy_edit(
                        existing, target, replacement
                    )
                    if applied:
                        new_content = fuzzy_content
                except Exception:
                    pass

            if new_content is None:
                err_msg = f"Target text was not found in '{action.path}'."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )

            if target_path.suffix == ".py":
                from orchestrator.sentinel.ast_guard import ASTGuard

                guard = ASTGuard()
                is_safe, err_msg, healed = guard.intercept_ast(target_path, new_content)
                if not is_safe:
                    return WorkspaceFileObservation(
                        content=[
                            TextContent(text=f"AST Integrity Violation: {err_msg}")
                        ],
                        is_error=True,
                        success=False,
                        message=f"AST Integrity Violation: {err_msg}",
                    )
                if healed:
                    new_content = healed

            target_path.write_text(new_content, encoding="utf-8")
            msg = f"Successfully edited '{action.path}'."
            return WorkspaceFileObservation(
                content=[TextContent(text=msg)],
                is_error=False,
                success=True,
                message=msg,
            )

        elif action.operation == "list":
            if not target_path.exists():
                err_msg = f"Directory '{action.path}' does not exist."
                return WorkspaceFileObservation(
                    content=[TextContent(text=err_msg)],
                    is_error=True,
                    success=False,
                    message=err_msg,
                )
            search_dir = target_path if target_path.is_dir() else target_path.parent
            ignored_dirs = {
                ".git",
                ".venv",
                "venv",
                "__pycache__",
                ".pytest_cache",
                ".ruff_cache",
                "node_modules",
                "dist",
                "build",
                ".idea",
                ".vscode",
                "diagnostics",
                ".agents",
            }
            file_list = []
            for root, dirs, files in os.walk(search_dir):
                dirs[:] = [
                    d for d in dirs if d not in ignored_dirs and not d.startswith(".")
                ]
                for f in files:
                    full_p = Path(root) / f
                    try:
                        file_list.append(str(full_p.relative_to(workspace_root)))
                    except ValueError:
                        file_list.append(str(full_p))
                    if len(file_list) >= 100:
                        file_list.append("... [Additional files omitted for brevity]")
                        break
                if len(file_list) >= 101:
                    break
            files_str = (
                "\n".join(file_list) if file_list else "(No files found in directory)"
            )
            msg = f"Found {len(file_list)} files:\n{files_str}"
            return WorkspaceFileObservation(
                content=[TextContent(text=msg)],
                is_error=False,
                success=True,
                message=msg,
                files=[f for f in file_list if not f.startswith("...")],
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
                    message=msg,
                )
            err_msg = f"File '{action.path}' does not exist."
            return WorkspaceFileObservation(
                content=[TextContent(text=err_msg)],
                is_error=True,
                success=False,
                message=err_msg,
            )

        err_msg = f"Unknown operation: {action.operation}"
        return WorkspaceFileObservation(
            content=[TextContent(text=err_msg)],
            is_error=True,
            success=False,
            message=err_msg,
        )

    except Exception as e:
        err_msg = f"Error performing '{action.operation}' on '{action.path}': {str(e)}"
        return WorkspaceFileObservation(
            content=[TextContent(text=err_msg)],
            is_error=True,
            success=False,
            message=err_msg,
        )


class WorkspaceFileExecutor(
    ToolExecutor[WorkspaceFileAction, WorkspaceFileObservation]
):
    def __init__(
        self,
        workspace_path: Optional[Path] = None,
        read_only: bool = False,
        allowed_write_prefixes: Optional[Sequence[str]] = None,
        blocked_write_prefixes: Optional[Sequence[str]] = None,
    ):
        self.workspace_path = workspace_path
        self.read_only = read_only
        self.allowed_write_prefixes = allowed_write_prefixes
        self.blocked_write_prefixes = blocked_write_prefixes

    def __call__(
        self,
        action: WorkspaceFileAction,
        conversation: Any = None,
    ) -> WorkspaceFileObservation:
        return execute_file_action(
            action,
            conversation,
            self.workspace_path,
            read_only=self.read_only,
            allowed_write_prefixes=self.allowed_write_prefixes,
            blocked_write_prefixes=self.blocked_write_prefixes,
        )


class WorkspaceFileTool(ToolDefinition[WorkspaceFileAction, WorkspaceFileObservation]):
    """Tool for reading, writing, editing, appending, listing, and deleting files inside the project workspace."""

    @classmethod
    def create(
        cls,
        conv_state: Optional[Any] = None,
        workspace_path: Optional[str] = None,
        read_only: bool = False,
        allowed_write_prefixes: Optional[Sequence[str]] = None,
        blocked_write_prefixes: Optional[Sequence[str]] = None,
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
                description="Read, write, edit, append, list, delete, or inspect specific functions/classes (operation='symbol', symbol='<name>') inside the project workspace.",
                action_type=WorkspaceFileAction,
                observation_type=WorkspaceFileObservation,
                executor=WorkspaceFileExecutor(
                    target_path,
                    read_only=read_only,
                    allowed_write_prefixes=allowed_write_prefixes,
                    blocked_write_prefixes=blocked_write_prefixes,
                ),
            )
        ]


# ==========================================
# 2. Workspace Terminal Tool
# ==========================================


class WorkspaceTerminalAction(Action):
    """Terminal execution action within the workspace environment."""

    model_config = ConfigDict(extra="ignore")
    command: str
    timeout_seconds: int = 30


class WorkspaceTerminalObservation(Observation):
    """Observation resulting from terminal command execution."""

    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


DEFAULT_ALLOWED_COMMANDS = {
    "pytest",
    "python",
    "py",
    "pip",
    "uv",
    "git",
    "ruff",
    "mypy",
    "graft",
    "ls",
    "dir",
    "cat",
    "type",
    "pwd",
    "tree",
    "find",
    "findstr",
    "del",
    "copy",
    "move",
    "cls",
    "grep",
    "rm",
    "cp",
    "mv",
    "clear",
    "select-string",
    "get-content",
    "get-childitem",
    "new-item",
    "remove-item",
    "get-command",
}


def get_allowed_command_binaries() -> set[str]:
    """Retrieve allowed command binaries from environment or defaults."""
    env_val = os.environ.get("ALLOWED_COMMANDS")
    if env_val:
        return {c.strip().lower() for c in env_val.split(",") if c.strip()}
    return set(DEFAULT_ALLOWED_COMMANDS)


DANGEROUS_CHAINING_TOKENS = {";", "&&", "||", "|", "&"}


def split_and_validate_command(command: str) -> tuple[bool, list[str], str]:
    """Parse command into argv tokens, verify allowlist, and block chaining injection."""
    clean = (command or "").strip()
    if not clean:
        return False, [], "Empty command string."
    try:
        tokens = shlex.split(clean, posix=True)
    except ValueError as e:
        return False, [], f"Command parse syntax error: {e}"

    if not tokens:
        return False, [], "No executable tokens found."

    # Block shell chaining injection tokens outside quoted arguments
    for tok in tokens:
        if tok in DANGEROUS_CHAINING_TOKENS:
            return (
                False,
                tokens,
                f"Security violation: Chained commands or pipeline operator '{tok}' are not permitted.",
            )

    base_cmd = Path(tokens[0].strip("'\"")).name.lower()
    if base_cmd.endswith(".exe"):
        base_cmd = base_cmd[:-4]

    if base_cmd not in get_allowed_command_binaries():
        return (
            False,
            tokens,
            f"Command binary '{base_cmd}' is not in permitted whitelist.",
        )

    return True, tokens, ""


def is_command_allowed(command: str) -> bool:
    """Validate that the command base binary is in the allowlist and contains no chaining."""
    allowed, _, _ = split_and_validate_command(command)
    return allowed


def execute_terminal_action(
    action: WorkspaceTerminalAction, conversation=None, base_dir: Optional[Path] = None
) -> WorkspaceTerminalObservation:
    """Execute terminal command safely inside workspace directory using parameterized execution."""
    workspace_root = (
        base_dir
        or Path(os.environ.get("WORKSPACE_PATH", str(DEFAULT_WORKSPACE_DIR))).resolve()
    )
    workspace_root.mkdir(parents=True, exist_ok=True)

    cmd_to_exec = action.command
    # Sentinel translation hook for UNIX commands on Windows
    try:
        from orchestrator.sentinel import TerminalCommandTranslator

        _, translated, _ = TerminalCommandTranslator.intercept_and_translate(
            cmd_to_exec
        )
        if translated:
            cmd_to_exec = translated
    except Exception:
        pass

    channel = getattr(conversation, "human_channel", None) or get_active_channel()
    is_pre_authorized = channel.is_command_approved(cmd_to_exec) if channel else False

    valid, cmd_tokens, reason = split_and_validate_command(cmd_to_exec)
    if not valid and not is_pre_authorized:
        granted = False
        feedback = ""
        allowed_list = sorted(get_allowed_command_binaries())
        if channel:
            granted, feedback = channel.request_permission(
                role="agent",
                action_type="terminal_command",
                target=action.command,
                reason=reason
                or f"Command binary is outside permitted whitelist {allowed_list}",
            )
        if not granted:
            err_msg = (
                f"Security policy violation: {reason or 'Command binary is not permitted.'} {feedback} "
                f"Allowed tools: {allowed_list}"
            ).strip()
            return WorkspaceTerminalObservation(
                content=[TextContent(text=err_msg)],
                is_error=True,
                exit_code=126,
                stdout="",
                stderr=err_msg,
                timed_out=False,
            )
        if not cmd_tokens:
            try:
                cmd_tokens = shlex.split(action.command, posix=True)
            except Exception:
                cmd_tokens = action.command.split()

    # Sanitize env to prevent leaking sensitive API keys / secrets to commands or child processes
    sensitive_keywords = {"KEY", "SECRET", "TOKEN", "PASSWORD", "AUTH", "CREDENTIAL"}
    env = {}
    for k, v in os.environ.items():
        k_upper = k.upper()
        if any(keyword in k_upper for keyword in sensitive_keywords):
            continue
        env[k] = v

    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    # Prepend workspace .venv bin/Scripts to PATH if present to ensure project tools and packages are used
    venv_bin = (
        workspace_root
        / ".venv"
        / ("Scripts" if (sys.platform == "win32" or os.name == "nt") else "bin")
    )
    if venv_bin.exists():
        existing_path = env.get("PATH", "")
        env["PATH"] = (
            f"{str(venv_bin)}{os.pathsep}{existing_path}"
            if existing_path
            else str(venv_bin)
        )
        env["VIRTUAL_ENV"] = str(workspace_root / ".venv")

    # Inject workspace_root into PYTHONPATH so project packages are always importable
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{str(workspace_root)}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(workspace_root)
    )

    # Command translation for Windows builtins or direct executable resolution
    base_name = Path(cmd_tokens[0]).name.lower()
    if base_name.endswith(".exe"):
        base_name = base_name[:-4]

    is_windows = sys.platform == "win32" or os.name == "nt"

    # Map unix shell aliases to windows builtins if on windows
    if is_windows:
        if base_name == "pwd":
            cmd_tokens = ["cd"]
            base_name = "cd"
        elif base_name == "ls":
            cmd_tokens = ["dir", *cmd_tokens[1:]]
            base_name = "dir"
        elif base_name == "cat":
            cmd_tokens = ["type", *cmd_tokens[1:]]
            base_name = "type"
        elif base_name == "grep":
            cmd_tokens = ["findstr", *cmd_tokens[1:]]
            base_name = "findstr"
        elif base_name == "rm":
            cmd_tokens = ["del", *cmd_tokens[1:]]
            base_name = "del"
        elif base_name == "cp":
            cmd_tokens = ["copy", *cmd_tokens[1:]]
            base_name = "copy"
        elif base_name == "mv":
            cmd_tokens = ["move", *cmd_tokens[1:]]
            base_name = "move"
        elif base_name == "clear":
            cmd_tokens = ["cls"]
            base_name = "cls"
        elif base_name in ("pytest", "ruff", "mypy"):
            cmd_tokens = ["python", "-m", base_name, *cmd_tokens[1:]]
            base_name = "python"
        elif base_name == "uv" and len(cmd_tokens) >= 3 and cmd_tokens[1] == "run":
            if cmd_tokens[2] in ("pytest", "ruff", "mypy"):
                cmd_tokens = [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    cmd_tokens[2],
                    *cmd_tokens[3:],
                ]

    shell_builtins = {
        "dir",
        "type",
        "cd",
        "echo",
        "where",
        "findstr",
        "del",
        "copy",
        "move",
        "cls",
    }
    powershell_cmdlets = {
        "select-string",
        "get-content",
        "get-childitem",
        "new-item",
        "remove-item",
        "get-command",
    }
    is_windows = sys.platform == "win32" or os.name == "nt"
    if is_windows and base_name in powershell_cmdlets:
        exec_args = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            cmd_to_exec,
        ]
    elif is_windows and base_name == "graft" and not shutil.which("graft", path=env.get("PATH")) and shutil.which("graft.ps1", path=env.get("PATH")):
        exec_args = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            cmd_to_exec,
        ]
    elif is_windows and base_name in shell_builtins:
        exec_args = ["cmd.exe", "/c", *cmd_tokens]
    else:
        resolved_bin = (
            shutil.which(cmd_tokens[0], path=env.get("PATH")) or cmd_tokens[0]
        )
        exec_args = [resolved_bin, *cmd_tokens[1:]]

    try:
        proc = subprocess.run(
            exec_args,
            shell=False,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=action.timeout_seconds,
            env=env,
        )
        stdout_text = sanitize_output_secrets(proc.stdout or "")
        stderr_text = sanitize_output_secrets(proc.stderr or "")

        # Truncate excessive terminal output to prevent LLM context explosion (max 4000 chars / ~60 lines)
        if len(stdout_text) > 4000:
            lines = stdout_text.splitlines()
            if len(lines) > 60:
                stdout_text = (
                    "\n".join(lines[:30])
                    + f"\n... [{len(lines) - 50} lines omitted to conserve token context] ...\n"
                    + "\n".join(lines[-20:])
                )
            else:
                stdout_text = (
                    stdout_text[:4000]
                    + "\n... [Output truncated to conserve token context] ..."
                )

        output_text = f"Exit code: {proc.returncode}\nStdout:\n{stdout_text}\nStderr:\n{stderr_text}"
        return WorkspaceTerminalObservation(
            content=[TextContent(text=output_text)],
            is_error=(proc.returncode != 0),
            exit_code=proc.returncode,
            stdout=stdout_text,
            stderr=stderr_text,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as te:
        timeout_msg = "Command timed out after specified seconds."
        stdout_str = sanitize_output_secrets(
            te.stdout
            if isinstance(te.stdout, str)
            else (te.stdout.decode("utf-8", errors="replace") if te.stdout else "")
        )
        stderr_str = sanitize_output_secrets(
            te.stderr
            if isinstance(te.stderr, str)
            else (
                te.stderr.decode("utf-8", errors="replace")
                if te.stderr
                else timeout_msg
            )
        )
        return WorkspaceTerminalObservation(
            content=[TextContent(text=timeout_msg)],
            is_error=True,
            exit_code=-1,
            stdout=stdout_str,
            stderr=stderr_str,
            timed_out=True,
        )
    except Exception as e:
        err_msg = f"Execution error: {str(e)}"
        return WorkspaceTerminalObservation(
            content=[TextContent(text=err_msg)],
            is_error=True,
            exit_code=-1,
            stdout="",
            stderr=err_msg,
            timed_out=False,
        )


class WorkspaceTerminalExecutor(
    ToolExecutor[WorkspaceTerminalAction, WorkspaceTerminalObservation]
):
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path

    def __call__(
        self,
        action: WorkspaceTerminalAction,
        conversation: Any = None,
    ) -> WorkspaceTerminalObservation:
        return execute_terminal_action(action, conversation, self.workspace_path)


class WorkspaceTerminalTool(
    ToolDefinition[WorkspaceTerminalAction, WorkspaceTerminalObservation]
):
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


# Register tools in OpenHands global tool registry
register_tool("WorkspaceFileTool", WorkspaceFileTool)
register_tool("WorkspaceTerminalTool", WorkspaceTerminalTool)


# ==========================================
# 3. Dynamic Permission Escalation Tool
# ==========================================


class RequestPermissionAction(Action):
    """Explicitly request approval from the human developer for a privileged or restricted task."""

    model_config = ConfigDict(extra="ignore")
    action_type: Literal[
        "terminal_command", "file_write", "dependency_install", "architectural_change"
    ]
    target: str = Field(
        description="Command, file path, or package name requiring authorization"
    )
    justification: str = Field(
        description="Clear technical rationale explaining why this operation is essential"
    )


class RequestPermissionObservation(Observation):
    """Result of human developer permission review."""

    granted: bool = False
    message: str = ""


class RequestPermissionExecutor(
    ToolExecutor[RequestPermissionAction, RequestPermissionObservation]
):
    def __call__(
        self,
        action: RequestPermissionAction,
        conversation: Any = None,
    ) -> RequestPermissionObservation:
        channel = getattr(conversation, "human_channel", None) or get_active_channel()
        if not channel:
            msg = "Permission request failed: No interactive human communication channel active."
            return RequestPermissionObservation(
                content=[TextContent(text=msg)],
                is_error=True,
                granted=False,
                message=msg,
            )

        granted, feedback = channel.request_permission(
            role="agent",
            action_type="terminal_command"
            if action.action_type in ("terminal_command", "dependency_install")
            else "file_write",
            target=action.target,
            reason=f"Agent request: {action.justification}",
        )
        if granted:
            msg = f"Permission GRANTED by developer for '{action.target}'. You may proceed with the operation."
            return RequestPermissionObservation(
                content=[TextContent(text=msg)],
                is_error=False,
                granted=True,
                message=msg,
            )
        else:
            msg = f"Permission DENIED by developer for '{action.target}'. Feedback: {feedback}"
            return RequestPermissionObservation(
                content=[TextContent(text=msg)],
                is_error=True,
                granted=False,
                message=msg,
            )


class RequestPermissionTool(
    ToolDefinition[RequestPermissionAction, RequestPermissionObservation]
):
    """Tool enabling agents to proactively ask developer permission before running privileged actions."""

    @classmethod
    def create(
        cls, conv_state: Optional[Any] = None, **params
    ) -> Sequence["RequestPermissionTool"]:
        return [
            cls(
                description="Request human developer approval before executing restricted actions (e.g. installing packages, modifying protected files).",
                action_type=RequestPermissionAction,
                observation_type=RequestPermissionObservation,
                executor=RequestPermissionExecutor(),
            )
        ]


register_tool("RequestPermissionTool", RequestPermissionTool)


# Factory functions to build tool specifications for Agents
def create_workspace_file_tool(
    workspace_path: Optional[Path] = None,
    read_only: bool = False,
    allowed_write_prefixes: Optional[Sequence[str]] = None,
    blocked_write_prefixes: Optional[Sequence[str]] = None,
) -> Tool:
    params: dict[str, Any] = {
        "read_only": read_only,
    }
    if workspace_path:
        params["workspace_path"] = str(Path(workspace_path).resolve())
    if allowed_write_prefixes:
        params["allowed_write_prefixes"] = list(allowed_write_prefixes)
    if blocked_write_prefixes:
        params["blocked_write_prefixes"] = list(blocked_write_prefixes)
    return Tool(name="WorkspaceFileTool", params=params)


def create_workspace_terminal_tool(workspace_path: Optional[Path] = None) -> Tool:
    params = {}
    if workspace_path:
        params["workspace_path"] = str(Path(workspace_path).resolve())
    return Tool(name="WorkspaceTerminalTool", params=params)


def create_request_permission_tool() -> Tool:
    """Tool for agents to request permission from the developer."""
    return Tool(name="RequestPermissionTool", params={})
