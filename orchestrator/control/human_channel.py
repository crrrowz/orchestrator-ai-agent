"""Human-in-the-Loop (HITL) Communication Channel and Approval Gates."""

import sys
import threading
from contextvars import ContextVar
from queue import Queue, Empty
from typing import Optional, Callable, Literal, Set

_active_channel_var: ContextVar[Optional["HumanInterventionChannel"]] = ContextVar(
    "active_channel", default=None
)


def get_active_channel() -> Optional["HumanInterventionChannel"]:
    """Retrieve the currently active HumanInterventionChannel for the current context."""
    return _active_channel_var.get()


def set_active_channel(channel: Optional["HumanInterventionChannel"]) -> None:
    """Register the active HumanInterventionChannel for the current context."""
    _active_channel_var.set(channel)


class HumanInterventionChannel:
    """Thread-safe channel allowing human guidance injection, approval gates, and control signals."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._message_queue: Queue[str] = Queue()
        self._stop_requested = threading.Event()
        self._pause_requested = threading.Event()
        self._session_allowed_paths: Set[str] = set()
        self._session_allowed_commands: Set[str] = set()

    def send_message(self, message: str) -> None:
        """Enqueue guidance message to be injected into the next agent prompt."""
        if message and message.strip():
            self._message_queue.put(message.strip())

    def has_message(self) -> bool:
        """Check if any human guidance messages are pending."""
        return not self._message_queue.empty()

    def get_message(self) -> Optional[str]:
        """Retrieve the next queued guidance message."""
        try:
            return self._message_queue.get_nowait()
        except Empty:
            return None

    def inject_into_prompt(self, base_prompt: str) -> str:
        """Prepend any pending human guidance messages to the agent prompt."""
        if not self.enabled:
            return base_prompt

        messages = []
        while self.has_message():
            msg = self.get_message()
            if msg:
                messages.append(msg)

        if not messages:
            return base_prompt

        guidance_block = "\n".join(f"- {m}" for m in messages)
        return f"[HUMAN OPERATOR GUIDANCE]:\n{guidance_block}\n\n{base_prompt}"

    def request_stop(self) -> None:
        """Signal the pipeline to stop after the current step."""
        self._stop_requested.set()

    def is_stop_requested(self) -> bool:
        """Check if stop signal was sent."""
        return self._stop_requested.is_set()

    def is_path_approved(self, path_str: str) -> bool:
        """Check if path has already been explicitly approved in this session."""
        return path_str in self._session_allowed_paths

    def is_command_approved(self, command_str: str) -> bool:
        """Check if command has already been explicitly approved in this session."""
        return command_str in self._session_allowed_commands

    def authorize_path(self, path_str: str) -> None:
        """Authorize a path for the remainder of the session."""
        self._session_allowed_paths.add(path_str)

    def authorize_command(self, command_str: str) -> None:
        """Authorize a command for the remainder of the session."""
        self._session_allowed_commands.add(command_str)

    def request_permission(
        self,
        role: str,
        action_type: str,
        target: str,
        reason: str = "",
        input_fn: Optional[Callable[[str], str]] = None,
    ) -> tuple[bool, str]:
        """Prompt developer for dynamic runtime permission escalation."""
        if not self.enabled:
            return False, "Permission denied: Human intervention channel is disabled."

        # Check if already approved during this session
        if action_type == "file_write" and target in self._session_allowed_paths:
            return (
                True,
                f"Permission already granted for path '{target}' in this session.",
            )
        if (
            action_type == "terminal_command"
            and target in self._session_allowed_commands
        ):
            return (
                True,
                f"Permission already granted for command '{target}' in this session.",
            )

        if input_fn is None and not (
            hasattr(sys.stdin, "isatty") and sys.stdin.isatty()
        ):
            return (
                False,
                f"Permission denied: Non-interactive environment cannot prompt developer for '{target}'.",
            )

        ask = input_fn or input
        prompt = (
            f"\n🛡️ [DEVELOPER PERMISSION REQUEST]\n"
            f"  Agent Role:  {role}\n"
            f"  Action:      {action_type}\n"
            f"  Target:      {target}\n"
            f"  Reason:      {reason}\n"
            f"Grant permission? [y] Approve / [n] Reject / [m] Provide Guidance: "
        )
        try:
            choice = ask(prompt).strip().lower()
            if choice in ("y", "yes"):
                if action_type == "file_write":
                    self.authorize_path(target)
                elif action_type == "terminal_command":
                    self.authorize_command(target)
                return True, "Permission explicitly granted by developer."
            elif choice in ("m", "modify", "g", "guidance"):
                feedback = ask("💬 Enter guidance for the agent: ").strip()
                if feedback:
                    self.send_message(feedback)
                return False, f"Permission denied with developer guidance: {feedback}"
            else:
                return False, "Permission rejected by developer."
        except (EOFError, KeyboardInterrupt):
            return False, "Permission request cancelled."

    def prompt_gate(
        self,
        gate_name: str,
        context_preview: str = "",
        input_fn: Optional[Callable[[str], str]] = None,
    ) -> Literal["approved", "rejected", "modified"]:
        """Interactive approval checkpoint for human review."""
        if not self.enabled:
            return "approved"

        # Check if stdin is interactive terminal or if an input_fn was provided
        if input_fn is None and not (
            hasattr(sys.stdin, "isatty") and sys.stdin.isatty()
        ):
            return "approved"

        ask = input_fn or input
        preview_text = (
            f"\n--- Context Preview ---\n{context_preview}\n-----------------------"
            if context_preview
            else ""
        )
        prompt = (
            f"\n🛑 [APPROVAL GATE: {gate_name}]"
            f"{preview_text}\n"
            f"Action: [y] Approve / [n] Reject / [m] Provide Guidance: "
        )
        try:
            choice = ask(prompt).strip().lower()
            if choice in ("y", "yes", ""):
                return "approved"
            elif choice in ("n", "no"):
                return "rejected"
            elif choice in ("m", "modify", "g", "guidance"):
                feedback = ask("💬 Enter guidance for the agent: ").strip()
                if feedback:
                    self.send_message(feedback)
                return "modified"
            return "approved"
        except (EOFError, KeyboardInterrupt):
            return "rejected"
