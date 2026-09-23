"""CLI entry point for Antigravity Multi-Agent Orchestrator."""

import os
import sys
import logging

# Suppress OpenHands banner box & debug spam immediately before any SDK import
os.environ["OPENHANDS_SUPPRESS_BANNER"] = "1"
os.environ["LITELLM_LOG"] = "CRITICAL"

for _logger_name in ["openhands", "litellm", "LiteLLM", "httpx", "httpcore", "urllib3", "asyncio"]:
    logging.getLogger(_logger_name).setLevel(logging.CRITICAL)

try:
    import litellm
    litellm.suppress_debug_info = True
    litellm.set_verbose = False
except ImportError:
    pass

import argparse
from pathlib import Path
from typing import Optional

from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.orchestrator import Orchestrator
from orchestrator.utils import ConsoleOutput


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-Agent Software Development Orchestrator powered by OpenHands SDK & Skills."
    )
    parser.add_argument(
        "task",
        nargs="?",
        default=None,
        help="Software development task description to execute.",
    )
    parser.add_argument(
        "--mode",
        choices=["dev-test", "full", "audit"],
        default="dev-test",
        help="Pipeline mode: 'dev-test' (MVP), 'full' (4-Agent Pipeline), or 'audit' (Deep Codebase Analysis).",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Target workspace directory for code generation and testing.",
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="List all skills discovered in .agents/skills/ and exit.",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Check configured models, API keys, and settings.",
    )
    parser.add_argument(
        "--self-audit",
        action="store_true",
        help="Run offline self-evolution analysis on historical execution reports.",
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Open the interactive collapsible log explorer (arrow keys / dropdowns) for the latest session.",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Enable Human-in-the-Loop (HITL) interactive guidance and approval checkpoints.",
    )
    parser.add_argument(
        "--approval-gates",
        type=str,
        default=None,
        help="Comma-separated approval checkpoints (e.g. 'after_architect,after_developer,before_commit').",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose stream showing full agent thoughts and detailed action parameters.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode showing only milestone transitions and errors.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume pipeline execution from previous checkpoint in .orchestrator_state.json.",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable cross-run historical memory injection to save tokens.",
    )
    parser.add_argument(
        "--estimate",
        action="store_true",
        help="Pre-execution token & cost projection without invoking LLMs.",
    )
    return parser.parse_args()


def resolve_task_input(task_input: Optional[str]) -> str:
    """If task_input is a path to an existing file, read and return its content; otherwise return task_input."""
    if not task_input:
        return ""
    clean_val = task_input.strip().strip("'\"")
    try:
        p = Path(clean_val)
        if p.exists() and p.is_file():
            content = p.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                ConsoleOutput.agent_step(
                    "INPUT",
                    f"Loaded task specification from file: [bold]{p.name}[/bold]",
                    f"Path: {p} ({len(content)} chars, {len(content.split())} words)"
                )
                return content
    except Exception:
        pass
    return task_input


def handle_list_skills(skill_manager: SkillManager) -> None:
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
    from orchestrator.utils import ConnectivityChecker
    ConnectivityChecker.run_zero_token_audit(config)
    print("\n" + "=" * 50)
    print("Environment & Cost Safety Controls:")
    print(f"  Workspace:             {config.workspace_path}")
    print(f"  Max Iterations Cap:    {config.max_iterations}")
    print(f"  Max Output Tokens:     {config.max_tokens_per_call}")
    print(f"  Max Budget (USD):      ${config.max_budget_usd:.2f}")
    print(f"  Circuit Breaker:       Trigger on {config.circuit_breaker_threshold} identical consecutive failures")
    print(f"  Auto Git Commit:       {config.auto_commit}")
    print(f"  Interactive (HITL):    {config.interactive}")
    print(f"  Approval Gates:        {config.approval_gates or 'None'}")
    print(f"  Verbosity Level:       {config.verbosity}")
    print("=" * 50)


def interactive_wizard(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    default_mode: Optional[str] = None
) -> tuple[str, str, Path]:
    """Interactive prompt wizard for users running without command-line arguments."""
    ConsoleOutput.banner(
        "Antigravity Multi-Agent Orchestrator",
        f"Active Skills: {len(skill_manager.available_skills)} loaded"
    )
    
    try:
        if default_mode == "audit":
            task_prompt = "\n📝 Audit Focus Directive [Default: Full codebase architecture & security audit]: "
            task_in = input(task_prompt).strip()
            task = task_in or "Comprehensive codebase architecture, security, and bug audit."
            mode = "audit"
        else:
            print("\nEnter the software task you want the multi-agent team to build.")
            print("Example: 'Create a JWT authentication service with token revocation and pytest tests'")
            task = input("\n📝 Task Description: ").strip()
            while not task:
                task = input("Please enter a non-empty task description: ").strip()

            if default_mode in ("dev-test", "full"):
                mode = default_mode
            else:
                print("\nChoose Pipeline Execution Mode:")
                print("  [1] Dev-Test Loop (Developer writes code, Tester runs pytest in loop) [Fast]")
                print("  [2] Full 4-Agent Pipeline (Architect -> Dev -> Test -> Independent Reviewer) [Complete]")
                print("  [3] Deep Code Analysis & Audit (Static AST + LLM Auditor -> AUDIT_REPORT.md) [Audit]")
                mode_choice = input("Select mode [1/2/3, default 1]: ").strip()
                if mode_choice == "3":
                    mode = "audit"
                elif mode_choice == "2":
                    mode = "full"
                else:
                    mode = "dev-test"

        ws_input = input(f"Target workspace directory [Default: {config.workspace_path}]: ").strip()
        workspace = Path(ws_input).resolve() if ws_input else config.workspace_path

        return task, mode, workspace
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user.")
        sys.exit(0)


def handle_self_audit() -> None:
    from orchestrator.evolution import SystemAuditor
    auditor = SystemAuditor()
    report_file = auditor.audit_and_generate_report()
    ConsoleOutput.banner("System Evolution & Self-Improvement Audit")
    ConsoleOutput.success(f"Audit report generated at: {report_file}")
    if report_file.exists():
        print("\n" + report_file.read_text(encoding="utf-8"))


def handle_view_logs(workspace: Optional[Path] = None) -> None:
    from orchestrator.config import DEFAULT_DIAGNOSTICS_DIR
    from orchestrator.utils import SessionLogStore, InteractiveLogExplorer
    from orchestrator.utils.visualizer import LogStep
    import json
    import re

    logs_base = DEFAULT_DIAGNOSTICS_DIR / "logs"
    log_file = logs_base / "latest_session.json"

    if workspace:
        p_slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", workspace.name.lower()).strip("_") or "default"
        project_log = logs_base / p_slug / "latest_session.json"
        if project_log.exists():
            log_file = project_log
        else:
            ConsoleOutput.info(f"No dedicated log found for workspace '{workspace.name}', checking global latest log.")

    if not log_file.exists():
        ConsoleOutput.warning(f"No session log found at {log_file}. Run a development task first.")
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



def main() -> None:
    args = parse_args()
    config = OrchestratorConfig()
    if args.interactive:
        config.interactive = True
    if args.approval_gates:
        config.approval_gates = [g.strip() for g in args.approval_gates.split(",") if g.strip()]
    if args.verbose:
        config.verbosity = "verbose"
    elif args.quiet:
        config.verbosity = "quiet"

    from orchestrator.config import ORCHESTRATOR_ROOT
    skill_manager = SkillManager(ORCHESTRATOR_ROOT)

    if args.no_memory:
        config.enable_memory = False

    if args.estimate:
        from orchestrator.control import CostEstimator
        task_desc = resolve_task_input(args.task) or "Sample development task"
        result = CostEstimator.estimate(task_desc, args.mode, config)
        CostEstimator.render(result, config)
        sys.exit(0)

    if args.list_skills:
        handle_list_skills(skill_manager)
        sys.exit(0)

    if args.check_config:
        handle_check_config(config)
        sys.exit(0)

    if args.self_audit:
        handle_self_audit()
        sys.exit(0)

    if args.logs:
        handle_view_logs(args.workspace)
        sys.exit(0)

    # Check for --resume, direct --mode audit, or interactive wizard
    cp = None
    if args.resume:
        from orchestrator.pipeline.checkpoint import PipelineCheckpointManager
        target_ws = args.workspace or config.workspace_path
        cp = PipelineCheckpointManager.load(target_ws)
        if cp:
            ConsoleOutput.banner("Resuming Pipeline Execution", f"Phase: {cp.current_phase} | Run: {cp.run_id}")
            task = cp.task
            mode = cp.mode
            workspace = target_ws
        else:
            ConsoleOutput.warning(f"No checkpoint file found at {target_ws}. Starting fresh.")
            if args.mode == "audit":
                task = resolve_task_input(args.task) if args.task else "Comprehensive codebase architecture, security, and bug audit."
                mode = "audit"
                workspace = target_ws
            elif not args.task:
                task, mode, workspace = interactive_wizard(config, skill_manager, default_mode=args.mode)
            else:
                task = args.task
                mode = args.mode or "dev-test"
                workspace = target_ws
    elif args.mode == "audit":
        # Audit mode does not require an interactive task prompt — audit target is the codebase itself
        task = resolve_task_input(args.task) if args.task else "Comprehensive codebase architecture, security, and bug audit."
        mode = "audit"
        workspace = args.workspace or config.workspace_path
    elif not args.task:
        task, mode, workspace = interactive_wizard(config, skill_manager, default_mode=args.mode)
    else:
        task = resolve_task_input(args.task)
        mode = args.mode or "dev-test"
        workspace = args.workspace or config.workspace_path

    orchestrator = Orchestrator(config)
    orchestrator.run_task(
        task=task,
        mode=mode,
        workspace_override=workspace,
        checkpoint=cp,
    )


if __name__ == "__main__":
    main()
