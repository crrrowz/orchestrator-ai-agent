"""Canonical Data Models and Schema Definitions for Hardened Tooling Sandbox.

Defines AST outline nodes, virtual file views, validated command structures,
and action/observation request-response envelopes.
"""

from __future__ import annotations

import dataclasses
import enum
from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field


class FileOperationType(str, enum.Enum):
    """Supported file manipulation operations in hardened sandbox."""

    READ = "read"
    WRITE = "write"
    PATCH = "patch"
    EDIT = "edit"
    OUTLINE = "outline"
    SYMBOL = "symbol"
    LIST = "list"
    DELETE = "delete"
    APPEND = "append"


@dataclasses.dataclass(frozen=True)
class SymbolOutlineNode:
    """Represents a structural code symbol in the hierarchical file outline."""

    name: str
    symbol_type: Literal["class", "method", "function", "async_function", "constant"]
    start_line: int
    end_line: int
    signature: str
    docstring_summary: Optional[str] = None
    children: Tuple[SymbolOutlineNode, ...] = dataclasses.field(default_factory=tuple)


@dataclasses.dataclass(frozen=True)
class VirtualFileView:
    """Virtualized file representation returned to agent observation channels."""

    file_path: str
    total_lines: int
    offset_line: int
    limit_lines: int
    content: str
    has_more_above: bool
    has_more_below: bool
    next_offset: Optional[int] = None
    outline: Optional[Tuple[SymbolOutlineNode, ...]] = None


class FileActionRequest(BaseModel):
    """Action payload for hardened workspace file operations."""

    model_config = ConfigDict(extra="ignore")

    operation: Literal[
        "read", "write", "patch", "edit", "outline", "symbol", "list", "delete", "append"
    ]
    path: str
    content: Optional[str] = None
    target_text: Optional[str] = None
    replacement_text: Optional[str] = None
    symbol: Optional[str] = None
    offset_line: int = Field(default=1, ge=1)
    limit_lines: int = Field(default=250, ge=1, le=500)
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class FileObservationResult(BaseModel):
    """Observation payload resulting from hardened file operations."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    message: str
    file_content: Optional[str] = None
    outline_summary: Optional[str] = None
    files: Optional[List[str]] = None
    is_error: bool = False


@dataclasses.dataclass(frozen=True)
class PipelineSegment:
    """Represents a single command segment within a piped terminal execution."""

    raw_segment: str
    base_command: str
    arguments: Tuple[str, ...]
    is_powershell_cmdlet: bool = False


@dataclasses.dataclass(frozen=True)
class ValidatedCommand:
    """Result of grammar-based command validation."""

    is_valid: bool
    executable_path: str
    command_line_args: Tuple[str, ...]
    pipeline_segments: Tuple[PipelineSegment, ...]
    rejection_reason: Optional[str] = None
    is_powershell_pipeline: bool = False


class TerminalActionRequest(BaseModel):
    """Action payload for hardened terminal command execution."""

    model_config = ConfigDict(extra="ignore")

    command: str
    timeout_seconds: int = Field(default=30, ge=1, le=300)


class TerminalObservationResult(BaseModel):
    """Observation payload resulting from hardened terminal execution."""

    model_config = ConfigDict(extra="ignore")

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    is_error: bool = False
    steering_directive: Optional[str] = None
