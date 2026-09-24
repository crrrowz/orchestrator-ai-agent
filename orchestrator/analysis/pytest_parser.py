"""Compact Pytest Failure Parser to minimize token consumption in fix prompts."""

import re
from typing import Tuple


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
        ]

        for pattern, explanation in runner_crash_patterns:
            if re.search(pattern, combined, flags=re.IGNORECASE):
                return True, f"Environment Runner Crash: {explanation}"

        # If no tests were run and runner crashed on startup
        if ("collected 0 items" in combined or "0 items" in combined) and (
            "Traceback (most recent call last):" in combined
            or "ModuleNotFoundError:" in combined
            or "ImportError:" in combined
        ):
            return True, "Test runner failed during initialization before running test suite"

        return False, ""

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
