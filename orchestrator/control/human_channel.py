"""Human-in-the-Loop (HITL) Communication Channel and Approval Gates."""

import sys
import threading
from queue import Queue, Empty
from typing import Optional, Callable, Literal


class HumanInterventionChannel:
    """Thread-safe channel allowing human guidance injection, approval gates, and control signals."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._message_queue: Queue[str] = Queue()
        self._stop_requested = threading.Event()
        self._pause_requested = threading.Event()

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
        return (
            f"[HUMAN OPERATOR GUIDANCE]:\n"
            f"{guidance_block}\n\n"
            f"{base_prompt}"
        )

    def request_stop(self) -> None:
        """Signal the pipeline to stop after the current step."""
        self._stop_requested.set()

    def is_stop_requested(self) -> bool:
        """Check if stop signal was sent."""
        return self._stop_requested.is_set()

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
        if input_fn is None and not (hasattr(sys.stdin, "isatty") and sys.stdin.isatty()):
            return "approved"

        ask = input_fn or input
        preview_text = f"\n--- Context Preview ---\n{context_preview}\n-----------------------" if context_preview else ""
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
