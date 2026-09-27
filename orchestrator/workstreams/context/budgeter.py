"""Token Budget Slicer & Dynamic Headroom Clamper for Context Workstream.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from orchestrator.control.adaptive.clamper import ASTAwareContextClamper

__all__ = ["ASTAwareContextClamper"]
