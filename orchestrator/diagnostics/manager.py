"""Unified Diagnostics Manager: Orchestrates Telemetry, Memory, Sentinel DB, and Logs."""

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.panel import Panel
from rich.table import Table

from orchestrator.config import DEFAULT_DIAGNOSTICS_DIR
from orchestrator.memory.conversation_store import ConversationStore, MemoryEntry
from orchestrator.rendering.output import ConsoleOutput, console
from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB


class DiagnosticsManager:
    """Unified engine to inspect, search, index, and maintain the diagnostics ecosystem."""

    def __init__(self, diagnostics_dir: Optional[Path] = None):
        self.base_dir = (diagnostics_dir or DEFAULT_DIAGNOSTICS_DIR).resolve()
        self.reports_dir = self.base_dir / "reports"
        self.memory_dir = self.base_dir / "memory"
        self.logs_dir = self.base_dir / "logs"
        self.db_path = self.base_dir / "sentinel_mesh.db"

        self.memory_store = ConversationStore(memory_dir=self.memory_dir)
        self.sentinel_db = SentinelDiagnosticsDB(db_path=self.db_path)

    def get_overview(self) -> Dict[str, Any]:
        """Aggregate high-level metrics across all diagnostics domains."""
        # 1. Reports stats
        report_files = list(self.reports_dir.glob("run_*.json")) if self.reports_dir.exists() else []
        total_reports = len(report_files)
        successful_reports = 0
        total_tokens = 0
        total_cost = 0.0
        latest_report_time = "Never"

        reports_list: List[Dict[str, Any]] = []
        for rf in sorted(report_files, key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(rf.read_text(encoding="utf-8"))
                reports_list.append(data)
                if data.get("completed_successfully"):
                    successful_reports += 1
                total_tokens += data.get("total_tokens", 0)
                total_cost += data.get("total_cost_usd", 0.0)
            except Exception:
                continue

        if reports_list and reports_list[0].get("start_time"):
            latest_report_time = str(reports_list[0]["start_time"])[:19]

        # 2. Memory stats
        mem_stats = self.memory_store.get_stats()

        # 3. Sentinel stats
        sentinel_stats = self.sentinel_db.get_stats()

        # 4. Logs stats
        log_projects = []
        total_log_files = 0
        if self.logs_dir.exists():
            for p in self.logs_dir.iterdir():
                if p.is_dir() and not p.name.startswith("test_"):
                    log_projects.append(p.name)
                    total_log_files += len(list(p.glob("*.json")))

        return {
            "reports": {
                "total": total_reports,
                "successful": successful_reports,
                "success_rate": (successful_reports / total_reports * 100) if total_reports else 100.0,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost,
                "latest_time": latest_report_time,
                "recent": reports_list[:5],
            },
            "memory": mem_stats,
            "sentinel": sentinel_stats,
            "logs": {
                "projects": log_projects,
                "total_sessions": total_log_files,
            },
        }

    def render_dashboard(self) -> None:
        """Render a unified Rich CLI dashboard of the diagnostics ecosystem."""
        overview = self.get_overview()

        ConsoleOutput.banner("Unified Diagnostics Intelligence Dashboard", f"Path: {self.base_dir}")

        # Summary Quadrant Table
        summary_table = Table(title="Diagnostics Subsystems Health & Metrics", border_style="cyan")
        summary_table.add_column("Subsystem", style="bold white", width=22)
        summary_table.add_column("Key Metric", style="cyan", width=25)
        summary_table.add_column("Secondary Metric", style="yellow", width=25)
        summary_table.add_column("Status", style="bold green", width=15)

        rep = overview["reports"]
        summary_table.add_row(
            "Telemetry Reports",
            f"Total Runs: [bold]{rep['total']}[/bold] ({rep['success_rate']:.1f}% OK)",
            f"Spend: [bold]${rep['total_cost_usd']:.4f}[/bold] ({rep['total_tokens']:,} tok)",
            "[green]ACTIVE[/green]" if rep["total"] > 0 else "[dim]EMPTY[/dim]",
        )

        mem = overview["memory"]
        summary_table.add_row(
            "Persistent Memory",
            f"Total Memories: [bold]{mem['total_memories']}[/bold]",
            f"Files Touched: [bold]{mem['unique_files_touched']}[/bold]",
            "[green]INDEXED[/green]" if mem["total_memories"] > 0 else "[dim]EMPTY[/dim]",
        )

        snt = overview["sentinel"]
        summary_table.add_row(
            "Sentinel SRE Mesh",
            f"Incidents: [bold]{snt['total_incidents']}[/bold] (Healed: {snt['auto_healed_count']})",
            f"Healing Rate: [bold]{snt['healing_rate'] * 100:.1f}%[/bold]",
            "[green]ENFORCING[/green]",
        )

        logs = overview["logs"]
        summary_table.add_row(
            "Session Logs",
            f"Projects: [bold]{len(logs['projects'])}[/bold]",
            f"Total Sessions: [bold]{logs['total_sessions']}[/bold]",
            "[green]RECORDING[/green]",
        )

        console.print(summary_table)

        # Recent Runs Table
        if rep["recent"]:
            runs_table = Table(title="Recent Pipeline Runs (Latest 5)", border_style="magenta")
            runs_table.add_column("Run ID", style="bold white", width=26)
            runs_table.add_column("Mode", style="cyan", width=12)
            runs_table.add_column("Status", width=10)
            runs_table.add_column("Tokens", justify="right", width=10)
            runs_table.add_column("Cost ($)", justify="right", width=10)
            runs_table.add_column("Task Description", style="dim white")

            for r in rep["recent"]:
                status_str = "[bold green]PASS[/bold green]" if r.get("completed_successfully") else "[bold red]FAIL[/bold red]"
                runs_table.add_row(
                    r.get("report_id", "unknown"),
                    r.get("pipeline_mode", "dev-test"),
                    status_str,
                    f"{r.get('total_tokens', 0):,}",
                    f"${r.get('total_cost_usd', 0.0):.4f}",
                    (r.get("task_description", "")[:60] + "...") if len(r.get("task_description", "")) > 60 else r.get("task_description", ""),
                )
            console.print(runs_table)

        # Recent Incidents Table
        incidents = self.sentinel_db.get_incident_history(limit=5)
        if incidents:
            inc_table = Table(title="Recent Sentinel Incidents (Latest 5)", border_style="yellow")
            inc_table.add_column("Incident ID", style="bold white", width=15)
            inc_table.add_column("Severity", width=10)
            inc_table.add_column("Module", style="cyan", width=16)
            inc_table.add_column("Error Signature", style="red", width=25)
            inc_table.add_column("Auto-Healed", width=12)

            for inc in incidents:
                healed_str = "[bold green]YES[/bold green]" if inc.get("auto_healed") else "[bold yellow]NO[/bold yellow]"
                inc_table.add_row(
                    str(inc.get("incident_id", ""))[:14],
                    str(inc.get("severity", "MEDIUM")),
                    str(inc.get("origin_module", "core")),
                    str(inc.get("error_signature", ""))[:24],
                    healed_str,
                )
            console.print(inc_table)

    def search(self, query: str) -> None:
        """Search across Reports, Memories, Incidents, and Logs simultaneously."""
        if not query or not query.strip():
            ConsoleOutput.warning("Search query cannot be empty.")
            return

        clean_q = query.strip()
        ConsoleOutput.banner(f"Diagnostics Universal Search: '{clean_q}'", f"Scope: {self.base_dir}")

        matches_found = 0

        # 1. Search Memories
        matching_mems = self.memory_store.search_memories(clean_q, limit=5)
        if matching_mems:
            matches_found += len(matching_mems)
            mem_table = Table(title=f"Matching Memories ({len(matching_mems)})", border_style="green")
            mem_table.add_column("ID", style="bold white", width=10)
            mem_table.add_column("Status", width=8)
            mem_table.add_column("Task", style="cyan", width=30)
            mem_table.add_column("Summary / Lessons", style="dim white")

            for m in matching_mems:
                status_str = "[green]PASS[/green]" if m.tests_passed else "[red]FAIL[/red]"
                detail = m.summary
                if m.lessons:
                    detail += f" | Lesson: {m.lessons}"
                mem_table.add_row(m.id, status_str, m.task[:28], detail[:70])
            console.print(mem_table)

        # 2. Search Reports
        matching_reports = []
        if self.reports_dir.exists():
            for rf in self.reports_dir.glob("run_*.json"):
                try:
                    text = rf.read_text(encoding="utf-8")
                    if clean_q.lower() in text.lower():
                        data = json.loads(text)
                        matching_reports.append(data)
                except Exception:
                    continue

        if matching_reports:
            matches_found += len(matching_reports)
            rep_table = Table(title=f"Matching Telemetry Reports ({len(matching_reports)})", border_style="magenta")
            rep_table.add_column("Report ID", style="bold white", width=26)
            rep_table.add_column("Mode", width=10)
            rep_table.add_column("Task", style="cyan", width=35)
            rep_table.add_column("Cost ($)", width=10)

            for r in matching_reports[:5]:
                rep_table.add_row(
                    r.get("report_id", ""),
                    r.get("pipeline_mode", ""),
                    r.get("task_description", "")[:33],
                    f"${r.get('total_cost_usd', 0.0):.4f}",
                )
            console.print(rep_table)

        # 3. Search Sentinel Incidents
        all_incidents = self.sentinel_db.get_incident_history(limit=50)
        matching_incidents = [
            inc for inc in all_incidents
            if clean_q.lower() in f"{inc.get('error_signature', '')} {inc.get('raw_payload', '')} {inc.get('remedy_description', '')} {inc.get('origin_module', '')}".lower()
        ]

        if matching_incidents:
            matches_found += len(matching_incidents)
            inc_table = Table(title=f"Matching Sentinel Incidents ({len(matching_incidents)})", border_style="yellow")
            inc_table.add_column("Incident ID", style="bold white", width=14)
            inc_table.add_column("Module", width=15)
            inc_table.add_column("Error Signature", style="red", width=25)
            inc_table.add_column("Remedy / Details", style="dim white")

            for inc in matching_incidents[:5]:
                inc_table.add_row(
                    str(inc.get("incident_id", ""))[:12],
                    str(inc.get("origin_module", "")),
                    str(inc.get("error_signature", ""))[:23],
                    str(inc.get("remedy_description", ""))[:45],
                )
            console.print(inc_table)

        if matches_found == 0:
            ConsoleOutput.info(f"No records matching '{clean_q}' found across diagnostics.")

    def clean(self, max_retained_reports: int = 20, max_retained_memories: int = 30) -> Dict[str, int]:
        """Prune test pollution, enforce strict retention, and rebuild indexes."""
        cleaned_counts = {
            "test_log_dirs_removed": 0,
            "stale_memory_files_pruned": 0,
            "stale_reports_pruned": 0,
            "tmp_files_removed": 0,
        }

        # 1. Clean test log directories from logs_dir
        if self.logs_dir.exists():
            for p in self.logs_dir.iterdir():
                if p.is_dir() and (p.name.startswith("test_") or p.name.startswith("tmp_")):
                    try:
                        shutil.rmtree(p)
                        cleaned_counts["test_log_dirs_removed"] += 1
                    except Exception:
                        pass

        # 2. Clean temporary .tmp files across diagnostics
        for tmp in self.base_dir.rglob("*.tmp"):
            try:
                tmp.unlink()
                cleaned_counts["tmp_files_removed"] += 1
            except Exception:
                pass

        # 3. Enforce memory retention
        self.memory_store.max_retained_memories = max_retained_memories
        pruned_mems = self.memory_store._prune_old_memories()
        self.memory_store._rebuild_index()
        cleaned_counts["stale_memory_files_pruned"] = pruned_mems

        # 4. Enforce reports retention
        if self.reports_dir.exists():
            report_files = sorted(
                self.reports_dir.glob("run_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if len(report_files) > max_retained_reports:
                for old_rf in report_files[max_retained_reports:]:
                    try:
                        old_rf.unlink()
                        cleaned_counts["stale_reports_pruned"] += 1
                    except Exception:
                        pass

        # 5. Rebuild INDEX.md
        self.generate_index_markdown()

        return cleaned_counts

    def generate_index_markdown(self) -> Path:
        """Generate human-readable INDEX.md in diagnostics root explaining the directory contents."""
        overview = self.get_overview()
        index_file = self.base_dir / "INDEX.md"

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "# Diagnostics & Telemetry Catalog",
            f"\n> **Last Indexed**: `{now_str}`",
            "\nThis directory contains structured execution diagnostics, cross-run memory, telemetry reports, and session logs for the Multi-Agent Orchestrator.",
            "\n## Directory Structure",
            "| Path | Component | Retention Policy | Purpose |",
            "|---|---|---|---|",
            "| `sentinel_mesh.db` | **SQLite SRE DB** | Persistent | Stores runtime cognitive incidents, circuit states, and cloud telemetry. |",
            "| `reports/` | **Telemetry Reports** | FIFO (20 runs) | Detailed JSON telemetry per pipeline execution (`run_*.json`). |",
            "| `reports/index.json` | **Reports Catalog** | Auto-updated | Fast index mapping Run IDs to task summaries and costs. |",
            "| `memory/` | **Task Memory** | FIFO (30 items) | Cross-run task learnings and architectural insights (`<id>.json`). |",
            "| `memory/index.json` | **Memory Catalog** | Auto-updated | Fast index of historical tasks and pass/fail statuses. |",
            "| `logs/<project>/` | **Session Logs** | FIFO (10 sessions) | Step-by-step interactive execution traces per workspace. |",
            "\n---",
            "\n## Recent Execution History (Latest 5 Runs)",
            "| Run ID | Mode | Status | Tokens | Cost | Task Summary |",
            "|---|---|---|---|---|---|",
        ]

        recent_reports = overview["reports"]["recent"]
        if recent_reports:
            for r in recent_reports:
                status = "✅ PASS" if r.get("completed_successfully") else "❌ FAIL"
                clean_task = r.get("task_description", "").replace("\n", " ")[:60]
                lines.append(
                    f"| `{r.get('report_id')}` | `{r.get('pipeline_mode')}` | {status} | {r.get('total_tokens', 0):,} | ${r.get('total_cost_usd', 0.0):.4f} | {clean_task} |"
                )
        else:
            lines.append("| _No runs recorded yet_ | - | - | - | - | - |")

        lines.extend([
            "\n---",
            "\n## CLI Commands for Diagnostics Management",
            "- **`orchestrator --diagnostics`**: Open visual interactive dashboard.",
            "- **`orchestrator --diagnostics-search <query>`**: Full-text search across all memories, reports, and logs.",
            "- **`orchestrator --diagnostics-clean`**: Clean test artifacts and prune stale logs.",
        ])

        index_file.write_text("\n".join(lines), encoding="utf-8")
        return index_file
