"""FSM Engine for ORAGAI Governance Control Plane.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestrator.pipeline.fsm.engine import GuardedFSMEngine
    from orchestrator.pipeline.fsm.context import FSMContext


def __getattr__(name: str):
    if name == "GuardedFSMEngine":
        from orchestrator.pipeline.fsm.engine import GuardedFSMEngine
        return GuardedFSMEngine
    if name == "FSMContext":
        from orchestrator.pipeline.fsm.context import FSMContext
        return FSMContext
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["GuardedFSMEngine", "FSMContext"]
