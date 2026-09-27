"""Abstract Interface Ports Package (typing.Protocol & ABCs).

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from orchestrator.ports.driving import (
    CLIControllerPort,
    FSMTriggerPort,
    LifecycleControllerPort,
    WorkstreamDispatchPort,
)
from orchestrator.ports.driven import (
    AgentExecutionOutcome,
    AgentRuntimePort,
    RollbackControllerPort,
    TelemetryStoragePort,
    ToolExecutionPort,
    VCSPort,
)

__all__ = [
    "CLIControllerPort",
    "FSMTriggerPort",
    "LifecycleControllerPort",
    "WorkstreamDispatchPort",
    "AgentExecutionOutcome",
    "AgentRuntimePort",
    "RollbackControllerPort",
    "TelemetryStoragePort",
    "ToolExecutionPort",
    "VCSPort",
]
