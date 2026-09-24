"""Interactive command-line wizard for non-argument runs."""

import sys
from pathlib import Path
from typing import Optional, Tuple
from rich.table import Table

from orchestrator.cli.handlers import resolve_task_input, resolve_workspace_dir
from orchestrator.core.config import OrchestratorConfig
from orchestrator.rendering.output import ConsoleOutput, console
from orchestrator.skills.manager import SkillManager


def interactive_wizard(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    default_mode: Optional[str] = None,
) -> Tuple[str, str, Path]:
    """Interactive prompt wizard for users running without command-line arguments."""
    ConsoleOutput.banner(
        "Antigravity Multi-Agent Orchestrator",
        f"Active Skills: {len(skill_manager.available_skills)} loaded | Workspace: {config.workspace_path}",
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
            task = (
                task_in
                or "Generate comprehensive project architecture and API documentation."
            )
            mode = "docs"
        else:
            console.print(
                "\n[bold cyan]What would you like the multi-agent team to build or solve?[/bold cyan]"
            )
            console.print(
                "[dim]Example: 'Create a JWT authentication service with token revocation and pytest tests'[/dim]"
            )
            task = input("\n📝 Task Description: ").strip()
            while not task:
                task = input("Please enter a non-empty task description: ").strip()

            if default_mode in ("dev-test", "full"):
                mode = default_mode
            else:
                table = Table(
                    title="Select Pipeline Execution Mode",
                    border_style="cyan",
                    header_style="bold cyan",
                    padding=(0, 1),
                )
                table.add_column("Key", style="bold yellow", justify="center", width=5)
                table.add_column("Pipeline Mode", style="bold white", width=22)
                table.add_column("Agent Workflow", style="cyan", width=34)
                table.add_column("Best For", style="dim")

                table.add_row(
                    "1",
                    "Dev-Test Loop",
                    "Developer ➔ Tester (Loop)",
                    "Fast iterative feature dev / bug fixes",
                )
                table.add_row(
                    "2",
                    "Full 4-Agent Pipeline",
                    "Architect ➔ Dev ➔ Test ➔ Review",
                    "Complete end-to-end architectures",
                )
                table.add_row(
                    "3",
                    "Codebase Deep Audit",
                    "Static AST + Auditor Agent",
                    "Security, bug & architectural audit",
                )
                table.add_row(
                    "4",
                    "Autonomous Audit & Fix",
                    "Scan ➔ Remediate ➔ Re-Verify",
                    "Self-healing zero-git remediation loop",
                )

                console.print()
                console.print(table)
                mode_choice = input("\nSelect mode [1/2/3/4, default 1]: ").strip()
                if mode_choice == "4":
                    mode = "audit-fix"
                elif mode_choice == "3":
                    mode = "audit"
                elif mode_choice == "2":
                    mode = "full"
                else:
                    mode = "dev-test"

        ws_input = input(
            f"\nTarget workspace directory [Default: {config.workspace_path}]: "
        ).strip()
        workspace = resolve_workspace_dir(
            Path(ws_input) if ws_input else None, config.workspace_path
        )

        return resolve_task_input(task), mode, workspace
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
