"""Sentinel Diagnostics Telemetry Database in SQLite WAL mode (P7)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.analysis.audit.models import CodebaseHealthMetrics, VerifiedAuditFinding


class SentinelDiagnosticsDB:
    """Embedded SQLite WAL database tracking codebase health, audit runs, and remediations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path.resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sentinel_audit_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    profile TEXT NOT NULL,
                    total_files INTEGER NOT NULL,
                    total_loc INTEGER NOT NULL,
                    chi_score REAL NOT NULL,
                    health_rating TEXT NOT NULL,
                    total_findings INTEGER NOT NULL,
                    critical_count INTEGER NOT NULL,
                    high_count INTEGER NOT NULL,
                    medium_count INTEGER NOT NULL,
                    low_count INTEGER NOT NULL,
                    duration_sec REAL NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sentinel_audit_findings (
                    finding_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_start INTEGER NOT NULL,
                    line_end INTEGER NOT NULL,
                    ast_symbol TEXT,
                    problem_statement TEXT NOT NULL,
                    remediation_status TEXT NOT NULL,
                    remediation_attempts INTEGER DEFAULT 0,
                    sha256_fingerprint TEXT NOT NULL,
                    PRIMARY KEY (finding_id, run_id),
                    FOREIGN KEY (run_id) REFERENCES sentinel_audit_runs(run_id)
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sentinel_remediation_log (
                    log_id TEXT PRIMARY KEY,
                    finding_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    attempt_index INTEGER NOT NULL,
                    preflight_syntax_passed INTEGER NOT NULL,
                    regression_tests_passed INTEGER NOT NULL,
                    diff_applied TEXT,
                    outcome TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)

    def record_run(
        self,
        run_id: str,
        profile: str,
        metrics: CodebaseHealthMetrics,
        findings: List[VerifiedAuditFinding],
        duration_sec: float,
    ) -> None:
        """Persist full audit run and associated findings to SQLite."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sentinel_audit_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    now,
                    profile,
                    metrics.total_files,
                    metrics.total_loc,
                    metrics.chi_score,
                    metrics.health_rating,
                    len(findings),
                    metrics.critical_findings_count,
                    metrics.high_findings_count,
                    metrics.medium_findings_count,
                    metrics.low_findings_count,
                    duration_sec,
                ),
            )
            for f in findings:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO sentinel_audit_findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f.finding_id,
                        run_id,
                        f.category.value,
                        f.severity.value,
                        f.source.value,
                        f.file_path,
                        f.line_start,
                        f.line_end,
                        f.ast_symbol,
                        f.problem_statement,
                        f.remediation_status.value,
                        f.remediation_attempts,
                        f.sha256_fingerprint,
                    ),
                )

    def record_remediation_attempt(
        self,
        log_id: str,
        finding_id: str,
        run_id: str,
        attempt_index: int,
        preflight_syntax_passed: bool,
        regression_tests_passed: bool,
        diff_applied: Optional[str],
        outcome: str,
    ) -> None:
        """Record an individual remediation attempt outcome."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sentinel_remediation_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    finding_id,
                    run_id,
                    attempt_index,
                    1 if preflight_syntax_passed else 0,
                    1 if regression_tests_passed else 0,
                    diff_applied or "",
                    outcome,
                    now,
                ),
            )

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve audit run record by run_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM sentinel_audit_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_findings_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all findings associated with a run_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM sentinel_audit_findings WHERE run_id = ?", (run_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_run(self) -> Optional[Dict[str, Any]]:
        """Retrieve the most recent audit run record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM sentinel_audit_runs ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None
