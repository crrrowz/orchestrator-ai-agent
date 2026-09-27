"""Outbound Driven Telemetry & Checkpoint Storage Port Protocol.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable
from orchestrator.domain.task_truth import TaskTruthGraph
from orchestrator.domain.evidence import EvidenceReference
from orchestrator.domain.audit_models import VerifiedAuditFinding


@runtime_checkable
class TelemetryStoragePort(Protocol):
    """Outbound port for SQLite WAL persistence of traces, telemetry, and findings."""

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
        ...

    def persist_evidence(self, evidence: EvidenceReference) -> None:
        ...

    def record_audit_finding(self, task_id: str, finding: VerifiedAuditFinding) -> None:
        ...

    def save_checkpoint(self, graph: TaskTruthGraph) -> str:
        ...

    def load_latest_checkpoint(self, task_id: str) -> Optional[TaskTruthGraph]:
        ...
