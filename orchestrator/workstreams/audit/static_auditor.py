"""Zero-Token Static Auditor for Audit Workstream.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Section 4 Step 9: Static sweeps over modified workspace (AST, Cyclomatic, Tarjan SCC).
"""

from __future__ import annotations

from orchestrator.analysis.audit.scanner import StaticAnalysisScanner

__all__ = ["StaticAnalysisScanner"]
