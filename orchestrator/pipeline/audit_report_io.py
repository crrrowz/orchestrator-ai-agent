"""Unified I/O utilities for locating, normalizing, and reading audit reports."""

from pathlib import Path
from typing import Optional


def locate_and_normalize_report(
    workspace_path: Path, filename: str = "AUDIT_REPORT.md"
) -> Optional[Path]:
    """Locate an audit report, migrating root-level report files to docs/ if found.

    Args:
        workspace_path: Root path of the target workspace.
        filename: Name of the report markdown file (e.g. AUDIT_REPORT.md or AUDIT_FIX_REPORT.md).

    Returns:
        The canonical Path under docs/ if found or migrated, otherwise None.
    """
    docs_dir = workspace_path / "docs"
    docs_file = docs_dir / filename
    root_file = workspace_path / filename

    if docs_file.exists():
        return docs_file

    if root_file.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        try:
            root_file.replace(docs_file)
            return docs_file
        except OSError:
            return root_file

    return None


def read_report(workspace_path: Path, filename: str = "AUDIT_REPORT.md") -> str:
    """Read the contents of an audit report, normalizing its location to docs/ if necessary.

    Returns:
        Stripped text content of the report file, or empty string if not found.
    """
    report_path = locate_and_normalize_report(workspace_path, filename=filename)
    if not report_path or not report_path.exists():
        return ""
    try:
        return report_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""
