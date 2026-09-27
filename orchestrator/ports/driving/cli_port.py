"""Inbound Driving CLI Port Protocol.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CLIControllerPort(Protocol):
    """Inbound driving port for presentation and CLI execution."""

    def start_task(self, prompt: str, workspace_path: str) -> int:
        ...

    def resume_task(self, task_id: str, workspace_path: str) -> int:
        ...
