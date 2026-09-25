"""Data models and schemas for the Deep Inspection and Self-Evolution Engine (P7)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class FindingCategory(str, Enum):
    """Formal taxonomy of codebase audit defect categories."""
    SECURITY = "SECURITY"
    ARCHITECTURE = "ARCHITECTURE"
    PERFORMANCE = "PERFORMANCE"
    RELIABILITY = "RELIABILITY"
    MAINTAINABILITY = "MAINTAINABILITY"
    CONVENTION = "CONVENTION"


class FindingSeverity(str, Enum):
    """Standardized finding severity hierarchy."""
    CRITICAL = "CRITICAL"          # Security vulnerability, data loss hazard, import cycle
    HIGH = "HIGH"                  # Core logic bug, unhandled crash, god module, public stub
    MEDIUM = "MEDIUM"              # Cyclomatic complexity > 15, missing error handling, DRY violation
    LOW = "LOW"                    # Internal TODO, minor convention deviation, unused import
    OPTIMIZATION = "OPTIMIZATION"  # Non-critical performance or clarity enhancement


class FindingSource(str, Enum):
    """Origin detector of the audit finding."""
    STATIC_AST = "STATIC_AST"
    STATIC_LINTER = "STATIC_LINTER"
    SECRET_SCAN = "SECRET_SCAN"
    COUPLING_ANALYZER = "COUPLING_ANALYZER"
    AUDITOR_LLM = "AUDITOR_LLM"


class RemediationStatus(str, Enum):
    """Lifecycle state of an individual finding in the remediation loop."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    QUARANTINED_BLOCKED = "QUARANTINED_BLOCKED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class AuditState(str, Enum):
    """Lifecycle state of the audit run."""
    AUDIT_STARTED = "AUDIT_STARTED"
    AUDIT_COMPLETED = "AUDIT_COMPLETED"
    AUDIT_CLEAN = "AUDIT_CLEAN"
    AUDIT_INCOMPLETE = "AUDIT_INCOMPLETE"
    AUDIT_FAILED = "AUDIT_FAILED"


class VerifiedAuditFinding(BaseModel):
    """Canonical, strongly typed audit defect entity with cryptographic fingerprinting."""

    finding_id: str = Field(..., description="Deterministic unique finding ID, e.g. SEC-001")
    category: FindingCategory
    severity: FindingSeverity
    source: FindingSource

    file_path: str = Field(..., description="Workspace-relative target path")
    line_start: int = Field(..., ge=1)
    line_end: int = Field(..., ge=1)
    ast_symbol: str = Field(default="")

    code_snippet: str = Field(..., min_length=3)
    problem_statement: str = Field(..., min_length=10)
    remediation_proposal: str = Field(..., min_length=10)

    cwe_id: Optional[str] = None
    blast_radius_files: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    remediation_status: RemediationStatus = Field(default=RemediationStatus.OPEN)
    remediation_attempts: int = Field(default=0, ge=0)
    remediation_diff: Optional[str] = None
    sha256_fingerprint: str = Field(default="")

    @field_validator("line_end")
    @classmethod
    def validate_line_bounds(cls, v: int, info) -> int:
        start = info.data.get("line_start")
        if start is not None and v < start:
            raise ValueError(f"line_end ({v}) cannot be less than line_start ({start})")
        return v

    def compute_fingerprint(self) -> str:
        """Compute deterministic SHA-256 fingerprint for identity and deduplication."""
        norm_snippet = re.sub(r"\s+", " ", self.code_snippet).strip()
        raw = f"{self.category.value}:{self.file_path}:{self.ast_symbol}:{norm_snippet}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class ClusterPartition:
    """Bounded functional partition of workspace files for targeted auditing."""
    cluster_id: str
    cluster_name: str
    files: List[str]
    total_loc: int
    dominant_layer: str


@dataclass(frozen=True)
class CodebaseHealthMetrics:
    """Empirical codebase health measurements."""
    total_files: int
    total_loc: int
    clean_static: bool
    chi_score: float
    health_rating: str
    critical_findings_count: int
    high_findings_count: int
    medium_findings_count: int
    low_findings_count: int
    circular_dependency_cycles: int
    mean_distance_main_sequence: float
    line_coverage_ratio: float
