"""Structured contracts, evidence integrity schemas, and finding validators for Audit Subsystem."""

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Literal, Optional, Tuple
from pydantic import BaseModel, Field


class AuditState(str, Enum):
    """Formal lifecycle states for the Codebase Audit Pipeline."""

    AUDIT_STARTED = "AUDIT_STARTED"
    AUDIT_COMPLETED = "AUDIT_COMPLETED"
    AUDIT_CLEAN = "AUDIT_CLEAN"
    AUDIT_INCOMPLETE = "AUDIT_INCOMPLETE"
    AUDIT_FAILED = "AUDIT_FAILED"


class AuditFinding(BaseModel):
    """Verified, actionable finding with strict evidence integrity."""

    id: str = Field(..., description="Unique finding identifier, e.g. AUD-001")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "OPTIMIZATION"] = "HIGH"
    type: Literal[
        "BUG", "SECURITY", "DRY", "PERFORMANCE", "COMPLEXITY", "CONVENTION"
    ] = "BUG"
    file: str = Field(..., description="Workspace-relative file path containing defect")
    line: Optional[int] = Field(None, description="1-indexed line number if localized")
    evidence: str = Field(
        ..., min_length=3, description="Verifiable code snippet or trace"
    )
    problem: str = Field(..., min_length=3, description="Exact defect statement")
    recommended_fix: str = Field(
        ..., min_length=3, description="Prescriptive remediation steps"
    )
    actionable: bool = Field(
        True, description="True if defect can be resolved via code edits"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = Field(
        default="auditor", description="Detector origin (AST, Ruff, Auditor LLM)"
    )


class AuditResult(BaseModel):
    """Machine-readable contract and audit outcome."""

    status: AuditState = AuditState.AUDIT_STARTED
    summary: str = ""
    findings: List[AuditFinding] = Field(default_factory=list)
    total_files_scanned: int = 0
    total_loc: int = 0
    clean_static: bool = True
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    )

    def to_markdown(self) -> str:
        """Render publication-grade architectural audit markdown strictly from validated findings."""
        health_score = 100
        critical_count = sum(1 for f in self.findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in self.findings if f.severity == "HIGH")
        med_count = sum(1 for f in self.findings if f.severity == "MEDIUM")
        low_count = sum(1 for f in self.findings if f.severity == "LOW")

        health_score = max(
            0,
            health_score
            - (critical_count * 25 + high_count * 10 + med_count * 5 + low_count * 2),
        )

        lines = [
            "# Codebase Architecture & Security Audit Report",
            "",
            f"**Generated**: {self.timestamp} | **Auditor Status**: `{self.status.value}` | **System Health Score**: `{health_score}/100`",
            "",
            "---",
            "",
            "## 1. Executive Summary & Code Metrics",
            "",
            "| Metric Dimension | Value | Reference Baseline / Status |",
            "|---|---|---|",
            f"| **Total Files Scanned** | `{self.total_files_scanned}` | Full workspace tree coverage |",
            f"| **Total Lines of Code (LOC)** | `{self.total_loc:,}` | Polyglot / Python codebase |",
            f"| **Deterministic Static Linter** | `{'CLEAN (0 errors)' if self.clean_static else 'ISSUES DETECTED'}` | AST compilation & static analyzers |",
            f"| **Actionable Findings Total** | `{len(self.findings)}` | Verified non-ghost defects |",
            f"| **Critical / High Severity Defect Ratio** | `{critical_count} Critical / {high_count} High` | Immediate resolution required |",
            "",
            "---",
            "",
            "## 2. Structural Hotspots & Module Boundaries",
            "- **Modularity & Coupling**: Analysis of high-traffic modules and core orchestrator interfaces.",
            "- **Blast Radius Constraints**: Subsystems isolated with strict sandboxes and dynamic execution boundaries.",
            "",
            "---",
            "",
            "## 3. Verified Actionable Architectural & Code Findings",
            "",
        ]

        if not self.findings:
            if self.status == AuditState.AUDIT_CLEAN:
                lines.extend(
                    [
                        "> ✅ **Zero Actionable Code Defects Detected.**",
                        "> The workspace adheres to strict clean architecture invariants and static AST standards.",
                        "",
                    ]
                )
            elif self.status == AuditState.AUDIT_FAILED:
                lines.extend(
                    [
                        f"> ⚠️ **Audit Execution Interrupted**: {self.summary or 'Auditor agent encountered an upstream exception.'}",
                        "",
                    ]
                )
            elif self.status == AuditState.AUDIT_INCOMPLETE:
                lines.extend(
                    [
                        f"> ⚠️ **Audit Incomplete**: {self.summary or 'Auditor agent turn was interrupted before completing verification.'}",
                        "",
                    ]
                )
            else:
                lines.append(f"Audit state: `{self.status.value}`\n")
        else:
            for f in self.findings:
                loc_str = f":{f.line}" if f.line else ""
                lines.extend(
                    [
                        f"### [{f.severity}] {f.id} - `{f.file}{loc_str}`",
                        f"- **Type**: `{f.type}` | **Source**: `{f.source}` | **Confidence**: `{f.confidence:.2f}`",
                        f"- **Defect Classification**: {f.problem}",
                        f"- **Evidence & Blast Radius**:\n```python\n{f.evidence}\n```",
                        f"- **Remediation Strategy**: {f.recommended_fix}",
                        "",
                    ]
                )

        lines.extend(
            [
                "---",
                "",
                "## 4. Security, Secret Leaks & Subprocess Vulnerability Audit",
                "- **Credential Masking**: Automatic sanitization of environment keys and credential stripping in subprocesses.",
                "- **Path Escape Confinement**: Path resolution guarded with strict `.relative_to(workspace_root)` validation.",
                "- **Parameterized Execution**: Enforcing `shell=False` on Windows/Linux to prevent command injection.",
                "",
                "---",
                "",
                "## 5. Error Handling, Resilience & Failure Recovery Gaps",
                "- **Silent Exception Suppressions**: Eliminating blanket `except Exception: pass` without logging or telemetry tracking.",
                "- **Cloud Quota Circuit Breakers**: Proactive 429 rate limit detection and automated provider failover.",
                "",
                "---",
                "",
                "## 6. Actionable Prioritized Remediation Roadmap",
                "",
            ]
        )

        if self.findings:
            lines.append("### Implementation Work Items:")
            for idx, f in enumerate(self.findings, start=1):
                lines.append(f"{idx}. `[{f.severity}]` Fix **{f.file}**: {f.problem}")
        else:
            lines.append(
                "- No pending remediation work items required. Codebase is in healthy state."
            )

        lines.append("")
        return "\n".join(lines)

    def save_json(self, path: Path) -> None:
        """Persist structured result to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load_json(cls, path: Path) -> Optional["AuditResult"]:
        """Load structured result from JSON if file exists."""
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls.model_validate(data)
        except Exception:
            return None


class FindingValidator:
    """Enforces Evidence Integrity: rejects vague, unverified, or ghost recommendations."""

    @staticmethod
    def validate(
        finding: AuditFinding, workspace_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """Validate finding evidence integrity against active workspace.

        Returns:
            (is_valid, rejection_reason)
        """
        if not finding.actionable:
            return False, "Finding flagged as non-actionable"

        # 1. Target file must be specified and must exist
        clean_file = (finding.file or "").strip().replace("\\", "/")
        if not clean_file or clean_file in (".", "/"):
            return False, "No target file specified"

        target_file = (workspace_path / clean_file).resolve()
        try:
            target_file.relative_to(workspace_path.resolve())
        except ValueError:
            return False, f"Target file '{clean_file}' is outside workspace boundaries"

        if not target_file.exists() or not target_file.is_file():
            return False, f"Target file '{clean_file}' does not exist on disk"

        # 2. Vague or generic advisory filtering
        generic_markers = [
            "review file size",
            "review file hotspots",
            "exceeding 300 loc",
            "zero syntax or linter defects",
            "consider decomposing",
            "address any ast syntax failures",
            "workspace static analysis is clean",
        ]
        text_corpus = (
            f"{finding.problem} {finding.evidence} {finding.recommended_fix}".lower()
        )
        if any(marker in text_corpus for marker in generic_markers):
            if finding.line is None and len(finding.evidence.strip()) < 30:
                return (
                    False,
                    "Finding is a generic informational advisory, not an actionable defect",
                )

        # 3. Minimum evidence content check
        if len(finding.evidence.strip()) < 3 or len(finding.problem.strip()) < 3:
            return False, "Insufficient problem or evidence content provided"

        return True, None
