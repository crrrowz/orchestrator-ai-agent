"""Compact Pytest Failure Parser (re-exported from orchestrator.analysis)."""

import warnings

warnings.warn(
    "Importing from 'orchestrator.utils.pytest_parser' is deprecated and scheduled for removal in Phase 3. "
    "Please import from 'orchestrator.analysis.pytest_parser' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from orchestrator.analysis.pytest_parser import (
    PytestOutputParser,
    TestExecutionResult,
    TestExecutionStatus,
)

__all__ = ["PytestOutputParser", "TestExecutionStatus", "TestExecutionResult"]
