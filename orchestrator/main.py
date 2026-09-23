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

    if not args.task:
        ConsoleOutput.error("No task specified. Provide a task description or use --help.")
        sys.exit(1)

    orchestrator = Orchestrator(config)
    orchestrator.run_task(
        task=args.task,
        mode=args.mode,
        workspace_override=args.workspace,
    )


if __name__ == "__main__":
    main()
