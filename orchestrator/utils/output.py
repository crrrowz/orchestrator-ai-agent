"""Terminal output formatting using Rich for pipeline status and agent updates."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "agent": "bold magenta",
})

console = Console(theme=custom_theme)


class ConsoleOutput:
    """Helper to display formatted output during multi-agent orchestration."""

    @staticmethod
    def banner(title: str, subtitle: str = "") -> None:
        text = f"[bold cyan]{title}[/bold cyan]"
        if subtitle:
            text += f"\n[dim]{subtitle}[/dim]"
        console.print(Panel(text, border_style="cyan", expand=False))

    @staticmethod
    def agent_step(agent_role: str, action: str, details: str = "") -> None:
        msg = f"[agent][{agent_role.upper()}][/agent] {action}"
        if details:
            msg += f"\n[dim]{details}[/dim]"
        console.print(Panel(msg, border_style="magenta", expand=False))

    @staticmethod
    def success(message: str) -> None:
        console.print(f"[success]✔[/success] {message}")

    @staticmethod
    def error(message: str) -> None:
        console.print(f"[danger]✘[/danger] {message}")

    @staticmethod
    def warning(message: str) -> None:
        console.print(f"[warning]⚠[/warning] {message}")

    @staticmethod
    def summary_table(iterations: int, status: str, commit_hash: str = "") -> None:
        table = Table(title="Pipeline Execution Summary", border_style="blue")
        table.add_column("Property", style="bold cyan")
        table.add_column("Value", style="white")

        table.add_row("Status", f"[green]{status}[/green]" if status == "SUCCESS" else f"[red]{status}[/red]")
        table.add_row("Total Iterations", str(iterations))
        if commit_hash:
            table.add_row("Git Commit", commit_hash)

        console.print(table)
