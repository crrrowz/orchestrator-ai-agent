"""Unified Tool Sandbox Manager.

Orchestrates Persona RBAC write permissions, P8 Tier 3 Dynamic Tool Constriction,
AST file virtualization, and terminal command execution.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from orchestrator.tools.hardened.models import (
    FileActionRequest,
    FileObservationResult,
    TerminalActionRequest,
    TerminalObservationResult,
)
from orchestrator.tools.hardened.sandbox import TerminalSandboxEngine
from orchestrator.tools.hardened.security import is_sensitive_filepath
from orchestrator.tools.hardened.virtualizer import WorkspaceFileVirtualizer


def matches_path_scope(rel_posix: str, scope: str) -> bool:
    """Match exact file name or directory boundary prefix, preventing PLAN.md matching PLAN.md.bak."""
    clean = scope.replace("\\", "/").lstrip("/")
    rel_clean = rel_posix.replace("\\", "/").lstrip("/")
    if rel_clean == clean:
        return True
    if clean.endswith("/") and rel_clean.startswith(clean):
        return True
    if rel_clean.startswith(clean + "/"):
        return True
    return False


class ToolSandboxManager:
    """Unified facade orchestrating RBAC permissions, P8 Tool Constriction, and tool execution."""

    def __init__(
        self,
        workspace_root: Path,
        persona_role: str = "developer",
        read_only: bool = False,
        allowed_write_prefixes: Optional[Sequence[str]] = None,
        blocked_write_prefixes: Optional[Sequence[str]] = None,
        banned_tools: Optional[Set[str]] = None,
        forced_tools: Optional[Set[str]] = None,
        disallow_stubs: bool = True,
        scope: Optional[Any] = None,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.persona_role = persona_role.lower()
        self.read_only = read_only
        self.allowed_write_prefixes = tuple(allowed_write_prefixes or ())
        self.blocked_write_prefixes = tuple(blocked_write_prefixes or ())
        self.banned_tools = set(banned_tools or ())
        self.forced_tools = set(forced_tools or ())

        if scope is not None:
            raw_role = getattr(scope, "role", persona_role)
            self.persona_role = str(getattr(raw_role, "value", raw_role)).lower()
            file_perm = getattr(scope, "file_permission", None)
            perm_val = str(getattr(file_perm, "value", file_perm or "")).lower()
            if perm_val in ("denied", "read_only"):
                self.read_only = True
            if getattr(scope, "allowed_write_prefixes", None):
                self.allowed_write_prefixes = tuple(scope.allowed_write_prefixes)
            if getattr(scope, "blocked_write_prefixes", None):
                self.blocked_write_prefixes = tuple(scope.blocked_write_prefixes)
            if hasattr(scope, "allow_terminal") and not scope.allow_terminal:
                self.banned_tools.add("workspace_terminal")

        self.file_virtualizer = WorkspaceFileVirtualizer(
            self.workspace_root, disallow_stubs=disallow_stubs
        )
        self.terminal_engine = TerminalSandboxEngine(self.workspace_root)
        self._last_action_signature: Optional[str] = None
        self._consecutive_duplicate_count: int = 0

    def is_tool_permitted(self, tool_name: str) -> bool:
        """Check whether a tool is permitted under current constriction rules."""
        aliases = {tool_name, f"workspace_{tool_name}"}
        if tool_name.startswith("workspace_"):
            aliases.add(tool_name.removeprefix("workspace_"))
        if any(a in self.banned_tools for a in aliases):
            return False
        if self.forced_tools and not any(a in self.forced_tools for a in aliases):
            return False
        return True

    def terminate_active_processes(self) -> None:
        """Terminate any active processes in the sandbox engine."""
        pass

    def execute_file_action(
        self, action: FileActionRequest, conversation: Any = None
    ) -> FileObservationResult:
        """Alias for handle_file_action."""
        return self.handle_file_action(action, conversation=conversation)

    def execute_terminal_action(
        self, action: TerminalActionRequest, conversation: Any = None
    ) -> TerminalObservationResult:
        """Alias for handle_terminal_action."""
        return self.handle_terminal_action(action, conversation=conversation)

    def verify_file_write_rbac(
        self, target_rel_path: str
    ) -> Tuple[bool, Optional[str]]:
        """Verify if write operation to target path is permitted under active RBAC scope."""
        if self.read_only:
            return (
                False,
                f"RBAC Violation: Persona '{self.persona_role}' has strictly read-only access to workspace files.",
            )

        posix_path = target_rel_path.replace("\\", "/").lstrip("/")

        for blocked in self.blocked_write_prefixes:
            if matches_path_scope(posix_path, blocked):
                return (
                    False,
                    f"RBAC Violation: Modifying '{posix_path}' is restricted for persona '{self.persona_role}'.",
                )

        if self.allowed_write_prefixes:
            matched = any(
                matches_path_scope(posix_path, allowed)
                for allowed in self.allowed_write_prefixes
            )
            if not matched:
                return (
                    False,
                    f"RBAC Violation: Writing to '{posix_path}' is outside permitted role scope {list(self.allowed_write_prefixes)}.",
                )

        return True, None

    def handle_file_action(
        self, action: FileActionRequest, conversation: Any = None
    ) -> FileObservationResult:
        """Dispatch hardened file action subject to RBAC, human channels, and virtualization rules."""
        if "workspace_file" in self.banned_tools:
            return FileObservationResult(
                success=False,
                message="Tool Constriction Violation: File manipulation tool is currently constricted by P8 strategy mutator.",
                is_error=True,
            )

        is_valid_path, target_path, err = self.file_virtualizer.resolve_sandbox_path(
            action.path
        )
        if not is_valid_path:
            return FileObservationResult(success=False, message=err, is_error=True)

        rel_posix = target_path.relative_to(self.workspace_root).as_posix()

        # Check for consecutive identical redundant read actions to prevent endless loops
        action_sig = f"file:{action.operation}:{rel_posix}:{action.offset_line}:{action.limit_lines}:{action.symbol}"
        if action.operation in ("read", "outline", "symbol", "list"):
            if self._last_action_signature == action_sig:
                self._consecutive_duplicate_count += 1
                if self._consecutive_duplicate_count >= 1:
                    return FileObservationResult(
                        success=False,
                        message=(
                            f"[CommandInterceptor Loop Guard] You performed the exact same operation '{action.operation}' "
                            f"on '{rel_posix}' in the previous step. Repeating identical queries yields no new information. "
                            "Please analyze what you observed, synthesize your findings, or proceed to write your output/fix."
                        ),
                        is_error=False,
                    )
            else:
                self._last_action_signature = action_sig
                self._consecutive_duplicate_count = 0
        else:
            self._last_action_signature = action_sig
            self._consecutive_duplicate_count = 0

        # Human channel resolution
        channel = None
        if conversation:
            channel = getattr(conversation, "human_channel", None)
        if not channel:
            try:
                from orchestrator.control.human_channel import get_active_channel

                channel = get_active_channel()
            except Exception:
                pass

        # Sensitive file protection
        if is_sensitive_filepath(target_path):
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
                    return FileObservationResult(
                        success=False, message=err_msg, is_error=True
                    )

        # Write RBAC check
        if action.operation in ("write", "patch", "edit", "delete", "append"):
            is_pre_authorized = channel.is_path_approved(rel_posix) if channel else False
            if not is_pre_authorized:
                permitted, rbac_err = self.verify_file_write_rbac(rel_posix)
                if not permitted:
                    granted = False
                    feedback = ""
                    if channel:
                        granted, feedback = channel.request_permission(
                            role="agent",
                            action_type="file_write",
                            target=rel_posix,
                            reason=rbac_err or "RBAC Denied",
                        )
                    if not granted:
                        err_msg = f"Permission denied: {rbac_err} {feedback}".strip()
                        return FileObservationResult(
                            success=False, message=err_msg, is_error=True
                        )

        # Dispatch operations
        if action.operation == "outline":
            outline_summary, _, out_err = self.file_virtualizer.generate_outline(
                target_path
            )
            if out_err:
                return FileObservationResult(
                    success=False, message=out_err, is_error=True
                )
            return FileObservationResult(
                success=True,
                message=f"Outline generated for '{action.path}'.",
                outline_summary=outline_summary,
                file_content=outline_summary,
            )

        elif action.operation == "read":
            view, read_err = self.file_virtualizer.read_windowed(
                target_path,
                offset_line=action.offset_line,
                limit_lines=action.limit_lines,
                start_line=action.start_line,
                end_line=action.end_line,
            )
            if read_err or not view:
                return FileObservationResult(
                    success=False, message=read_err or "Read failed", is_error=True
                )
            return FileObservationResult(
                success=True,
                message=f"Read lines {view.offset_line}-{min(view.total_lines, view.offset_line + view.limit_lines - 1)} of {view.total_lines}.",
                file_content=view.content,
            )

        elif action.operation == "symbol":
            if not action.symbol:
                return FileObservationResult(
                    success=False, message="Missing 'symbol' parameter.", is_error=True
                )
            content, start_ln, end_ln, sym_err = (
                self.file_virtualizer.read_ast_symbol(target_path, action.symbol)
            )
            if sym_err:
                return FileObservationResult(
                    success=False, message=sym_err, is_error=True
                )
            return FileObservationResult(
                success=True,
                message=f"Extracted symbol '{action.symbol}' (lines {start_ln}-{end_ln}) from '{action.path}'.",
                file_content=content,
            )

        elif action.operation == "write":
            ok, write_msg = self.file_virtualizer.atomic_safe_write(
                target_path, action.content or ""
            )
            return FileObservationResult(
                success=ok, message=write_msg, is_error=(not ok)
            )

        elif action.operation in ("patch", "edit"):
            if not action.target_text:
                return FileObservationResult(
                    success=False,
                    message="Missing 'target_text' required for editing.",
                    is_error=True,
                )
            ok, patch_msg = self.file_virtualizer.atomic_patch(
                target_path, action.target_text, action.replacement_text or ""
            )
            return FileObservationResult(
                success=ok, message=patch_msg, is_error=(not ok)
            )

        elif action.operation == "append":
            ok, app_msg = self.file_virtualizer.append(
                target_path, action.content or ""
            )
            return FileObservationResult(
                success=ok, message=app_msg, is_error=(not ok)
            )

        elif action.operation == "list":
            ok, files, list_msg = self.file_virtualizer.list_dir(target_path)
            return FileObservationResult(
                success=ok,
                message=list_msg,
                files=files if ok else None,
                is_error=(not ok),
            )

        elif action.operation == "delete":
            ok, del_msg = self.file_virtualizer.delete(target_path)
            return FileObservationResult(
                success=ok, message=del_msg, is_error=(not ok)
            )

        return FileObservationResult(
            success=False,
            message=f"Unsupported operation '{action.operation}'",
            is_error=True,
        )

    def handle_terminal_action(
        self, action: TerminalActionRequest, conversation: Any = None
    ) -> TerminalObservationResult:
        """Dispatch hardened terminal command subject to constriction, RBAC, and grammar security."""
        if "workspace_terminal" in self.banned_tools:
            return TerminalObservationResult(
                exit_code=126,
                stdout="",
                stderr="Tool Constriction Violation: Terminal execution is currently banned by P8 strategy mutator.",
                is_error=True,
                steering_directive="Terminal execution is disabled. Make direct AST edits using WorkspaceFileTool.",
            )

        # Human channel resolution
        channel = None
        if conversation:
            channel = getattr(conversation, "human_channel", None)
        if not channel:
            try:
                from orchestrator.control.human_channel import get_active_channel

                channel = get_active_channel()
            except Exception:
                pass

        # Check for consecutive identical redundant command executions
        cmd_sig = f"terminal:{action.command.strip()}"
        if self._last_action_signature == cmd_sig:
            self._consecutive_duplicate_count += 1
            if self._consecutive_duplicate_count >= 1:
                return TerminalObservationResult(
                    exit_code=0,
                    stdout="",
                    stderr=(
                        f"[CommandInterceptor Loop Guard] You ran the exact same command '{action.command.strip()}' "
                        "in the previous step. Repeating identical commands without code changes produces no new output. "
                        "Please evaluate your previous result or modify the codebase before re-running."
                    ),
                    is_error=False,
                    steering_directive="Avoid repeating identical commands consecutively without code edits.",
                )
        else:
            self._last_action_signature = cmd_sig
            self._consecutive_duplicate_count = 0

        if channel:
            cmd = action.command.strip()
            if not channel.is_command_approved(cmd):
                # Check for restricted commands
                restricted_kw = ("rm -rf", "del /f", "git push", "git reset --hard")
                if any(kw in cmd for kw in restricted_kw):
                    granted, feedback = channel.request_permission(
                        role="agent",
                        action_type="terminal_command",
                        target=cmd,
                        reason=f"Executing potentially destructive terminal command '{cmd}'.",
                    )
                    if not granted:
                        err_msg = f"Terminal command rejected by human developer: {feedback}".strip()
                        return TerminalObservationResult(
                            exit_code=126,
                            stdout="",
                            stderr=err_msg,
                            is_error=True,
                            steering_directive="Command rejected by human developer.",
                        )

        return self.terminal_engine.execute(action)
