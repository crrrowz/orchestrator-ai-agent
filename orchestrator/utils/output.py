from typing import Optional
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
    def agent_step(agent_role: str, action: str, details: str = "", model: str = "") -> None:
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

        table.add_row("Status", f"[green]{status}[/green]" if status == "SUCCESS" else f"[red]{status}[/red]")
        table.add_row("Total Iterations", str(actual_iterations))
        if total_tokens > 0:
            table.add_row("Total Tokens", f"{total_tokens:,}")
        if total_cost_usd > 0.0 or total_tokens > 0:
            cost_str = f"${total_cost_usd:.4f}" if total_cost_usd > 0.0 else "$0.0000 (Free Tier)"
            table.add_row("Total Cost", cost_str)
        if commit_hash:
            table.add_row("Git Commit", commit_hash)

        console.print(table)

