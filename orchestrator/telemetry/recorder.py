"""Telemetry recorder and Circuit Breaker for runaway loop prevention."""

import hashlib
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from orchestrator.telemetry.schemas import DiagnosticReport, StepIncident, StepMetric


class TelemetryRecorder:
    """Monitors pipeline execution, prevents token burn via circuit breaker, and logs reports."""

    def __init__(
        self,
        task_description: str,
        pipeline_mode: str,
        reports_dir: Optional[Path] = None,
        circuit_breaker_threshold: int = 2,
    ):
        self.task_description = task_description
        self.pipeline_mode = pipeline_mode
        self.report_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.reports_dir = (reports_dir or Path("diagnostics/reports")).resolve()
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.start_time = datetime.utcnow()
        self._start_perf = time.perf_counter()
        
        self.metrics: list[StepMetric] = []
        self.incidents: list[StepIncident] = []
        self.recommendations: list[str] = []
        
        # State tracking for circuit breaker
        self._last_diff_hash: Optional[str] = None
        self._last_error_hash: Optional[str] = None
        self._identical_failure_count: int = 0
        self.circuit_breaker_triggered: bool = False

    def record_step(
        self,
        agent_role: str,
        action_type: str,
        iteration: int,
        duration_seconds: float,
        success: bool,
        diff_text: str = "",
        error_summary: Optional[str] = None,
    ) -> None:
        """Log a completed agent turn or pipeline step."""
        diff_hash = hashlib.sha256(diff_text.encode("utf-8")).hexdigest()[:12] if diff_text else None
        metric = StepMetric(
            agent_role=agent_role,
            action_type=action_type,
            iteration=iteration,
            duration_seconds=round(duration_seconds, 2),
            success=success,
            diff_hash=diff_hash,
            diff_size_bytes=len(diff_text.encode("utf-8")),
            error_summary=error_summary,
        )
        self.metrics.append(metric)

    def record_incident(self, step_name: str, incident_type: str, details: str) -> None:
        """Log a failure or anomaly during execution."""
        incident = StepIncident(
            step_name=step_name,
            incident_type=incident_type,
            details=details,
        )
        self.incidents.append(incident)

    def check_circuit_breaker(self, diff_text: str, error_text: str) -> bool:
        """
        Check if the pipeline is stuck in an identical failure loop.
        Returns True if the circuit breaker tripped and execution should halt immediately.
        """
        curr_diff_hash = hashlib.sha256(diff_text.strip().encode("utf-8")).hexdigest()
        curr_error_hash = hashlib.sha256(error_text.strip().encode("utf-8")).hexdigest()

        if curr_diff_hash == self._last_diff_hash and curr_error_hash == self._last_error_hash:
            self._identical_failure_count += 1
        else:
            self._identical_failure_count = 1

        self._last_diff_hash = curr_diff_hash
        self._last_error_hash = curr_error_hash

        if self._identical_failure_count >= self.circuit_breaker_threshold:
            self.circuit_breaker_triggered = True
            self.record_incident(
                step_name="CircuitBreaker",
                incident_type="circuit_breaker",
                details=(
                    f"Identical code diff and error output detected across {self._identical_failure_count} "
                    "consecutive iterations. Halting execution to prevent token burn."
                ),
            )
            self.recommendations.append(
                "Review Developer skill or prompt: Agent repeated the exact same code modifications without resolving test error."
            )
            return True

        return False

    def finalize(self, completed_successfully: bool) -> DiagnosticReport:
        """Complete the telemetry session, generate report, and save to disk."""
        end_time = datetime.utcnow()
        total_duration = round(time.perf_counter() - self._start_perf, 2)
        total_iterations = max((m.iteration for m in self.metrics), default=1)

        # Generate automatic recommendations
        if not completed_successfully and not self.circuit_breaker_triggered:
            self.recommendations.append("Task did not pass all tests within iteration budget. Consider increasing max_iterations or decomposing task.")

        report = DiagnosticReport(
            report_id=self.report_id,
            task_description=self.task_description,
            pipeline_mode=self.pipeline_mode,
            start_time=self.start_time,
            end_time=end_time,
            total_duration_seconds=total_duration,
            total_iterations=total_iterations,
            completed_successfully=completed_successfully,
            circuit_breaker_triggered=self.circuit_breaker_triggered,
            metrics=self.metrics,
            incidents=self.incidents,
            recommendations=self.recommendations,
        )

        # Write to JSON file
        report_file = self.reports_dir / f"{self.report_id}.json"
        report_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        return report
