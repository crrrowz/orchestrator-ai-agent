"""Universal Language Driver Port Definitions for ORAGAI.

Specification: docs/plans/P14_POLYGLOT_ADAPTATION_AND_INTELLIGENT_LANGUAGE_MESH_PLAN.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class LanguageType(str, Enum):
    """Supported language types."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    C = "c"
    CPP = "cpp"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    GENERIC = "generic"


class TestStatus(str, Enum):
    """Normalized test execution outcome statuses."""
    __test__ = False
    PASSED = "PASSED"
    FAILED = "FAILED"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"
    NO_TESTS = "NO_TESTS"


class StubSeverity(str, Enum):
    """Severity classification for placeholder code stubs."""
    CRITICAL = "CRITICAL"  # Blocks milestone / completion gate
    WARNING = "WARNING"    # Audit warning (e.g. TODO in test mock)


class SymbolKind(str, Enum):
    """Categorization for extracted AST and source entities."""
    CLASS = "CLASS"
    STRUCT = "STRUCT"
    INTERFACE = "INTERFACE"
    TRAIT = "TRAIT"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    ENUM = "ENUM"
    MODULE = "MODULE"
    TYPE_ALIAS = "TYPE_ALIAS"


@dataclass(frozen=True)
class SyntaxCheckResult:
    """Immutable result of a zero-token syntax validation check."""
    is_clean: bool
    error_count: int
    error_messages: List[str]
    failing_file: Optional[Path] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None


@dataclass(frozen=True)
class CompactedFailureFrame:
    """High-signal diagnostic frame extracted from test/compiler failure logs."""
    test_identifier: str
    file_path: str
    line_number: Optional[int]
    error_type: str
    diagnostic_message: str
    context_snippet: Optional[str] = None


@dataclass(frozen=True)
class TestExecutionOutcome:
    """Normalized outcome of a test suite execution run."""
    __test__ = False
    status: TestStatus
    exit_code: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration_seconds: float
    raw_stdout: str
    raw_stderr: str
    compacted_failures: List[CompactedFailureFrame]
    compaction_summary: str


@dataclass(frozen=True)
class StubViolation:
    """Record of a placeholder or stub pattern detected in source code."""
    file_path: Path
    line_number: int
    severity: StubSeverity
    symbol_name: str
    pattern_matched: str
    snippet: str


@dataclass(frozen=True)
class SymbolEntity:
    """Node in an AST symbol outline hierarchy."""
    name: str
    kind: SymbolKind
    start_line: int
    end_line: int
    signature: str
    docstring: Optional[str] = None
    children: List[SymbolEntity] = field(default_factory=list)


@dataclass(frozen=True)
class SymbolOutline:
    """Compressed symbol outline representation for agent context efficiency."""
    file_path: Path
    total_lines: int
    entities: List[SymbolEntity]
    raw_outline_text: str


@dataclass(frozen=True)
class StaticAnalysisResult:
    """Result of static analysis/linter run."""
    is_clean: bool
    violation_count: int
    violations: List[str]
    tool_name: str


@dataclass(frozen=True)
class CodebaseMetrics:
    """Ecosystem and size metrics collected for a workspace."""
    language: LanguageType
    total_files: int
    total_loc: int
    test_files_count: int
    test_loc: int
    ecosystem_metadata: Dict[str, Any] = field(default_factory=dict)


class DynamicEcosystemProfile(BaseModel):
    """Pydantic model representing a persistent, synthesized ecosystem profile.

    Stored atomically at `<workspace>/.oragai/language_profile.json` following
    a one-time discovery probe. Governs zero-token subsequent execution.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    language_name: str = Field(..., description="Normalized ecosystem identifier (e.g., 'zig', 'elixir', 'swift')")
    manifest_files: List[str] = Field(default_factory=list, description="List of manifest filenames (e.g., ['build.zig'])")
    file_extensions: List[str] = Field(default_factory=list, description="Source file extensions (e.g., ['.zig'])")
    syntax_check_template: str = Field(..., description="Shell template for zero-token syntax validation (e.g., 'zig ast-check {file_path}')")
    test_command_template: str = Field(..., description="Shell template for test execution (e.g., 'zig test {target_test}')")
    failure_regexes: List[str] = Field(default_factory=list, description="Regex patterns capturing test and compiler failures")
    stub_regexes: List[str] = Field(default_factory=list, description="Regex patterns identifying placeholder stubs")
    symbol_outline_command: Optional[str] = Field(None, description="Optional shell command to generate symbol outlines")
    version: str = Field("1.0.0", description="Schema version of this ecosystem profile")


@runtime_checkable
class ILanguageDriver(Protocol):
    """Universal Language Driver Protocol for Polyglot Workspaces."""

    @property
    def language_type(self) -> LanguageType:
        """Return the concrete LanguageType enum value."""
        ...

    @property
    def language_name(self) -> str:
        """Human-readable identifier for the language ecosystem."""
        ...

    def detect(self, workspace: Path) -> bool:
        """Evaluate if this driver matches the target workspace directory."""
        ...

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        """Perform zero-token deterministic syntax verification on a single source file."""
        ...

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        """Execute deterministic offline code formatting / auto-fixing."""
        ...

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        """Execute ecosystem linter/analyzer without LLM intervention."""
        ...

    def has_test_suite(self, workspace: Path) -> bool:
        """Check if test configurations or test files exist."""
        ...

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        """Generate the shell command required to execute the test suite."""
        ...

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        """Execute the test suite in a sandboxed subprocess and return parsed outcome."""
        ...

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        """Extract high-signal failure frames from raw test output."""
        ...

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        """Scan file for stub patterns, empty bodies, and TODO markers."""
        ...

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        """Generate symbol tree outline for token-efficient agent context injection."""
        ...

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        """Fold function and class bodies exceeding max_lines threshold."""
        ...

    def get_developer_prompt_guidance(self) -> str:
        """Return ecosystem-specific best practices for developer agent prompts."""
        ...

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        """Gather file counts, LOC, test metrics, and ecosystem metadata."""
        ...
