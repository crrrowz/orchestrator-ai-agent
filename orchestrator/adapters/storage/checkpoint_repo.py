"""SQLite and File-Based Checkpoint Store.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from orchestrator.domain.task_truth import TaskTruthGraph


class CheckpointRepository:
    """Persists and loads TaskTruthGraph state snapshots."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.checkpoint_dir = workspace_path / ".orchestrator_checkpoints"

    def save_checkpoint(self, graph: TaskTruthGraph) -> str:
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.checkpoint_dir / f"{graph.task_id}_checkpoint.json"
        file_path.write_text(graph.model_dump_json(indent=2), encoding="utf-8")
        return str(file_path)

    def load_latest_checkpoint(self, task_id: str) -> Optional[TaskTruthGraph]:
        file_path = self.checkpoint_dir / f"{task_id}_checkpoint.json"
        if not file_path.exists():
            return None
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return TaskTruthGraph.model_validate(data)
