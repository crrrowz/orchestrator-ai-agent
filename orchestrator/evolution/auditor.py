"""System Evolution Auditor: Analyzes execution telemetry to propose self-improvements."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

from orchestrator.telemetry.schemas import DiagnosticReport
from orchestrator.utils import ConsoleOutput


class SystemAuditor:
    """Offline audit engine that reads execution telemetry and generates self-improvement recommendations."""

    def __init__(self, reports_dir: Optional[Path] = None):
        self.reports_dir = (reports_dir or Path("diagnostics/reports")).resolve()

    def load_reports(self) -> list[DiagnosticReport]:
        """Load and validate all JSON diagnostic reports from disk."""
        reports: list[DiagnosticReport] = []
        if not self.reports_dir.exists():
            return reports

        for path in self.reports_dir.glob("run_*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                reports.append(DiagnosticReport.model_validate(data))
            except Exception as e:
                ConsoleOutput.warning(f"Skipping corrupted report '{path.name}': {e}")
        return reports

    def audit_and_generate_report(self) -> Path:
        """Analyze historical execution telemetry and produce SYSTEM_EVOLUTION_REPORT.md."""
        reports = self.load_reports()
        output_path = self.reports_dir.parent / "SYSTEM_EVOLUTION_REPORT.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not reports:
            content = (
                "# System Evolution & Self-Improvement Report\n\n"
                f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}\n\n"
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
            f"\n**Audit Date**: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}`",
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
                severity = "HIGH" if "circuit_breaker" in itype or "timeout" in itype else "MEDIUM"
                lines.append(f"| `{itype}` | {count} | **{severity}** |")
        else:
            lines.append("| None | 0 | LOW |")

        lines.extend([
            "\n---",
            "\n## 2. Actionable Self-Evolution Directives",
            "Based on telemetry pattern analysis, the following updates are recommended for the Orchestrator:",
        ])

        if recurring_recommendations:
            for rec, count in recurring_recommendations.most_common(5):
                lines.append(f"- **[Frequency: {count}x]**: {rec}")
        else:
            lines.append("- All historical runs completed without recurring failure patterns.")

        lines.extend([
            "\n---",
            "\n## 3. Targeted Skill Refinements",
            "- If test failures persist > 2 iterations: Expand `.agents/skills/systematic-debugging/SKILL.md` with explicit AST analysis.",
            "- If circuit breaker trips: Enforce single-file surgical diffs in `.agents/skills/clean-python-architecture/SKILL.md`.",
            "- If review rejections occur on security: Update `.agents/skills/security-audit-hardening/SKILL.md`.",
        ])

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path
