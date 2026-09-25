"""Master Unified Deep Inspection & Self-Evolution Engine Façade (P7)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import List, Optional, Set, Tuple

from orchestrator.analysis.audit.cluster import ClusterPartitionEngine
from orchestrator.analysis.audit.db import SentinelDiagnosticsDB
from orchestrator.analysis.audit.fixer import AuditFixOrchestrator
from orchestrator.analysis.audit.models import (
    CodebaseHealthMetrics,
    FindingCategory,
    FindingSeverity,
    RemediationStatus,
    VerifiedAuditFinding,
)
from orchestrator.analysis.audit.scanner import StaticAnalysisScanner
from orchestrator.analysis.audit.validator import FindingValidator


class DeepInspectionEngine:
    """Master facade orchestrating static sweeps, cluster analysis, CHI calculation, and report generation."""

    EXCLUDE_DIRS = {
        ".venv", "venv", ".git", "__pycache__", "build", "dist",
        ".pytest_cache", ".ruff_cache", "site-packages", "node_modules"
    }

    def __init__(self, workspace_path: Path, db_path: Optional[Path] = None):
        self.workspace_path = workspace_path.resolve()
        self.scanner = StaticAnalysisScanner(self.workspace_path)
        self.cluster_engine = ClusterPartitionEngine(self.workspace_path)
        self.fix_engine = AuditFixOrchestrator(self.workspace_path)
        
        actual_db_path = db_path or (self.workspace_path / ".oragai" / "sentinel_diagnostics.db")
        self.db = SentinelDiagnosticsDB(actual_db_path)

    @classmethod
    def compute_chi(
        cls,
        findings: List[VerifiedAuditFinding],
        circular_cycles: int = 0,
        line_coverage_ratio: float = 0.85,
    ) -> Tuple[float, str]:
        """Compute the Codebase Health Index (CHI) and health rating classification."""
        crit = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
        high = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
        med = sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM)
        low = sum(1 for f in findings if f.severity == FindingSeverity.LOW)
        opt = sum(1 for f in findings if f.severity == FindingSeverity.OPTIMIZATION)

        penalty = (
            crit * 30.0
            + high * 15.0
            + med * 5.0
            + low * 1.0
            + opt * 0.5
            + circular_cycles * 20.0
        )

        chi = max(0.0, min(100.0, 100.0 - penalty))

        if chi >= 90.0:
            rating = "EXEMPLARY"
        elif chi >= 75.0:
            rating = "HEALTHY"
        elif chi >= 50.0:
            rating = "DEGRADED"
        elif chi >= 25.0:
            rating = "FRAGILE"
        else:
            rating = "CRITICAL"

        return chi, rating

    def execute_static_sweep(
        self,
        record_db: bool = True,
        generate_report_files: bool = False,
    ) -> Tuple[List[VerifiedAuditFinding], CodebaseHealthMetrics]:
        """Execute Phase 1 zero-token static audit and compute codebase health metrics."""
        t_start = time.perf_counter()
        raw_findings = self.scanner.scan_workspace()

        # Validate findings through the multi-layer FindingValidator gate
        verified_findings: List[VerifiedAuditFinding] = []
        seen_fingerprints: Set[str] = set()

        for f in raw_findings:
            is_valid, _ = FindingValidator.validate(f, self.workspace_path)
            if is_valid:
                fp = f.sha256_fingerprint or f.compute_fingerprint()
                if fp not in seen_fingerprints:
                    f.sha256_fingerprint = fp
                    verified_findings.append(f)
                    seen_fingerprints.add(fp)

        # Count total Python files and LOC
        total_files = 0
        total_loc = 0
        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            for file in files:
                if not file.endswith(".py"):
                    continue
                full = Path(root) / file
                total_files += 1
                try:
                    total_loc += len(full.read_text(encoding="utf-8", errors="replace").splitlines())
                except Exception:
                    pass

        crit = sum(1 for f in verified_findings if f.severity == FindingSeverity.CRITICAL)
        high = sum(1 for f in verified_findings if f.severity == FindingSeverity.HIGH)
        med = sum(1 for f in verified_findings if f.severity == FindingSeverity.MEDIUM)
        low = sum(1 for f in verified_findings if f.severity == FindingSeverity.LOW)
        cycles = sum(1 for f in verified_findings if "ARCH-CYCLE" in f.finding_id)

        chi, rating = self.compute_chi(verified_findings, circular_cycles=cycles)

        metrics = CodebaseHealthMetrics(
            total_files=total_files,
            total_loc=total_loc,
            clean_static=len(verified_findings) == 0,
            chi_score=chi,
            health_rating=rating,
            critical_findings_count=crit,
            high_findings_count=high,
            medium_findings_count=med,
            low_findings_count=low,
            circular_dependency_cycles=cycles,
            mean_distance_main_sequence=0.0,
            line_coverage_ratio=0.85,
        )

        duration = time.perf_counter() - t_start
        run_id = f"RUN-{int(time.time())}"

        if record_db:
            try:
                self.db.record_run(run_id, "AUDIT", metrics, verified_findings, duration)
            except Exception:
                pass

        if generate_report_files:
            self.generate_reports(verified_findings, metrics)

        return verified_findings, metrics

    def generate_reports(
        self,
        findings: List[VerifiedAuditFinding],
        metrics: CodebaseHealthMetrics,
        output_dir: Optional[Path] = None,
    ) -> Tuple[Path, Path]:
        """Generate docs/audit_findings.json and docs/AUDIT_REPORT.md."""
        target_dir = output_dir or (self.workspace_path / "docs")
        target_dir.mkdir(parents=True, exist_ok=True)

        json_path = target_dir / "audit_findings.json"
        md_path = target_dir / "AUDIT_REPORT.md"

        # 1. audit_findings.json
        findings_payload = {
            "health_metrics": {
                "total_files": metrics.total_files,
                "total_loc": metrics.total_loc,
                "chi_score": metrics.chi_score,
                "health_rating": metrics.health_rating,
                "clean_static": metrics.clean_static,
                "critical": metrics.critical_findings_count,
                "high": metrics.high_findings_count,
                "medium": metrics.medium_findings_count,
                "low": metrics.low_findings_count,
                "circular_cycles": metrics.circular_dependency_cycles,
            },
            "findings": [f.model_dump() for f in findings],
        }
        json_path.write_text(json.dumps(findings_payload, indent=2), encoding="utf-8")

        # 2. AUDIT_REPORT.md
        md_content = [
            "# ORAGAI Codebase Deep Inspection & Audit Report",
            "",
            "## Executive Summary",
            f"- **Codebase Health Index (CHI):** {metrics.chi_score:.1f} / 100.0",
            f"- **Health Rating:** **{metrics.health_rating}**",
            f"- **Total Files Scanned:** {metrics.total_files}",
            f"- **Total Lines of Code:** {metrics.total_loc:,}",
            f"- **Total Verified Findings:** {len(findings)}",
            "",
            "### Defect Severity Distribution",
            f"- **CRITICAL:** {metrics.critical_findings_count}",
            f"- **HIGH:** {metrics.high_findings_count}",
            f"- **MEDIUM:** {metrics.medium_findings_count}",
            f"- **LOW:** {metrics.low_findings_count}",
            f"- **Circular Cycles:** {metrics.circular_dependency_cycles}",
            "",
            "## Verified Findings Detail",
            "",
        ]

        if not findings:
            md_content.append("No active defects detected. Codebase static analysis is 100% clean.")
        else:
            md_content.append("| ID | Category | Severity | Location | Defect Summary | Proposed Remediation |")
            md_content.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for f in findings:
                loc = f"`{f.file_path}:{f.line_start}`"
                clean_prob = f.problem_statement.replace("|", "\\|")
                clean_fix = f.remediation_proposal.replace("|", "\\|")
                md_content.append(
                    f"| **{f.finding_id}** | {f.category.value} | {f.severity.value} | {loc} | {clean_prob} | {clean_fix} |"
                )

        md_content.append("")
        md_path.write_text("\n".join(md_content), encoding="utf-8")

        return json_path, md_path
