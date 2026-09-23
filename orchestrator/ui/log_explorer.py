"""Collapsible keyboard-driven log viewer using terminal controls."""

import json
import os
import sys
from typing import Optional, Set

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from orchestrator.ui.session_store import SessionLogStore


class InteractiveLogExplorer:
    """Collapsible keyboard-driven log viewer using arrow keys (up/down/expand/collapse)."""

    def __init__(self, store: SessionLogStore, console: Optional[Console] = None):
        self.store = store
        self.console = console or Console()
        self.selected_idx: int = 0
        self.expanded_indices: Set[int] = set()

    def render_view(self) -> Panel:
        """Render the collapsible interactive tree and status panel."""
        table = Table.grid(padding=(0, 1))
        table.add_column("Indicator", justify="center", width=3)
        table.add_column("Index", justify="right", width=4)
        table.add_column("Time", style="dim", width=9)
        table.add_column("Role", style="bold cyan", width=12)
        table.add_column("Action / Summary", style="white")

        steps = self.store.steps
        if not steps:
            content = Text(
                "No recorded execution events in this session.", style="yellow"
            )
            return Panel(content, title="Interactive Log Explorer", border_style="cyan")

        for idx, step in enumerate(steps):
            is_selected = idx == self.selected_idx
            is_expanded = idx in self.expanded_indices

            # Cursor & Expand indicator
            cursor = ">" if is_selected else " "
            drop_icon = "[v]" if is_expanded else "[>]"
            ind_style = "bold yellow" if is_selected else "dim"

            role_color = (
                "cyan"
                if step.role == "Developer"
                else ("green" if step.role == "Tester" else "magenta")
            )
            status_style = (
                "bold red"
                if step.is_error
                else ("bold white" if is_selected else "white")
            )

            indicator_text = f"{cursor}{drop_icon}"
            table.add_row(
                Text(indicator_text, style=ind_style),
                Text(f"#{step.index}", style="dim"),
                Text(step.timestamp, style="dim"),
                Text(step.role, style=role_color),
                Text(step.summary, style=status_style),
            )

            # If dropdown expanded, render detail block
            if is_expanded:
                detail_text = Text()
                if step.thought:
                    detail_text.append(
                        f"  Thought:\n    {step.thought}\n\n", style="italic gray"
                    )
                if step.arguments:
                    args_str = json.dumps(step.arguments, indent=2, ensure_ascii=False)
                    detail_text.append(
                        f"  Arguments:\n{args_str}\n\n", style="dim cyan"
                    )
                if step.observation:
                    obs_preview = step.observation[:800] + (
                        "..." if len(step.observation) > 800 else ""
                    )
                    color = "red" if step.is_error else "green"
                    detail_text.append(
                        f"  Observation Output:\n    {obs_preview}\n", style=color
                    )

                detail_panel = Panel(
                    detail_text,
                    border_style="yellow" if is_selected else "dim",
                    title=f"[dim]Step #{step.index} Details[/dim]",
                    padding=(0, 1),
                )
                table.add_row("", "", "", "", detail_panel)

        instructions = Text(
            "[Up/Down: Navigate]  [Enter/Right: Open Dropdown]  [Left: Close]  [A: All]  [Q: Exit]",
            style="bold cyan",
        )

        return Panel(
            table,
            title="[bold cyan]Interactive Log Explorer (Collapsible Dropdowns)[/bold cyan]",
            subtitle=instructions,
            border_style="cyan",
            padding=(1, 2),
        )

    def run(self) -> None:
        """Run interactive loop with keyboard control."""
        if not self.store.steps:
            self.console.print("[yellow]No steps recorded to explore.[/yellow]")
            return

        # On non-interactive/redirected stdout, print static tree and return
        if not sys.stdin.isatty():
            self.console.print(self.render_view())
            return

        # Windows interactive key handling
        try:
            import msvcrt

            while True:
                # Clear terminal and render current view
                os.system("cls" if os.name == "nt" else "clear")
                self.console.print(self.render_view())

                ch = msvcrt.getch()

                # Arrow keys on Windows emit 0x00 or 0xE0 prefix
                if ch in (b"\x00", b"\xe0"):
                    sub_ch = msvcrt.getch()
                    if sub_ch == b"H":  # Up arrow
                        self.selected_idx = max(0, self.selected_idx - 1)
                    elif sub_ch == b"P":  # Down arrow
                        self.selected_idx = min(
                            len(self.store.steps) - 1, self.selected_idx + 1
                        )
                    elif sub_ch == b"M":  # Right arrow (expand)
                        self.expanded_indices.add(self.selected_idx)
                    elif sub_ch == b"K":  # Left arrow (collapse)
                        self.expanded_indices.discard(self.selected_idx)
                elif ch in (b"\r", b"\n", b" "):  # Enter or Space (toggle dropdown)
                    if self.selected_idx in self.expanded_indices:
                        self.expanded_indices.remove(self.selected_idx)
                    else:
                        self.expanded_indices.add(self.selected_idx)
                elif ch in (b"a", b"A"):  # Toggle all
                    if len(self.expanded_indices) == len(self.store.steps):
                        self.expanded_indices.clear()
                    else:
                        self.expanded_indices = set(range(len(self.store.steps)))
                elif ch in (b"q", b"Q", b"\x1b"):  # q or Escape
                    break

        except ImportError:
            # Fallback for non-Windows or environments without msvcrt
            self.console.print(self.render_view())

        os.system("cls" if os.name == "nt" else "clear")
