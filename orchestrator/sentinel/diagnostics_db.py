"""Persistent SQLite diagnostics database for the Cognitive Sentinel SRE Mesh."""

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.core.constants import SENTINEL_DIAGNOSTICS_DB_PATH
from orchestrator.core.protocols import (
    CognitiveIncident,
    IncidentSeverity,
    InterventionAction,
)


class SentinelDiagnosticsDB:
    """Thread-safe and resilient SQLite storage for Sentinel incidents and telemetry."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or SENTINEL_DIAGNOSTICS_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=15000;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    timestamp REAL,
                    severity TEXT,
                    origin_module TEXT,
                    target_role TEXT,
                    error_signature TEXT,
                    raw_payload TEXT,
                    suggested_action TEXT,
                    auto_healed INTEGER,
                    remedy_description TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cloud_telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    provider TEXT,
                    model TEXT,
                    latency_ms REAL,
                    status_code INTEGER,
                    success INTEGER,
                    error_message TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS drift_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    role TEXT,
                    steps INTEGER,
                    tokens_burned INTEGER,
                    edits_done INTEGER,
                    drift_detected INTEGER,
                    recommendation TEXT
                )
                """
            )
            conn.commit()

    def record_incident(self, incident: CognitiveIncident) -> None:
        """Persist a cognitive incident into the diagnostics database."""
        payload_str = (
            incident.raw_payload
            if isinstance(incident.raw_payload, str)
            else json.dumps(incident.raw_payload, default=str)
        )
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO incidents (
                    incident_id, timestamp, severity, origin_module, target_role,
                    error_signature, raw_payload, suggested_action, auto_healed, remedy_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.incident_id,
                    incident.timestamp_epoch or time.time(),
                    incident.severity.value
                    if isinstance(incident.severity, IncidentSeverity)
                    else str(incident.severity),
                    incident.origin_module,
                    incident.target_role,
                    incident.error_signature,
                    payload_str,
                    incident.suggested_action.value
                    if isinstance(incident.suggested_action, InterventionAction)
                    else str(incident.suggested_action),
                    1 if incident.auto_healed else 0,
                    incident.remedy_description,
                ),
            )
            conn.commit()

    def record_cloud_call(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        success: bool,
        status_code: Optional[int] = None,
        error_message: str = "",
    ) -> None:
        """Persist cloud telemetry call result."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cloud_telemetry (
                    timestamp, provider, model, latency_ms, status_code, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    provider,
                    model,
                    latency_ms,
                    status_code or 0,
                    1 if success else 0,
                    error_message,
                ),
            )
            conn.commit()

    def record_drift_check(
        self,
        role: str,
        steps: int,
        tokens_burned: int,
        edits_done: int,
        drift_detected: bool,
        recommendation: str = "",
    ) -> None:
        """Persist drift analysis state."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO drift_records (
                    timestamp, role, steps, tokens_burned, edits_done, drift_detected, recommendation
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    role,
                    steps,
                    tokens_burned,
                    edits_done,
                    1 if drift_detected else 0,
                    recommendation,
                ),
            )
            conn.commit()

    def get_incident_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent incidents."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM incidents ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate total incidents and healing success rate."""
        with self._get_connection() as conn:
            total_incidents = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[
                0
            ]
            auto_healed_count = conn.execute(
                "SELECT COUNT(*) FROM incidents WHERE auto_healed = 1"
            ).fetchone()[0]
            total_cloud_calls = conn.execute(
                "SELECT COUNT(*) FROM cloud_telemetry"
            ).fetchone()[0]
            failed_cloud_calls = conn.execute(
                "SELECT COUNT(*) FROM cloud_telemetry WHERE success = 0"
            ).fetchone()[0]

            return {
                "total_incidents": total_incidents,
                "auto_healed_count": auto_healed_count,
                "healing_rate": (auto_healed_count / total_incidents)
                if total_incidents > 0
                else 1.0,
                "total_cloud_calls": total_cloud_calls,
                "failed_cloud_calls": failed_cloud_calls,
            }
