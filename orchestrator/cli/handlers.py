"""CLI action handlers for zero-token audits, diagnostics, logs, and task resolution."""

import json
import re
import sys
from pathlib import Path
from typing import Optional

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

    # 2. Check if text contains a file path (e.g. 'افحص D:\path\AUDIT_REPORT.md')
    path_matches = re.findall(r"([a-zA-Z]:[\\/][^\s\"'<>|]+|/[^\s\"'<>|]+)", task_input)
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
