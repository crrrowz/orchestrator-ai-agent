"""Codebase Health Index (CHI) Calculator for Audit Workstream.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Section 4 Step 9: CHI(W) = max(0.0, min(100.0, 100.0 - P_findings - P_coupling - P_complexity + R_coverage))
Enforces Monotonic Health Invariant: ΔCHI >= 0.0.
"""

from __future__ import annotations

from typing import Any, Dict, List


class CHICalculator:
    """Computes Codebase Health Index (CHI) on [0.0, 100.0] scale."""

    @staticmethod
    def calculate(
        critical_count: int = 0,
        high_count: int = 0,
        medium_count: int = 0,
        low_count: int = 0,
        circular_import_count: int = 0,
        cyclomatic_penalty: float = 0.0,
        coverage_bonus: float = 0.0,
    ) -> float:
        p_findings = (
            critical_count * 20.0
            + high_count * 10.0
            + medium_count * 5.0
            + low_count * 1.0
        )
        p_coupling = circular_import_count * 15.0
        p_complexity = cyclomatic_penalty
        r_coverage = coverage_bonus

        raw_chi = 100.0 - p_findings - p_coupling - p_complexity + r_coverage
        return max(0.0, min(100.0, float(raw_chi)))
