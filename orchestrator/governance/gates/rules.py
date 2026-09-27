"""Deterministic Completion Rules (100% Mandatory Verification).

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant 2: False Completion Rate Barrier (FCR == 0.000).
Invariant 3: Zero Agent Self-Certification.
"""

from __future__ import annotations

from typing import Any, List, Tuple
from pathlib import Path


def verify_mandatory_criteria_satisfied(graph: Any) -> Tuple[bool, List[str]]:
    """Evaluates whether all mandatory requirements in task truth graph are VERIFIED."""
    if not graph:
        return True, []

    unmet = []
    reqs = getattr(graph, "requirements", [])
    if isinstance(reqs, dict):
        req_list = list(reqs.values())
    else:
        req_list = list(reqs)

    for req in req_list:
        is_mand = getattr(req, "is_mandatory", True)
        if not is_mand:
            continue
        v_state = getattr(req, "verification_state", None)
        v_state_str = getattr(v_state, "value", str(v_state))
        if v_state_str not in ("VERIFIED", "VerificationState.VERIFIED"):
            unmet.append(
                f"{getattr(req, 'id', 'REQ')}: state={v_state_str} is not VERIFIED"
            )

    return len(unmet) == 0, unmet
