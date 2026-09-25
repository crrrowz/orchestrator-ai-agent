"""Grammar-based Command Security Parser and Pipeline Validator.

Distinguishes legitimate PowerShell and UNIX pipelines from dangerous shell
chaining, subshell substitution, and arbitrary code evaluation escapes.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import List, Set, Tuple

from orchestrator.tools.hardened.models import (
    PipelineSegment,
    ValidatedCommand,
)
from orchestrator.tools.hardened.security import (
    APPROVED_PIPELINE_CMDLETS,
    APPROVED_ROOT_COMMANDS,
    DISALLOWED_OPERATORS,
)


class CommandGrammarValidator:
    """Grammar-based parser distinguishing safe pipelines from shell injection attacks."""

    @classmethod
    def _split_pipeline_segments(cls, command: str) -> List[str]:
        """Split a command by '|' while respecting single and double quotes."""
        segments: List[str] = []
        current: List[str] = []
        in_single = False
        in_double = False

        for char in command:
            if char == "'" and not in_double:
                in_single = not in_single
                current.append(char)
            elif char == '"' and not in_single:
                in_double = not in_double
                current.append(char)
            elif char == "|" and not in_single and not in_double:
                segments.append("".join(current))
                current = []
            else:
                current.append(char)

        if current:
            segments.append("".join(current))

        return segments

    @classmethod
    def validate_command(cls, raw_command: str) -> ValidatedCommand:
        """Parse, tokenize, and validate command syntax and pipeline dataflows."""
        clean = (raw_command or "").strip()
        if not clean:
            return ValidatedCommand(
                is_valid=False,
                executable_path="",
                command_line_args=(),
                pipeline_segments=(),
                rejection_reason="Empty command string.",
            )

        # 1. Check for unquoted shell operators, subshell expressions ($(...)), backticks (``), and redirections
        if "$(" in clean:
            return ValidatedCommand(
                is_valid=False,
                executable_path="",
                command_line_args=(),
                pipeline_segments=(),
                rejection_reason="Security policy violation: Subshell substitution '$(' is not permitted.",
            )
        if "`" in clean:
            return ValidatedCommand(
                is_valid=False,
                executable_path="",
                command_line_args=(),
                pipeline_segments=(),
                rejection_reason="Security policy violation: Backtick command substitution '`' is not permitted.",
            )
        if "||" in clean:
            return ValidatedCommand(
                is_valid=False,
                executable_path="",
                command_line_args=(),
                pipeline_segments=(),
                rejection_reason="Security policy violation: Chained commands or pipeline operator '||' are not permitted.",
            )
        if "&&" in clean:
            return ValidatedCommand(
                is_valid=False,
                executable_path="",
                command_line_args=(),
                pipeline_segments=(),
                rejection_reason="Security policy violation: Chained commands or pipeline operator '&&' are not permitted.",
            )

        # Check for unquoted redirection and chaining operators outside quotes
        in_s = False
        in_d = False
        for c_idx, ch in enumerate(clean):
            if ch == "'" and not in_d:
                in_s = not in_s
            elif ch == '"' and not in_s:
                in_d = not in_d
            elif not in_s and not in_d:
                if ch == ";":
                    return ValidatedCommand(
                        is_valid=False,
                        executable_path="",
                        command_line_args=(),
                        pipeline_segments=(),
                        rejection_reason="Security policy violation: Chained commands or pipeline operator ';' are not permitted.",
                    )
                elif ch in (">", "<"):
                    return ValidatedCommand(
                        is_valid=False,
                        executable_path="",
                        command_line_args=(),
                        pipeline_segments=(),
                        rejection_reason="Security policy violation: Shell redirection operator is prohibited.",
                    )

        # 2. Split pipeline on unquoted |
        raw_segments = cls._split_pipeline_segments(clean)
        pipeline_segments: List[PipelineSegment] = []

        for idx, seg in enumerate(raw_segments):
            seg_trimmed = seg.strip()
            if not seg_trimmed:
                return ValidatedCommand(
                    is_valid=False,
                    executable_path="",
                    command_line_args=(),
                    pipeline_segments=(),
                    rejection_reason="Syntax Error: Empty pipeline segment.",
                )

            # Preserve Windows backslashes while splitting quotes
            try:
                escaped_seg = seg_trimmed.replace("\\", "\\\\")
                tokens = shlex.split(escaped_seg, posix=True)
            except ValueError as e:
                return ValidatedCommand(
                    is_valid=False,
                    executable_path="",
                    command_line_args=(),
                    pipeline_segments=(),
                    rejection_reason=f"Lexer Syntax Error in segment '{seg_trimmed}': {str(e)}",
                )

            if not tokens:
                return ValidatedCommand(
                    is_valid=False,
                    executable_path="",
                    command_line_args=(),
                    pipeline_segments=(),
                    rejection_reason="Syntax Error: No executable tokens found in segment.",
                )

            # Check for shell operator chaining tokens (;, &&, ||, &)
            for tok in tokens:
                if tok in (";", "&&", "||", "&"):
                    return ValidatedCommand(
                        is_valid=False,
                        executable_path="",
                        command_line_args=(),
                        pipeline_segments=(),
                        rejection_reason=f"Security policy violation: Chained commands or pipeline operator '{tok}' are not permitted.",
                    )

            base_token = tokens[0].strip("\"'")
            base_bin = Path(base_token).name.lower()
            if base_bin.endswith(".exe"):
                base_bin = base_bin[:-4]

            # Check disallowed dangerous command verbs
            if base_bin in DISALLOWED_OPERATORS or any(
                tok.lower() in ("invoke-expression", "iex", "start-process", "invoke-webrequest", "iwr", "format")
                for tok in tokens
            ):
                return ValidatedCommand(
                    is_valid=False,
                    executable_path="",
                    command_line_args=(),
                    pipeline_segments=(),
                    rejection_reason=f"Security policy violation: Command or operator '{base_bin}' is prohibited.",
                )

            # Check for destructive recursive deletions (e.g. rm -rf, del /f /s)
            if base_bin in ("rm", "del", "remove-item"):
                lower_tokens = [t.lower() for t in tokens[1:]]
                if (
                    "-rf" in lower_tokens
                    or "-fr" in lower_tokens
                    or ("-r" in lower_tokens and "-f" in lower_tokens)
                    or ("-recurse" in lower_tokens and "-force" in lower_tokens)
                ):
                    return ValidatedCommand(
                        is_valid=False,
                        executable_path="",
                        command_line_args=(),
                        pipeline_segments=(),
                        rejection_reason="Security policy violation: Destructive command 'rm -rf' is prohibited.",
                    )

            if idx == 0:
                if (
                    base_bin not in APPROVED_ROOT_COMMANDS
                    and base_bin not in APPROVED_PIPELINE_CMDLETS
                ):
                    return ValidatedCommand(
                        is_valid=False,
                        executable_path="",
                        command_line_args=(),
                        pipeline_segments=(),
                        rejection_reason=f"Security policy violation: Command binary '{base_bin}' is not in permitted whitelist.",
                    )
            else:
                if base_bin not in APPROVED_PIPELINE_CMDLETS:
                    return ValidatedCommand(
                        is_valid=False,
                        executable_path="",
                        command_line_args=(),
                        pipeline_segments=(),
                        rejection_reason=f"Security policy violation: Pipeline cmdlet '{base_bin}' is not in approved pipeline allowlist.",
                    )

            is_pwsh = (
                base_bin in APPROVED_PIPELINE_CMDLETS
                or base_bin.startswith("get-")
                or base_bin.startswith("select-")
                or base_bin.startswith("new-")
                or base_bin.startswith("remove-")
            )

            pipeline_segments.append(
                PipelineSegment(
                    raw_segment=seg_trimmed,
                    base_command=base_bin,
                    arguments=tuple(tokens[1:]),
                    is_powershell_cmdlet=is_pwsh,
                )
            )

        is_pwsh_pipeline = len(pipeline_segments) > 1 or any(
            p.is_powershell_cmdlet for p in pipeline_segments
        )

        return ValidatedCommand(
            is_valid=True,
            executable_path=pipeline_segments[0].base_command,
            command_line_args=pipeline_segments[0].arguments,
            pipeline_segments=tuple(pipeline_segments),
            is_powershell_pipeline=is_pwsh_pipeline,
        )
