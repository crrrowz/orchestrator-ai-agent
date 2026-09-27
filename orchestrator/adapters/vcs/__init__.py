"""VCS Adapters Package.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from orchestrator.adapters.vcs.git_adapter import GitOpsAdapter
from orchestrator.adapters.vcs.rollback_manager import RollbackManager

__all__ = ["GitOpsAdapter", "RollbackManager"]
