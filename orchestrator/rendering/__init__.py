"""Rendering layer for console outputs, rich diffs, and markdown reports."""

from orchestrator.rendering.diff_renderer import DiffRenderer
from orchestrator.rendering.output import ConsoleOutput, console
from orchestrator.rendering.report_generator import MarkdownReportGenerator

__all__ = [
    "console",
    "ConsoleOutput",
    "DiffRenderer",
    "MarkdownReportGenerator",
]
