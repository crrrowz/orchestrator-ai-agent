"""CLI entry point for Antigravity Multi-Agent Orchestrator."""

import argparse
import sys
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
        "-i",
        "--interactive",
        action="store_true",
        help="Launch interactive setup wizard.",
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
    ConsoleOutput.banner("Orchestrator Configuration & Model Matrix")
    print(f"Workspace: {config.workspace_path}")
    print(f"Max Iterations: {config.max_iterations}")
    print(f"Auto-commit: {config.auto_commit}")
    print("-" * 50)
    print(f"Developer Model:   {config.developer.model} (Skills: {', '.join(config.developer.skills)})")
    print(f"Tester Model:      {config.tester.model} (Skills: {', '.join(config.tester.skills)})")
    print(f"Reviewer Model:    {config.reviewer.model} (Skills: {', '.join(config.reviewer.skills)})")
    print(f"Architect Model:   {config.architect.model} (Skills: {', '.join(config.architect.skills)})")
    print("-" * 50)
    print("API Key Status:")
    print(f"  Anthropic:  {'Set' if config.anthropic_api_key else 'Missing'}")
    print(f"  OpenAI:     {'Set' if config.openai_api_key else 'Missing'}")
    print(f"  Gemini:     {'Set' if config.gemini_api_key else 'Missing'}")
    print(f"  OpenRouter: {'Set' if config.openrouter_api_key else 'Missing'}")


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

    # If no task is provided, run the friendly interactive wizard
    if not args.task or args.interactive:
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
