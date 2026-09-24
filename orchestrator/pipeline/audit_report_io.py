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
    candidates = [filename, filename.lower(), filename.upper()]

    # 1. Check under docs/
    for name in candidates:
        cand_path = docs_dir / name
        if cand_path.exists() and cand_path.is_file():
            return cand_path

    # 2. Check at workspace root and migrate to docs/
    for name in candidates:
        root_cand = workspace_path / name
        if root_cand.exists() and root_cand.is_file():
            docs_dir.mkdir(parents=True, exist_ok=True)
            target = docs_dir / filename
            try:
                root_cand.replace(target)
                return target
            except OSError:
                return root_cand

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
