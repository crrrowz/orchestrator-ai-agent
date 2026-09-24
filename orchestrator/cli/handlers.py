"""CLI action handlers for zero-token audits, diagnostics, logs, and task resolution."""

import json
import re
from pathlib import Path
from typing import Any, Optional

from orchestrator.analysis.connectivity import ConnectivityChecker
from orchestrator.core.config import OrchestratorConfig
from orchestrator.core.constants import DEFAULT_DIAGNOSTICS_DIR
from orchestrator.rendering.output import ConsoleOutput
from orchestrator.skills.manager import SkillManager
from orchestrator.ui.log_explorer import InteractiveLogExplorer
from orchestrator.ui.session_store import LogStep, SessionLogStore


def resolve_task_input(task_input: Optional[str]) -> str:
    """If task_input is or contains a path to an existing file, read its content into the task context."""
    if not task_input:
        return ""
    clean_val = task_input.strip().strip("'\"")

    # 1. Exact file path check
    try:
        p = Path(clean_val)
        if p.exists() and p.is_file():
            content = p.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                ConsoleOutput.agent_step(
                    "INPUT",
                    f"Loaded task specification from file: [bold]{p.name}[/bold]",
                    f"Path: {p} ({len(content)} chars, {len(content.split())} words)",
                )
                return content
    except Exception:
        pass

    # 2. Check for quoted paths (e.g. 'D:\path with spaces\file.md' or "docs/plan.md")
    quoted_matches = re.findall(
        r'["\']([^"\']+\.(?:md|py|json|yaml|yml|txt|toml|cfg|ini|html|css|js|ts|sh|sql|xml|csv))["\']',
        task_input,
    )
    for candidate in quoted_matches:
        try:
            cand_p = Path(candidate.strip())
            if cand_p.exists() and cand_p.is_file():
                file_text = cand_p.read_text(encoding="utf-8", errors="replace").strip()
                if file_text:
                    ConsoleOutput.agent_step(
                        "INPUT",
                        f"Embedded file specification loaded: [bold]{cand_p.name}[/bold]",
                        f"Path: {cand_p} ({len(file_text)} chars)",
                    )
                    return f"{task_input}\n\n[Referenced File Content ({cand_p.name})]:\n{file_text}"
        except Exception:
            pass

    # 3. Check if text contains a file path without spaces (e.g. 'افحص D:\path\AUDIT_REPORT.md')
    path_matches = re.findall(
        r"([a-zA-Z]:[\\/][^\s\"'<>|]+|/[^\s\"'<>|]+|\.?\./[^\s\"'<>|]+)",
        task_input,
    )
    for candidate in path_matches:
        try:
            cand_p = Path(candidate.strip())
            if cand_p.exists() and cand_p.is_file():
                file_text = cand_p.read_text(encoding="utf-8", errors="replace").strip()
                if file_text:
                    ConsoleOutput.agent_step(
                        "INPUT",
                        f"Embedded file specification loaded: [bold]{cand_p.name}[/bold]",
                        f"Path: {cand_p} ({len(file_text)} chars)",
                    )
                    return f"{task_input}\n\n[Referenced File Content ({cand_p.name})]:\n{file_text}"
        except Exception:
            pass

    return task_input


def resolve_workspace_dir(target: Optional[Path], default: Path) -> Path:
    """Resolve target path ensuring it is a directory, falling back to parent if a file was given."""
    if not target:
        return default.resolve()
    resolved = target.resolve()
    if resolved.is_file():
        ConsoleOutput.warning(
            f"Target workspace '{resolved}' is a file. Resolving to parent directory: '{resolved.parent}'."
        )
        return resolved.parent
    return resolved


def handle_list_skills(skill_manager: SkillManager) -> None:
    """Display discovered skills in the project."""
    ConsoleOutput.banner("Discovered Architectural & Testing Skills")
    skills = skill_manager.available_skills
    if not skills:
        ConsoleOutput.warning("No skills found in .agents/skills/")
        return

    for name in sorted(skills):
        skill = skill_manager.get_skill(name)
        desc = skill.description if skill else "No description"
        ConsoleOutput.agent_step("SKILL", f"[bold]{name}[/bold]", desc)


def handle_check_config(config: OrchestratorConfig) -> None:
    """Verify provider connectivity and output environment safety configuration."""
    ConnectivityChecker.run_zero_token_audit(config)
    print("\n" + "=" * 50)
    print("Environment & Cost Safety Controls:")
    loaded_from = getattr(config, "_loaded_from_path", None)
    if loaded_from:
        print(f"  Configuration File:    {loaded_from}")
    else:
        print("  Configuration File:    Environment / Defaults (.env)")
    print(f"  Active Domain:         {config.active_domain}")
    print(f"  Workspace:             {config.workspace_path}")
    print(f"  Max Iterations Cap:    {config.max_iterations}")
    print(f"  Max Output Tokens:     {config.max_tokens_per_call}")
    print(f"  Max Budget (USD):      ${config.max_budget_usd:.2f}")
    print(
        f"  Circuit Breaker:       Trigger on {config.circuit_breaker_threshold} identical consecutive failures"
    )
    print(f"  Auto Git Commit:       {config.auto_commit}")
    print(f"  Interactive (HITL):    {config.interactive}")
    print(f"  Approval Gates:        {config.approval_gates or 'None'}")
    print(f"  Verbosity Level:       {config.verbosity}")
    print("=" * 50)


def handle_self_audit() -> None:
    """Run offline self-evolution analysis on historical reports."""
    from orchestrator.evolution import SystemAuditor

    auditor = SystemAuditor()
    report_file = auditor.audit_and_generate_report()
    ConsoleOutput.banner("System Evolution & Self-Improvement Audit")
    ConsoleOutput.success(f"Audit report generated at: {report_file}")
    if report_file.exists():
        print("\n" + report_file.read_text(encoding="utf-8"))


def handle_view_logs(workspace: Optional[Path] = None) -> None:
    """Open interactive TUI log viewer for recent sessions."""
    logs_base = DEFAULT_DIAGNOSTICS_DIR / "logs"
    log_file = logs_base / "latest_session.json"

    if workspace:
        p_slug = (
            re.sub(r"[^a-zA-Z0-9_\-]+", "_", workspace.name.lower()).strip("_")
            or "default"
        )
        project_log = logs_base / p_slug / "latest_session.json"
        if project_log.exists():
            log_file = project_log
        else:
            ConsoleOutput.info(
                f"No dedicated log found for workspace '{workspace.name}', checking global latest log."
            )

    if not log_file.exists():
        ConsoleOutput.warning(
            f"No session log found at {log_file}. Run a development task first."
        )
        return

    try:
        data = json.loads(log_file.read_text(encoding="utf-8"))
        store = SessionLogStore(workspace_path=workspace)
        for step_dict in data.get("steps", []):
            store.steps.append(LogStep(**step_dict))
        ConsoleOutput.banner("Interactive Log Explorer", f"Log: {log_file}")
        InteractiveLogExplorer(store).run()
    except Exception as e:
        ConsoleOutput.error(f"Error loading session log: {str(e)}")


def handle_sentinel_status(config: Optional[Any] = None) -> None:
    """Display Sentinel diagnostics, mesh circuit health, and self-healing statistics."""
    from rich.table import Table

    from orchestrator.rendering.output import console
    from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB

    ConsoleOutput.banner(
        "Autonomous Cognitive Sentinel & SRE Mesh Status", "Live System Telemetry"
    )

    db = SentinelDiagnosticsDB()
    stats = db.get_stats()

    table = Table(title="Sentinel Operational Statistics", border_style="yellow")
    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="cyan")

    table.add_row(
        "Sentinel Mode", "[bold green]● ENFORCING (Autonomous Protection)[/bold green]"
    )
    table.add_row("Total Incidents Intercepted", str(stats.get("total_incidents", 0)))
    table.add_row("Self-Healed Anomaly Count", str(stats.get("auto_healed_count", 0)))
    table.add_row(
        "Self-Healing Success Rate", f"{stats.get('healing_rate', 1.0) * 100:.1f}%"
    )
    table.add_row("Total Cloud LLM Calls", str(stats.get("total_cloud_calls", 0)))
    table.add_row("Cloud Failures / Throttled", str(stats.get("failed_cloud_calls", 0)))

    console.print(table)


def handle_sentinel_heal(target_path: Path) -> None:
    """Run standalone zero-token AST audit and auto-healing on a Python file or directory."""
    from rich.table import Table

    from orchestrator.rendering.output import console
    from orchestrator.sentinel.ast_guard import ASTGuard

    if not target_path.exists():
        ConsoleOutput.error(f"Path '{target_path}' not found.")
        return

    guard = ASTGuard()

    # Case 1: Target is a single file
    if target_path.is_file():
        if target_path.suffix.lower() != ".py":
            ConsoleOutput.warning(f"Skipping non-Python file: {target_path}")
            return
        content = target_path.read_text(encoding="utf-8", errors="replace")
        is_safe, msg, healed = guard.intercept_ast(target_path, content)
        if not is_safe:
            ConsoleOutput.error(f"AST Audit failed on '{target_path.name}': {msg}")
        elif healed and healed != content:
            target_path.write_text(healed, encoding="utf-8")
            ConsoleOutput.success(
                f"Successfully auto-healed '{target_path.name}': {msg}"
            )
        else:
            ConsoleOutput.success(
                f"'{target_path.name}' verified clean. 0 defects detected."
            )
        return

    # Case 2: Target is a directory -> recursively scan and heal all Python files
    resolved_dir = target_path.resolve()
    ConsoleOutput.banner(
        "Autonomous Sentinel AST Workspace Self-Healing",
        f"Scanning: {resolved_dir}",
    )
    ignored_dirs = {
        ".venv",
        "venv",
        ".git",
        "__pycache__",
        "build",
        "dist",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
        ".agents",
    }

    py_files: list[Path] = []
    for p in resolved_dir.rglob("*.py"):
        if any(part in ignored_dirs for part in p.parts):
            continue
        py_files.append(p)

    if not py_files:
        ConsoleOutput.warning(f"No Python files found in '{target_path}'.")
        return

    total = len(py_files)
    healed_count = 0
    failed_count = 0
    clean_count = 0

    for py_file in py_files:
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
            is_safe, msg, healed = guard.intercept_ast(py_file, content)
            rel_name = py_file.relative_to(resolved_dir)
            if not is_safe:
                failed_count += 1
                ConsoleOutput.error(f"[{rel_name}] AST syntax failure: {msg}")
            elif healed and healed != content:
                healed_count += 1
                py_file.write_text(healed, encoding="utf-8")
                ConsoleOutput.success(f"[{rel_name}] Auto-healed: {msg}")
            else:
                clean_count += 1
        except Exception as e:
            failed_count += 1
            ConsoleOutput.error(f"[{py_file.name}] Read/Heal error: {e}")

    table = Table(title="AST Audit & Auto-Healing Summary", border_style="cyan")
    table.add_column("Total Files Scanned", justify="center")
    table.add_column("Verified Clean", justify="center", style="bold green")
    table.add_column("Auto-Healed", justify="center", style="bold yellow")
    table.add_column("Syntax Errors / Blocked", justify="center", style="bold red")

    table.add_row(str(total), str(clean_count), str(healed_count), str(failed_count))
    console.print(table)


def handle_sentinel_test_mesh(config: Optional[Any] = None) -> None:
    """Test cloud resilience mesh readiness and verify provider circuit breakers."""
    from rich.table import Table

    from orchestrator.config import ConfigLoader
    from orchestrator.llm.manager import CloudResilienceMesh
    from orchestrator.rendering.output import console

    cfg = config or ConfigLoader.load()
    mesh = CloudResilienceMesh(cfg)
    results = mesh.test_mesh()

    ConsoleOutput.banner(
        "Cloud Resilience Mesh Probe", "Multi-Tier Fallback Health & Readiness"
    )

    table = Table(title="Cloud LLM Fallback Tiers", border_style="cyan")
    table.add_column("Tier", style="bold yellow", justify="center", width=6)
    table.add_column("Model Identifier", style="bold white")
    table.add_column("Gateway Provider", style="cyan")
    table.add_column("Circuit State", style="bold")
    table.add_column("API Credentials", style="bold")

    for r in results:
        circuit_color = (
            "green"
            if "ONLINE" in r["circuit_state"]
            else ("yellow" if "STANDBY" in r["circuit_state"] else "red")
        )
        cred_text = (
            "[green]VALID (Detected)[/green]"
            if r["has_key"]
            else f"[yellow]MISSING ({', '.join(r['keys_checked'])})[/yellow]"
        )
        table.add_row(
            str(r["tier"]),
            r["model"],
            r["provider"].upper(),
            f"[{circuit_color}]{r['circuit_state']}[/{circuit_color}]",
            cred_text,
        )

    console.print(table)
