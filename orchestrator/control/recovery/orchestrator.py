"""Recovery Orchestrator Façade for ORAGAI (P8).

Coordinates:
- SemanticProgressTracker (4-dimensional velocity vector & PER 2.0)
- OscillationDetector (Sliding-window finite sequence autocorrelation)
- AdaptiveCircuitBreaker (4-tier adaptive circuit breaker state machine)
- StrategyMutator (4-tier dynamic strategy mutation directives)
- GitOps Checkpoints and Transactional Rollback handles
- Sentinel SQLite WAL Telemetry Persistence
- Milestone Quarantine Management (docs/quarantined_findings.json)
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from .circuit_breaker import AdaptiveCircuitBreaker
from .models import (
    BreakerState,
    CyclePattern,
    MutationStrategyType,
    ProgressHealth,
    ProgressVelocityMetrics,
    QuarantinedMilestoneRecord,
    RecoveryActionType,
    RecoveryDecision,
    StateFingerprint,
    StrategyMutationDirective,
)
from .mutator import StrategyMutator
from .oscillation import OscillationDetector
from .tracker import SemanticProgressTracker


class RecoveryOrchestrator:
    """
    Unified Recovery Façade coordinating Progress Tracking, Oscillation Detection,
    Adaptive Circuit Breaking, Strategy Mutation, GitOps Rollback, and SQLite WAL Logging.
    """

    def __init__(
        self,
        workspace_path: Path,
        db_path: Optional[Path] = None,
        quarantine_path: Optional[Path] = None,
    ):
        self.workspace_path = workspace_path
        self.tracker = SemanticProgressTracker(workspace_path)
        self.oscillation_detector = OscillationDetector(window_size=5)
        self.circuit_breaker = AdaptiveCircuitBreaker(max_mutation_tiers=4)
        self.mutator = StrategyMutator()
        self.db_path = db_path or (workspace_path / ".oragai" / "sentinel_diagnostics.db")
        self.quarantine_path = quarantine_path or (workspace_path / "docs" / "quarantined_findings.json")
        self._init_sqlite_schema()

    def _init_sqlite_schema(self) -> None:
        """Initialize SQLite WAL schema for recovery diagnostics."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS sentinel_progress_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                v_code REAL NOT NULL,
                v_verif REAL NOT NULL,
                v_evid REAL NOT NULL,
                v_defect REAL NOT NULL,
                per_score REAL NOT NULL,
                health TEXT NOT NULL,
                breaker_state TEXT NOT NULL,
                cycle_pattern TEXT NOT NULL,
                cycle_period INTEGER NOT NULL,
                timestamp REAL NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS sentinel_recovery_events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                mutation_tier INTEGER NOT NULL,
                details TEXT NOT NULL,
                timestamp REAL NOT NULL
            );
            """)
            conn.commit()

    def _compute_state_fingerprint(
        self,
        turn_index: int,
        failed_test_nodes: Dict[str, str],
        open_defect_ids: Set[str],
    ) -> StateFingerprint:
        """Derive deterministic composite state fingerprint for turn."""
        # Canonical representation of workspace AST symbols
        sorted_symbols: List[str] = []
        for file_rel in sorted(self.tracker._last_symbols.keys()):
            for sym in sorted(
                self.tracker._last_symbols[file_rel],
                key=lambda s: (s.symbol_type, s.name, s.body_ast_hash),
            ):
                sorted_symbols.append(f"{file_rel}:{sym.symbol_type}:{sym.name}:{sym.body_ast_hash}")

        ast_hash = hashlib.sha256(";".join(sorted_symbols).encode("utf-8")).hexdigest()
        fail_hash = hashlib.sha256(json.dumps(sorted(failed_test_nodes.keys())).encode("utf-8")).hexdigest()
        def_hash = hashlib.sha256(json.dumps(sorted(list(open_defect_ids))).encode("utf-8")).hexdigest()

        return StateFingerprint(
            turn_index=turn_index,
            ast_composite_hash=ast_hash,
            failing_tests_hash=fail_hash,
            defect_state_hash=def_hash,
        )

    def evaluate_turn_outcome(
        self,
        run_id: str,
        turn_index: int,
        passed_test_nodes: Set[str],
        failed_test_nodes: Dict[str, str],
        satisfied_ac_ids: Set[str],
        open_defect_ids: Set[str],
        tokens_consumed: int,
        active_milestone_id: str,
        checkpoint_ref: Optional[str] = None,
        task_id: str = "default_task",
    ) -> RecoveryDecision:
        """
        Evaluate post-turn outcome, detect oscillations, advance circuit breaker,
        generate mutation/rollback directives, and log telemetry.
        """
        # 1. Compute Progress Metrics
        metrics = self.tracker.record_turn_snapshot(
            turn_index=turn_index,
            passed_test_nodes=passed_test_nodes,
            failed_test_nodes=failed_test_nodes,
            satisfied_ac_ids=satisfied_ac_ids,
            open_defect_ids=open_defect_ids,
            tokens_consumed=tokens_consumed,
        )

        # 2. Compute State Fingerprint & Detect Cycles
        fingerprint = self._compute_state_fingerprint(
            turn_index=turn_index,
            failed_test_nodes=failed_test_nodes,
            open_defect_ids=open_defect_ids,
        )
        cycle_pattern, cycle_period = self.oscillation_detector.register_state(fingerprint)

        # 3. Evaluate Breaker State Transition
        new_breaker_state = self.circuit_breaker.evaluate_state_transition(metrics, cycle_pattern)

        # 4. Formulate Recovery Action & Mutation
        action = RecoveryActionType.CONTINUE_NORMAL
        mutation: Optional[StrategyMutationDirective] = None
        rollback_ref: Optional[str] = None
        explanation = f"Turn {turn_index} evaluated: {metrics.health.value}. Breaker: {new_breaker_state.value}."

        if (metrics.v_verif < -2.0 or metrics.health == ProgressHealth.REGRESSING) and checkpoint_ref:
            action = RecoveryActionType.TRANSACTIONAL_ROLLBACK
            rollback_ref = checkpoint_ref
            explanation += f" Severe regression detected (V_verif={metrics.v_verif}). Emitting atomic rollback directive to {checkpoint_ref}."

        elif new_breaker_state == BreakerState.TRIPPED_ESCALATING:
            action = RecoveryActionType.QUARANTINE_MILESTONE
            explanation += " All strategy mutation tiers exhausted. Quarantining milestone."
            self._persist_quarantined_milestone(
                milestone_id=active_milestone_id,
                task_id=task_id,
                failing_test_nodes=list(failed_test_nodes.keys()),
                diagnostic_summary=explanation,
            )

        elif new_breaker_state == BreakerState.STRATEGY_MUTATING:
            action = RecoveryActionType.INJECT_MUTATION
            mutation = self.mutator.generate_mutation(
                current_tier=self.circuit_breaker.mutation_tier_level,
                failing_tests=failed_test_nodes,
                cycle_pattern=cycle_pattern,
                active_milestone_id=active_milestone_id,
            )
            explanation += f" Triggered Strategy Mutation Tier {mutation.tier_level} ({mutation.mutation_type.value})."

        # 5. Persist snapshot & recovery event to Sentinel SQLite DB
        self._log_telemetry(
            run_id=run_id,
            turn_index=turn_index,
            metrics=metrics,
            breaker_state=new_breaker_state,
            cycle_pattern=cycle_pattern,
            cycle_period=cycle_period,
            action=action,
            mutation=mutation,
        )

        return RecoveryDecision(
            action=action,
            breaker_state=new_breaker_state,
            health=metrics.health,
            detected_cycle=cycle_pattern,
            cycle_period=cycle_period,
            mutation_directive=mutation,
            rollback_checkpoint_ref=rollback_ref,
            explanation=explanation,
        )

    def _persist_quarantined_milestone(
        self,
        milestone_id: str,
        task_id: str,
        failing_test_nodes: List[str],
        diagnostic_summary: str,
    ) -> None:
        """Append record to docs/quarantined_findings.json."""
        try:
            self.quarantine_path.parent.mkdir(parents=True, exist_ok=True)
            existing: List[Dict] = []
            if self.quarantine_path.exists():
                try:
                    existing = json.loads(self.quarantine_path.read_text(encoding="utf-8"))
                except Exception:
                    existing = []

            record = QuarantinedMilestoneRecord(
                milestone_id=milestone_id,
                task_id=task_id,
                quarantine_timestamp=datetime.now(timezone.utc).isoformat(),
                exhausted_mutations=[
                    MutationStrategyType.PROMPT_STEERING.value,
                    MutationStrategyType.TARGET_DECOMPOSITION.value,
                    MutationStrategyType.TOOL_CONSTRICTION.value,
                    MutationStrategyType.MODEL_ELEVATION.value,
                ],
                failing_test_nodes=failing_test_nodes,
                last_ast_diff="",
                diagnostic_summary=diagnostic_summary,
                suggested_human_action="Review quarantined milestone, relax constraints or supply manual fix.",
            )
            existing.append(record.model_dump())
            self.quarantine_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _log_telemetry(
        self,
        run_id: str,
        turn_index: int,
        metrics: ProgressVelocityMetrics,
        breaker_state: BreakerState,
        cycle_pattern: CyclePattern,
        cycle_period: int,
        action: RecoveryActionType,
        mutation: Optional[StrategyMutationDirective],
    ) -> None:
        """Persist snapshot and recovery event into SQLite WAL database."""
        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                snap_id = f"SNAP-{run_id}-{turn_index}-{int(time.time() * 1000)}"
                conn.execute(
                    """
                    INSERT INTO sentinel_progress_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        snap_id,
                        run_id,
                        turn_index,
                        metrics.v_code,
                        metrics.v_verif,
                        metrics.v_evid,
                        metrics.v_defect,
                        metrics.per_score,
                        metrics.health.value,
                        breaker_state.value,
                        cycle_pattern.value,
                        cycle_period,
                        time.time(),
                    ),
                )
                if action != RecoveryActionType.CONTINUE_NORMAL:
                    event_id = f"REC-{run_id}-{turn_index}-{int(time.time() * 1000)}"
                    conn.execute(
                        """
                        INSERT INTO sentinel_recovery_events VALUES (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            event_id,
                            run_id,
                            turn_index,
                            action.value,
                            mutation.tier_level if mutation else 0,
                            json.dumps(
                                {
                                    "action": action.value,
                                    "mutation_type": mutation.mutation_type.value if mutation else None,
                                    "tier_level": mutation.tier_level if mutation else 0,
                                }
                            ),
                            time.time(),
                        ),
                    )
                conn.commit()
        except Exception:
            pass
