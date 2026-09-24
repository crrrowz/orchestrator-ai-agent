"""Terminal output styling and formatted status tables."""

from typing import Any, Dict, List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "danger": "bold red",
        "success": "bold green",
        "agent": "bold magenta",
        "developer": "bold magenta",
        "tester": "bold green",
        "architect": "bold cyan",
        "reviewer": "bold yellow",
        "auditor": "bold blue",
        "documentation": "bold white",
        "system": "bold blue",
    }
)

console = Console(theme=custom_theme, legacy_windows=False)


class ConsoleOutput:
    """Helper to display formatted, low-noise output during multi-agent orchestration."""

    @staticmethod
    def banner(title: str, subtitle: str = "") -> None:
        """Render a clean, modern header banner."""
        grid = Table.grid(padding=(0, 1), expand=True)
        grid.add_column(justify="left")
        grid.add_row(f"[bold cyan]{title}[/bold cyan]")
        if subtitle:
            grid.add_row(f"[dim]{subtitle}[/dim]")
        console.print(Panel(grid, border_style="cyan", padding=(0, 1), expand=False))

    @staticmethod
    def agent_step(
        agent_role: str, action: str, details: str = "", model: str = ""
    ) -> None:
        """Render a streamlined, inline agent step badge to prevent box clutter."""
        role_lower = agent_role.lower()
        role_color = (
            "magenta"
            if role_lower in ("developer", "dev")
            else (
                "green"
                if role_lower in ("tester", "test")
                else (
                    "cyan"
                    if role_lower in ("architect", "arch")
                    else ("yellow" if role_lower in ("reviewer", "review") else "blue")
                )
            )
        )
        model_str = f" [dim]({model})[/dim]" if model else ""
        header = f"[{role_color}][{agent_role.upper()}][/{role_color}]{model_str}"
        console.print(f" {header} [bold white]{action}[/bold white]")
        if details:
            for line in details.splitlines()[:3]:
                console.print(f"   [dim]↳ {line}[/dim]")

    @staticmethod
    def pipeline_stage(
        stage_name: str,
        current_idx: int = 1,
        total_stages: int = 4,
        description: str = "",
    ) -> None:
        """Render a high-level pipeline progress indicator."""
        stage_badge = f"[bold cyan]Stage [{current_idx}/{total_stages}][/bold cyan] [bold white]{stage_name}[/bold white]"
        if description:
            stage_badge += f" — [dim]{description}[/dim]"
        console.print(f"\n[bold blue]━━━[/bold blue] {stage_badge}")

    @staticmethod
    def success(message: str) -> None:
        console.print(f" [bold green][✓ OK][/bold green] {message}")

    @staticmethod
    def info(message: str) -> None:
        console.print(f" [bold cyan][INFO][/bold cyan] {message}")

    @staticmethod
    def error(message: str) -> None:
        console.print(f" [bold red][✗ ERR][/bold red] {message}")

    @staticmethod
    def warning(message: str) -> None:
        console.print(f" [bold yellow][! WARN][/bold yellow] {message}")

    @staticmethod
    def test_failure_callout(command: str, failure_text: str) -> None:
        """Render a structured diagnostic card for test failures."""
        grid = Table.grid(padding=(0, 1))
        grid.add_column(style="bold red", width=14)
        grid.add_column(style="white")
        grid.add_row("Test Command:", f"[bold white]{command}[/bold white]")

        # Truncate failure snippet to reasonable size
        snippet_lines = failure_text.splitlines()
        preview = "\n".join(snippet_lines[:15])
        if len(snippet_lines) > 15:
            preview += (
                f"\n[dim]... [{len(snippet_lines) - 15} lines truncated] ...[/dim]"
            )
        grid.add_row("Failure Output:", f"[yellow]{preview}[/yellow]")

        panel = Panel(
            grid,
            title="[bold red]🧪 Test Suite Failures Detected[/bold red]",
            border_style="red",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def summary_table(
        iterations: int = 1,
        status: str = "SUCCESS",
        commit_hash: str = "",
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
        iteration: Optional[int] = None,
        duration_seconds: Optional[float] = None,
        report_path: Optional[str] = None,
    ) -> None:
        actual_iterations = iteration if iteration is not None else iterations
        status_style = (
            "bold green" if status in ("SUCCESS", "CONVERGED_CLEAN") else "bold red"
        )
        status_icon = "✓" if status in ("SUCCESS", "CONVERGED_CLEAN") else "✗"

        table = Table(
            title="🎯 Pipeline Execution Summary",
            border_style="blue",
            header_style="bold cyan",
            padding=(0, 1),
        )
        table.add_column("Metric", style="bold white", width=22)
        table.add_column("Result", style="white")

        table.add_row(
            "Final Status", f"[{status_style}]{status_icon} {status}[/{status_style}]"
        )
        table.add_row("Iterations Completed", str(actual_iterations))
        if duration_seconds is not None and duration_seconds > 0:
            table.add_row("Execution Duration", f"{duration_seconds:.1f}s")
        if total_tokens > 0:
            table.add_row("Total Tokens Consumed", f"{total_tokens:,}")
        if total_cost_usd > 0.0 or total_tokens > 0:
            cost_str = (
                f"${total_cost_usd:.4f}"
                if total_cost_usd > 0.0
                else "$0.0000 (Free Tier)"
            )
            table.add_row("Total Estimated Cost", cost_str)
        if commit_hash:
            table.add_row("Git Checkpoint Hash", f"[cyan]{commit_hash}[/cyan]")
        if report_path:
            table.add_row("Diagnostic Report", f"[dim]{report_path}[/dim]")

        console.print(table)

    @staticmethod
    def skills_table(skills: List[Tuple[str, str, str]]) -> None:
        """Render a structured table of architectural and testing skills."""
        table = Table(
            title="🧩 Discovered Skills & Agent Capabilities",
            border_style="cyan",
            header_style="bold cyan",
            padding=(0, 1),
        )
        table.add_column("Skill Name", style="bold magenta", width=28)
        table.add_column("Domain / Category", style="cyan", width=20)
        table.add_column("Description", style="white")

        for name, category, desc in skills:
            table.add_row(name, category, desc)

        console.print(table)

    @staticmethod
    def config_table(sections: Dict[str, Dict[str, Any]]) -> None:
        """Render a comprehensive, categorized configuration verification table."""
        console.print("\n[bold cyan]Environment & Cost Safety Controls:[/bold cyan]")
        table = Table(
            title="⚙️ Orchestrator Configuration & Safety Controls",
            border_style="cyan",
            header_style="bold cyan",
            padding=(0, 1),
        )
        table.add_column("Category", style="bold cyan", width=36)
        table.add_column("Setting", style="bold white", width=28)
        table.add_column("Active Value", style="white")

        for category, settings in sections.items():
            first = True
            for key, val in settings.items():
                cat_col = category if first else ""
                table.add_row(cat_col, key, str(val))
                first = False

        console.print(table)

    @staticmethod
    def quota_error(error: Any) -> None:
        """Render a formatted, high-visibility card when an upstream LLM quota ceiling is exceeded."""
        provider = getattr(error, "provider", "LLM Provider")
        message = getattr(error, "message", str(error))
        reset_info = getattr(error, "reset_info", "")
        remedy = getattr(error, "remedy", "")

        grid = Table.grid(padding=(0, 1))
        grid.add_column(style="bold yellow", width=14)
        grid.add_column(style="white")
        grid.add_row("Provider:", f"[bold cyan]{provider}[/bold cyan]")
        grid.add_row(
            "Status:",
            "[bold red]HTTP 429 Too Many Requests (Quota Exhausted)[/bold red]",
        )
        grid.add_row("Details:", f"[yellow]{message}[/yellow]")
        if reset_info:
            grid.add_row("Reset Info:", f"[dim]{reset_info}[/dim]")
        if remedy:
            grid.add_row("Remedy:", f"[bold green]{remedy}[/bold green]")

        panel = Panel(
            grid,
            title="[bold red]◈ Upstream Provider Quota Ceiling Exceeded[/bold red]",
            border_style="red",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def provider_error(
        provider: str = "LLM Provider",
        error_type: str = "Provider Error",
        message: str = "",
        remedy: str = "",
        code: Optional[int] = None,
    ) -> None:
        """Render a formatted, high-visibility card for any upstream LLM provider error."""
        grid = Table.grid(padding=(0, 1))
        grid.add_column(style="bold yellow", width=14)
        grid.add_column(style="white")
        grid.add_row("Provider:", f"[bold cyan]{provider}[/bold cyan]")
        status_text = f"[bold red]{error_type}{f' ({code})' if code else ''}[/bold red]"
        grid.add_row("Status:", status_text)
        grid.add_row("Details:", f"[yellow]{message}[/yellow]")
        if remedy:
            grid.add_row("Action Needed:", f"[bold green]{remedy}[/bold green]")

        panel = Panel(
            grid,
            title=f"[bold red]◈ Upstream Provider Error ({provider})[/bold red]",
            border_style="red",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def execution_error(
        title: str = "Execution Error",
        message: str = "",
        hint: str = "",
    ) -> None:
        """Render a formatted, high-visibility panel for runtime errors."""
        grid = Table.grid(padding=(0, 1))
        grid.add_column(style="bold yellow", width=14)
        grid.add_column(style="white")
        grid.add_row("Status:", f"[bold red]{title}[/bold red]")
        grid.add_row("Details:", f"[yellow]{message}[/yellow]")
        if hint:
            grid.add_row("Action Needed:", f"[bold green]{hint}[/bold green]")

        panel = Panel(
            grid,
            title=f"[bold red]◈ {title}[/bold red]",
            border_style="red",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def sentinel_step(action: str, details: str = "") -> None:
        """Render a formatted step for Cognitive Sentinel supervision."""
        header = "[bold yellow]🛡️ [SENTINEL][/bold yellow]"
        msg = f"{header} [white]{action}[/white]"
        if details:
            msg += f" [dim]({details})[/dim]"
        console.print(msg)

    @staticmethod
    def self_healing_alert(file_path: str, issue: str, fix: str) -> None:
        """Render a high-visibility alert when self-healing intercepts and repairs code."""
        grid = Table.grid(padding=(0, 1))
        grid.add_column(style="bold yellow", width=14)
        grid.add_column(style="white")
        grid.add_row("Target File:", f"[bold cyan]{file_path}[/bold cyan]")
        grid.add_row("Detected:", f"[bold red]{issue}[/bold red]")
        grid.add_row("Self-Healed:", f"[bold green]{fix}[/bold green]")
        panel = Panel(
            grid,
            title="[bold yellow]🛡️ Cognitive Sentinel Auto-Healing Interception[/bold yellow]",
            border_style="yellow",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def cloud_failover_banner(
        failed_model: str, target_model: str, reason: str = ""
    ) -> None:
        """Render an alert when LLM mesh triggers automated provider failover."""
        grid = Table.grid(padding=(0, 1))
        grid.add_column(style="bold yellow", width=16)
        grid.add_column(style="white")
        grid.add_row("Degraded Model:", f"[bold red]{failed_model}[/bold red]")
        grid.add_row("Active Failover:", f"[bold green]{target_model}[/bold green]")
        if reason:
            grid.add_row("Trigger Reason:", f"[dim yellow]{reason}[/dim yellow]")
        panel = Panel(
            grid,
            title="[bold red]🌐 Cloud Resilience Mesh: Automated Failover[/bold red]",
            border_style="red",
            padding=(0, 1),
        )
        console.print(panel)
