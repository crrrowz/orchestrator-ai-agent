"""Hardened Sandbox & AST Virtualizer Package.

Provides AST file virtualization, grammar-based command security,
persona RBAC enforcement, dynamic tool constriction, and Windows NT isolation.
"""

from orchestrator.tools.hardened.grammar import CommandGrammarValidator
from orchestrator.tools.hardened.manager import (
    ToolSandboxManager,
    matches_path_scope,
)
from orchestrator.tools.hardened.models import (
    AgentExecutionScope,
    FileActionRequest,
    FileObservationResult,
    FileOperationType,
    PipelineSegment,
    SymbolOutlineNode,
    TerminalActionRequest,
    TerminalObservationResult,
    ToolPermissionLevel,
    ValidatedCommand,
    VirtualFileView,
)
from orchestrator.tools.hardened.sandbox import TerminalSandboxEngine
from orchestrator.tools.hardened.security import (
    APPROVED_PIPELINE_CMDLETS,
    APPROVED_ROOT_COMMANDS,
    DISALLOWED_OPERATORS,
    PROHIBITED_DEVICE_NAMES,
    is_sensitive_filepath,
    sanitize_text_secrets,
)
from orchestrator.tools.hardened.virtualizer import (
    MAX_APPENDS_PER_FILE,
    MAX_READ_CHARS,
    MAX_READ_LINES,
    WorkspaceFileVirtualizer,
    reset_hardened_append_counts,
)

__all__ = [
    "WorkspaceFileVirtualizer",
    "CommandGrammarValidator",
    "TerminalSandboxEngine",
    "ToolSandboxManager",
    "matches_path_scope",
    "FileOperationType",
    "ToolPermissionLevel",
    "AgentExecutionScope",
    "SymbolOutlineNode",
    "VirtualFileView",
    "FileActionRequest",
    "FileObservationResult",
    "PipelineSegment",
    "ValidatedCommand",
    "TerminalActionRequest",
    "TerminalObservationResult",
    "APPROVED_ROOT_COMMANDS",
    "APPROVED_PIPELINE_CMDLETS",
    "DISALLOWED_OPERATORS",
    "PROHIBITED_DEVICE_NAMES",
    "is_sensitive_filepath",
    "sanitize_text_secrets",
    "MAX_READ_LINES",
    "MAX_READ_CHARS",
    "MAX_APPENDS_PER_FILE",
    "reset_hardened_append_counts",
]
