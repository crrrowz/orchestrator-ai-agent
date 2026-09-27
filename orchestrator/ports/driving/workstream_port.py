"""Inbound Driving Workstream Dispatch Port Protocol.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable
from pathlib import Path


@runtime_checkable
class WorkstreamDispatchPort(Protocol):
    """Inbound driving port for dispatching application workstreams."""

    def dispatch(
        self,
        mode: str,
        workspace_path: Path,
        task_description: str,
        options: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        ...
