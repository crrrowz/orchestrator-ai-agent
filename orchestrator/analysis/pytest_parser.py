"""Compact Pytest Failure Parser and Test Execution Classifier."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class TestExecutionStatus(str, Enum):
    """Categorized status for test execution outcomes."""

    __test__ = False
    PASSED = "PASSED"
    TEST_FAILURE = "TEST_FAILURE"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    COMMAND_ERROR = "COMMAND_ERROR"
    TIMEOUT = "TIMEOUT"
    NO_TESTS_FOUND = "NO_TESTS_FOUND"


@dataclass
class TestExecutionResult:
    """Structured classification of test execution."""

    __test__ = False
    status: TestExecutionStatus
    exit_code: int
    summary: str
    failure_details: str
    is_infra_or_env: bool
    raw_stdout: str = ""
    raw_stderr: str = ""


class PytestOutputParser:
    """Extracts only actionable test failure details, stripping passing tests and environment noise."""

    @staticmethod
    def is_runner_crash(stdout: str, stderr: str) -> Tuple[bool, str]:
        """Detect whether test execution failed due to a launcher, trampoline, or environment crash rather than code logic."""
        combined = f"{stdout}\n{stderr}".strip()
        if not combined:
            return False, ""

        runner_crash_patterns = [
            (
                r"uv trampoline failed to canonicalize script path",
                "uv launcher trampoline failure on Windows path with spaces",
            ),
            (
                r"No module named pytest",
                "pytest not installed in active virtual environment",
            ),
            (
                r"is not recognized as an internal or external command",
                "executable binary not found in Windows PATH",
            ),
            (
                r"command not found",
                "executable binary not found in system PATH",
            ),
            (
                r"PermissionError: \[WinError 5\]",
                "Windows filesystem permission denied during process invocation",
            ),
            (
                r"executable file not found in %PATH%",
                "executable binary missing from system PATH",
            ),
            (
                r"The system cannot find the path specified",
                "filesystem path not found on Windows",
            ),
            (
                r"The system cannot find the file specified",
                "executable or script file not found on Windows",
            ),
            (
                r"cannot find the path specified",
                "path resolution failure on Windows",
            ),
            (
                r"Fatal Python error:",
                "Fatal Python interpreter crash during startup",
            ),
            (
                r"DLL load failed while importing",
                "Windows dynamic library dependency missing",
            ),
            (
                r"pytest: error: unrecognized arguments",
                "invalid CLI invocation arguments passed to pytest",
            ),
            (
                r"usage: pytest \[options\]",
                "invalid CLI usage passed to pytest",
            ),
            (
                r"ERROR: usage: pytest",
                "pytest CLI argument error",
            ),
        ]

        for pattern, explanation in runner_crash_patterns:
            if re.search(pattern, combined, flags=re.IGNORECASE):
                return True, f"Environment Runner Crash: {explanation}"

        # If no tests were run and runner crashed on startup or collection
        if ("collected 0 items" in combined or "0 items" in combined) and (
            "Traceback (most recent call last):" in combined
            or "ModuleNotFoundError:" in combined
            or "ImportError:" in combined
        ):
            return True, "Test runner failed during initialization before running test suite"

        # Pytest collection errors on all items
        if "Interrupted: " in combined and "errors during collection" in combined:
            return True, "Test runner interrupted due to collection errors"

        return False, ""

    @staticmethod
    def classify_execution(
        exit_code: int,
        stdout: str,
        stderr: str,
        timed_out: bool = False,
    ) -> TestExecutionResult:
        """Classify test process outcome into distinct failure classes."""
        combined = f"{stdout}\n{stderr}".strip()

        if timed_out is True or (exit_code == -1 and "timed out" in combined.lower()):
            return TestExecutionResult(
                status=TestExecutionStatus.TIMEOUT,
                exit_code=exit_code,
                summary="Test execution timed out before completion.",
                failure_details=combined[:2000],
                is_infra_or_env=True,
                raw_stdout=stdout,
                raw_stderr=stderr,
            )

        if exit_code == 0:
            return TestExecutionResult(
                status=TestExecutionStatus.PASSED,
                exit_code=0,
                summary="All unit tests executed and passed successfully.",
                failure_details="",
                is_infra_or_env=False,
                raw_stdout=stdout,
                raw_stderr=stderr,
            )

        # Pytest exit code 5: No tests were collected
        if exit_code == 5 or "collected 0 items" in combined and "failed" not in combined.lower():
            return TestExecutionResult(
                status=TestExecutionStatus.NO_TESTS_FOUND,
                exit_code=exit_code,
                summary="No test items were collected or discovered.",
                failure_details=combined[:1000],
                is_infra_or_env=False,
                raw_stdout=stdout,
                raw_stderr=stderr,
            )

        # Check for runner crash / environment error
        is_crash, crash_reason = PytestOutputParser.is_runner_crash(stdout, stderr)
        if is_crash:
            # Distinguish environment vs infrastructure vs command
            env_keywords = [
                "PATH",
                "not installed",
                "PermissionError",
                "WinError 5",
                "DLL load failed",
                "cannot find the file",
            ]
            cmd_keywords = ["unrecognized arguments", "usage: pytest"]

            if any(k in crash_reason or k in combined for k in cmd_keywords):
                status = TestExecutionStatus.COMMAND_ERROR
            elif any(k in crash_reason or k in combined for k in env_keywords):
                status = TestExecutionStatus.ENVIRONMENT_ERROR
            else:
                status = TestExecutionStatus.INFRASTRUCTURE_ERROR

            return TestExecutionResult(
                status=status,
                exit_code=exit_code,
                summary=f"Test runner failed to execute ({crash_reason}).",
                failure_details=PytestOutputParser.extract_compact_failures(stdout, stderr),
                is_infra_or_env=True,
                raw_stdout=stdout,
                raw_stderr=stderr,
            )

        # Check for command permissions / security denial (e.g. exit code 126/127)
        if exit_code in (126, 127) or "Security policy violation" in combined:
            return TestExecutionResult(
                status=TestExecutionStatus.COMMAND_ERROR,
                exit_code=exit_code,
                summary=f"Test command rejected or executable not found (Exit Code {exit_code}).",
                failure_details=combined[:1500],
                is_infra_or_env=True,
                raw_stdout=stdout,
                raw_stderr=stderr,
            )

        # If tests actually ran (exit_code == 1 or failures detected in output)
        compact_failures = PytestOutputParser.extract_compact_failures(stdout, stderr)
        return TestExecutionResult(
            status=TestExecutionStatus.TEST_FAILURE,
            exit_code=exit_code,
            summary=f"Pytest suite reported test failure(s) (Exit Code {exit_code}).",
            failure_details=compact_failures,
            is_infra_or_env=False,
            raw_stdout=stdout,
            raw_stderr=stderr,
        )

    @staticmethod
    def extract_compact_failures(
        stdout: str, stderr: str, max_chars: int = 2500
    ) -> str:
        """Parse pytest stdout/stderr and return a concise, targeted failure report."""
        combined = f"{stdout}\n{stderr}".strip()
        if not combined:
            return "No output captured from pytest execution."

        is_crash, crash_reason = PytestOutputParser.is_runner_crash(stdout, stderr)
        if is_crash:
            return (
                f"[ENVIRONMENT RUNNER LAUNCHER CRASH - DO NOT MODIFY CODE LOGIC]\n"
                f"Diagnostic: {crash_reason}\n"
                f"Raw Output:\n{combined[:1000]}"
            )

        lines = combined.splitlines()
        failures: list[str] = []
        current_failure: list[str] = []
        capturing = False

        for line in lines:
            # Capture failure headers like: _____ test_name _____
            if re.match(r"^_{3,}\s+.*\s+_{3,}$", line.strip()) or re.match(
                r"^__+\s+.*\s+__+$", line.strip()
            ):
                if current_failure:
                    failures.append(
                        "\n".join(current_failure[-15:])
                    )  # Keep only the last 15 lines of trace
                    current_failure = []
                capturing = True
                current_failure.append(line.strip())
            elif capturing:
                if line.startswith("===") and "short test summary info" in line:
                    capturing = False
                    if current_failure:
                        failures.append("\n".join(current_failure[-15:]))
                        current_failure = []
                else:
                    current_failure.append(line)

        if current_failure:
            failures.append("\n".join(current_failure[-15:]))

        # Extract short test summary section if present
        summary_section = []
        in_summary = False
        for line in lines:
            if "short test summary info" in line:
                in_summary = True
                summary_section.append(line)
            elif in_summary:
                if line.startswith("===") and (
                    "failed" in line or "passed" in line or "error" in line
                ):
                    summary_section.append(line)
                    break
                summary_section.append(line)

        summary_text = "\n".join(summary_section).strip()
        failures_text = "\n\n".join(failures).strip()

        report_parts = []
        if summary_text:
            report_parts.append(f"### Test Summary:\n{summary_text}")
        if failures_text:
            report_parts.append(f"### Specific Failure Traces:\n{failures_text}")
        elif not summary_text:
            # Fallback if pytest format was non-standard
            report_parts.append(combined[-max_chars:])

        result = "\n\n".join(report_parts).strip()
        if len(result) > max_chars:
            return result[:max_chars] + "\n... [Truncated for brevity]"
        return result
