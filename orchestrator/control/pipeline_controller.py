"""Signal-based non-blocking pipeline controller for pause, stop, and abort operations."""

import threading
from typing import Literal


class PipelineController:
    """Non-blocking control plane managing execution lifecycle signals."""

    def __init__(self):
        self._state: Literal["running", "paused", "stopping", "abort"] = "running"
        self._state_lock = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially

    @property
    def state(self) -> str:
        with self._state_lock:
            return self._state

    def request_pause(self) -> None:
        """Pause pipeline execution before the next step."""
        with self._state_lock:
            self._state = "paused"
            self._pause_event.clear()

    def resume(self) -> None:
        """Resume pipeline execution from paused state."""
        with self._state_lock:
            self._state = "running"
            self._pause_event.set()

    def request_stop_after_current(self) -> None:
        """Gracefully stop after the active step completes."""
        with self._state_lock:
            self._state = "stopping"

    def request_abort(self) -> None:
        """Immediately abort pipeline execution."""
        with self._state_lock:
            self._state = "abort"
            self._pause_event.set()  # Unblock if waiting on pause

    def check_should_continue(self) -> bool:
        """Returns True if the pipeline should proceed with next operation."""
        # Wait if paused until resumed or aborted
        self._pause_event.wait()
        with self._state_lock:
            return self._state not in ("stopping", "abort")
