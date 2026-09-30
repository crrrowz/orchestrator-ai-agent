"""Chaos and Erratic Execution Detector for agent tool streams."""

from __future__ import annotations

from typing import List, Sequence, Tuple
from orchestrator.governance.models import StepRecord


class ChaosDetector:
    """Detects chaotic, erratic, or thrashing agent behaviors before budget exhaustion."""

    def __init__(
        self,
        consecutive_error_threshold: int = 3,
        error_rate_threshold: float = 0.60,
        window_size: int = 6,
    ) -> None:
        self.consecutive_error_threshold = consecutive_error_threshold
        self.error_rate_threshold = error_rate_threshold
        self.window_size = window_size

    def check_chaos(self, steps: Sequence[StepRecord]) -> Tuple[bool, str]:
        """Examine recent steps and return (is_chaotic, explanation)."""
        if not steps or len(steps) < 3:
            return False, ""

        window = steps[-self.window_size:] if len(steps) >= self.window_size else steps

        # 1. Consecutive error burst
        trailing_errors = 0
        for s in reversed(steps):
            if s.is_error:
                trailing_errors += 1
            else:
                break

        if trailing_errors >= self.consecutive_error_threshold:
            recent_errs = [s.error_message for s in steps[-trailing_errors:] if s.error_message]
            sample_err = recent_errs[0] if recent_errs else "Repeated tool errors"
            return True, f"Error burst detected: {trailing_errors} consecutive failures ({sample_err[:100]})."

        # 2. High error density in sliding window
        errors_in_window = sum(1 for s in window if s.is_error)
        window_error_rate = errors_in_window / len(window)
        if len(window) >= 4 and window_error_rate >= self.error_rate_threshold:
            return True, f"High error density: {errors_in_window}/{len(window)} actions failed in current window."

        # 3. Repeated identical failing commands/actions
        failing_cmds: List[str] = [s.command or s.action_type for s in window if s.is_error]
        if failing_cmds and len(failing_cmds) >= 2:
            counts = collections_counter(failing_cmds)
            most_common, freq = counts.most_common(1)[0]
            if freq >= 2:
                return True, f"Repetitive execution failure: '{most_common}' failed {freq} times in window."

        return False, ""


def collections_counter(items: List[str]):
    import collections
    return collections.Counter(items)
