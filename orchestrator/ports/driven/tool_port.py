"""Outbound Driven Tool Execution Port Protocol.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import Protocol, Tuple, runtime_checkable


@runtime_checkable
class ToolExecutionPort(Protocol):
    """Outbound port for executing workspace tools (AST-safe file operations & grammar-checked bash)."""

    def read_file(self, relative_path: str) -> str:
        ...

    def write_file_ast_guarded(self, relative_path: str, content: str) -> bool:
        ...

    def execute_grammar_checked_command(
        self,
        command: str,
        timeout_sec: int = 60,
    ) -> Tuple[int, str, str]:
        ...
