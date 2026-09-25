"""Programmatic Graft Context Engine for Zero-Token Codebase Orientation."""

import warnings

warnings.warn(
    "Importing GraftContextProvider from 'orchestrator.utils.graft_context' is deprecated and scheduled for removal in Phase 3. "
    "Please import from 'orchestrator.analysis.graft_context' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from orchestrator.analysis.graft_context import GraftContextProvider

__all__ = ["GraftContextProvider"]
