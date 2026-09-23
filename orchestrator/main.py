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
        choices=["dev-test", "full"],
        default="dev-test",
        help="Pipeline mode: 'dev-test' (MVP) or 'full' (Architect + Dev + Test + Reviewer).",
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
    return parser.parse_args()


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
    print("=" * 50)


def interactive_wizard(config: OrchestratorConfig, skill_manager: SkillManager) -> tuple[str, str, Path]:
    """Interactive prompt wizard for users running without command-line arguments."""
    ConsoleOutput.banner(
        "Antigravity Multi-Agent Orchestrator",
        f"Active Skills: {len(skill_manager.available_skills)} loaded"
    )
    print("\nEnter the software task you want the multi-agent team to build.")
    print("Example: 'Create a JWT authentication service with token revocation and pytest tests'")
    
    try:
        task = input("\n📝 Task Description: ").strip()
        while not task:
            task = input("Please enter a non-empty task description: ").strip()

        print("\nChoose Pipeline Execution Mode:")
        print("  [1] Dev-Test Loop (Developer writes code, Tester runs pytest in loop) [Fast]")
        print("  [2] Full 4-Agent Pipeline (Architect -> Dev -> Test -> Independent Reviewer) [Complete]")
        mode_choice = input("Select mode [1/2, default 1]: ").strip()
        mode = "full" if mode_choice == "2" else "dev-test"

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


def handle_view_logs() -> None:
    from orchestrator.utils import SessionLogStore, InteractiveLogExplorer
    from orchestrator.utils.visualizer import LogStep
    import json

    log_file = Path("diagnostics/logs/latest_session.json")
    if not log_file.exists():
        ConsoleOutput.warning("No session log found at diagnostics/logs/latest_session.json. Run a development task first.")
        return

    try:
        data = json.loads(log_file.read_text(encoding="utf-8"))
        store = SessionLogStore()
        for step_dict in data.get("steps", []):
            store.steps.append(LogStep(**step_dict))
        InteractiveLogExplorer(store).run()
    except Exception as e:
        ConsoleOutput.error(f"Error loading session log: {str(e)}")


def main() -> None:
    args = parse_args()
    config = OrchestratorConfig()
    skill_manager = SkillManager(Path.cwd())

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
        handle_view_logs()
        sys.exit(0)

    # If no task is provided, run the friendly interactive wizard
    if not args.task:
        task, mode, workspace = interactive_wizard(config, skill_manager)
    else:
        task = args.task
        mode = args.mode
        workspace = args.workspace or config.workspace_path

    orchestrator = Orchestrator(config)
    orchestrator.run_task(
        task=task,
        mode=mode,
        workspace_override=workspace,
    )


if __name__ == "__main__":
    main()
