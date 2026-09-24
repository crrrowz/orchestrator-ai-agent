"""Terminal output styling and formatted status tables."""

from typing import Any, Optional
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
    }
)

console = Console(theme=custom_theme, legacy_windows=False)


class ConsoleOutput:
    """Helper to display formatted output during multi-agent orchestration."""

    @staticmethod
    def banner(title: str, subtitle: str = "") -> None:
        text = f"[bold cyan]{title}[/bold cyan]"
        if subtitle:
            text += f"\n[dim]{subtitle}[/dim]"
        console.print(Panel(text, border_style="cyan", expand=False))

    @staticmethod
    def agent_step(
        agent_role: str, action: str, details: str = "", model: str = ""
    ) -> None:
        header = f"[agent][{agent_role.upper()}][/agent]"
        if model:
            header += f" [cyan]({model})[/cyan]"
        msg = f"{header} {action}"
        if details:
            msg += f"\n[dim]{details}[/dim]"
        console.print(Panel(msg, border_style="magenta", expand=False))

    @staticmethod
    def success(message: str) -> None:
        console.print(f"[success][OK][/success] {message}")

    @staticmethod
    def info(message: str) -> None:
        console.print(f"[info][INFO][/info] {message}")

    @staticmethod
    def error(message: str) -> None:
        console.print(f"[danger][ERR][/danger] {message}")

    @staticmethod
    def warning(message: str) -> None:
        console.print(f"[warning][WARN][/warning] {message}")

    @staticmethod
    def summary_table(
        iterations: int = 1,
        status: str = "SUCCESS",
        commit_hash: str = "",
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
        iteration: Optional[int] = None,
    ) -> None:
        actual_iterations = iteration if iteration is not None else iterations
        table = Table(title="Pipeline Execution Summary", border_style="blue")
        table.add_column("Property", style="bold cyan")
        table.add_column("Value", style="white")

        table.add_row(
            "Status",
            f"[green]{status}[/green]"
            if status == "SUCCESS"
            else f"[red]{status}[/red]",
        )
        table.add_row("Total Iterations", str(actual_iterations))
        if total_tokens > 0:
            table.add_row("Total Tokens", f"{total_tokens:,}")
        if total_cost_usd > 0.0 or total_tokens > 0:
            cost_str = (
                f"${total_cost_usd:.4f}"
                if total_cost_usd > 0.0
                else "$0.0000 (Free Tier)"
            )
            table.add_row("Total Cost", cost_str)
        if commit_hash:
            table.add_row("Git Commit", commit_hash)

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
            padding=(1, 2),
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
            padding=(1, 2),
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
            padding=(1, 2),
        )
        console.print(panel)

    @staticmethod
    def sentinel_step(action: str, details: str = "") -> None:
        """Render a formatted step for Cognitive Sentinel supervision."""
        header = "[bold yellow]🛡️ [SENTINEL][/bold yellow]"
        msg = f"{header} [white]{action}[/white]"
        if details:
            msg += f"\n[dim]{details}[/dim]"
        console.print(Panel(msg, border_style="yellow", expand=False))

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
            padding=(1, 2),
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
            padding=(1, 2),
        )
        console.print(panel)
