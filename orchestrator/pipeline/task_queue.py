"""Sequential Multi-Task Queue and Orchestration Engine for ORAGAI."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Union
from pydantic import BaseModel, Field

logger = logging.getLogger("orchestrator.pipeline.task_queue")


class TaskQueueItemStatus(str, Enum):
    """Execution status for an item in the sequential task queue."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class SequentialTaskItem(BaseModel):
    """Record representing a single discrete task in a sequential workflow."""

    task_id: str = Field(default_factory=lambda: f"TASK-{str(uuid.uuid4())[:6].upper()}")
    description: str
    status: TaskQueueItemStatus = TaskQueueItemStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


class SequentialTaskQueue(BaseModel):
    """Manages sequential execution and durable progress of a task list."""

    queue_id: str = Field(default_factory=lambda: f"Q-{str(uuid.uuid4())[:8]}")
    tasks: List[SequentialTaskItem] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    FILENAME: ClassVar[str] = ".oragai_task_queue.json"

    @classmethod
    def from_descriptions(
        cls, descriptions: List[str]
    ) -> SequentialTaskQueue:
        """Construct a new task queue from a list of plain-text task descriptions."""
        items = [
            SequentialTaskItem(
                task_id=f"TASK-{idx + 1:03d}",
                description=desc.strip(),
            )
            for idx, desc in enumerate(descriptions)
            if desc and desc.strip()
        ]
        return cls(tasks=items)

    @classmethod
    def from_file(cls, file_path: Path) -> SequentialTaskQueue:
        """Parse tasks from markdown or text file (e.g. TASKS.md or tasks.json)."""
        content = file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() == ".json":
            data = json.loads(content)
            if isinstance(data, list):
                return cls.from_descriptions([str(item) for item in data])
            if isinstance(data, dict) and "tasks" in data:
                return cls.model_validate(data)

        # Markdown / text lines parser: bullet lists or numbered lists
        lines = content.splitlines()
        tasks: List[str] = []
        for line in lines:
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue
            if cleaned.startswith(("- [ ]", "- [x]", "- [X]", "* [ ]", "* [x]")):
                tasks.append(cleaned[5:].strip())
            elif cleaned.startswith(("-", "*", "+")):
                tasks.append(cleaned[1:].strip())
            elif cleaned[0].isdigit() and ("." in cleaned[:4] or ")" in cleaned[:4]):
                sep_idx = cleaned.find(".") if "." in cleaned[:4] else cleaned.find(")")
                tasks.append(cleaned[sep_idx + 1:].strip())
            else:
                tasks.append(cleaned)

        return cls.from_descriptions(tasks)

    def save(self, workspace_path: Path) -> Path:
        """Persist task queue state to workspace."""
        self.updated_at = time.time()
        out_path = workspace_path / self.FILENAME
        out_path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return out_path

    @classmethod
    def load(cls, workspace_path: Path) -> Optional[SequentialTaskQueue]:
        """Load persisted task queue from workspace."""
        path = workspace_path / cls.FILENAME
        if not path.exists():
            return None
        try:
            return cls.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Could not load task queue from %s: %s", path, e)
            return None

    def get_next_pending(self) -> Optional[SequentialTaskItem]:
        """Return the next pending task item."""
        for t in self.tasks:
            if t.status == TaskQueueItemStatus.PENDING:
                return t
        return None

    def mark_in_progress(self, task_id: str) -> None:
        """Mark a task item as in-progress."""
        for t in self.tasks:
            if t.task_id == task_id:
                t.status = TaskQueueItemStatus.IN_PROGRESS
                break

    def mark_completed(
        self,
        task_id: str,
        result: Dict[str, Any],
        duration_seconds: float = 0.0,
    ) -> None:
        """Record completed result and duration for a task item."""
        for t in self.tasks:
            if t.task_id == task_id:
                t.status = TaskQueueItemStatus.COMPLETED
                t.result = result
                t.duration_seconds = duration_seconds
                break

    def mark_failed(
        self,
        task_id: str,
        result: Dict[str, Any],
        duration_seconds: float = 0.0,
        error_message: Optional[str] = None,
    ) -> None:
        """Record failed result for a task item."""
        for t in self.tasks:
            if t.task_id == task_id:
                t.status = TaskQueueItemStatus.FAILED
                t.result = result
                t.duration_seconds = duration_seconds
                t.error_message = error_message or result.get("error_message")
                break

    @property
    def is_all_completed(self) -> bool:
        """Return True if all tasks finished with COMPLETED status."""
        return bool(self.tasks) and all(
            t.status == TaskQueueItemStatus.COMPLETED for t in self.tasks
        )

    @property
    def has_failures(self) -> bool:
        """Return True if any task failed."""
        return any(t.status == TaskQueueItemStatus.FAILED for t in self.tasks)
