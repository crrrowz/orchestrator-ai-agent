"""Rollback & Health Verification Harness for ORAGAI Strangler Fig Migration.

Module: orchestrator.pipeline.migration_guard
Specification: docs/plans/P12_STRANGLER_FIG_MIGRATION_AND_SAFE_ROLLOUT_PLAN.md
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger("orchestrator.pipeline.migration_guard")

DEFAULT_ROUTING_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "migration_routing.json"
)


class ExecutionPlane(str, Enum):
    """Active execution plane for autonomous orchestrator pipelines."""

    MODERN_GUARDED_FSM = "MODERN_GUARDED_FSM"
    LEGACY_FALLBACK = "LEGACY_FALLBACK"


class CircuitBreakerStatus(str, Enum):
    """Operational state of the migration safety circuit breaker."""

    CLOSED = "CLOSED"  # Normal: traffic allowed to target modern plane
    OPEN = "OPEN"  # Tripped: all traffic routed to legacy fallback
    HALF_OPEN = "HALF_OPEN"  # Probing: testing small canary sample


class MigrationRoutingConfig(BaseModel):
    """Strongly typed dynamic runtime traffic routing configuration."""

    use_guarded_fsm: bool = True
    use_clean_sdk_bridge: bool = True
    use_hardened_sandbox: bool = True
    use_ast_virtualizer: bool = True
    use_adaptive_governance: bool = True
    use_context_handoff_mesh: bool = True
    use_deep_inspection_engine: bool = True
    use_stagnation_recovery_engine: bool = True
    use_benchmark_engine: bool = True
    strangler_active: bool = True
    migration_phase: str = "PHASE_4_CANARY"
    canary_percentage: int = Field(default=100, ge=0, le=100)
    fallback_to_legacy_on_error: bool = True
    circuit_breaker_error_threshold: int = Field(default=3, ge=1)
    circuit_breaker_max_fcr: float = Field(default=0.000, ge=0.0, le=1.0)
    circuit_breaker_cooldown_seconds: float = Field(default=60.0, ge=0.0)


class PlaneTelemetryRecord(BaseModel):
    """Captured telemetry record for single pipeline plane execution."""

    timestamp: float = Field(default_factory=time.time)
    task_id: str = ""
    mode: str = "dev-test"
    plane: ExecutionPlane
    success: bool
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    fallback_triggered: bool = False
    catastrophic_failure: bool = False


class MigrationGuard:
    """Runtime health verification, feature flag routing, circuit breaker, and rollback harness."""

    _instance: Optional[MigrationGuard] = None

    def __init__(
        self,
        config_path: Optional[Path] = None,
        auto_reload: bool = True,
    ) -> None:
        self.config_path = config_path or DEFAULT_ROUTING_CONFIG_PATH
        self.auto_reload = auto_reload
        self._last_mtime: float = 0.0
        self._manual_override: bool = False
        self.config = self.load_config()
        self.circuit_status = CircuitBreakerStatus.CLOSED
        self.consecutive_errors: int = 0
        self.telemetry_records: List[PlaneTelemetryRecord] = []
        self._circuit_trip_reason: Optional[str] = None
        self._circuit_tripped_at: Optional[float] = None

    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> MigrationGuard:
        """Singleton accessor for global migration guard."""
        if cls._instance is None:
            cls._instance = cls(config_path=config_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset global singleton instance for test isolation and clean restart."""
        cls._instance = None

    def reset(self) -> None:
        """Reset in-memory circuit breaker and telemetry state."""
        self.circuit_status = CircuitBreakerStatus.CLOSED
        self.consecutive_errors = 0
        self._circuit_trip_reason = None
        self._circuit_tripped_at = None
        self.telemetry_records.clear()

    def load_config(self) -> MigrationRoutingConfig:
        """Load configuration from disk or return default model."""
        if self.config_path.exists():
            try:
                self._last_mtime = self.config_path.stat().st_mtime
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                return MigrationRoutingConfig(**data)
            except Exception as e:
                logger.warning(
                    "Failed to load migration routing config from %s: %s. Using defaults.",
                    self.config_path,
                    e,
                )
        return MigrationRoutingConfig()

    def reload(self) -> MigrationRoutingConfig:
        """Force reload routing configuration from disk."""
        self.config = self.load_config()
        self._manual_override = False
        return self.config

    def update_config(
        self, overrides: Dict[str, Any], persist: bool = False
    ) -> MigrationRoutingConfig:
        """Apply dynamic configuration overrides in memory or persist to disk."""
        curr_dict = self.config.model_dump()
        curr_dict.update(overrides)
        self.config = MigrationRoutingConfig(**curr_dict)
        self._manual_override = not persist
        if persist:
            try:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                self.config_path.write_text(
                    json.dumps(self.config.model_dump(), indent=2),
                    encoding="utf-8",
                )
                self._last_mtime = self.config_path.stat().st_mtime
            except Exception as e:
                logger.error("Failed to persist migration routing config: %s", e)
        return self.config

    def should_route_to_modern(
        self,
        mode: str,
        task: str = "",
        workspace: Optional[Path] = None,
    ) -> bool:
        """Determine whether request executes on Modern Guarded FSM or Legacy Fallback."""
        if self.auto_reload and not self._manual_override and self.config_path.exists():
            try:
                mtime = self.config_path.stat().st_mtime
                if mtime > self._last_mtime:
                    self.reload()
            except Exception:
                pass

        # 1. Check Circuit Breaker
        if self.circuit_status == CircuitBreakerStatus.OPEN:
            cooldown = getattr(self.config, "circuit_breaker_cooldown_seconds", 60.0)
            if self._circuit_tripped_at and (time.time() - self._circuit_tripped_at >= cooldown):
                logger.info(
                    "Circuit breaker cooldown (%.1fs) expired. Transitioning OPEN -> HALF_OPEN for probe canary.",
                    cooldown,
                )
                self.circuit_status = CircuitBreakerStatus.HALF_OPEN
            else:
                logger.warning(
                    "Circuit breaker is OPEN (Reason: %s). Forcing LEGACY_FALLBACK route.",
                    self._circuit_trip_reason,
                )
                return False

        # 2. Check Global Flags
        if not self.config.strangler_active:
            return False
        if not self.config.use_guarded_fsm:
            return False

        # 3. Check Canary Percentages
        if self.config.canary_percentage >= 100:
            return True
        if self.config.canary_percentage <= 0:
            return False

        # 4. Deterministic Canary Bucket Calculation (0..99)
        ws_str = str(workspace.resolve()) if workspace else ""
        hash_seed = f"{mode}:{task}:{ws_str}".encode("utf-8")
        bucket = int(hashlib.sha256(hash_seed).hexdigest()[:8], 16) % 100
        return bucket < self.config.canary_percentage

    def get_active_plane(
        self,
        mode: str = "dev-test",
        task: str = "",
        workspace: Optional[Path] = None,
    ) -> ExecutionPlane:
        """Return the active execution plane for the specified task context."""
        if self.should_route_to_modern(mode=mode, task=task, workspace=workspace):
            return ExecutionPlane.MODERN_GUARDED_FSM
        return ExecutionPlane.LEGACY_FALLBACK

    def record_success(
        self,
        plane: ExecutionPlane,
        task_id: str = "",
        mode: str = "dev-test",
        duration_seconds: float = 0.0,
        fallback_triggered: bool = False,
    ) -> None:
        """Record successful execution telemetry and reset consecutive errors."""
        if plane == ExecutionPlane.MODERN_GUARDED_FSM:
            self.consecutive_errors = 0
            if self.circuit_status == CircuitBreakerStatus.HALF_OPEN:
                self.circuit_status = CircuitBreakerStatus.CLOSED
                self._circuit_trip_reason = None
                logger.info("Circuit breaker transitioned HALF_OPEN -> CLOSED on success.")

        rec = PlaneTelemetryRecord(
            task_id=task_id,
            mode=mode,
            plane=plane,
            success=True,
            duration_seconds=duration_seconds,
            fallback_triggered=fallback_triggered,
        )
        self.telemetry_records.append(rec)
        logger.info(
            "[MIGRATION TELEMETRY] Plane=%s Mode=%s Duration=%.2fs Success=True",
            plane.value,
            mode,
            duration_seconds,
        )

    def record_failure(
        self,
        plane: ExecutionPlane,
        error: Union[str, Exception],
        task_id: str = "",
        mode: str = "dev-test",
        catastrophic: bool = False,
        duration_seconds: float = 0.0,
        fallback_triggered: bool = False,
    ) -> bool:
        """Record failed execution telemetry and evaluate circuit breaker trip conditions."""
        err_msg = str(error)
        tripped = False

        if plane == ExecutionPlane.MODERN_GUARDED_FSM:
            self.consecutive_errors += 1
            if (
                catastrophic
                or self.consecutive_errors >= self.config.circuit_breaker_error_threshold
            ):
                reason = (
                    f"Catastrophic failure: {err_msg}"
                    if catastrophic
                    else f"Exceeded consecutive error threshold ({self.consecutive_errors}/{self.config.circuit_breaker_error_threshold})"
                )
                self.trip_circuit_breaker(reason)
                tripped = True

        rec = PlaneTelemetryRecord(
            task_id=task_id,
            mode=mode,
            plane=plane,
            success=False,
            duration_seconds=duration_seconds,
            error_message=err_msg,
            fallback_triggered=fallback_triggered,
            catastrophic_failure=catastrophic,
        )
        self.telemetry_records.append(rec)
        logger.error(
            "[MIGRATION TELEMETRY] Plane=%s Mode=%s Duration=%.2fs Success=False Error=%s",
            plane.value,
            mode,
            duration_seconds,
            err_msg,
        )
        return tripped

    def trip_circuit_breaker(self, reason: str = "Manual or Invariant Trip") -> None:
        """Instantly trip circuit breaker to OPEN state, diverting all traffic to legacy."""
        self.circuit_status = CircuitBreakerStatus.OPEN
        self._circuit_trip_reason = reason
        self._circuit_tripped_at = time.time()
        logger.critical(
            "CIRCUIT BREAKER TRIPPED -> OPEN. Reason: %s. All routes forced to LEGACY.",
            reason,
        )

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker to CLOSED state."""
        self.circuit_status = CircuitBreakerStatus.CLOSED
        self.consecutive_errors = 0
        self._circuit_trip_reason = None
        self._circuit_tripped_at = None
        logger.info("Circuit breaker manually reset to CLOSED.")

    def execute_instant_rollback(
        self,
        reason: str = "Emergency Rollback",
        persist: bool = True,
    ) -> None:
        """Instantly divert all traffic to legacy and update configuration."""
        self.trip_circuit_breaker(reason=reason)
        self.update_config(
            {"canary_percentage": 0, "use_guarded_fsm": False},
            persist=persist,
        )
        logger.critical("[ROLLBACK] Instant rollback executed. Reason: %s", reason)

    def verify_runtime_health(self, workspace: Optional[Path] = None) -> Dict[str, Any]:
        """Perform comprehensive runtime health verification across configuration, circuit, and syntax."""
        ws = (workspace or Path.cwd()).resolve()
        syntax_ok = True
        syntax_err = ""
        try:
            from orchestrator.guards.preflight import PreFlightGuard

            syntax_ok, syntax_err = PreFlightGuard.check_syntax(ws, auto_heal=False)
        except Exception as e:
            syntax_ok = False
            syntax_err = str(e)

        return {
            "healthy": syntax_ok and self.circuit_status != CircuitBreakerStatus.OPEN,
            "circuit_status": self.circuit_status.value,
            "trip_reason": self._circuit_trip_reason,
            "consecutive_errors": self.consecutive_errors,
            "strangler_active": self.config.strangler_active,
            "use_guarded_fsm": self.config.use_guarded_fsm,
            "canary_percentage": self.config.canary_percentage,
            "syntax_clean": syntax_ok,
            "syntax_error": syntax_err if not syntax_ok else None,
            "total_telemetry_events": len(self.telemetry_records),
        }

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Summarize telemetry counts by plane."""
        modern_runs = [
            r for r in self.telemetry_records if r.plane == ExecutionPlane.MODERN_GUARDED_FSM
        ]
        legacy_runs = [
            r for r in self.telemetry_records if r.plane == ExecutionPlane.LEGACY_FALLBACK
        ]
        return {
            "total_events": len(self.telemetry_records),
            "circuit_status": self.circuit_status.value,
            "modern_runs": len(modern_runs),
            "modern_successes": sum(1 for r in modern_runs if r.success),
            "modern_failures": sum(1 for r in modern_runs if not r.success),
            "legacy_runs": len(legacy_runs),
            "legacy_successes": sum(1 for r in legacy_runs if r.success),
            "legacy_failures": sum(1 for r in legacy_runs if not r.success),
            "fallbacks_triggered": sum(1 for r in self.telemetry_records if r.fallback_triggered),
        }
