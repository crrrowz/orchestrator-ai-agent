"""Telemetry recorder and Circuit Breaker for runaway loop prevention."""

import difflib
import hashlib
import re
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from orchestrator.config import DEFAULT_DIAGNOSTICS_DIR
from orchestrator.control.budget_guard import BudgetGuard
from orchestrator.telemetry.schemas import DiagnosticReport, StepIncident, StepMetric


def get_llm_usage(llm) -> dict:
    """Safely extract prompt/completion tokens and cost from an OpenHands LLM instance."""
    metrics = getattr(llm, "metrics", None)
    if not metrics:
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    tu = getattr(metrics, "accumulated_token_usage", None)
    prompt = getattr(tu, "prompt_tokens", 0) if tu else 0
    completion = getattr(tu, "completion_tokens", 0) if tu else 0
    cost = getattr(metrics, "accumulated_cost", 0.0)
    try:
        cost = float(cost)
    except (TypeError, ValueError):
        cost = 0.0

    try:
        prompt = int(prompt)
    except (TypeError, ValueError):
        prompt = 0

    try:
        completion = int(completion)
    except (TypeError, ValueError):
        completion = 0

    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "estimated_cost_usd": cost,
    }


class TelemetryRecorder:
    """Monitors pipeline execution, prevents token burn via circuit breaker and budget limits, and logs reports."""

    def __init__(
        self,
        task_description: str,
        pipeline_mode: str = "dev-test",
        reports_dir: Optional[Path] = None,
        circuit_breaker_threshold: int = 2,
        max_budget_usd: float = 0.50,
        max_retained_reports: int = 20,
    ):
        self.task_description = task_description
        self.pipeline_mode = pipeline_mode
        now_utc = datetime.now(timezone.utc)
        self.report_id = (
            f"run_{now_utc.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        )
        self.reports_dir = (
            reports_dir or DEFAULT_DIAGNOSTICS_DIR / "reports"
        ).resolve()
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.max_budget_usd = max_budget_usd
        self.max_retained_reports = max_retained_reports
        self.budget_guard = BudgetGuard(max_budget_usd=max_budget_usd)
        self.start_time = now_utc
        self._start_perf = time.perf_counter()

        self.metrics: list[StepMetric] = []
        self.incidents: list[StepIncident] = []
        self.recommendations: list[str] = []

        # State tracking for circuit breaker
        self._last_diff_hash: Optional[str] = None
        self._last_error_hash: Optional[str] = None
        self._last_error_text: Optional[str] = None
        self._last_failing_tests: Optional[set[str]] = None
        self._identical_failure_count: int = 0
        self.circuit_breaker_triggered: bool = False
        self.budget_exhausted: bool = False

    def reset(self) -> None:
        """Reset circuit breaker, metrics, incidents, budget guard, and timing for a fresh pipeline run.

        This clears all accumulated state so that a reused recorder starts with
        a clean slate and zero state leaks across runs.
        """
        self.start_time = datetime.now(timezone.utc)
        self._start_perf = time.perf_counter()
        self.metrics.clear()
        self.incidents.clear()
        self.recommendations.clear()
        self.budget_guard = BudgetGuard(max_budget_usd=self.max_budget_usd)
        self._last_diff_hash = None
        self._last_error_hash = None
        self._last_error_text = None
        self._last_failing_tests = None
        self._identical_failure_count = 0
        self.circuit_breaker_triggered = False
        self.budget_exhausted = False

    def record_step(
        self,
        agent_role: str,
        action_type: str,
        iteration: int,
        duration_seconds: float,
        success: bool,
        diff_text: str = "",
        error_summary: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        """Log a completed agent turn or pipeline step with token metrics."""
        diff_hash = (
            hashlib.sha256(diff_text.encode("utf-8")).hexdigest()[:12]
            if diff_text
            else None
        )
        metric = StepMetric(
            agent_role=agent_role,
            action_type=action_type,
            iteration=iteration,
            duration_seconds=round(duration_seconds, 2),
            success=success,
            diff_hash=diff_hash,
            diff_size_bytes=len(diff_text.encode("utf-8")),
            error_summary=error_summary,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=round(estimated_cost_usd, 6),
        )
        self.metrics.append(metric)

    @contextmanager
    def timed_step(
        self,
        agent_role: str,
        action_type: str,
        iteration: int = 1,
        agent: Optional[Any] = None,
        diff_text: str = "",
        error_summary: Optional[str] = None,
    ):
        """Context manager to measure step duration and automatically record token metrics."""
        t0 = time.perf_counter()
        step_state = {
            "success": True,
            "error_summary": error_summary,
            "diff_text": diff_text,
        }
        try:
            yield step_state
        except Exception as e:
            step_state["success"] = False
            step_state["error_summary"] = str(e)
            raise
        finally:
            dur = time.perf_counter() - t0
            u = (
                get_llm_usage(getattr(agent, "llm", None))
                if agent
                else {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                }
            )
            self.record_step(
                agent_role=agent_role,
                action_type=action_type,
                iteration=iteration,
                duration_seconds=dur,
                success=step_state.get("success", True),
                diff_text=step_state.get("diff_text", ""),
                error_summary=step_state.get("error_summary"),
                prompt_tokens=u["prompt_tokens"],
                completion_tokens=u["completion_tokens"],
                total_tokens=u["total_tokens"],
                estimated_cost_usd=u["estimated_cost_usd"],
            )

    def record_incident(self, step_name: str, incident_type: str, details: str) -> None:
        """Log a failure or anomaly during execution."""
        incident = StepIncident(
            step_name=step_name,
            incident_type=incident_type,
            details=details,
        )
        self.incidents.append(incident)

    @property
    def remaining_budget(self) -> float:
        """Calculate remaining dollar budget before ceiling."""
        return self.budget_guard.remaining_budget

    def check_budget(self, total_cost: float) -> bool:
        """Check if accumulated spend has exceeded max_budget_usd."""
        if self.budget_guard.update_cost(total_cost):
            self.budget_exhausted = True
            self.record_incident(
                step_name="BudgetGuard",
                incident_type="budget_exceeded",
                details=f"Current spend (${total_cost:.4f}) reached or exceeded budget ceiling (${self.max_budget_usd:.2f}).",
            )
            self.recommendations.append(
                f"Budget limit (${self.max_budget_usd:.2f}) reached. Review prompt length, skill inclusion, or model tier."
            )
            return True
        return False

    def check_circuit_breaker(self, diff_text: str, error_text: str) -> bool:
        """
        Smart semantic circuit breaker:
        Checks for:
        1. Exact identical diff hash and error hash
        2. Exact same failing pytest test cases repeating across iterations
        3. High error message similarity (>=0.88) indicating repetitive failure
        """
        curr_diff_hash = hashlib.sha256(diff_text.strip().encode("utf-8")).hexdigest()
        curr_error_hash = hashlib.sha256(error_text.strip().encode("utf-8")).hexdigest()
        curr_error_clean = error_text.strip()

        # Extract failed test identifiers if present (e.g. FAILED tests/test_app.py::test_feature)
        failing_tests = set(
            re.findall(r"(?:FAILED|ERROR)\s+([^\s:]+(?:::[\w_]+)?)", curr_error_clean)
        )

        is_repeated = False

        if (
            curr_diff_hash == self._last_diff_hash
            and curr_error_hash == self._last_error_hash
        ):
            is_repeated = True
        elif (
            failing_tests
            and self._last_failing_tests
            and failing_tests == self._last_failing_tests
        ):
            is_repeated = True
        elif self._last_error_text and len(curr_error_clean) > 50:
            sim = difflib.SequenceMatcher(
                None, curr_error_clean[:1000], self._last_error_text[:1000]
            ).ratio()
            if sim >= 0.88:
                is_repeated = True

        if is_repeated:
            self._identical_failure_count += 1
        else:
            self._identical_failure_count = 1

        self._last_diff_hash = curr_diff_hash
        self._last_error_hash = curr_error_hash
        self._last_error_text = curr_error_clean
        self._last_failing_tests = failing_tests

        if self._identical_failure_count >= self.circuit_breaker_threshold:
            self.circuit_breaker_triggered = True
            self.record_incident(
                step_name="CircuitBreaker",
                incident_type="circuit_breaker",
                details=(
                    f"Repetitive failure loop detected across {self._identical_failure_count} "
                    f"consecutive iterations (Threshold: {self.circuit_breaker_threshold}). Halting execution to prevent token burn."
                ),
            )
            self.recommendations.append(
                "Circuit breaker tripped: Agent repeatedly failed the same tests or produced similar failures without progress."
            )
            return True

        return False

    @staticmethod
    def calculate_per(resolved_findings_delta: int, tokens_consumed: int) -> float:
        """Calculate Progress Efficiency Ratio (PER): (resolved / tokens) * 100,000."""
        if tokens_consumed <= 0:
            return 0.0
        return round((resolved_findings_delta / tokens_consumed) * 100_000, 3)

    def finalize(
        self, completed_successfully: bool, resolved_findings_delta: int = 0
    ) -> DiagnosticReport:
        """Complete the telemetry session, generate report, and save to disk."""
        end_time = datetime.now(timezone.utc)
        total_duration = round(time.perf_counter() - self._start_perf, 2)
        total_iterations = max((m.iteration for m in self.metrics), default=1)
        total_tok = sum(m.total_tokens for m in self.metrics)
        total_cost = sum(m.estimated_cost_usd for m in self.metrics)
        per = self.calculate_per(resolved_findings_delta, total_tok)

        # Generate automatic recommendations
        if (
            not completed_successfully
            and not self.circuit_breaker_triggered
            and not self.budget_exhausted
        ):
            self.recommendations.append(
                "Task did not pass all tests within iteration budget. Consider increasing max_iterations or decomposing task."
            )

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
            budget_exhausted=self.budget_exhausted,
            total_tokens=total_tok,
            total_cost_usd=round(total_cost, 6),
            progress_efficiency_ratio=per,
            metrics=self.metrics,
            incidents=self.incidents,
            recommendations=self.recommendations,
        )

        # Write to JSON file
        report_file = self.reports_dir / f"{self.report_id}.json"
        report_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        # Automatically enforce report retention policy (FIFO auto-pruning)
        self._prune_old_reports()

        return report

    def _prune_old_reports(self) -> int:
        """Enforce retention policy by pruning oldest run_*.json files exceeding max_retained_reports."""
        if self.max_retained_reports <= 0:
            return 0
        try:
            report_files = sorted(
                self.reports_dir.glob("run_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            pruned = 0
            if len(report_files) > self.max_retained_reports:
                for old_file in report_files[self.max_retained_reports :]:
                    try:
                        old_file.unlink()
                        pruned += 1
                    except OSError:
                        pass
            return pruned
        except Exception:
            return 0
