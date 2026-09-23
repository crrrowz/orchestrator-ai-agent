"""Antigravity-style rich syntax-highlighted diff rendering engine."""

import difflib
from pathlib import Path
from typing import List, Optional

from rich.panel import Panel

from orchestrator.rendering.output import console
from orchestrator.vcs.git_ops import GitOps


class DiffRenderer:
    """Renders side-by-side or inline code diffs with syntax highlighting and visual indicators."""

    @staticmethod
    def render_file_change(
        filepath: str,
        old_content: str,
        new_content: str,
        language: str = "python",
        title: Optional[str] = None,
    ) -> Panel:
        """Render a single file change with highlighted additions, removals, and unchanged lines."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        diff = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                lineterm="",
                fromfile="original",
                tofile="modified",
            )
        )
        if not diff:
            return Panel(
                f"[dim]No changes in {filepath}[/dim]",
                title=title or f"📄 {filepath}",
                border_style="dim",
            )

        diff_lines: List[str] = []
        for line in diff:
            if line.startswith("+++") or line.startswith("---"):
                diff_lines.append(f"[bold cyan]{line}[/bold cyan]")
            elif line.startswith("@@"):
                diff_lines.append(f"[bold yellow]{line}[/bold yellow]")
            elif line.startswith("+"):
                diff_lines.append(f"[green]{line}[/green]")
            elif line.startswith("-"):
                diff_lines.append(f"[red]{line}[/red]")
            else:
                diff_lines.append(f"[dim]{line}[/dim]")

        content = "\n".join(diff_lines)
        return Panel(
            content,
            title=title or f"📝 [bold cyan]{filepath}[/bold cyan]",
            border_style="cyan",
            expand=False,
        )

    @classmethod
    def render_git_diff_rich(
        cls,
        workspace: Path,
        staged: bool = False,
        max_lines_per_file: int = 50,
        max_chars: int = 4000,
    ) -> None:
        """Read workspace git diff and render formatted Rich panels per modified file."""
        git = GitOps(workspace)
        diff_text = git.get_diff(staged=staged)
        if not diff_text.strip():
            console.print("[dim]No working tree modifications detected.[/dim]")
            return

        # Split into per-file diff blocks
        file_diffs: List[str] = []
        current_block: List[str] = []

        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                if current_block:
                    file_diffs.append("\n".join(current_block))
                    current_block = []
            current_block.append(line)

        if current_block:
            file_diffs.append("\n".join(current_block))

        for file_diff in file_diffs:
            lines = file_diff.splitlines()
            target_name = "Modified File"
            for line in lines[:4]:
                if line.startswith("diff --git"):
                    parts = line.split()
                    if len(parts) >= 4:
                        target_name = parts[-1].lstrip("b/")
                    break

            colored_lines: List[str] = []
            count = 0
            for line in lines:
                count += 1
                if count > max_lines_per_file:
                    colored_lines.append("[dim]... [diff truncated for display][/dim]")
                    break
                if line.startswith("+++") or line.startswith("---"):
                    colored_lines.append(f"[bold cyan]{line}[/bold cyan]")
                elif line.startswith("@@"):
                    colored_lines.append(f"[bold yellow]{line}[/bold yellow]")
                elif line.startswith("+"):
                    colored_lines.append(f"[green]{line}[/green]")
                elif line.startswith("-"):
                    colored_lines.append(f"[red]{line}[/red]")
                else:
                    colored_lines.append(f"[dim]{line}[/dim]")

            panel_text = "\n".join(colored_lines)
            if len(panel_text) > max_chars:
                panel_text = (
                    panel_text[:max_chars] + "\n[dim]... [content truncated][/dim]"
                )

            panel = Panel(
                panel_text,
                title=f"📝 [bold cyan]{target_name}[/bold cyan]",
                border_style="cyan",
            )
            console.print(panel)
