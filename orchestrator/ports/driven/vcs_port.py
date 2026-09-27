"""Outbound Driven VCS & Rollback Port Protocol.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class VCSPort(Protocol):
    """Outbound port for GitOps operations and atomic rollbacks."""

    def create_atomic_checkpoint(self, milestone_id: str, message: str) -> str:
        ...

    def rollback_to_checkpoint(self, commit_sha: str) -> bool:
        ...

    def get_workspace_merkle_root(self) -> str:
        ...


@runtime_checkable
class RollbackControllerPort(Protocol):
    """Outbound port for automated rollback triggering upon health or test regression."""

    def can_rollback(self) -> bool:
        ...

    def trigger_health_rollback(self, previous_chi: float, current_chi: float) -> bool:
        ...
