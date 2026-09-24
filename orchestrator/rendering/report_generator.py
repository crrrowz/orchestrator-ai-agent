"""Markdown report generator for pipeline telemetry, audits, and execution logs."""

from typing import Any, Dict, List, Optional


class MarkdownReportGenerator:
    """Generates structured, production-grade markdown reports for pipeline runs."""

    @staticmethod
    def generate_pipeline_summary(
        task: str,
        mode: str,
        status: str,
        iterations: int,
        duration_seconds: float,
        total_tokens: int,
        total_cost_usd: float,
        steps: Optional[List[Dict[str, Any]]] = None,
        incidents: Optional[List[Dict[str, Any]]] = None,
        sentinel_stats: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Construct a formatted Markdown document summarizing pipeline run outcomes."""
        lines = [
            "# 🚀 Orchestrator Pipeline Run Report",
            "",
            f"- **Task**: `{task}`",
            f"- **Execution Mode**: `{mode}`",
            f"- **Status**: `{'✅ ' + status if status == 'SUCCESS' else '❌ ' + status}`",
            f"- **Iterations**: `{iterations}`",
            f"- **Duration**: `{duration_seconds:.2f}s`",
            f"- **Total Tokens Consumed**: `{total_tokens:,}`",
            f"- **Estimated Cost**: `${total_cost_usd:.4f}`",
            "",
            "---",
            "",
            "## 📋 Execution Steps",
            "",
            "| Phase | Action | Iteration | Duration | Status | Tokens | Cost ($) |",
            "|---|---|---|---|---|---|---|",
        ]

        if steps:
            for s in steps:
                agent = s.get("agent_role", "system")
                action = s.get("action_type", "step")
                it = s.get("iteration", 1)
                dur = s.get("duration_seconds", 0.0)
                st = "✅" if s.get("success", True) else "❌"
                tok = s.get("total_tokens", 0)
                cost = s.get("estimated_cost_usd", 0.0)
                lines.append(
                    f"| `{agent}` | `{action}` | {it} | {dur:.2f}s | {st} | {tok:,} | ${cost:.4f} |"
                )
        else:
            lines.append("| - | No recorded steps | - | - | - | - | - |")

        if sentinel_stats:
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 🛡️ Cognitive Sentinel & Digital Immunity",
                    "",
                    f"- **Total Intercepted Incidents**: `{sentinel_stats.get('total_incidents', 0)}`",
                    f"- **Autonomous Self-Healed Count**: `{sentinel_stats.get('auto_healed_count', 0)}`",
                    f"- **Healing Success Rate**: `{sentinel_stats.get('healing_rate', 1.0) * 100:.1f}%`",
                    f"- **Cloud Failover Events**: `{sentinel_stats.get('failed_cloud_calls', 0)}`",
                ]
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## ⚠️ Incidents & Circuit Breaker Logs",
                "",
            ]
        )

        if incidents:
            for inc in incidents:
                step = inc.get("step_name", "general")
                itype = inc.get("incident_type", "warning")
                detail = inc.get("details", "")
                lines.append(f"### Incident: `{step}` ({itype})")
                lines.append("```text")
                lines.append(detail.strip())
                lines.append("```")
                lines.append("")
        else:
            lines.append("No incidents recorded. Clean execution.")

        return "\n".join(lines).strip()
