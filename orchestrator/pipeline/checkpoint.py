"""Pipeline checkpoint persistence and resume manager."""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class PipelineCheckpoint(BaseModel):
    """Schema for persisted pipeline checkpoint."""

    run_id: str
    task: str
    mode: str
    current_phase: str
    completed_phases: list[str] = Field(default_factory=list)
    tests_passed: bool = False
    review_approved: bool = False
    iteration: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineCheckpointManager:
    """Manages reading and writing `.orchestrator_state.json` checkpoints for pipeline resume."""

    FILENAME = ".orchestrator_state.json"

    @classmethod
    def get_checkpoint_path(cls, workspace: Path) -> Path:
        return workspace.resolve() / cls.FILENAME

    @classmethod
    def save(
        cls,
        workspace: Path,
        run_id: str,
        task: str,
        mode: str,
        current_phase: str,
        completed_phases: Optional[list[str]] = None,
        tests_passed: bool = False,
        review_approved: bool = False,
        iteration: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Persist current execution checkpoint to disk."""
        checkpoint = PipelineCheckpoint(
            run_id=run_id,
            task=task,
            mode=mode,
            current_phase=current_phase,
            completed_phases=completed_phases or [],
            tests_passed=tests_passed,
            review_approved=review_approved,
            iteration=iteration,
            metadata=metadata or {},
        )
        path = cls.get_checkpoint_path(workspace)
        path.write_text(checkpoint.model_dump_json(indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, workspace: Path) -> Optional[PipelineCheckpoint]:
        """Load valid checkpoint from disk if present."""
        path = cls.get_checkpoint_path(workspace)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return PipelineCheckpoint(**data)
        except Exception:
            return None

    @classmethod
    def clear(cls, workspace: Path) -> bool:
        """Remove checkpoint after successful pipeline conclusion."""
        path = cls.get_checkpoint_path(workspace)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception:
                return False
        return False
