"""Autonomous Remediation Engine with Atomic Rollback & Quarantine Circuit Breaker (P7)."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from orchestrator.analysis.audit.models import (
    FindingCategory,
    FindingSeverity,
    RemediationStatus,
    VerifiedAuditFinding,
)


class AuditFixOrchestrator:
    """Executes closed-loop remediation of verified audit findings with atomic rollback."""

    CATEGORY_WEIGHTS = {
        FindingCategory.ARCHITECTURE: 0,
        FindingCategory.SECURITY: 1,
        FindingCategory.RELIABILITY: 2,
        FindingCategory.PERFORMANCE: 3,
        FindingCategory.MAINTAINABILITY: 4,
        FindingCategory.CONVENTION: 5,
    }

    SEVERITY_WEIGHTS = {
        FindingSeverity.CRITICAL: 0,
        FindingSeverity.HIGH: 1,
        FindingSeverity.MEDIUM: 2,
        FindingSeverity.LOW: 3,
        FindingSeverity.OPTIMIZATION: 4,
    }

    def __init__(self, workspace_path: Path, max_attempts_per_finding: int = 2):
        self.workspace_path = workspace_path.resolve()
        self.max_attempts = max_attempts_per_finding

    def sort_findings_dag(self, findings: List[VerifiedAuditFinding]) -> List[VerifiedAuditFinding]:
        """Order open findings prioritizing root architectural and security defects."""
        open_findings = [f for f in findings if f.remediation_status == RemediationStatus.OPEN]
        return sorted(
            open_findings,
            key=lambda f: (
                self.CATEGORY_WEIGHTS.get(f.category, 99),
                self.SEVERITY_WEIGHTS.get(f.severity, 99),
            ),
        )

    def verify_preflight_syntax(self, target_rel_path: str) -> Tuple[bool, Optional[str]]:
        """Verify modified file passes AST compilation and syntax checks."""
        clean_path = target_rel_path.strip().replace("\\", "/")
        full_path = self.workspace_path / clean_path
        if not full_path.exists():
            return False, f"Target file '{clean_path}' deleted during remediation."
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            ast.parse(content, filename=clean_path)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Compilation error: {e}"

    def backup_file(self, target_rel_path: str) -> Optional[str]:
        """Capture pre-fix file snapshot for atomic rollback."""
        clean_path = target_rel_path.strip().replace("\\", "/")
        full_path = self.workspace_path / clean_path
        if not full_path.exists():
            return None
        return full_path.read_text(encoding="utf-8", errors="replace")

    def rollback_file(self, target_rel_path: str, backup_content: str) -> None:
        """Atomically revert file to pre-remediation backup."""
        clean_path = target_rel_path.strip().replace("\\", "/")
        full_path = self.workspace_path / clean_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(backup_content, encoding="utf-8")

    def record_attempt(self, finding: VerifiedAuditFinding, success: bool) -> None:
        """Record remediation attempt and apply quarantine circuit breaker if failed."""
        finding.remediation_attempts += 1
        if success:
            finding.remediation_status = RemediationStatus.RESOLVED
        else:
            if finding.remediation_attempts >= self.max_attempts:
                finding.remediation_status = RemediationStatus.QUARANTINED_BLOCKED
            else:
                finding.remediation_status = RemediationStatus.OPEN

    def apply_fix_with_guard(
        self,
        finding: VerifiedAuditFinding,
        patch_fn: Callable[[], bool],
        test_fn: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Execute closed-loop remediation step with preflight syntax guard, test check, and rollback."""
        backup = self.backup_file(finding.file_path)
        if backup is None:
            self.record_attempt(finding, False)
            return False

        finding.remediation_status = RemediationStatus.IN_PROGRESS

        try:
            # 1. Apply patch
            applied = patch_fn()
            if not applied:
                self.rollback_file(finding.file_path, backup)
                self.record_attempt(finding, False)
                return False

            # 2. PreFlight syntax verification
            syntax_ok, _ = self.verify_preflight_syntax(finding.file_path)
            if not syntax_ok:
                self.rollback_file(finding.file_path, backup)
                self.record_attempt(finding, False)
                return False

            # 3. Regression test suite verification (if provided)
            if test_fn is not None:
                tests_passed = test_fn()
                if not tests_passed:
                    self.rollback_file(finding.file_path, backup)
                    self.record_attempt(finding, False)
                    return False

            # Success
            self.record_attempt(finding, True)
            return True

        except Exception:
            self.rollback_file(finding.file_path, backup)
            self.record_attempt(finding, False)
            return False
