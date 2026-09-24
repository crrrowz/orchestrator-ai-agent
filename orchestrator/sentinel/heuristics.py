"""Cognitive heuristics and agent exploration drift detector."""

import json
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.core.constants import MAX_SEMANTIC_HALLUCINATION_STEPS


class HeuristicsDriftDetector:
    """Detects unproductive cognitive exploration loops, repeated tool calls, and token bleeding."""

    def __init__(
        self,
        max_steps_without_edit: int = MAX_SEMANTIC_HALLUCINATION_STEPS,
        token_burn_threshold: int = 35_000,
    ) -> None:
        self.max_steps_without_edit = max_steps_without_edit
        self.token_burn_threshold = token_burn_threshold
        self._recent_tool_calls: List[Tuple[str, str]] = []

    def evaluate_investigation_drift(
        self, role: str, steps: int, tokens_burned: int, edits_done: int
    ) -> Tuple[bool, str]:
        """Evaluates whether the agent has entered an exploratory cognitive drift.

        Returns:
            Tuple[bool, str]: (drift_detected, intervention_directive)
        """
        # Auditors may do more reads, but after high token burn with zero output, they should wrap up
        step_threshold = (
            self.max_steps_without_edit * 2
            if role.lower() in ("auditor", "reviewer")
            else self.max_steps_without_edit
        )

        if (
            steps >= step_threshold
            and edits_done == 0
            and tokens_burned >= self.token_burn_threshold
        ):
            directive = (
                f"SENTINEL INTERVENTION: Agent '{role}' has executed {steps} turns consuming "
                f"{tokens_burned:,} tokens without applying concrete file modifications. "
                "CEASE exploration immediately. Synthesize findings and execute the final action."
            )
            return True, directive

        return False, ""

    def check_repeated_tool_call(
        self, tool_name: str, tool_args: Optional[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """Detects if the agent is calling the exact same tool with identical arguments consecutively."""
        serialized_args = json.dumps(tool_args or {}, sort_keys=True, default=str)
        call_signature = (tool_name, serialized_args)

        self._recent_tool_calls.append(call_signature)
        if len(self._recent_tool_calls) > 10:
            self._recent_tool_calls.pop(0)

        # Check if last 2 calls are identical
        if len(self._recent_tool_calls) >= 2:
            if self._recent_tool_calls[-1] == self._recent_tool_calls[-2]:
                return True, f"Identical repeated call detected for tool '{tool_name}'."

        return False, ""

    def reset(self) -> None:
        """Clear recent tracking state."""
        self._recent_tool_calls.clear()
