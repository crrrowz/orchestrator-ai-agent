"""Interactive command-line wizard for non-argument runs."""

import sys
from pathlib import Path
from typing import Optional, Tuple

from orchestrator.cli.handlers import resolve_workspace_dir
from orchestrator.core.config import OrchestratorConfig
from orchestrator.rendering.output import ConsoleOutput
from orchestrator.skills.manager import SkillManager


def interactive_wizard(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    default_mode: Optional[str] = None,
) -> Tuple[str, str, Path]:
    """Interactive prompt wizard for users running without command-line arguments."""
    ConsoleOutput.banner(
        "Antigravity Multi-Agent Orchestrator",
        f"Active Skills: {len(skill_manager.available_skills)} loaded",
    )

    try:
        if default_mode == "audit":
            task_prompt = "\n📝 Audit Focus Directive [Default: Full codebase architecture & security audit]: "
            task_in = input(task_prompt).strip()
            task = (
                task_in
                or "Comprehensive codebase architecture, security, and bug audit."
            )
            mode = "audit"
        elif default_mode == "audit-fix":
            task_prompt = "\n📝 Fix Directive [Default: Autonomous codebase defect and optimization fix loop]: "
            task_in = input(task_prompt).strip()
            task = task_in or "Autonomous codebase defect and optimization fix loop."
            mode = "audit-fix"
        elif default_mode == "docs":
            task_prompt = "\n📝 Documentation Directive [Default: Generate full codebase documentation]: "
            task_in = input(task_prompt).strip()
            task = task_in or "Generate comprehensive project architecture and API documentation."
            mode = "docs"
        else:
            print("\nEnter the software task you want the multi-agent team to build.")
            print(
                "Example: 'Create a JWT authentication service with token revocation and pytest tests'"
            )
            task = input("\n📝 Task Description: ").strip()
            while not task:
                task = input("Please enter a non-empty task description: ").strip()

            if default_mode in ("dev-test", "full"):
                mode = default_mode
            else:
                print("\nChoose Pipeline Execution Mode:")
                print(
                    "  [1] Dev-Test Loop (Developer writes code, Tester runs pytest in loop) [Fast]"
                )
                print(
                    "  [2] Full 4-Agent Pipeline (Architect -> Dev -> Test -> Independent Reviewer) [Complete]"
                )
                print(
                    "  [3] Deep Code Analysis & Audit (Static AST + LLM Auditor -> AUDIT_REPORT.md) [Audit]"
                )
                print(
                    "  [4] Autonomous Audit & Auto-Fix Loop (Inspect & Auto-Remediate without Git) [Fix]"
                )
                mode_choice = input("Select mode [1/2/3/4, default 1]: ").strip()
                if mode_choice == "4":
                    mode = "audit-fix"
                elif mode_choice == "3":
                    mode = "audit"
                elif mode_choice == "2":
                    mode = "full"
                else:
                    mode = "dev-test"

        ws_input = input(
            f"Target workspace directory [Default: {config.workspace_path}]: "
        ).strip()
        workspace = resolve_workspace_dir(
            Path(ws_input) if ws_input else None, config.workspace_path
        )

        return task, mode, workspace
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user.")
        sys.exit(0)
