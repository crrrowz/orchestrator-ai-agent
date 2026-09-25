"""System Evolution Auditor: Analyzes execution telemetry to propose self-improvements."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from orchestrator.config import DEFAULT_DIAGNOSTICS_DIR
from orchestrator.rendering.output import ConsoleOutput
from orchestrator.telemetry.schemas import DiagnosticReport


class SystemAuditor:
    """Offline audit engine that reads execution telemetry and generates self-improvement recommendations."""

    def __init__(self, reports_dir: Optional[Path] = None):
        self.reports_dir = (
            reports_dir or DEFAULT_DIAGNOSTICS_DIR / "reports"
        ).resolve()

    def load_reports(self) -> list[DiagnosticReport]:
        """Load and validate all JSON diagnostic reports from disk."""
        reports: list[DiagnosticReport] = []
        if self.reports_dir.exists():
            for path in self.reports_dir.glob("run_*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    reports.append(DiagnosticReport.model_validate(data))
                except Exception as e:
                    ConsoleOutput.warning(
                        f"Skipping corrupted report '{path.name}': {e}"
                    )

        # Fallback: Recover from latest_session.json if no finalized reports exist
        if not reports:
            session_log = self.reports_dir.parent / "logs" / "latest_session.json"
            if session_log.exists():
                try:
                    data = json.loads(session_log.read_text(encoding="utf-8"))
                    steps_data = data.get("steps", [])
                    if steps_data:
                        from orchestrator.telemetry.schemas import (
                            StepIncident,
                            StepMetric,
                        )

                        start_ts = data.get(
                            "session_start", datetime.now(timezone.utc).timestamp()
                        )
                        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
                        total_dur = (
                            steps_data[-1].get("duration_s", 0.0) if steps_data else 0.0
                        )
                        end_dt = datetime.fromtimestamp(
                            start_ts + total_dur, tz=timezone.utc
                        )

                        incidents = []
                        metrics = []
                        completed_ok = True
                        for s in steps_data:
                            if s.get("is_error"):
                                obs = (
                                    s.get("observation")
                                    or s.get("summary")
                                    or "Unknown error"
                                )
                                inc_type = "tool_error"
                                if (
                                    "KeyboardInterrupt" in obs
                                    or "KeyboardInterrupt" in s.get("summary", "")
                                ):
                                    inc_type = "user_interruption"
                                    completed_ok = False
                                elif "not recognized" in obs or "command" in s.get(
                                    "action_type", ""
                                ):
                                    inc_type = "os_incompatible_command"
                                elif (
                                    "pytest" in obs
                                    or "test" in s.get("phase", "").lower()
                                ):
                                    inc_type = "test_failure"
                                incidents.append(
                                    StepIncident(
                                        step_name=f"{s.get('role', 'Agent')}_{s.get('phase', 'Phase')}",
                                        incident_type=inc_type,
                                        details=str(obs)[:300],
                                        timestamp=datetime.now(timezone.utc),
                                    )
                                )
                            metrics.append(
                                StepMetric(
                                    agent_role=s.get("role", "Unknown"),
                                    action_type=s.get("action_type") or "action",
                                    iteration=1,
                                    duration_seconds=s.get("duration_s", 0.0),
                                    success=not s.get("is_error", False),
                                    error_summary=str(s.get("observation"))[:200]
                                    if s.get("is_error")
                                    else None,
                                )
                            )

                        recs = []
                        if any(
                            inc.incident_type == "user_interruption"
                            for inc in incidents
                        ):
                            recs.append(
                                "Execution was interrupted by user (KeyboardInterrupt). Improve loop responsiveness or decompose task."
                            )
                        if any(
                            inc.incident_type == "os_incompatible_command"
                            for inc in incidents
                        ):
                            recs.append(
                                "Agent executed Linux commands (e.g. 'tail') on Windows shell. Enforce Windows-compatible commands or cross-platform tools."
                            )
                        if any(
                            inc.incident_type == "test_failure" for inc in incidents
                        ):
                            recs.append(
                                "Pytest failures detected during test iteration. Review Developer and Tester prompt specifications."
                            )

                        recovered_report = DiagnosticReport(
                            report_id="run_recovered_from_session",
                            task_description="Recovered from diagnostics/logs/latest_session.json",
                            pipeline_mode="recovered",
                            start_time=start_dt,
                            end_time=end_dt,
                            total_duration_seconds=total_dur,
                            total_iterations=1,
                            completed_successfully=completed_ok,
                            circuit_breaker_triggered=False,
                            metrics=metrics,
                            incidents=incidents,
                            recommendations=recs,
                        )
                        self.reports_dir.mkdir(parents=True, exist_ok=True)
                        (
                            self.reports_dir / "run_recovered_from_session.json"
                        ).write_text(
                            recovered_report.model_dump_json(indent=2), encoding="utf-8"
                        )
                        reports.append(recovered_report)
                except Exception as e:
                    ConsoleOutput.warning(f"Failed to recover from session log: {e}")

        return reports

    def audit_and_generate_report(self) -> Path:
        """Analyze historical execution telemetry and produce SYSTEM_EVOLUTION_REPORT.md."""
        reports = self.load_reports()
        output_path = self.reports_dir.parent / "SYSTEM_EVOLUTION_REPORT.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not reports:
            content = (
                "# System Evolution & Self-Improvement Report\n\n"
                f"Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}\n\n"
                "No execution reports found in `diagnostics/reports/`. "
                "Run development tasks to collect telemetry data."
            )
            output_path.write_text(content, encoding="utf-8")
            return output_path

        total_runs = len(reports)
        successful_runs = sum(1 for r in reports if r.completed_successfully)
        circuit_breaker_trips = sum(1 for r in reports if r.circuit_breaker_triggered)
        success_rate = (successful_runs / total_runs) * 100

        # Incidents breakdown
        incident_types = Counter()
        for r in reports:
            for inc in r.incidents:
                incident_types[inc.incident_type] += 1

        # Recommendations breakdown
        recurring_recommendations = Counter()
        for r in reports:
            for rec in r.recommendations:
                recurring_recommendations[rec] += 1

        # Average iterations
        avg_iterations = sum(r.total_iterations for r in reports) / total_runs

        # Compile Markdown Report
        lines = [
            "# System Evolution & Self-Improvement Audit Report",
            f"\n**Audit Date**: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`",
            f"**Total Analyzed Runs**: `{total_runs}`",
            f"**Overall Success Rate**: `{success_rate:.1f}%` ({successful_runs}/{total_runs})",
            f"**Circuit Breaker Interventions**: `{circuit_breaker_trips}` (runaway loops prevented)",
            f"**Average Iterations per Task**: `{avg_iterations:.2f}`",
            "\n---",
            "\n## 1. Incident & Bottleneck Distribution",
            "| Incident Type | Occurrences | Systemic Severity |",
            "|---|---|---|",
        ]

        if incident_types:
            for itype, count in incident_types.most_common():
                severity = (
                    "HIGH"
                    if "circuit_breaker" in itype or "timeout" in itype
                    else "MEDIUM"
                )
                lines.append(f"| `{itype}` | {count} | **{severity}** |")
        else:
            lines.append("| None | 0 | LOW |")

        lines.extend(
            [
                "\n---",
                "\n## 2. Actionable Self-Evolution Directives",
                "Based on telemetry pattern analysis, the following updates are recommended for the Orchestrator:",
            ]
        )

        if recurring_recommendations:
            for rec, count in recurring_recommendations.most_common(5):
                lines.append(f"- **[Frequency: {count}x]**: {rec}")
        else:
            lines.append(
                "- All historical runs completed without recurring failure patterns."
            )

        lines.extend(
            [
                "\n---",
                "\n## 3. Targeted Skill Refinements",
                "- If test failures persist > 2 iterations: Expand `.agents/skills/systematic-debugging/SKILL.md` with explicit AST analysis.",
                "- If circuit breaker trips: Enforce single-file surgical diffs in `.agents/skills/clean-python-architecture/SKILL.md`.",
                "- If review rejections occur on security: Update `.agents/skills/security-audit-hardening/SKILL.md`.",
            ]
        )

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path
