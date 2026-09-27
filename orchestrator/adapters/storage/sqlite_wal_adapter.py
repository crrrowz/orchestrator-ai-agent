"""SQLite WAL Storage Adapter (Sentinel DB Telemetry & Metrics).

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from orchestrator.domain.task_truth import TaskTruthGraph
from orchestrator.domain.evidence import EvidenceReference
from orchestrator.domain.audit_models import VerifiedAuditFinding
from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB


class SQLiteWALStorageAdapter:
    """Outbound storage adapter persisting telemetry, findings, and evidence in SQLite WAL mode."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db = SentinelDiagnosticsDB(db_path)

    def log_turn_telemetry(
        self,
        task_id: str,
        milestone_id: str,
        turn_index: int,
        persona: str,
        tokens_used: int,
        cost_usd: float,
        chi_score: float,
    ) -> None:
        pass

    def persist_evidence(self, evidence: EvidenceReference) -> None:
        pass

    def record_audit_finding(
        self, task_id: str, finding: VerifiedAuditFinding
    ) -> None:
        pass
