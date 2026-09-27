"""Rollback Manager & Health Preservation Controller.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant 7: Monotonic Codebase Health (ΔCHI >= 0.0) and Atomic Rollbacks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from orchestrator.adapters.vcs.git_adapter import GitOpsAdapter


class RollbackManager:
    """Manages automatic rollbacks when health or test regression occurs."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.adapter = GitOpsAdapter(workspace_path)
        self._last_checkpoint_sha: Optional[str] = None

    def record_checkpoint(self, milestone_id: str, message: str) -> str:
        sha = self.adapter.create_atomic_checkpoint(milestone_id, message)
        self._last_checkpoint_sha = sha
        return sha

    def can_rollback(self) -> bool:
        return self._last_checkpoint_sha is not None

    def execute_health_rollback(
        self, previous_chi: float, current_chi: float
    ) -> bool:
        if current_chi < previous_chi and self.can_rollback():
            assert self._last_checkpoint_sha is not None
            return self.adapter.rollback_to_checkpoint(self._last_checkpoint_sha)
        return False
