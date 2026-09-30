"""Progress Monitor: Observes and records actual agent actions and observations."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set
from orchestrator.governance.models import ProgressMetricsSnapshot, StepRecord
from orchestrator.governance.progress_metrics import ProgressMetricsCalculator


class ProgressMonitor:
    """Passively observes agent execution steps without altering agent action stream."""

    def __init__(self) -> None:
        self._steps: List[StepRecord] = []
        self._mutated_files: Set[str] = set()
        self._read_files: Set[str] = set()
        self._step_counter: int = 0

    @property
    def steps(self) -> List[StepRecord]:
        return list(self._steps)

    @property
    def step_count(self) -> int:
        return len(self._steps)

    @property
    def mutated_files(self) -> Set[str]:
        return set(self._mutated_files)

    @property
    def read_files(self) -> Set[str]:
        return set(self._read_files)

    def record_step(
        self,
        action_type: str,
        tool_name: str,
        target_path: Optional[str] = None,
        command: Optional[str] = None,
        is_error: bool = False,
        error_message: Optional[str] = None,
    ) -> StepRecord:
        """Record an observed execution step."""
        self._step_counter += 1
        norm_op = (action_type or "").lower()
        norm_tool = (tool_name or "").lower()

        is_mutation = any(
            k in norm_op or k in norm_tool
            for k in ("write", "patch", "edit", "append", "delete", "create", "modify")
        )
        is_read = any(
            k in norm_op or k in norm_tool
            for k in ("read", "list", "view", "cat", "find", "grep", "search")
        )
        is_terminal = "terminal" in norm_op or "terminal" in norm_tool or bool(command)

        if is_mutation and target_path:
            self._mutated_files.add(str(target_path))
        if is_read and target_path:
            self._read_files.add(str(target_path))

        step = StepRecord(
            step_index=self._step_counter,
            action_type=action_type,
            tool_name=tool_name,
            target_path=target_path,
            command=command,
            is_mutation=is_mutation,
            is_read=is_read,
            is_terminal=is_terminal,
            is_error=is_error,
            error_message=error_message,
            timestamp=time.time(),
        )
        self._steps.append(step)
        return step

    def mark_last_step_error(self, error_message: Optional[str] = None) -> None:
        """Update the most recently recorded step to mark an error observation."""
        if self._steps:
            last = self._steps[-1]
            updated = StepRecord(
                step_index=last.step_index,
                action_type=last.action_type,
                tool_name=last.tool_name,
                target_path=last.target_path,
                command=last.command,
                is_mutation=last.is_mutation,
                is_read=last.is_read,
                is_terminal=last.is_terminal,
                is_error=True,
                error_message=error_message,
                timestamp=last.timestamp,
            )
            self._steps[-1] = updated

    def get_metrics(self) -> ProgressMetricsSnapshot:
        """Compute the current progress metrics across all observed steps."""
        return ProgressMetricsCalculator.calculate(self._steps)

    def reset(self) -> None:
        """Clear recorded steps for a fresh session."""
        self._steps.clear()
        self._mutated_files.clear()
        self._read_files.clear()
        self._step_counter = 0
