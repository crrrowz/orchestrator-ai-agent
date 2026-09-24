"""Base abstraction for Polyglot Project Adapters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ProjectAdapter(ABC):
    """Abstract interface defining language and framework operations for workspace analysis, auto-fixing, and testing."""

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Name of the programming language / ecosystem (e.g. 'python', 'nodejs', 'generic')."""
        pass

    @abstractmethod
    def detect(self, workspace: Path) -> bool:
        """Return True if this adapter matches the project in the workspace."""
        pass

    @abstractmethod
    def check_syntax(self, workspace: Path) -> Tuple[bool, List[str]]:
        """Perform offline zero-token syntax validation. Returns (is_clean, list_of_errors)."""
        pass

    @abstractmethod
    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        """Execute deterministic local code fixes/formatting without LLM invocation."""
        pass

    @abstractmethod
    def run_static_analysis(self, workspace: Path) -> Tuple[bool, List[str]]:
        """Run linter or static analysis tools. Returns (is_clean, list_of_issues)."""
        pass

    @abstractmethod
    def has_test_suite(self, workspace: Path) -> bool:
        """Return True if tests or test configurations exist in the workspace."""
        pass

    def get_test_command(self, workspace: Path) -> str:
        """Return the shell command to execute the test suite."""
        return "pytest -v"

    @abstractmethod
    def parse_test_failures(self, stdout: str, stderr: str) -> str:
        """Extract a compact summary of test failures to minimize prompt token overhead."""
        pass

    @abstractmethod
    def get_developer_prompt_guidance(self) -> str:
        """Return language-specific engineering best practices and architectural guidance."""
        pass

    @abstractmethod
    def collect_codebase_metrics(self, workspace: Path) -> Dict[str, Any]:
        """Gather source file counts, lines of code, and key statistics."""
        pass
