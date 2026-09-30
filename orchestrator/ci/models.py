"""Data models, taxonomies, and evidence schemas for CI Failure Analysis."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Categorized severity levels for CI log entries and diagnostic findings."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    NOTICE = "NOTICE"
    INFO = "INFO"


class FailureCategory(str, Enum):
    """Fine-grained classification taxonomy for CI pipeline failures."""

    TEST_FAILURE = "TEST_FAILURE"
    BUILD_FAILURE = "BUILD_FAILURE"
    LINT_FAILURE = "LINT_FAILURE"
    TYPE_CHECK_FAILURE = "TYPE_CHECK_FAILURE"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    CACHE_FAILURE = "CACHE_FAILURE"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
    CONFIGURATION_FAILURE = "CONFIGURATION_FAILURE"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    PERMISSION_FAILURE = "PERMISSION_FAILURE"
    TOOLCHAIN_FAILURE = "TOOLCHAIN_FAILURE"
    TIMEOUT = "TIMEOUT"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    UNKNOWN = "UNKNOWN"
    WARNING = "WARNING"
    MAINTENANCE_WARNING = "MAINTENANCE_WARNING"


class RootCauseStatus(str, Enum):
    """Confidence grade for root cause determination."""

    CONFIRMED = "CONFIRMED"
    LIKELY = "LIKELY"
    POSSIBLE = "POSSIBLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class EnvironmentInfo(BaseModel):
    """Execution context and target runner environment metadata."""

    os: str = "unknown"
    os_family: str = "unknown"  # "windows", "linux", "macos", "unknown"
    runtime: str = "python"
    runtime_version: str = "unknown"
    runner_name: Optional[str] = None
    matrix_params: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_matrix(
        cls,
        matrix: Dict[str, Any],
        os_str: Optional[str] = None,
        python_ver: Optional[str] = None,
    ) -> "EnvironmentInfo":
        """Construct EnvironmentInfo from matrix dictionary or explicit strings."""
        resolved_os = os_str or str(matrix.get("os", "unknown")).lower()
        family = "unknown"
        if "win" in resolved_os:
            family = "windows"
        elif "ubuntu" in resolved_os or "linux" in resolved_os:
            family = "linux"
        elif "mac" in resolved_os or "darwin" in resolved_os:
            family = "macos"

        ver = python_ver or str(
            matrix.get("python-version")
            or matrix.get("python_version")
            or matrix.get("python")
            or "unknown"
        )

        return cls(
            os=resolved_os,
            os_family=family,
            runtime="python",
            runtime_version=ver,
            matrix_params=matrix,
        )

    def display_name(self) -> str:
        """User-friendly environment label, e.g. 'Windows / Python 3.12'."""
        os_label = self.os_family.capitalize() if self.os_family != "unknown" else self.os
        if self.runtime_version and self.runtime_version != "unknown":
            return f"{os_label} / Python {self.runtime_version}"
        return os_label


class FailureItem(BaseModel):
    """Structured representation of an individual failure or diagnostic finding."""

    id: str = Field(..., description="Unique deterministic failure identifier")
    provider: str = Field(default="github", description="CI provider origin, e.g. github, gitlab, local")
    workflow: str = Field(default="", description="Workflow name or file")
    run_id: str = Field(default="", description="Workflow run ID")
    job: str = Field(..., description="Failing job name")
    step: str = Field(..., description="Step name where failure occurred")
    environment: EnvironmentInfo = Field(default_factory=EnvironmentInfo)
    category: FailureCategory = FailureCategory.UNKNOWN
    severity: Severity = Severity.ERROR
    status: str = Field(default="failed", description="Step conclusion, e.g. failure, cancelled")
    message: str = Field(..., description="Concise error message or summary")
    raw_evidence: str = Field(default="", description="Original raw snippet or trace")
    normalized_evidence: str = Field(default="", description="Sanitized, path-neutral, secret-redacted evidence")
    fingerprint: str = Field(default="", description="Deterministic hash/token for deduplication")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )
    related_failures: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    blocking: bool = Field(default=True, description="True if this failure halts workflow success")


class CorrelationPattern(BaseModel):
    """Cross-matrix and multi-job failure correlation discovery."""

    pattern_type: str = Field(
        ...,
        description="e.g. OS_SPECIFIC, RUNTIME_SPECIFIC, STEP_SPECIFIC, SAME_ERROR_SIGNATURE, TRANSIENT",
    )
    description: str
    affected_environments: List[str] = Field(default_factory=list)
    unaffected_environments: List[str] = Field(default_factory=list)
    failure_ids: List[str] = Field(default_factory=list)
    shared_signature: Optional[str] = None
    confidence: float = 1.0


class RootCauseHypothesis(BaseModel):
    """Evaluated root cause assessment with verifiable evidence links."""

    status: RootCauseStatus = RootCauseStatus.UNKNOWN
    candidate_cause: str = ""
    supporting_evidence: List[str] = Field(default_factory=list)
    required_additional_evidence: List[str] = Field(default_factory=list)
    affected_component: Optional[str] = None
    confidence: float = 0.0


class EvidenceGateDecision(BaseModel):
    """Deterministic barrier guarding Developer Agent from guessing on incomplete data."""

    can_proceed_to_developer: bool = False
    status: Literal["PASSED", "BLOCKED"] = "BLOCKED"
    reason: str = ""
    required_evidence: List[str] = Field(default_factory=list)
    actionable_failures: List[FailureItem] = Field(default_factory=list)


class CIDiagnosticReport(BaseModel):
    """Publication-grade, structured CI diagnostic report contract."""

    run_id: str
    workflow_name: str
    status: str
    jobs_total: int = 0
    jobs_passed: int = 0
    jobs_failed: int = 0
    failures: List[FailureItem] = Field(default_factory=list)
    patterns: List[CorrelationPattern] = Field(default_factory=list)
    root_cause: RootCauseHypothesis = Field(default_factory=RootCauseHypothesis)
    gate_decision: EvidenceGateDecision = Field(default_factory=EvidenceGateDecision)
    next_actions: List[str] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )

    def to_markdown(self) -> str:
        """Render human-readable diagnostic report adhering to specification format."""
        lines = [
            "CI DIAGNOSTIC REPORT",
            "",
            f"Run:\n{self.run_id}",
            "",
            f"Status:\n{self.status.upper()}",
            "",
            f"Jobs:\n{self.jobs_total}",
            "",
            f"Passed:\n{self.jobs_passed}",
            "",
            f"Failed:\n{self.jobs_failed}",
            "",
            "",
            "FAILURES",
            "",
        ]

        if not self.failures:
            lines.append("No active failures recorded.\n")
        else:
            for idx, f in enumerate(self.failures, 1):
                lines.extend([
                    f"[{idx}]",
                    "Category:",
                    f"{f.category.value}",
                    "",
                    "Environment:",
                    f"{f.environment.display_name()}",
                    "",
                    "Evidence:",
                    f"{f.message}",
                    "",
                    "Blocking:",
                    f"{'Yes' if f.blocking else 'No'}",
                    "",
                    "",
                ])

        lines.extend([
            "PATTERNS",
            "",
        ])
        if self.patterns:
            for p in self.patterns:
                lines.append(f"{p.description}\n")
                if p.affected_environments:
                    lines.append(f"Affected:\n{', '.join(p.affected_environments)}\n")
                if p.unaffected_environments:
                    lines.append(f"Unaffected:\n{', '.join(p.unaffected_environments)}\n")
        else:
            lines.append("No cross-matrix patterns identified.\n")

        lines.extend([
            "",
            "ROOT CAUSE",
            "",
            "Status:",
            f"{self.root_cause.status.value}",
            "",
        ])
        if self.root_cause.candidate_cause:
            lines.extend([
                "Candidate Cause:",
                f"{self.root_cause.candidate_cause}",
                "",
            ])

        lines.extend([
            "",
            "NEXT ACTION",
            "",
        ])
        if self.next_actions:
            lines.append("\n".join(self.next_actions))
        elif self.gate_decision.status == "BLOCKED":
            reqs = ", ".join(self.gate_decision.required_evidence) or "relevant diagnostic details"
            lines.append(f"Retrieve {reqs}.")
        else:
            lines.append("Pass structured diagnostic report to Developer Agent for targeted resolution.")

        return "\n".join(lines).strip()
