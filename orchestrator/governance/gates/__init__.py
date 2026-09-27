"""Completion Gates Package for ORAGAI Control Plane.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from orchestrator.governance.gates.completion_gate import CompletionGate
from orchestrator.governance.gates.rules import verify_mandatory_criteria_satisfied

__all__ = ["CompletionGate", "verify_mandatory_criteria_satisfied"]
