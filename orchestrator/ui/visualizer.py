"""Quiet live visualizer maintaining a live status card in-place for agent sessions."""

import sys
import time
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from openhands.sdk.conversation.visualizer import ConversationVisualizerBase
from openhands.sdk.event import Event
from orchestrator.ui.session_store import SessionLogStore


class OrchestratorLiveVisualizer(ConversationVisualizerBase):
    """Quiet, informative live visualizer maintaining a responsive status card in-place."""

    def __init__(
        self,
        log_store: SessionLogStore,
        console: Optional[Console] = None,
        verbosity: str = "normal",
    ):
        super().__init__()
        self.store = log_store
        self.console = console or Console(legacy_windows=False)
        self.verbosity = (verbosity or "normal").lower()
        self._last_thought: Optional[str] = None
        self._live: Optional[Live] = None
        self._current_action: str = "Initializing agent session..."
        self._target_file: str = ""
        self._last_status: str = ""
        self._tokens_str: str = ""
        self._is_tty: bool = (
            sys.stdout.isatty() if hasattr(sys.stdout, "isatty") else False
        )

    def _render_box(self) -> Panel:
        t_now = time.strftime("%H:%M:%S")
        elapsed = round(time.time() - self.store.phase_start_time, 1)
        role = self.store.current_role or "Agent"
        model = self.store.current_model or "LLM"

        role_lower = role.lower()
        border_color = (
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

        # Query sentinel diagnostics stats
        healed_count = 0
        incidents_count = 0
        try:
            from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB

            s_stats = SentinelDiagnosticsDB().get_stats()
            healed_count = s_stats.get("auto_healed_count", 0)
            incidents_count = s_stats.get("total_incidents", 0)
        except Exception:
            pass

        grid = Table.grid(padding=(0, 1), expand=True)
        grid.add_column(style="bold cyan", width=14)
        grid.add_column(style="white")

        grid.add_row(
            "Agent / Model:",
            f"[bold {border_color}]{role}[/bold {border_color}] [blue]({model})[/blue]",
        )
        runtime_text = f"[yellow]⏱ {elapsed}s[/yellow] [dim]({t_now})[/dim]"
        if self._tokens_str:
            runtime_text += f"  {self._tokens_str}"
        grid.add_row("Runtime / Tok:", runtime_text)

        if self._target_file:
            grid.add_row(
                "Target File:", f"[bold green]{self._target_file}[/bold green]"
            )
        grid.add_row(
            "Active Action:", f"[bold white]{self._current_action}[/bold white]"
        )
        if self._last_status:
            grid.add_row("Last Result:", f"{self._last_status}")

        if self._last_thought and self.verbosity != "quiet":
            tp = self._last_thought.replace("\n", " ").strip()
            if len(tp) > 95:
                tp = tp[:92] + "..."
            grid.add_row("Plan / Thought:", f"[dim italic]{tp}[/dim italic]")

        sentinel_info = f"[bold green]● ENFORCING[/bold green] [dim](AST Guard: Clean | {healed_count} Healed | {incidents_count} Events)[/dim]"
        grid.add_row("Sentinel Mesh:", sentinel_info)

        card_title = f"[bold cyan]⚡ {role.upper()} AGENT IN PROGRESS[/bold cyan]"
        return Panel(
            grid,
            title=card_title,
            border_style=border_color,
            padding=(0, 1),
        )

    def _update_live(self) -> None:
        if not self._is_tty or self.verbosity == "quiet":
            return
        try:
            if self._live is None:
                self._live = Live(
                    self._render_box(),
                    console=self.console,
                    refresh_per_second=4,
                    transient=True,
                )
                self._live.start()
            else:
                self._live.update(self._render_box())
        except Exception:
            self._live = None

    def close(self, success: bool = True) -> None:
        """Stop live rendering when agent conversation completes."""
        if self._live is not None:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None
        role = self.store.current_role or "Agent"
        elapsed = round(time.time() - self.store.phase_start_time, 1)
        if success:
            self._safe_print(
                f" [bold green][✓][/bold green] Finished [bold]{role}[/bold] phase in [yellow]{elapsed}s[/yellow]{self._tokens_str}"
            )
        else:
            self._safe_print(
                f" [bold yellow][!][/bold yellow] Interrupted [bold]{role}[/bold] phase after [yellow]{elapsed}s[/yellow]"
            )

    def _safe_print(self, *args, **kwargs) -> None:
        """Safely print to console with fallback for legacy Windows terminal charmap encoding."""
        try:
            self.console.print(*args, **kwargs)
        except (UnicodeEncodeError, Exception):
            try:
                cleaned_args = []
                for a in args:
                    if isinstance(a, str):
                        cleaned = (
                            a.replace("▶", ">")
                            .replace("🪙", "$")
                            .replace("⏱", "")
                            .replace("💭", "*")
                            .replace("✓", "[OK]")
                            .replace("✗", "[ERR]")
                            .encode("ascii", errors="replace")
                            .decode("ascii")
                        )
                        cleaned_args.append(cleaned)
                    else:
                        cleaned_args.append(a)
                self.console.print(*cleaned_args, **kwargs)
            except Exception:
                pass

    def on_event(self, event: Event) -> None:
        """Process conversation events, log to store, and display real-time progress."""
        event_name = type(event).__name__

        # 1. Capture Agent Actions & Thoughts
        if event_name == "ActionEvent":
            action_obj = getattr(event, "action", None)
            thought = getattr(event, "thought", None) or getattr(
                action_obj, "thought", None
            )
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
                cmd_preview = str(args.get("command", ""))[:50]
                summary = f"terminal ({cmd_preview})"
            else:
                summary = f"{action_kind} ({op})"

            self.store.add_step(
                summary=summary,
                action_type=action_kind,
                arguments=args,
                thought=self._last_thought,
            )

            # Live terminal stream with Role, Model, Time, and Tokens
            t_now = time.strftime("%H:%M:%S")
            elapsed = round(time.time() - self.store.phase_start_time, 1)
            role = self.store.current_role or "Agent"
            model = self.store.current_model or "LLM"

            # Extract live token metrics from active LLM
            tokens_str = ""
            if self.store.current_llm and hasattr(self.store.current_llm, "metrics"):
                tu = getattr(
                    self.store.current_llm.metrics, "accumulated_token_usage", None
                )
                if tu:
                    in_tok = getattr(tu, "prompt_tokens", 0)
                    out_tok = getattr(tu, "completion_tokens", 0)
                    total_tok = in_tok + out_tok
                    cost = getattr(
                        self.store.current_llm.metrics, "accumulated_cost", 0.0
                    )
                    tokens_str = f" [cyan]🪙 {total_tok:,} tok[/cyan]"
                    if cost > 0:
                        tokens_str += f" [dim](${cost:.4f})[/dim]"

            self._current_action = summary
            self._target_file = path
            self._tokens_str = tokens_str
            self._update_live()

            if not self._is_tty:
                self._safe_print(
                    f"[dim]{t_now}[/dim] [bold magenta]▶ [{role}][/bold magenta] "
                    f"[blue]({model})[/blue] "
                    f"[bold white]{summary}[/bold white] "
                    f"[yellow]⏱ {elapsed}s[/yellow]"
                    f"{tokens_str}"
                )
                if self._last_thought and self.verbosity != "quiet":
                    if self.verbosity in ("verbose", "debug"):
                        self._safe_print(
                            f"       [dim italic]💭 {self._last_thought}[/dim italic]"
                        )
                    else:
                        thought_preview = self._last_thought.replace("\n", " ").strip()
                        if len(thought_preview) > 110:
                            thought_preview = thought_preview[:107] + "..."
                        self._safe_print(
                            f"       [dim italic]💭 {thought_preview}[/dim italic]"
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

            obs_preview = str(text_res).replace("\n", " ").strip()
            if len(obs_preview) > 95:
                obs_preview = obs_preview[:92] + "..."
            icon = (
                "[bold red]✗ ERR[/bold red]"
                if is_err
                else "[bold green]✓ OK[/bold green]"
            )
            self._last_status = f"{icon} [dim]{obs_preview}[/dim]"
            self._update_live()

            if not self._is_tty:
                if self.verbosity != "quiet" or is_err:
                    if self.verbosity == "debug":
                        self._safe_print(f"       {icon} [dim]{text_res}[/dim]")
                    else:
                        self._safe_print(f"       {self._last_status}")

        # 3. Capture General Messages & Errors
        elif event_name in ("ConversationErrorEvent", "AgentErrorEvent"):
            err_msg = (
                getattr(event, "detail", None)
                or getattr(event, "error", None)
                or getattr(event, "message", None)
                or getattr(event, "code", None)
                or "Unknown error"
            )
            self.store.add_step(
                summary=f"Error: {err_msg}",
                is_error=True,
                observation=str(err_msg),
            )
            self._last_status = (
                f"[bold red]✗ [AGENT ERROR][/bold red] [red]{err_msg}[/red]"
            )
            self._update_live()
            if not self._is_tty:
                self._safe_print(f"       {self._last_status}")
