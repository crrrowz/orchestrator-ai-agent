"""Utilities package re-exporting modules for backward compatibility."""

import warnings

warnings.warn(
    "Importing from 'orchestrator.utils' is deprecated and scheduled for removal in Phase 3. "
    "Please import directly from the respective domain packages (e.g. orchestrator.rendering.output, "
    "orchestrator.vcs.git_ops, orchestrator.analysis.pytest_parser, orchestrator.skills.compressor, "
    "orchestrator.ui.visualizer, orchestrator.analysis.graft_context).",
    DeprecationWarning,
    stacklevel=2,
)

from orchestrator.analysis.connectivity import ConnectivityChecker
from orchestrator.analysis.graft_context import GraftContextProvider
from orchestrator.analysis.pytest_parser import (
    PytestOutputParser,
    TestExecutionResult,
    TestExecutionStatus,
)
from orchestrator.rendering.diff_renderer import DiffRenderer
from orchestrator.rendering.output import ConsoleOutput
from orchestrator.rendering.report_generator import MarkdownReportGenerator
from orchestrator.skills.compressor import CompactSkillInjector
from orchestrator.ui.log_explorer import InteractiveLogExplorer
from orchestrator.ui.session_store import SessionLogStore
from orchestrator.ui.visualizer import OrchestratorLiveVisualizer
from orchestrator.vcs.git_ops import GitOps

__all__ = [
    "GitOps",
    "ConsoleOutput",
    "ConnectivityChecker",
    "OrchestratorLiveVisualizer",
    "SessionLogStore",
    "InteractiveLogExplorer",
    "PytestOutputParser",
    "TestExecutionResult",
    "TestExecutionStatus",
    "GraftContextProvider",
    "CompactSkillInjector",
    "DiffRenderer",
    "MarkdownReportGenerator",
]
