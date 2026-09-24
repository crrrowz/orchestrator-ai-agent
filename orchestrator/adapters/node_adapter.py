"""Node.js and TypeScript ecosystem project adapter."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.adapters.base import ProjectAdapter
from orchestrator.analysis.pytest_parser import (
    TestExecutionResult,
    TestExecutionStatus,
)


class NodeAdapter(ProjectAdapter):
    """Adapter for Node.js and TypeScript projects (npm, pnpm, yarn, bun, vitest, jest, eslint, biome)."""

    @property
    def language_name(self) -> str:
        return "nodejs"

    def detect(self, workspace: Path) -> bool:
        """Detect Node.js projects by presence of package.json."""
        return (workspace / "package.json").exists()

    def _read_package_json(self, workspace: Path) -> Dict[str, Any]:
        """Read and parse package.json safely."""
        pkg_file = workspace / "package.json"
        if not pkg_file.exists():
            return {}
        try:
            return json.loads(pkg_file.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return {}

    def check_syntax(self, workspace: Path) -> Tuple[bool, List[str]]:
        """Verify TypeScript or JavaScript syntax without emitting files."""
        issues: List[str] = []

        # 1. If tsconfig.json exists, run TypeScript compiler dry-run
        if (workspace / "tsconfig.json").exists():
            tsc_bin = shutil.which("tsc") or ("npx" if shutil.which("npx") else None)
            if tsc_bin:
                cmd = (
                    ["tsc", "--noEmit"]
                    if tsc_bin != "npx"
                    else ["npx", "--no-install", "tsc", "--noEmit"]
                )
                try:
                    res = subprocess.run(
                        cmd,
                        cwd=str(workspace),
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if res.returncode != 0 and (
                        res.stdout.strip() or res.stderr.strip()
                    ):
                        raw = res.stdout.strip() or res.stderr.strip()
                        lines = [
                            line.strip() for line in raw.splitlines() if line.strip()
                        ][:10]
                        issues.append(
                            "[TypeScript Compiler Errors]\n" + "\n".join(lines)
                        )
                except Exception:
                    pass

        return (len(issues) == 0, issues)

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        """Execute deterministic auto-fixes using Biome or ESLint / Prettier."""
        # 1. Check for Biome
        has_biome_config = (workspace / "biome.json").exists() or (
            workspace / "biome.jsonc"
        ).exists()
        biome_bin = shutil.which("biome")
        if biome_bin or has_biome_config:
            cmd = (
                ["biome", "check", "--write", "."]
                if biome_bin
                else ["npx", "@biomejs/biome", "check", "--write", "."]
            )
            try:
                subprocess.run(
                    cmd,
                    cwd=str(workspace),
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                return (True, "Biome auto-fixes applied")
            except Exception:
                pass

        # 2. Check for ESLint / Prettier
        pkg = self._read_package_json(workspace)
        scripts = pkg.get("scripts", {})
        if "format" in scripts:
            npm_bin = shutil.which("npm") or "npm"
            try:
                subprocess.run(
                    [npm_bin, "run", "format"],
                    cwd=str(workspace),
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                return (True, "npm run format executed")
            except Exception:
                pass

        return (True, "No auto-fixer configured for Node.js project")

    def run_static_analysis(self, workspace: Path) -> Tuple[bool, List[str]]:
        """Run linter or static type checking for Node.js / TypeScript."""
        issues: List[str] = []

        # TypeScript check
        syntax_ok, syntax_issues = self.check_syntax(workspace)
        if not syntax_ok:
            issues.extend(syntax_issues)

        # ESLint or Biome
        pkg = self._read_package_json(workspace)
        scripts = pkg.get("scripts", {})
        if "lint" in scripts:
            npm_bin = shutil.which("npm") or "npm"
            try:
                res = subprocess.run(
                    [npm_bin, "run", "lint"],
                    cwd=str(workspace),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if res.returncode != 0:
                    raw = res.stdout.strip() or res.stderr.strip()
                    lines = [line.strip() for line in raw.splitlines() if line.strip()][
                        :15
                    ]
                    issues.append("[ESLint / Linter Issues]\n" + "\n".join(lines))
            except Exception:
                pass

        return (len(issues) == 0, issues)

    def has_test_suite(self, workspace: Path) -> bool:
        """Check whether test script or test files exist."""
        pkg = self._read_package_json(workspace)
        scripts = pkg.get("scripts", {})
        test_script = scripts.get("test", "")
        if test_script and "no test specified" not in test_script:
            return True

        test_indicators = [
            workspace / "tests",
            workspace / "test",
            workspace / "__tests__",
            workspace / "vitest.config.ts",
            workspace / "vitest.config.js",
            workspace / "jest.config.js",
            workspace / "jest.config.ts",
        ]
        if any(p.exists() for p in test_indicators):
            return True

        for ext in ("*.test.ts", "*.test.js", "*.spec.ts", "*.spec.js"):
            try:
                if any(workspace.glob(f"**/{ext}")):
                    return True
            except Exception:
                pass

        return False

    def get_test_command(self, workspace: Path) -> Optional[str]:
        """Determine package-manager-aware test runner command."""
        pkg = self._read_package_json(workspace)
        scripts = pkg.get("scripts", {})
        test_script = scripts.get("test", "")

        # Select package manager based on lockfiles
        runner = "npm test"
        if (workspace / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
            runner = "pnpm test"
        elif (workspace / "yarn.lock").exists() and shutil.which("yarn"):
            runner = "yarn test"
        elif (
            (workspace / "bun.lockb").exists()
            or (workspace / "bun.lock").exists()
            and shutil.which("bun")
        ):
            runner = "bun test"

        if test_script and "no test specified" not in test_script:
            return runner

        # Fallback to direct runners
        if (workspace / "vitest.config.ts").exists() or (
            workspace / "vitest.config.js"
        ).exists():
            return "npx vitest run"
        if (workspace / "jest.config.js").exists() or (
            workspace / "jest.config.ts"
        ).exists():
            return "npx jest"

        return runner if self.has_test_suite(workspace) else None

    def parse_test_failures(self, stdout: str, stderr: str) -> str:
        """Strip npm/yarn noise and format compact test failures."""
        combined = f"{stdout}\n{stderr}"
        lines = combined.splitlines()

        filtered: List[str] = []
        capture = False

        for line in lines:
            # Strip npm error spam
            if re.match(r"^npm ERR!", line) or re.match(r"^yarn run v", line):
                continue
            # Vitest / Jest failure headers
            if any(
                marker in line
                for marker in (
                    "FAIL ",
                    "✕ ",
                    "AssertionError",
                    "Expected:",
                    "Received:",
                )
            ):
                capture = True

            if capture or "Error:" in line or "failed" in line.lower():
                filtered.append(line.rstrip())

        if not filtered:
            # Fallback to tail of output
            filtered = [line.strip() for line in lines if line.strip()][-25:]

        return "\n".join(filtered[:30])

    def classify_test_result(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        timed_out: bool = False,
    ) -> TestExecutionResult:
        """Classify JavaScript/TypeScript test runner outcomes."""
        combined = f"{stdout}\n{stderr}".strip()
        if timed_out or exit_code == -1 and "timed out" in combined.lower():
            return TestExecutionResult(
                status=TestExecutionStatus.TIMEOUT,
                exit_code=exit_code,
                summary="Node.js test execution timed out.",
                failure_details=combined[:2000],
                is_infra_or_env=True,
                raw_stdout=stdout,
                raw_stderr=stderr,
            )
        if exit_code == 0:
            return TestExecutionResult(
                status=TestExecutionStatus.PASSED,
                exit_code=0,
                summary="All Node.js / TypeScript unit tests passed successfully.",
                failure_details="",
                is_infra_or_env=False,
                raw_stdout=stdout,
                raw_stderr=stderr,
            )
        crash_patterns = [
            r"npm ERR! code ENOENT",
            r"command not found",
            r"is not recognized as an internal or external command",
            r"No such file or directory",
            r"cannot find module",
            r"ERR_MODULE_NOT_FOUND",
        ]
        if any(re.search(pat, combined, re.IGNORECASE) for pat in crash_patterns) and not any(
            marker in combined for marker in ("FAIL ", "✕ ", "AssertionError")
        ):
            return TestExecutionResult(
                status=TestExecutionStatus.ENVIRONMENT_ERROR,
                exit_code=exit_code,
                summary="Node.js test runner environment failed to execute.",
                failure_details=combined[:1500],
                is_infra_or_env=True,
                raw_stdout=stdout,
                raw_stderr=stderr,
            )
        return TestExecutionResult(
            status=TestExecutionStatus.TEST_FAILURE,
            exit_code=exit_code,
            summary=f"Node.js test runner reported test failures (Exit Code {exit_code}).",
            failure_details=self.parse_test_failures(stdout, stderr),
            is_infra_or_env=False,
            raw_stdout=stdout,
            raw_stderr=stderr,
        )

    def get_developer_prompt_guidance(self) -> str:
        """Return architectural and coding standards for Node.js / TypeScript codebases."""
        return (
            "Node.js / TypeScript Architecture & Standards:\n"
            "- Use modern ESModules syntax (import/export) and strict TypeScript type annotations.\n"
            "- Maintain clean architecture with clear separation between routes, controllers, and services.\n"
            "- Write comprehensive unit tests using Vitest or Jest with clear assertions.\n"
            "- Handle asynchronous operations safely using async/await and robust error handling."
        )

    def collect_codebase_metrics(self, workspace: Path) -> Dict[str, Any]:
        """Collect Node.js/TypeScript-specific codebase statistics."""
        ignored_dirs = {
            ".git",
            "node_modules",
            ".next",
            "dist",
            "build",
            ".turbo",
            "coverage",
        }
        source_exts = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
        src_files: List[Path] = []
        for root, dirs, files in os.walk(workspace):
            dirs[:] = [
                d for d in dirs if d not in ignored_dirs and not d.startswith(".")
            ]
            for f in files:
                p = Path(root) / f
                if p.suffix in source_exts:
                    src_files.append(p)

        total_lines = 0
        file_metrics = []
        for f in src_files:
            try:
                line_count = len(
                    f.read_text(encoding="utf-8", errors="replace").splitlines()
                )
                total_lines += line_count
                file_metrics.append((str(f.relative_to(workspace)), line_count))
            except Exception:
                pass

        file_metrics.sort(key=lambda x: x[1], reverse=True)
        total_files = len(src_files)
        avg_loc = (total_lines // total_files) if total_files > 0 else 0
        return {
            "total_files": total_files,
            "total_loc": total_lines,
            "total_lines": total_lines,
            "avg_loc": avg_loc,
            "top_files": file_metrics[:10],
            "language": "Node.js / TypeScript",
        }
