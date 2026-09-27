"""Verified Audit Models for ORAGAI Pure Domain Core.

Classification: Enterprise Architectural Blueprint & Canonical System Standard
Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant: Zero external framework dependencies (stdlib + pydantic only).
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class FindingCategory(str, Enum):
    """Category of verified audit finding."""

    ARCHITECTURE = "ARCHITECTURE"
    SECURITY = "SECURITY"
    CORRECTNESS = "CORRECTNESS"
    PERFORMANCE = "PERFORMANCE"
    MAINTAINABILITY = "MAINTAINABILITY"


class FindingSeverity(str, Enum):
    """Severity rating of finding."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class VerifiedAuditFinding(BaseModel):
    """Strongly-typed, verifiable static analysis defect finding."""

    id: str = Field(..., description="Finding ID, e.g., 'FIND-SEC-001'")
    category: FindingCategory
    severity: FindingSeverity
    file_path: str = Field(..., description="Workspace-relative file path")
    line_number: Optional[int] = Field(default=None)
    rule_id: str = Field(..., description="Static analysis rule identifier")
    description: str = Field(..., description="Detailed vulnerability or defect description")
    remediation_advice: str = Field(..., description="Actionable fix recommendation")
    is_quarantined: bool = Field(default=False)
    resolved_in_commit: Optional[str] = Field(default=None)


class FindingDAG(BaseModel):
    """Directed acyclic dependency graph of audit findings for topological remediation."""

    findings: List[VerifiedAuditFinding] = Field(default_factory=list)
    total_critical: int = 0
    total_high: int = 0
    total_medium: int = 0
    total_low: int = 0
