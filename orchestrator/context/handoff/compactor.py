"""Diagnostic Trace Compactor for Pytest and Compiler Failure Distillation.

File Location: orchestrator/context/handoff/compactor.py
Architecture Reference: docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md Section 5
"""

from __future__ import annotations

import re
from typing import List, Optional

from orchestrator.context.handoff.models import (
    CompactedFrame,
    DiagnosticFailureTrace,
    DiagnosticTraceSummary,
)


class DiagnosticTraceCompactor:
    """Extracts high-signal failure traces from verbose pytest and compiler logs.

    Filters passing test noise, strips ANSI escape sequences, discards foreign site-packages
    stack frames, isolates exact assertion diffs, and synthesizes compact, actionable
    Markdown blocks that fit within strict context headroom limits (<= 800 tokens).
    """

    ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    PYTEST_FAIL_HEADER = re.compile(r"_{10,}\s*(.*?)\s*_{10,}")
    ASSERT_DIFF_REGEX = re.compile(r"E\s+assert\s+(.*)")
    FRAME_REGEX = re.compile(r"^(.*?):(\d+):\s+in\s+(.*)$")

    @classmethod
    def strip_ansi(cls, text: str) -> str:
        """Remove ANSI terminal color and control escape sequences."""
        return cls.ANSI_ESCAPE_REGEX.sub("", text)

    @classmethod
    def compact_pytest_output(
        cls,
        stdout: str,
        stderr: str = "",
        max_traces: int = 5,
        exit_code: int = 1,
    ) -> DiagnosticTraceSummary:
        """Parse raw pytest stdout/stderr into a structured, compacted diagnostic summary."""
        cleaned_out = cls.strip_ansi(stdout or "")
        cleaned_err = cls.strip_ansi(stderr or "")
        raw_combined = cleaned_out + ("\n" + cleaned_err if cleaned_err else "")

        traces: List[DiagnosticFailureTrace] = []

        # Split on pytest failure separator blocks (e.g. ________ test_foo ________)
        sections = cls.PYTEST_FAIL_HEADER.split(cleaned_out)
        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                if len(traces) >= max_traces:
                    break
                node_id = sections[i].strip()
                failure_body = sections[i + 1] if (i + 1) < len(sections) else ""
                trace = cls._parse_single_failure_section(node_id, failure_body)
                traces.append(trace)

        # If no header blocks matched, check for failure lines (e.g., FAILED tests/test_foo.py::test_bar)
        if not traces:
            failed_lines = [
                line.strip()
                for line in raw_combined.splitlines()
                if line.strip().startswith("FAILED ") or line.strip().startswith("ERROR ")
            ]
            for line in failed_lines[:max_traces]:
                parts = line.split(maxsplit=1)
                node_id = parts[1] if len(parts) > 1 else line
                traces.append(
                    DiagnosticFailureTrace(
                        node_id=node_id,
                        exception_type="TestFailure",
                        exception_message=line,
                        primary_frame=None,
                        assertion_diff=None,
                        captured_stdout_tail=cleaned_out[-400:].strip() if cleaned_out else None,
                    )
                )

        # Fallback for runner crash, syntax error, or unformatted failure
        if not traces and (exit_code != 0 or "FAILED" in raw_combined or "ERROR" in raw_combined):
            last_line = cls._extract_last_meaningful_line(raw_combined)
            traces.append(
                DiagnosticFailureTrace(
                    node_id="pytest_execution_error",
                    exception_type="TestRunnerFailure",
                    exception_message=last_line,
                    primary_frame=None,
                    captured_stdout_tail=raw_combined[-500:].strip() if raw_combined else None,
                )
            )

        compacted_md = "\n".join(t.to_markdown() for t in traces)
        return DiagnosticTraceSummary(
            total_failures=len(traces),
            traces=traces,
            summary_text=f"{len(traces)} failure(s) isolated from test runner output.",
            exit_code=exit_code,
            raw_output_length=len(stdout or "") + len(stderr or ""),
            compacted_output_length=len(compacted_md),
        )

    @classmethod
    def _parse_single_failure_section(cls, node_id: str, body: str) -> DiagnosticFailureTrace:
        """Extract workspace call frame, exception, and assertion diff from a failure block."""
        lines = body.splitlines()
        exception_type = "AssertionError"
        exception_message = "Test assertion failed"
        primary_frame: Optional[CompactedFrame] = None
        assertion_diff: Optional[str] = None
        stdout_tail: Optional[str] = None

        diff_lines: List[str] = []
        workspace_frames: List[CompactedFrame] = []

        for idx, line in enumerate(lines):
            stripped = line.strip()
            match = cls.FRAME_REGEX.match(stripped)
            if match:
                fpath, lnum, fname = match.groups()
                # Check next line for code snippet
                code = lines[idx + 1].strip() if (idx + 1) < len(lines) else ""
                frame = CompactedFrame(
                    file_path=fpath,
                    line_number=int(lnum),
                    function_name=fname,
                    code_line=code,
                )
                # Prioritize workspace/test files over site-packages / virtualenvs
                if "site-packages" not in fpath and "_pytest" not in fpath:
                    workspace_frames.append(frame)
                elif not primary_frame:
                    primary_frame = frame

            if stripped.startswith("E "):
                error_content = stripped[2:].strip()
                diff_lines.append(error_content)
                if ":" in error_content:
                    parts = error_content.split(":", 1)
                    if len(parts) == 2 and any(err_word in parts[0] for err_word in ("Error", "Exception", "Fault")):
                        exception_type = parts[0].strip()
                        exception_message = parts[1].strip()
                elif any(err_word in error_content for err_word in ("Error", "Exception", "Fault")):
                    exception_type = error_content.strip()

        # If we found workspace frames, the deepest one is typically the leaf call site
        if workspace_frames:
            primary_frame = workspace_frames[-1]

        if diff_lines:
            assertion_diff = "\n".join(diff_lines[:10])

        # Extract captured stdout tail if present
        if "----------------------------- Captured stdout" in body:
            tail_parts = body.split("----------------------------- Captured stdout", 1)
            if len(tail_parts) > 1:
                tail_lines = tail_parts[1].splitlines()
                # Trim section headers
                tail_content = [l for l in tail_lines if not l.startswith("---") and l.strip()]
                if tail_content:
                    stdout_tail = "\n".join(tail_content[-8:])

        return DiagnosticFailureTrace(
            node_id=node_id,
            exception_type=exception_type,
            exception_message=exception_message,
            primary_frame=primary_frame,
            assertion_diff=assertion_diff,
            captured_stdout_tail=stdout_tail,
        )

    @classmethod
    def compact_syntax_error(cls, stderr: str) -> DiagnosticFailureTrace:
        """Parse raw compiler/syntax error traceback into a compacted diagnostic trace."""
        cleaned = cls.strip_ansi(stderr or "")
        lines = cleaned.splitlines()
        primary_frame: Optional[CompactedFrame] = None
        exception_type = "SyntaxError"
        exception_message = "Syntax error in source file"

        file_match = re.search(r'File "([^"]+)", line (\d+)', cleaned)
        if file_match:
            fpath, lnum = file_match.groups()
            code_line = ""
            # Search following lines for line snippet
            for idx, line in enumerate(lines):
                if fpath in line:
                    if idx + 1 < len(lines):
                        code_line = lines[idx + 1].strip()
                    break
            primary_frame = CompactedFrame(
                file_path=fpath,
                line_number=int(lnum),
                function_name="<module>",
                code_line=code_line,
            )

        for line in reversed(lines):
            stripped = line.strip()
            if any(err in stripped for err in ("SyntaxError:", "IndentationError:", "TabError:")):
                parts = stripped.split(":", 1)
                exception_type = parts[0].strip()
                if len(parts) > 1:
                    exception_message = parts[1].strip()
                break

        return DiagnosticFailureTrace(
            node_id="compilation_syntax_error",
            exception_type=exception_type,
            exception_message=exception_message,
            primary_frame=primary_frame,
            assertion_diff=None,
            captured_stdout_tail=None,
        )

    @classmethod
    def _extract_last_meaningful_line(cls, text: str) -> str:
        """Find the trailing non-delimiter, non-empty line of text."""
        for line in reversed(text.splitlines()):
            stripped = line.strip()
            if stripped and not stripped.startswith("=") and not stripped.startswith("-"):
                return stripped
        return "Unknown test execution failure"


# Convenience alias matching P6 spec
DiagnosticCompactor = DiagnosticTraceCompactor
