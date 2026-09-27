"""Task Complexity Estimator for ORAGAI Governance Resource Layer.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Section 4 Step 3: C_T = min(10.0, 0.3 * (LOC/100) + 0.3 * CyclomaticMax + 0.2 * DepCount + 0.2 * |M_deps|)
"""

from __future__ import annotations

import math
from typing import Any, Optional


def compute_task_complexity(
    lines_of_code: int = 100,
    cyclomatic_max: int = 5,
    dependency_count: int = 2,
    milestone_dependency_count: int = 1,
) -> float:
    """Computes task complexity score C_T clamped to [1.0, 10.0]."""
    raw_ct = (
        0.3 * (lines_of_code / 100.0)
        + 0.3 * float(cyclomatic_max)
        + 0.2 * float(dependency_count)
        + 0.2 * float(milestone_dependency_count)
    )
    return max(1.0, min(10.0, float(raw_ct)))


class ComplexityEstimator:
    """Estimates codebase and milestone complexity for dynamic turn allocation."""

    @staticmethod
    def estimate(
        loc: int = 100,
        cyclomatic: int = 5,
        dep_count: int = 2,
        milestone_deps: int = 1,
    ) -> float:
        return compute_task_complexity(loc, cyclomatic, dep_count, milestone_deps)
