"""Quiet live visualizer and interactive collapsible log explorer for Antigravity Orchestrator."""

import os
import sys
import time
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Set

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.live import Live

from openhands.sdk.conversation.visualizer import ConversationVisualizerBase
from openhands.sdk.event import Event


@dataclass
class LogStep:
    index: int
    role: str
    phase: str
    timestamp: str
    summary: str
    action_type: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    thought: Optional[str] = None
    observation: Optional[str] = None
    is_error: bool = False
    duration_s: float = 0.0


class SessionLogStore:
    """Stores full structured execution logs for interactive exploration."""

    def __init__(self, workspace_path: Optional[Path] = None):
        self.steps: List[LogStep] = []
        self.workspace_path = workspace_path
        self.current_role: str = "System"
        self.current_phase: str = "Initializing"
        self.milestones: List[str] = []
        self.start_time: float = time.time()

    def set_agent_context(self, role: str, phase: str) -> None:
        self.current_role = role
        self.current_phase = phase

    def add_step(
        self,
        summary: str,
        action_type: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        thought: Optional[str] = None,
        observation: Optional[str] = None,
        is_error: bool = False,
    ) -> LogStep:
        t_str = time.strftime("%H:%M:%S")
        step = LogStep(
            index=len(self.steps) + 1,
            role=self.current_role,
            phase=self.current_phase,
            timestamp=t_str,
            summary=summary,
            action_type=action_type,
            arguments=arguments,
            thought=thought,
            observation=observation,
            is_error=is_error,
            duration_s=round(time.time() - self.start_time, 2),
        )
        self.steps.append(step)
        short_msg = f"[{t_str}] [{self.current_role}] {summary}"
        self.milestones.append(short_msg)
        if len(self.milestones) > 6:
            self.milestones.pop(0)
        return step

    def save_to_file(self, target_dir: Optional[Path] = None) -> Path:
        out_dir = target_dir or Path("diagnostics/logs")
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "latest_session.json"
        data = {
            "session_start": self.start_time,
            "total_steps": len(self.steps),
            "steps": [asdict(s) for s in self.steps],
        }
        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return file_path


class OrchestratorLiveVisualizer(ConversationVisualizerBase):
    """Headless, quiet visualizer that suppresses prompt floods and powers the live fixed UI."""

    def __init__(self, log_store: SessionLogStore, console: Optional[Console] = None):
        super().__init__()
        self.store = log_store
        self.console = console or Console()
        self._last_thought: Optional[str] = None

    def on_event(self, event: Event) -> None:
        """Process conversation events silently into the store and update fixed status."""
        event_name = type(event).__name__

        # 1. Capture Agent Actions & Thoughts
        if event_name == "ActionEvent":
            action_obj = getattr(event, "action", None)
            thought = getattr(event, "thought", None) or getattr(action_obj, "thought", None)
            if thought:
                self._last_thought = str(thought).strip()

            action_kind = getattr(action_obj, "__class__", type(action_obj)).__name__
            args = {}
            summary = "Performing action"

            if hasattr(action_obj, "model_dump"):
                args = action_obj.model_dump()
            elif hasattr(action_obj, "__dict__"):
                args = action_obj.__dict__

            op = args.get("operation") or args.get("command") or action_kind
            path = args.get("path", "")
            if path:
                summary = f"{action_kind} ({op} {path})"
            elif "command" in args:
                cmd_preview = str(args.get("command", ""))[:40]
                summary = f"terminal ({cmd_preview})"
            else:
                summary = f"{action_kind} ({op})"

            self.store.add_step(
                summary=summary,
                action_type=action_kind,
                arguments=args,
                thought=self._last_thought,
            )

        # 2. Capture Tool Observations
        elif event_name == "ObservationEvent":
            obs_obj = getattr(event, "observation", None)
            is_err = getattr(obs_obj, "is_error", False)
            text_res = getattr(obs_obj, "text", "")
            if callable(text_res):
                try:
                    text_res = text_res()
                except Exception:
                    text_res = str(text_res)
            elif not text_res and hasattr(obs_obj, "message"):
                text_res = getattr(obs_obj, "message", "")

            # Attach observation to last step if pending
            if self.store.steps:
                last_step = self.store.steps[-1]
                if last_step.observation is None:
                    last_step.observation = str(text_res).strip()
                    last_step.is_error = is_err

        # 3. Capture General Messages & Errors
        elif event_name == "ConversationErrorEvent":
            err_msg = getattr(event, "error", "Unknown error")
            self.store.add_step(
                summary=f"Error encountered: {err_msg}",
                is_error=True,
                observation=str(err_msg),
            )


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
            content = Text("No recorded execution events in this session.", style="yellow")
            return Panel(content, title="Interactive Log Explorer", border_style="cyan")

        for idx, step in enumerate(steps):
            is_selected = (idx == self.selected_idx)
            is_expanded = (idx in self.expanded_indices)

            # Cursor & Expand indicator
            cursor = ">" if is_selected else " "
            drop_icon = "[v]" if is_expanded else "[>]"
            ind_style = "bold yellow" if is_selected else "dim"

            role_color = "cyan" if step.role == "Developer" else ("green" if step.role == "Tester" else "magenta")
            status_style = "bold red" if step.is_error else ("bold white" if is_selected else "white")

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
                    detail_text.append(f"  Thought:\n    {step.thought}\n\n", style="italic gray")
                if step.arguments:
                    args_str = json.dumps(step.arguments, indent=2, ensure_ascii=False)
                    detail_text.append(f"  Arguments:\n{args_str}\n\n", style="dim cyan")
                if step.observation:
                    obs_preview = step.observation[:800] + ("..." if len(step.observation) > 800 else "")
                    color = "red" if step.is_error else "green"
                    detail_text.append(f"  Observation Output:\n    {obs_preview}\n", style=color)

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
                        self.selected_idx = min(len(self.store.steps) - 1, self.selected_idx + 1)
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
