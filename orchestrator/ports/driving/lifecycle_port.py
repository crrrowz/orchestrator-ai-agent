"""Inbound Driving Lifecycle and FSM Trigger Port Protocols.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable
from pathlib import Path


@runtime_checkable
class FSMTriggerPort(Protocol):
    """Inbound port for triggering FSM state transitions."""

    def trigger_event(self, event_name: str, payload: Dict[str, Any]) -> bool:
        ...


@runtime_checkable
class LifecycleControllerPort(Protocol):
    """Inbound port for controlling execution lifecycle."""

    def run_lifecycle(
        self, workspace_path: Path, task_description: str
    ) -> Dict[str, Any]:
        ...
