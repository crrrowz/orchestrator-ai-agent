"""OpenHands SDK v1.49.4 Runtime Bridge and Clean Boundary Seam.

Governs the execution boundary between ORAGAI Control Plane and OpenHands SDK v1.49.4.
Enforces Inversion of Control (IoC), bounded turn envelopes, official ToolDefinition
protocols, synchronous telemetry streaming, and deterministic exit status classification
with ZERO monkey-patching.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import os
import re
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Self

from openhands.sdk.agent import Agent
from openhands.sdk.conversation import (
    ConversationExecutionStatus,
    LocalConversation,
)
from openhands.sdk.event import (
    ActionEvent,
    AgentErrorEvent,
    Event,
    ObservationEvent,
)
from openhands.sdk.event.conversation_error import ConversationErrorEvent
from openhands.sdk.tool import (
    Action,
    Observation,
    ToolDefinition,
    ToolExecutor,
    register_tool,
)
from openhands.sdk.tool.schema import TextContent
from orchestrator.rendering.output import ConsoleOutput

if TYPE_CHECKING:
    from orchestrator.config import OrchestratorConfig
    from orchestrator.llm.manager import LLMManager
    from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB
    from orchestrator.tools.hardened.manager import ToolSandboxManager
    from orchestrator.ui.session_store import SessionLogStore
    from orchestrator.ui.visualizer import OrchestratorLiveVisualizer

logger = logging.getLogger(__name__)


# =====================================================================
# 1. Data Models & Exit Taxonomy
# =====================================================================


class AgentExitReason(str, enum.Enum):
    """Explicit, non-ambiguous exit status classification for an agent turn."""

    NATURAL_COMPLETION = "natural_completion"
    STEP_LIMIT_REACHED = "step_limit_reached"
    TOKEN_LIMIT_REACHED = "token_limit_reached"
    TOOL_REJECTION = "tool_rejection"
    AGENT_STUCK = "agent_stuck"
    ABORTED = "aborted"
    FATAL_ERROR = "fatal_error"


@dataclasses.dataclass(frozen=True)
class PromptView:
    """Compiled prompt and contextual tiers for an agent turn."""

    compiled_prompt: str
    tier0_system_prompt: str = ""
    tier1_handoff: Optional[str] = None
    tier2_digest: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class TurnEnvelope:
    """Dynamic turn bounds allocated by resource governor."""

    max_turns: int = 15
    token_ceiling: int = 50_000
    timeout_seconds: int = 300


@dataclasses.dataclass(frozen=True)
class AgentExecutionOutcome:
    """Immutable record of an ephemeral agent turn's execution."""

    role: str
    exit_reason: AgentExitReason
    completed_naturally: bool
    iterations_executed: int
    max_iterations_allocated: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    error_message: Optional[str]
    mutated_files: Tuple[str, ...]
    final_thought: Optional[str]
    handoff_payload: Optional[Any] = None
    progress_metrics: Optional[Any] = None
    governance_decision: Optional[Any] = None


# =====================================================================
# 2. Hardened Tool Action & Observation Models (P9 Integration)
# =====================================================================


class FileOperationType(str, enum.Enum):
    """Supported operations for workspace file tools."""

    READ = "read"
    WRITE = "write"
    PATCH = "patch"
    EDIT = "edit"
    SYMBOL = "symbol"
    OUTLINE = "outline"
    LIST = "list"
    DELETE = "delete"
    APPEND = "append"


class HardenedFileAction(Action):
    """Strict action model for AST-virtualized file operations with alias support."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    operation: FileOperationType = Field(
        default=FileOperationType.READ,
        description="The file operation: 'read', 'write', 'patch', 'edit', 'symbol', 'outline', 'list', 'delete', 'append'.",
    )
    path: str = Field(
        ...,
        alias="file_path",
        description="Workspace-relative path to the target file or directory.",
    )
    content: Optional[str] = Field(
        default=None,
        alias="text",
        description="Content for 'write' or 'append' operation.",
    )
    patch_find: Optional[str] = Field(
        default=None,
        alias="target_text",
        description="Exact substring to find for 'patch' or 'edit' operation.",
    )
    patch_replace: Optional[str] = Field(
        default=None,
        alias="replacement_text",
        description="Replacement substring for 'patch' or 'edit' operation.",
    )
    symbol_name: Optional[str] = Field(
        default=None,
        alias="symbol",
        description="Target function, class, or method name for 'symbol' extraction.",
    )
    offset_line: int = Field(
        default=1,
        ge=1,
        description="1-based starting line number for bounded 'read' window.",
    )
    limit_lines: int = Field(
        default=250,
        ge=1,
        le=1000,
        description="Maximum lines to return in 'read' window.",
    )
    start_line: Optional[int] = Field(
        default=None,
        description="Optional 1-based start line for 'read' window.",
    )
    end_line: Optional[int] = Field(
        default=None,
        description="Optional 1-based end line for 'read' window.",
    )


class HardenedFileObservation(Observation):
    """Sanitized, structured observation returned from file operations."""

    model_config = ConfigDict(extra="ignore")

    success: bool = True
    operation: str = "read"
    path: str = ""
    content: Optional[Any] = None
    total_lines: int = 0
    returned_lines: int = 0
    has_more: bool = False
    ast_valid: bool = True
    error_message: Optional[str] = None
    outline_summary: Optional[str] = None
    files: Optional[List[str]] = None

    @property
    def to_llm_content(self) -> Sequence[Any]:
        llm_content = []
        if self.is_error or not self.success:
            err = self.error_message or "An error occurred during file operation."
            llm_content.append(TextContent(text=f"[Error: {err}]\n"))
        text_parts = []
        if self.content:
            if isinstance(self.content, list):
                for item in self.content:
                    if hasattr(item, "text"):
                        text_parts.append(item.text)
                    elif isinstance(item, str):
                        text_parts.append(item)
            elif isinstance(self.content, str):
                text_parts.append(self.content)
        elif self.files:
            text_parts.append("\n".join(self.files))
        elif self.outline_summary:
            text_parts.append(self.outline_summary)
        elif self.success:
            text_parts.append(f"Successfully performed {self.operation} on {self.path}")
        main_text = "\n".join(text_parts) if text_parts else "Success"
        llm_content.append(TextContent(text=main_text))
        return llm_content

    @property
    def text(self) -> str:
        return "".join(item.text for item in self.to_llm_content if hasattr(item, "text"))


class HardenedTerminalAction(Action):
    """Strict action model for grammar-validated terminal commands."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    command: str = Field(
        ...,
        alias="cmd",
        description="The CLI command to execute within the workspace sandbox.",
    )
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=600,
        description="Execution timeout in seconds.",
    )


class HardenedTerminalObservation(Observation):
    """Sanitized, secret-masked observation returned from terminal commands."""

    model_config = ConfigDict(extra="ignore")

    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    security_violation: bool = False
    error_message: Optional[str] = None
    steering_directive: Optional[str] = None

    @property
    def to_llm_content(self) -> Sequence[Any]:
        llm_content = []
        if self.is_error or self.exit_code != 0:
            err = self.error_message or self.stderr or f"Command failed with exit code {self.exit_code}"
            llm_content.append(TextContent(text=f"[Exit Code {self.exit_code}]\n{err}\n"))
        text_parts = []
        if self.stdout:
            text_parts.append(self.stdout)
        if self.stderr and self.exit_code == 0:
            text_parts.append(self.stderr)
        if self.steering_directive:
            text_parts.append(f"\n[Directive: {self.steering_directive}]")
        main_text = "\n".join(text_parts) if text_parts else f"[Exit Code: {self.exit_code}]"
        llm_content.append(TextContent(text=main_text))
        return llm_content

    @property
    def text(self) -> str:
        return "".join(item.text for item in self.to_llm_content if hasattr(item, "text"))


# =====================================================================
# 3. Tool Executors & Tool Definitions
# =====================================================================


class HardenedFileExecutor(ToolExecutor[HardenedFileAction, HardenedFileObservation]):
    """ToolExecutor delegating file operations to P9 ToolSandboxManager."""

    def __init__(self, sandbox_manager: Any) -> None:
        self.sandbox = sandbox_manager

    def __call__(
        self,
        action: HardenedFileAction,
        conversation: Optional[LocalConversation] = None,
    ) -> HardenedFileObservation:
        from orchestrator.tools.hardened.models import FileActionRequest

        op_val = (
            action.operation.value
            if hasattr(action.operation, "value")
            else str(action.operation)
        )
        req = FileActionRequest(
            operation=op_val,  # type: ignore[arg-type]
            path=action.path,
            content=action.content,
            target_text=action.patch_find,
            replacement_text=action.patch_replace,
            symbol=action.symbol_name,
            offset_line=action.offset_line,
            limit_lines=min(action.limit_lines, 500),
            start_line=action.start_line,
            end_line=action.end_line,
        )
        res = self.sandbox.handle_file_action(req, conversation=conversation)
        return HardenedFileObservation(
            success=res.success,
            operation=op_val,
            path=action.path,
            content=res.file_content,
            outline_summary=res.outline_summary,
            files=res.files,
            ast_valid=not res.is_error,
            error_message=res.message if not res.success else None,
        )

    def close(self) -> None:
        pass


class HardenedTerminalExecutor(
    ToolExecutor[HardenedTerminalAction, HardenedTerminalObservation]
):
    """ToolExecutor delegating terminal commands to P9 ToolSandboxManager."""

    def __init__(self, sandbox_manager: Any) -> None:
        self.sandbox = sandbox_manager

    def __call__(
        self,
        action: HardenedTerminalAction,
        conversation: Optional[LocalConversation] = None,
    ) -> HardenedTerminalObservation:
        from orchestrator.tools.hardened.models import TerminalActionRequest

        req = TerminalActionRequest(
            command=action.command,
            timeout_seconds=action.timeout_seconds,
        )
        res = self.sandbox.handle_terminal_action(req, conversation=conversation)
        is_sec_violation = (
            res.exit_code == 126
            or "Security" in (res.stderr or "")
            or "Violation" in (res.stderr or "")
            or "rejected" in (res.stderr or "").lower()
        )
        return HardenedTerminalObservation(
            exit_code=res.exit_code,
            stdout=res.stdout,
            stderr=res.stderr,
            timed_out=res.timed_out,
            security_violation=is_sec_violation,
            error_message=res.stderr if res.is_error else None,
            steering_directive=res.steering_directive,
        )

    def close(self) -> None:
        if hasattr(self.sandbox, "terminate_active_processes"):
            self.sandbox.terminate_active_processes()


class HardenedWorkspaceFileTool(
    ToolDefinition[HardenedFileAction, HardenedFileObservation]
):
    """Official OpenHands SDK ToolDefinition for AST-virtualized file operations."""

    name: ClassVar[str] = "workspace_file"

    @classmethod
    def create(
        cls,
        conv_state: Optional[Any] = None,
        sandbox_manager: Optional[Any] = None,
        **params: Any,
    ) -> Sequence[Self]:
        mgr = sandbox_manager
        if mgr is None and conv_state is not None:
            mgr = getattr(conv_state, "sandbox_manager", None)
            if mgr is None and hasattr(conv_state, "workspace"):
                from orchestrator.tools.hardened.manager import ToolSandboxManager

                ws = getattr(conv_state, "workspace")
                ws_path = getattr(ws, "working_dir", ws)
                if ws_path:
                    mgr = ToolSandboxManager(workspace_root=Path(ws_path))
        if mgr is None:
            raise ValueError(
                "HardenedWorkspaceFileTool requires an active ToolSandboxManager instance."
            )
        return [
            cls(
                description=(
                    "Read, write, patch, edit, list, delete, or inspect AST symbols/outlines in workspace files. "
                    "Supports bounded line windowing and hierarchical outline extraction."
                ),
                action_type=HardenedFileAction,
                observation_type=HardenedFileObservation,
                executor=HardenedFileExecutor(mgr),
            )
        ]


class HardenedWorkspaceTerminalTool(
    ToolDefinition[HardenedTerminalAction, HardenedTerminalObservation]
):
    """Official OpenHands SDK ToolDefinition for grammar-secured terminal commands."""

    name: ClassVar[str] = "workspace_terminal"

    @classmethod
    def create(
        cls,
        conv_state: Optional[Any] = None,
        sandbox_manager: Optional[Any] = None,
        **params: Any,
    ) -> Sequence[Self]:
        mgr = sandbox_manager
        if mgr is None and conv_state is not None:
            mgr = getattr(conv_state, "sandbox_manager", None)
            if mgr is None and hasattr(conv_state, "workspace"):
                from orchestrator.tools.hardened.manager import ToolSandboxManager

                ws = getattr(conv_state, "workspace")
                ws_path = getattr(ws, "working_dir", ws)
                if ws_path:
                    mgr = ToolSandboxManager(workspace_root=Path(ws_path))
        if mgr is None:
            raise ValueError(
                "HardenedWorkspaceTerminalTool requires an active ToolSandboxManager instance."
            )
        return [
            cls(
                description=(
                    "Execute secured CLI commands (pytest, ruff, python, git, etc.) in the workspace. "
                    "Validates commands with strict grammar security and handles Windows PowerShell pipelines."
                ),
                action_type=HardenedTerminalAction,
                observation_type=HardenedTerminalObservation,
                executor=HardenedTerminalExecutor(mgr),
            )
        ]


try:
    register_tool("workspace_file", HardenedWorkspaceFileTool)
except Exception:
    pass

try:
    register_tool("workspace_terminal", HardenedWorkspaceTerminalTool)
except Exception:
    pass


# =====================================================================
# 4. Secret Masking & Telemetry Bridge
# =====================================================================


class SecretMaskingFilter:
    """Masks credentials, API keys, and sensitive tokens from telemetry streams."""

    PATTERNS: Tuple[re.Pattern[str], ...] = (
        re.compile(
            r"(?i)(api[_-]?key|secret|token|password|auth|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"
        ),
        re.compile(r"Bearer\s+([a-zA-Z0-9_\-\.=]{12,})", re.IGNORECASE),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"sk-ant-[a-zA-Z0-9_\-]{20,}"),
        re.compile(r"sk-or-v1-[a-f0-9]{32,}"),
        re.compile(r"sk-[a-zA-Z0-9]{20,}"),
        re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
        re.compile(
            r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC )?PRIVATE KEY-----"
        ),
    )

    @classmethod
    def mask(cls, text: str) -> str:
        """Apply regex mask filters and environment variable redaction across text."""
        if not text:
            return text
        sanitized = str(text)

        # 1. Mask active environment variables matching sensitive terms
        for k, v in os.environ.items():
            k_upper = k.upper()
            if any(term in k_upper for term in ("KEY", "SECRET", "TOKEN", "PASSWORD", "AUTH", "BEARER", "CREDENTIAL")):
                if v and len(v.strip()) >= 8 and v.strip() in sanitized:
                    sanitized = sanitized.replace(v.strip(), f"[REDACTED_{k_upper}]")

        # 2. Apply structured pattern masks
        for pattern in cls.PATTERNS:
            if "PRIVATE KEY" in pattern.pattern:
                sanitized = pattern.sub("[REDACTED_PRIVATE_KEY]", sanitized)
            elif "Bearer" in pattern.pattern:
                sanitized = pattern.sub("Bearer [REDACTED_SECRET]", sanitized)
            elif any(prefix in pattern.pattern for prefix in ("ghp_", "sk-", "AIza")):
                sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
            else:
                sanitized = pattern.sub(r"\1: [REDACTED_SECRET]", sanitized)
        return sanitized

    @classmethod
    def mask_text(cls, text: str) -> str:
        """Alias for mask() conforming to P10 specification naming."""
        return cls.mask(text)


class OpenHandsTelemetryBridge:
    """Synchronous EventStream callback bridge mapping SDK events to ORAGAI telemetry."""

    def __init__(
        self,
        log_store: Optional[Any] = None,
        visualizer: Optional[Any] = None,
        diagnostics_db: Optional[Any] = None,
        telemetry_recorder: Optional[Any] = None,
        role_name: str = "agent",
        progress_monitor: Optional[Any] = None,
    ) -> None:
        self.store = log_store
        self.visualizer = visualizer
        self.db = diagnostics_db
        self.recorder = telemetry_recorder
        self.role_name = role_name
        self.progress_monitor = progress_monitor
        self.mutated_files: Set[str] = set()
        self.step_count: int = 0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_tokens: int = 0
        self.estimated_cost_usd: float = 0.0

    def update_token_metrics(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: Optional[int] = None,
        cost_usd: float = 0.0,
    ) -> None:
        """Update cumulative token metrics and estimated USD cost."""
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = (
            total_tokens
            if total_tokens is not None
            else (prompt_tokens + completion_tokens)
        )
        self.estimated_cost_usd = cost_usd

    def on_event(self, event: Event) -> None:
        """Synchronously process SDK event on emission with secret masking."""
        event_name = type(event).__name__

        if event_name == "TokenEvent":
            prompt_ids = getattr(event, "prompt_token_ids", None) or []
            resp_ids = getattr(event, "response_token_ids", None) or []
            if prompt_ids:
                self.prompt_tokens += len(prompt_ids)
            if resp_ids:
                self.completion_tokens += len(resp_ids)
            self.total_tokens = self.prompt_tokens + self.completion_tokens

        elif event_name == "ActionEvent":
            self.step_count += 1
            action = getattr(event, "action", None)
            thought_raw = getattr(event, "thought", "") or getattr(
                action, "thought", ""
            )
            if isinstance(thought_raw, (list, tuple)):
                thought_str = " ".join(
                    str(getattr(t, "text", t)) for t in thought_raw if t
                )
            else:
                thought_str = str(thought_raw or "")

            masked_thought = (
                SecretMaskingFilter.mask(thought_str) if thought_str else None
            )

            tool_name = (
                getattr(event, "tool_name", "")
                or getattr(action, "__class__", type(action)).__name__
            )
            args: Dict[str, Any] = {}
            if hasattr(action, "model_dump"):
                args = action.model_dump()
            elif hasattr(action, "__dict__"):
                args = dict(action.__dict__)

            op_raw = args.get("operation") or args.get("command") or ""
            op = (
                op_raw.value
                if hasattr(op_raw, "value")
                else str(op_raw or "")
            )
            target_path = str(args.get("path") or args.get("file_path") or "")

            if op in ("write", "patch", "edit", "delete", "append") and target_path:
                self.mutated_files.add(target_path)

            if self.progress_monitor and hasattr(self.progress_monitor, "record_step"):
                try:
                    cmd_val = str(args.get("command")) if args.get("command") else None
                    self.progress_monitor.record_step(
                        action_type=op or tool_name,
                        tool_name=tool_name,
                        target_path=target_path or None,
                        command=cmd_val,
                        is_error=False,
                    )
                except Exception:
                    pass

            if self.store:
                summary = (
                    f"{tool_name} ({op} {target_path})"
                    if target_path
                    else f"{tool_name} ({op})"
                )
                self.store.add_step(
                    summary=summary,
                    action_type=tool_name,
                    arguments={
                        k: SecretMaskingFilter.mask(str(v))
                        for k, v in args.items()
                    },
                    thought=masked_thought,
                )

            if self.visualizer and hasattr(self.visualizer, "on_event"):
                try:
                    self.visualizer.on_event(event)
                except Exception as ex:
                    logger.debug("Visualizer on_event error: %s", ex)
            elif masked_thought:
                preview = masked_thought.replace("\n", " ").strip()
                if len(preview) > 100:
                    preview = preview[:97] + "..."
                ConsoleOutput.agent_step(self.role_name, f"Thinking: {preview}")

        elif event_name == "ObservationEvent":
            obs = getattr(event, "observation", None)
            tool_name = getattr(event, "tool_name", "")
            obs_dict: Dict[str, Any] = {}
            if hasattr(obs, "model_dump"):
                obs_dict = obs.model_dump()
            elif hasattr(obs, "__dict__"):
                obs_dict = dict(obs.__dict__)

            is_err = bool(obs_dict.get("is_error", False)) or not bool(
                obs_dict.get("success", True)
            )
            stdout = SecretMaskingFilter.mask(str(obs_dict.get("stdout", "")))
            stderr = SecretMaskingFilter.mask(str(obs_dict.get("stderr", "")))
            error_msg = SecretMaskingFilter.mask(
                str(obs_dict.get("error_message", ""))
            )
            summary = (
                f"Observation: {tool_name} error={is_err}"
                if is_err
                else f"Observation: {tool_name} success"
            )

            if is_err and self.progress_monitor and hasattr(self.progress_monitor, "mark_last_step_error"):
                try:
                    self.progress_monitor.mark_last_step_error(error_msg or stderr or stdout)
                except Exception:
                    pass

            if self.store:
                self.store.add_step(
                    summary=summary,
                    action_type=tool_name,
                    observation=stdout or stderr or error_msg,
                    is_error=is_err,
                )

            if self.recorder and hasattr(self.recorder, "record_step"):
                try:
                    current_role = getattr(
                        self.store, "current_role", self.role_name
                    ) or self.role_name
                    self.recorder.record_step(
                        agent_role=current_role,
                        action_type=tool_name or "observation",
                        iteration=self.step_count,
                        duration_seconds=0.0,
                        success=not is_err,
                        error_summary=error_msg if is_err else None,
                        prompt_tokens=self.prompt_tokens,
                        completion_tokens=self.completion_tokens,
                        total_tokens=self.total_tokens,
                        estimated_cost_usd=self.estimated_cost_usd,
                    )
                except Exception:
                    pass

            if self.visualizer and hasattr(self.visualizer, "on_event"):
                try:
                    self.visualizer.on_event(event)
                except Exception as ex:
                    logger.debug("Visualizer on_event error: %s", ex)
            else:
                ConsoleOutput.agent_step(self.role_name, f"Observation: {tool_name} (error={is_err})")

        elif event_name in ("AgentErrorEvent", "ConversationErrorEvent"):
            code = str(getattr(event, "code", "Error"))
            detail = SecretMaskingFilter.mask(
                str(getattr(event, "detail", getattr(event, "error", "")))
            )
            if self.store:
                self.store.add_step(
                    summary=f"Error [{code}]: {detail[:80]}",
                    action_type="Error",
                    observation=detail,
                    is_error=True,
                )

            if self.recorder and hasattr(self.recorder, "record_incident"):
                try:
                    current_role = getattr(
                        self.store, "current_role", self.role_name
                    ) or self.role_name
                    self.recorder.record_incident(
                        step_name=current_role,
                        incident_type=code,
                        details=detail,
                    )
                except Exception:
                    pass

            if self.visualizer and hasattr(self.visualizer, "on_event"):
                try:
                    self.visualizer.on_event(event)
                except Exception:
                    pass

        if self.db and hasattr(self.db, "log_incident"):
            try:
                role = (
                    getattr(self.store, "current_role", self.role_name)
                    if self.store
                    else self.role_name
                )
                self.db.log_incident(
                    severity="INFO",
                    origin_module="OpenHandsRuntimeBridge",
                    target_role=role,
                    error_signature=event_name,
                    raw_payload=SecretMaskingFilter.mask(str(event)),
                )
            except Exception:
                pass


# =====================================================================
# 5. SDK Tool Adapter & Agent Factory
# =====================================================================


class SDKToolAdapter:
    """Binds hardened P9 tools to OpenHands SDK ToolDefinition sequences."""

    @staticmethod
    def create_tools_for_persona(
        sandbox_manager: Any,
        role_name: str,
        scope: Optional[Any] = None,
    ) -> List[ToolDefinition[Any, Any]]:
        """Instantiate hardened tools configured with persona RBAC and constrictions."""
        tools: List[ToolDefinition[Any, Any]] = []

        # 1. Hardened Workspace File Tool (Always included with RBAC write boundaries)
        file_tools = HardenedWorkspaceFileTool.create(
            sandbox_manager=sandbox_manager
        )
        tools.extend(file_tools)

        # 2. Hardened Workspace Terminal Tool (Conditionally included based on role, scope, and constrictions)
        terminal_permitted = True
        if scope is not None and hasattr(scope, "allow_terminal"):
            terminal_permitted = bool(scope.allow_terminal)

        if terminal_permitted and hasattr(sandbox_manager, "is_tool_permitted"):
            terminal_permitted = bool(
                sandbox_manager.is_tool_permitted("workspace_terminal")
                or sandbox_manager.is_tool_permitted("terminal")
            )

        if terminal_permitted:
            terminal_tools = HardenedWorkspaceTerminalTool.create(
                sandbox_manager=sandbox_manager
            )
            tools.extend(terminal_tools)

        return tools


class SDKAgentFactory:
    """Creates configured OpenHands Agent instances per persona without monkey-patching."""

    @staticmethod
    def get_default_system_prompt_for_role(role_name: str) -> str:
        """Retrieve canonical expert system prompt for a persona role."""
        norm_role = role_name.strip().lower()
        if norm_role == "auditor":
            from orchestrator.agents.auditor import AUDITOR_SYSTEM_PROMPT
            return AUDITOR_SYSTEM_PROMPT
        elif norm_role == "architect":
            from orchestrator.agents.architect import ARCHITECT_SYSTEM_PROMPT
            return ARCHITECT_SYSTEM_PROMPT
        elif norm_role == "reviewer":
            from orchestrator.agents.reviewer import REVIEWER_SYSTEM_PROMPT
            return REVIEWER_SYSTEM_PROMPT
        elif norm_role == "tester":
            from orchestrator.agents.tester import TESTER_SYSTEM_PROMPT
            return TESTER_SYSTEM_PROMPT
        elif norm_role == "documentation":
            from orchestrator.agents.documentation import DOCUMENTATION_SYSTEM_PROMPT
            return DOCUMENTATION_SYSTEM_PROMPT
        elif norm_role == "developer":
            from orchestrator.agents.developer import DEVELOPER_SYSTEM_PROMPT
            return DEVELOPER_SYSTEM_PROMPT
        return f"You are a helpful software engineer acting as {role_name}."

    @staticmethod
    def get_default_scope_for_role(
        role_name: str,
        config: Optional[Any] = None,
    ) -> Any:
        """Return standardized AgentExecutionScope for canonical persona roles."""
        from orchestrator.tools.hardened.models import (
            AgentExecutionScope,
            ToolPermissionLevel,
        )

        norm_role = role_name.strip().lower()
        if norm_role == "architect":
            allowed_prefixes = ("PLAN.md", "docs/")
            if config and hasattr(config, "allowed_write_prefixes_architect"):
                allowed_prefixes = tuple(config.allowed_write_prefixes_architect)
            return AgentExecutionScope(
                role="architect",
                file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
                allowed_write_prefixes=allowed_prefixes,
                max_turns_ceiling=20,
                allow_terminal=True,
            )
        elif norm_role == "tester":
            return AgentExecutionScope(
                role="tester",
                file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
                allowed_write_prefixes=("tests/",),
                max_turns_ceiling=25,
                allow_terminal=True,
            )
        elif norm_role == "reviewer":
            return AgentExecutionScope(
                role="reviewer",
                file_permission=ToolPermissionLevel.READ_ONLY,
                allowed_write_prefixes=("docs/code_review.md", "docs/review/"),
                max_turns_ceiling=15,
                allow_terminal=True,
            )
        elif norm_role == "auditor":
            allowed_prefixes = ("docs/", ".oragai/")
            if config and hasattr(config, "allowed_write_prefixes_auditor"):
                allowed_prefixes = tuple(config.allowed_write_prefixes_auditor)
            return AgentExecutionScope(
                role="auditor",
                file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
                allowed_write_prefixes=allowed_prefixes,
                max_turns_ceiling=20,
                allow_terminal=True,
            )
        elif norm_role == "remediation":
            return AgentExecutionScope(
                role="remediation",
                file_permission=ToolPermissionLevel.FULL_WRITE,
                max_turns_ceiling=25,
                allow_terminal=True,
            )
        else:  # developer and fallback
            return AgentExecutionScope(
                role="developer",
                file_permission=ToolPermissionLevel.FULL_WRITE,
                max_turns_ceiling=30,
                allow_terminal=True,
            )

    @staticmethod
    def create_agent(
        config: Any,
        llm_manager: Any,
        role_name: str,
        system_prompt: str,
        tools: Sequence[Any],
        include_default_tools: Optional[Sequence[str]] = None,
    ) -> Agent:
        """Construct Agent instance with clean SDK configuration."""
        from openhands.sdk.tool import Tool

        if hasattr(llm_manager, "get_llm"):
            llm = llm_manager.get_llm(role_name)
        elif hasattr(llm_manager, "create_llm_for_role"):
            llm = llm_manager.create_llm_for_role(role_name, config)
        else:
            from orchestrator.llm import create_llm_for_role

            llm = create_llm_for_role(role_name, config)

        sdk_tools: List[Tool] = []
        for t in tools:
            if isinstance(t, Tool):
                sdk_tools.append(t)
            elif hasattr(t, "name"):
                sdk_tools.append(Tool(name=t.name))
            elif isinstance(t, str):
                sdk_tools.append(Tool(name=t))
            elif isinstance(t, type):
                sdk_tools.append(Tool(name=t.__name__))

        default_tools_list: List[str] = (
            list(include_default_tools) if include_default_tools is not None else []
        )

        return Agent(
            llm=llm,
            tools=sdk_tools,
            system_prompt=system_prompt,
            include_default_tools=default_tools_list,
            tool_concurrency_limit=1,
        )

    @classmethod
    def create_persona_agent(
        cls,
        config: Any,
        llm_manager: Any,
        role_name: str,
        prompt_view: Union[PromptView, str],
        sandbox_manager: Optional[Any] = None,
        scope: Optional[Any] = None,
        workspace_path: Optional[Path] = None,
    ) -> Agent:
        """Standardized persona agent construction injecting AgentExecutionScope and prompt views."""
        from orchestrator.tools.hardened.manager import ToolSandboxManager

        resolved_scope = scope or cls.get_default_scope_for_role(role_name, config)
        mgr = sandbox_manager
        if mgr is None and workspace_path is not None:
            mgr = ToolSandboxManager(
                workspace_root=workspace_path,
                scope=resolved_scope,
            )

        tools = (
            SDKToolAdapter.create_tools_for_persona(
                sandbox_manager=mgr,
                role_name=role_name,
                scope=resolved_scope,
            )
            if mgr is not None
            else []
        )

        system_prompt = (
            prompt_view.tier0_system_prompt
            if isinstance(prompt_view, PromptView) and prompt_view.tier0_system_prompt
            else (
                getattr(prompt_view, "tier0_system_prompt", None)
                or cls.get_default_system_prompt_for_role(role_name)
            )
        )

        return cls.create_agent(
            config=config,
            llm_manager=llm_manager,
            role_name=role_name,
            system_prompt=system_prompt,
            tools=tools,
            include_default_tools=[],
        )


# =====================================================================
# 6. Deterministic Exit Status Classifier
# =====================================================================


class ExitStatusClassifier:
    """Deterministically classifies ConversationState into AgentExecutionOutcome."""

    @staticmethod
    def classify(
        conv: Any,
        role: str,
        max_turns: int,
        initial_tokens: int,
        token_ceiling: int,
        mutated_files: Sequence[str],
        execution_exception: Optional[Exception] = None,
    ) -> AgentExecutionOutcome:
        """Classify state and event stream of a finished or halted turn."""
        state = getattr(conv, "state", None)
        status = getattr(state, "execution_status", None) if state else None
        events = list(getattr(state, "events", [])) if state else []

        # 1. Extract Token Usage
        tu = getattr(getattr(getattr(conv, "agent", None), "llm", None), "metrics", None)
        pt, ct = 0, 0
        if tu and hasattr(tu, "accumulated_token_usage"):
            pt = getattr(tu.accumulated_token_usage, "prompt_tokens", 0) or 0
            ct = getattr(tu.accumulated_token_usage, "completion_tokens", 0) or 0
        total_tokens = max(0, (pt + ct) - initial_tokens)

        # 2. Extract Final Thought
        final_thought = None
        for ev in reversed(events):
            if type(ev).__name__ == "ActionEvent" and getattr(ev, "thought", None):
                th = getattr(ev, "thought", None)
                if isinstance(th, (list, tuple)):
                    final_thought = " ".join(
                        str(getattr(t, "text", t)) for t in th if t
                    ).strip()
                else:
                    final_thought = str(th).strip()
                if final_thought:
                    break

        # 3. Check for Fatal Execution Exception
        if execution_exception is not None:
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.FATAL_ERROR,
                completed_naturally=False,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=f"Runtime crash in agent execution: {execution_exception}",
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )

        # 4. Check for Fatal ConversationErrorEvent or Security Violations
        latest_error_event = next(
            (ev for ev in reversed(events) if type(ev).__name__ == "ConversationErrorEvent"),
            None,
        )

        has_tool_rejection = False
        tool_rejection_msg = None
        for ev in reversed(events):
            if type(ev).__name__ == "ObservationEvent":
                obs = getattr(ev, "observation", None)
                if obs:
                    if getattr(obs, "security_violation", False):
                        has_tool_rejection = True
                        tool_rejection_msg = getattr(obs, "error_message", None) or "Security sandbox violation"
                        break
                    err_m = str(getattr(obs, "error_message", "") or "")
                    if "RBAC Violation" in err_m or "Tool Constriction Violation" in err_m:
                        has_tool_rejection = True
                        tool_rejection_msg = err_m
                        break

        # 4. Deterministic Classification Logic
        if status == ConversationExecutionStatus.FINISHED:
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.NATURAL_COMPLETION,
                completed_naturally=True,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=None,
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )

        if latest_error_event and getattr(latest_error_event, "code", "") == "MaxIterationsReached":
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.STEP_LIMIT_REACHED,
                completed_naturally=False,
                iterations_executed=max_turns,
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=f"Turn step limit reached ({max_turns} turns).",
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )

        if token_ceiling > 0 and total_tokens >= token_ceiling:
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.TOKEN_LIMIT_REACHED,
                completed_naturally=False,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=f"Turn token budget exhausted ({total_tokens:,} >= {token_ceiling:,}).",
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )

        if has_tool_rejection:
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.TOOL_REJECTION,
                completed_naturally=False,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=tool_rejection_msg or "Tool execution rejected by security policy.",
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )

        if status == ConversationExecutionStatus.STUCK:
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.AGENT_STUCK,
                completed_naturally=False,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message="Agent loop repetition detected by SDK stuck detector.",
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )

        if status == ConversationExecutionStatus.ERROR or latest_error_event:
            err_msg = (
                getattr(latest_error_event, "detail", "Unknown SDK runtime error")
                if latest_error_event
                else "Execution error"
            )
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.FATAL_ERROR,
                completed_naturally=False,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=str(err_msg),
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )

        return AgentExecutionOutcome(
            role=role,
            exit_reason=AgentExitReason.STEP_LIMIT_REACHED,
            completed_naturally=False,
            iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
            max_iterations_allocated=max_turns,
            prompt_tokens=pt,
            completion_tokens=ct,
            total_tokens=total_tokens,
            cost_usd=0.0,
            error_message="Turn completed without explicit FINISHED state.",
            mutated_files=tuple(mutated_files),
            final_thought=final_thought,
            handoff_payload=None,
        )


# =====================================================================
# 7. Ephemeral Session Runner
# =====================================================================


class SDKSessionRunner:
    """Executes single-turn bounded conversations with synchronous lifecycle control."""

    @staticmethod
    def run_turn(
        agent: Agent,
        workspace_path: Path,
        prompt_view: Union[PromptView, str],
        turn_envelope: Union[TurnEnvelope, Dict[str, Any]],
        telemetry_bridge: OpenHandsTelemetryBridge,
        role_name: str,
    ) -> AgentExecutionOutcome:
        """Execute a single bounded turn envelope without background polling threads."""
        if isinstance(turn_envelope, TurnEnvelope):
            max_turns = turn_envelope.max_turns
            token_ceiling = turn_envelope.token_ceiling
        elif isinstance(turn_envelope, dict):
            max_turns = turn_envelope.get("max_turns", 15)
            token_ceiling = turn_envelope.get("token_ceiling", 50_000)
        else:
            max_turns = getattr(turn_envelope, "max_turns", 15)
            token_ceiling = getattr(turn_envelope, "token_ceiling", 50_000)

        compiled_prompt = (
            prompt_view.compiled_prompt
            if isinstance(prompt_view, PromptView)
            else (
                getattr(prompt_view, "compiled_prompt", None)
                or str(prompt_view)
            )
        )

        # 1. Baseline Token Inspection
        initial_tokens = 0
        llm = getattr(agent, "llm", None)
        if (
            llm
            and hasattr(llm, "metrics")
            and hasattr(llm.metrics, "accumulated_token_usage")
        ):
            tu = llm.metrics.accumulated_token_usage
            if tu:
                initial_tokens = int(
                    (getattr(tu, "prompt_tokens", 0) or 0)
                    + (getattr(tu, "completion_tokens", 0) or 0)
                )

        # 2. Ephemeral LocalConversation Instantiation
        conv = LocalConversation(
            agent=agent,
            workspace=workspace_path,
            max_iteration_per_run=max_turns,
            stuck_detection=True,
            callbacks=[telemetry_bridge.on_event],
            delete_on_close=True,
            visualizer=None,
        )

        # 3. Ingest Initial Prompt
        conv.send_message(compiled_prompt)

        # 4. Synchronous Execution
        execution_exception: Optional[Exception] = None
        try:
            conv.run()
        except Exception as e:
            execution_exception = e
            logger.error(
                f"Execution error in {role_name} turn: {e}",
                exc_info=True,
            )

        # 5. Classify Exit Status
        outcome = ExitStatusClassifier.classify(
            conv=conv,
            role=role_name,
            max_turns=max_turns,
            initial_tokens=initial_tokens,
            token_ceiling=token_ceiling,
            mutated_files=list(telemetry_bridge.mutated_files),
            execution_exception=execution_exception,
        )

        if telemetry_bridge and telemetry_bridge.progress_monitor and hasattr(telemetry_bridge.progress_monitor, "get_metrics"):
            try:
                metrics = telemetry_bridge.progress_monitor.get_metrics()
                outcome = dataclasses.replace(outcome, progress_metrics=metrics)
            except Exception:
                pass

        # 6. Ephemeral Teardown
        try:
            conv.close()
        except Exception:
            pass

        if telemetry_bridge and telemetry_bridge.visualizer and hasattr(telemetry_bridge.visualizer, "close"):
            try:
                telemetry_bridge.visualizer.close(success=outcome.success)
            except Exception:
                pass

        return outcome


# =====================================================================
# 8. Master Orchestration Facade
# =====================================================================


class OpenHandsRuntimeBridge:
    """Master facade providing clean execution delegation from ORAGAI to OpenHands SDK."""

    def __init__(
        self,
        config: Any,
        llm_manager: Any,
        log_store: Optional[Any] = None,
        visualizer: Optional[Any] = None,
        diagnostics_db: Optional[Any] = None,
        telemetry_recorder: Optional[Any] = None,
    ) -> None:
        self.config = config
        self.llm_manager = llm_manager
        self.log_store = log_store
        self.visualizer = visualizer
        self.diagnostics_db = diagnostics_db
        self.telemetry_recorder = telemetry_recorder

    def execute_bounded_turn(
        self,
        role_name: str,
        workspace_path: Path,
        prompt_view: Union[PromptView, str],
        turn_envelope: Union[TurnEnvelope, Dict[str, Any]],
        sandbox_manager: Any,
        progress_monitor: Optional[Any] = None,
    ) -> AgentExecutionOutcome:
        """Execute a single bounded turn for the specified persona."""
        # 1. Build Agent via SDKAgentFactory
        scope = getattr(sandbox_manager, "scope", None)
        agent = SDKAgentFactory.create_persona_agent(
            config=self.config,
            llm_manager=self.llm_manager,
            role_name=role_name,
            prompt_view=prompt_view,
            sandbox_manager=sandbox_manager,
            scope=scope,
            workspace_path=workspace_path,
        )

        llm_instance = getattr(agent, "llm", None)
        model_name = getattr(llm_instance, "model", "") if llm_instance else ""

        if self.log_store and hasattr(self.log_store, "set_agent_context"):
            self.log_store.set_agent_context(
                role=role_name,
                phase=role_name,
                model=model_name,
                llm=llm_instance,
            )

        # 2. Create Telemetry Bridge
        telemetry_bridge = OpenHandsTelemetryBridge(
            log_store=self.log_store,
            visualizer=self.visualizer,
            diagnostics_db=self.diagnostics_db,
            telemetry_recorder=self.telemetry_recorder,
            role_name=role_name,
            progress_monitor=progress_monitor,
        )

        # 3. Run Ephemeral Bounded Session
        outcome = SDKSessionRunner.run_turn(
            agent=agent,
            workspace_path=workspace_path,
            prompt_view=prompt_view,
            turn_envelope=turn_envelope,
            telemetry_bridge=telemetry_bridge,
            role_name=role_name,
        )

        return outcome
