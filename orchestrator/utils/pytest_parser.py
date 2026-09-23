"""Compact Pytest Failure Parser to minimize token consumption in fix prompts."""

import re


class PytestOutputParser:
    """Extracts only actionable test failure details, stripping passing tests and environment noise."""

    @staticmethod
    def extract_compact_failures(
        stdout: str, stderr: str, max_chars: int = 2500
    ) -> str:
        """Parse pytest stdout/stderr and return a concise, targeted failure report."""
        combined = f"{stdout}\n{stderr}".strip()
        if not combined:
            return "No output captured from pytest execution."

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
