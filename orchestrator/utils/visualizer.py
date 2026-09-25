"""Visualizer and interactive session explorer utilities (re-exported from orchestrator.ui)."""

import warnings

warnings.warn(
    "Importing from 'orchestrator.utils.visualizer' is deprecated and scheduled for removal in Phase 3. "
    "Please import from 'orchestrator.ui.visualizer', 'orchestrator.ui.session_store', or 'orchestrator.ui.log_explorer' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from orchestrator.ui.log_explorer import InteractiveLogExplorer
from orchestrator.ui.session_store import LogStep, SessionLogStore
from orchestrator.ui.visualizer import OrchestratorLiveVisualizer

__all__ = [
    "LogStep",
    "SessionLogStore",
    "OrchestratorLiveVisualizer",
    "InteractiveLogExplorer",
]
