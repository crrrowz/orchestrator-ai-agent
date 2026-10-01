"""FSM Checkpoint, Serialization Schema, and Zero-Token Safe Resume Manager."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from pydantic import BaseModel, Field

# FSMContext is referenced by forward-ref string in checkpoint methods


class MilestoneStateSnapshot(BaseModel):
    """Execution state of a single milestone."""

    milestone_id: str
    title: str
    content: str = ""
    target_files: List[str] = Field(default_factory=list)
    dependencies: List[int] = Field(default_factory=list)
    is_completed: bool = False
    verified_criteria_ids: List[str] = Field(default_factory=list)
    output_hash: Optional[str] = None


class FSMCheckpoint(BaseModel):
    """Complete, recoverable snapshot of the Guarded FSM execution state."""

    run_id: str
    task_description: str
    profile_name: str
    current_state: str
    state_history: List[str] = Field(default_factory=list)
    active_milestone_id: Optional[str] = None
    active_milestone_index: int = 0
    milestones: List[MilestoneStateSnapshot] = Field(default_factory=list)
    task_truth_graph_json: Optional[str] = None
    workspace_root_hash: str
    iteration_count: int = 1
    total_iterations: int = 0
    stagnation_counter: int = 0
    last_workspace_hash: Optional[str] = None
    mutated_files: List[str] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_tokens_consumed: int = 0
    saved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FSMCheckpointManager:
    """Manages cryptographic checkpointing and zero-token safe resume."""

    FILENAME = ".orchestrator_state.json"

    @classmethod
    def compute_workspace_hash(cls, workspace_path: Path) -> str:
        """Calculate composite SHA-256 digest of all source files in workspace."""
        hasher = hashlib.sha256()
        ignored_dirs = {
            "__pycache__",
            ".venv",
            "venv",
            "build",
            "dist",
            "node_modules",
            ".git",
            ".pytest_cache",
            ".ruff_cache",
            ".mypy_cache",
            ".coverage",
            "htmlcov",
            ".oragai_logs",
            ".diagnostics",
        }
        ignored_extensions = (
            ".pyc",
            ".pyo",
            ".log",
            ".db",
            ".sqlite",
            ".sqlite3",
            ".coverage",
        )
        ignored_files = {
            cls.FILENAME,
            "diagnostics.db",
            "coverage.xml",
            ".coverage",
        }

        files_to_hash: List[Path] = []
        if workspace_path.exists() and workspace_path.is_dir():
            for root, dirs, files in os.walk(workspace_path):
                dirs[:] = [
                    d
                    for d in dirs
                    if d not in ignored_dirs
                    and not (d.startswith(".") and d not in (".github", ".agents"))
                ]
                for f in sorted(files):
                    if (
                        f not in ignored_files
                        and not f.endswith(ignored_extensions)
                        and not f.startswith(".orchestrator_")
                    ):
                        files_to_hash.append(Path(root) / f)

        for fp in sorted(files_to_hash):
            try:
                rel_p = str(fp.relative_to(workspace_path)).replace("\\", "/")
                hasher.update(rel_p.encode("utf-8"))
                hasher.update(fp.read_bytes())
            except Exception:
                continue

        return hasher.hexdigest()

    @classmethod
    def get_checkpoint_path(cls, workspace: Path) -> Path:
        """Resolve absolute path to state file."""
        return workspace.resolve() / cls.FILENAME

    @classmethod
    def save_checkpoint(cls, context: "FSMContext") -> Path:
        """Persist current FSM execution state to disk."""
        ws = context.workspace_path
        ws_hash = cls.compute_workspace_hash(ws)

        graph_json = None
        if context.task_truth_graph is not None:
            if hasattr(context.task_truth_graph, "model_dump_json"):
                graph_json = context.task_truth_graph.model_dump_json()
            elif hasattr(context.task_truth_graph, "json"):
                graph_json = context.task_truth_graph.json()
            else:
                graph_json = json.dumps(str(context.task_truth_graph))

        milestone_snapshots: List[MilestoneStateSnapshot] = []
        for ms in context.milestone_dag:
            ms_id = str(getattr(ms, "index", getattr(ms, "id", "MS-01")))
            ms_title = str(getattr(ms, "title", f"Milestone {ms_id}"))
            ms_content = str(getattr(ms, "content", ""))
            ms_targets = list(getattr(ms, "target_files", []))
            ms_deps = list(getattr(ms, "dependencies", []))
            ms_completed = bool(getattr(ms, "is_completed", False))
            milestone_snapshots.append(
                MilestoneStateSnapshot(
                    milestone_id=ms_id,
                    title=ms_title,
                    content=ms_content,
                    target_files=ms_targets,
                    dependencies=ms_deps,
                    is_completed=ms_completed,
                )
            )

        checkpoint = FSMCheckpoint(
            run_id=context.run_id,
            task_description=context.task_description,
            profile_name=getattr(context.profile, "mode", "dev-test").value
            if hasattr(getattr(context.profile, "mode", None), "value")
            else str(getattr(context.profile, "mode", "dev-test")),
            current_state=context.current_state.value
            if hasattr(context.current_state, "value")
            else str(context.current_state),
            state_history=[
                s.value if hasattr(s, "value") else str(s)
                for s in context.state_history
            ],
            active_milestone_id=context.active_milestone_id,
            active_milestone_index=getattr(context, "active_milestone_index", 0),
            milestones=milestone_snapshots,
            task_truth_graph_json=graph_json,
            workspace_root_hash=ws_hash,
            iteration_count=context.iteration_count,
            total_iterations=getattr(context, "total_iterations", context.iteration_count),
            stagnation_counter=getattr(context, "stagnation_counter", 0),
            last_workspace_hash=getattr(context, "last_workspace_hash", None),
            mutated_files=sorted(list(getattr(context, "mutated_files", []))),
            total_cost_usd=context.total_cost_usd,
            total_tokens_consumed=context.total_tokens_consumed,
            metadata=dict(context.metadata),
        )

        path = cls.get_checkpoint_path(ws)
        path.write_text(checkpoint.model_dump_json(indent=2), encoding="utf-8")
        return path

    @classmethod
    def load_checkpoint(cls, workspace: Path) -> Optional[FSMCheckpoint]:
        """Read and validate serialized checkpoint from disk."""
        path = cls.get_checkpoint_path(workspace)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return FSMCheckpoint.model_validate(data)
        except Exception:
            return None

    @classmethod
    def clear_checkpoint(cls, workspace: Path) -> bool:
        """Remove state checkpoint after successful terminal execution."""
        path = cls.get_checkpoint_path(workspace)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception:
                return False
        return False
