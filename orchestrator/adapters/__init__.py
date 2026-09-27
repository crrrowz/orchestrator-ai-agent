"""Polyglot Project and Infrastructure Adapter package.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from orchestrator.adapters.base import ProjectAdapter
from orchestrator.adapters.generic_adapter import GenericAdapter
from orchestrator.adapters.node_adapter import NodeAdapter
from orchestrator.adapters.python_adapter import PythonAdapter
from orchestrator.adapters.registry import detect_adapter, get_available_adapters
from orchestrator.adapters.runtime import OpenHandsSDKAdapter, ToolDefinition
from orchestrator.adapters.sandbox import (
    ASTVirtualizer,
    HardenedFileAdapter,
    HardenedTerminalAdapter,
)
from orchestrator.adapters.storage import (
    CheckpointRepository,
    SQLiteWALStorageAdapter,
)
from orchestrator.adapters.vcs import GitOpsAdapter, RollbackManager

__all__ = [
    "ProjectAdapter",
    "PythonAdapter",
    "NodeAdapter",
    "GenericAdapter",
    "detect_adapter",
    "get_available_adapters",
    "OpenHandsSDKAdapter",
    "ToolDefinition",
    "HardenedFileAdapter",
    "HardenedTerminalAdapter",
    "ASTVirtualizer",
    "SQLiteWALStorageAdapter",
    "CheckpointRepository",
    "GitOpsAdapter",
    "RollbackManager",
]
