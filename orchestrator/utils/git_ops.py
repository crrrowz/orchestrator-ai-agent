"""Git operations utility for managing workspace commits and branches."""

import warnings

warnings.warn(
    "Importing GitOps from 'orchestrator.utils.git_ops' is deprecated and scheduled for removal in Phase 3. "
    "Please import from 'orchestrator.vcs.git_ops' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from orchestrator.vcs.git_ops import GitOps

__all__ = ["GitOps"]
