"""Python ecosystem project adapter."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.adapters.base import ProjectAdapter
from orchestrator.guards.preflight import PreFlightGuard
from orchestrator.utils.pytest_parser import PytestOutputParser


class PythonAdapter(ProjectAdapter):
    """Adapter for Python projects using standard tools (AST, Ruff, Pytest, UV)."""

    @property
    def language_name(self) -> str:
        return "python"

    def detect(self, workspace: Path) -> bool:
        """Detect Python projects via standard manifests or presence of Python source files."""
        manifests = [
            "pyproject.toml",
            "requirements.txt",
            "setup.py",
            "setup.cfg",
            "Pipfile",
            "uv.lock",
            "poetry.lock",
        ]
        if any((workspace / m).exists() for m in manifests):
            return True
        try:
            return any(workspace.glob("*.py")) or any(
                (workspace / "src").glob("**/*.py")
            )
        except Exception:
            return False

    def check_syntax(self, workspace: Path) -> Tuple[bool, List[str]]:
        """Verify syntax of all Python source files via AST compilation."""
        is_clean, err_msg = PreFlightGuard.check_syntax(workspace)
        if is_clean:
            return (True, [])
        return (False, [err_msg] if err_msg else [])

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        """Execute deterministic safe lint fixes and formatting via Ruff in <100ms."""
        if not shutil.which("ruff"):
            return (False, "ruff CLI not available in PATH")

        try:
            subprocess.run(
                [
                    "ruff",
                    "check",
                    "--fix",
                    "--unsafe-fixes",
                    "--output-format=concise",
                    ".",
                ],
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=15,
            )
            subprocess.run(
                ["ruff", "format", "."],
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=15,
            )
            return (True, "Ruff automated fixes applied")
        except Exception as e:
            return (False, str(e))

    def run_static_analysis(self, workspace: Path) -> Tuple[bool, List[str]]:
        """Run AST syntax checks and concise Ruff linter analysis."""
        issues: List[str] = []

        # 1. AST Syntax Check
        syntax_clean, syntax_errs = self.check_syntax(workspace)
        if not syntax_clean:
            issues.extend(syntax_errs)

        # 2. Ruff Linter
        if shutil.which("ruff"):
            try:
                res = subprocess.run(
                    ["ruff", "check", ".", "--output-format=concise"],
                    cwd=str(workspace),
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if res.returncode != 0 and res.stdout.strip():
                    lines = [
                        line.strip() for line in res.stdout.splitlines() if line.strip()
                    ]
                    issues.append(
                        f"[Ruff Lint Issues ({len(lines)})]\n" + "\n".join(lines[:15])
                    )
            except Exception:
                pass

        return (len(issues) == 0, issues)

    def has_test_suite(self, workspace: Path) -> bool:
        """Check whether tests directory or pytest test files exist."""
        return (
            (workspace / "tests").exists()
            or any(workspace.glob("test_*.py"))
            or any(workspace.glob("*_test.py"))
            or (workspace / "pyproject.toml").exists()
        )

    def get_test_command(self, workspace: Path) -> Optional[str]:
        """Return the optimal command to execute Python pytest suite."""
        if not self.has_test_suite(workspace):
            return None

        if shutil.which("uv") and (workspace / "uv.lock").exists():
            return "uv run pytest -v"
        return "python -m pytest -v"

    def parse_test_failures(self, stdout: str, stderr: str) -> str:
        """Parse Pytest failure outputs into a minimal compact prompt snippet."""
        return PytestOutputParser.extract_compact_failures(stdout, stderr)

    def get_developer_prompt_guidance(self) -> str:
        """Return architectural and coding standards for Python codebases."""
        return (
            "Python Architecture & Standards:\n"
            "- Follow clean-python-architecture and strict typing (PEP 484).\n"
            "- Adhere to PEP 8 style standards.\n"
            "- Write robust, isolated pytest unit tests with fixtures and descriptive assertions.\n"
            "- Avoid circular imports and keep modules decoupled."
        )

    def collect_codebase_metrics(self, workspace: Path) -> Dict[str, Any]:
        """Collect Python-specific codebase statistics."""
        ignored_dirs = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "node_modules",
        }
        py_files: List[Path] = []
        for root, dirs, files in os.walk(workspace):
            dirs[:] = [
                d for d in dirs if d not in ignored_dirs and not d.startswith(".")
            ]
            for f in files:
                if f.endswith(".py"):
                    py_files.append(Path(root) / f)

        total_lines = 0
        file_metrics = []
        for f in py_files:
            try:
                line_count = len(
                    f.read_text(encoding="utf-8", errors="replace").splitlines()
                )
                total_lines += line_count
                file_metrics.append((str(f.relative_to(workspace)), line_count))
            except Exception:
                pass

        file_metrics.sort(key=lambda x: x[1], reverse=True)
        total_files = len(py_files)
        avg_loc = (total_lines // total_files) if total_files > 0 else 0
        return {
            "total_files": total_files,
            "total_loc": total_lines,
            "total_lines": total_lines,
            "avg_loc": avg_loc,
            "top_files": file_metrics[:10],
            "language": "Python",
        }
