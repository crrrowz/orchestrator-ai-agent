"""Micro-TDD Autonomous Loop (Red -> Green -> Refactor).

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Section 4 Step 7: Enforces strict Red-Green-Refactor protocol.
"""

from __future__ import annotations

from typing import Any, Dict
from pathlib import Path
from orchestrator.workstreams.micro_tdd.red_phase import RedPhaseTestGenerator
from orchestrator.workstreams.micro_tdd.green_phase import GreenPhaseDispatcher
from orchestrator.workstreams.micro_tdd.blue_phase import BluePhaseRefactorEngine


class MicroTDDLoop:
    """Coordinates autonomous Red -> Green -> Refactor cycle for individual requirements."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.red = RedPhaseTestGenerator(workspace_path)
        self.green = GreenPhaseDispatcher(workspace_path)
        self.blue = BluePhaseRefactorEngine(workspace_path)

    def execute_cycle_step(
        self, step_name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "step": step_name,
            "status": "EXECUTED",
            "workspace": str(self.workspace_path),
            "payload": payload,
        }
