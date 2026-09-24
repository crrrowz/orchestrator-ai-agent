"""Embedded File Path Detection and Resolution within Task Specifications."""

import re
from pathlib import Path
from typing import List, Set, Tuple


class FilePathResolver:
    """Detects and resolves file paths embedded within task descriptions and inlines their content."""

    PATH_PATTERNS = [
        r'["\']([A-Za-z]:\\[^"\'<>|\n\r]+?\.\w{1,5}|/[^"\'<>|\n\r]+?\.\w{1,5}|\./[^"\'<>|\n\r]+?\.\w{1,5}|[^"\'<>|\n\r]+/[^"\'<>|\n\r]+?\.\w{1,5})["\']',  # Quoted paths (supports spaces)
        r'(?:[A-Za-z]:\\[^\s"\'<>|\n\r]+?\.\w{1,5})',  # Windows absolute: D:\specs\auth.md
        r"(?:/[a-zA-Z0-9_\-.]+/[a-zA-Z0-9_\-/.]+\.\w{1,5})",  # Unix absolute: /etc/config.json
        r"(?:\./[a-zA-Z0-9_\-/.]+\.\w{1,5})",  # Explicit relative: ./specs/auth.md
        r"(?:(?<![a-zA-Z0-9_\-.])[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-/.]+\.\w{1,5})",  # Bare relative: specs/auth.md
        r"(?:(?<![a-zA-Z0-9_\-.])[a-zA-Z0-9_\-]+\.(?:md|py|json|yaml|yml|txt|toml|cfg|ini|html|css|js|ts|sh|sql|xml|csv))\b",  # Bare filename
    ]

    @classmethod
    def extract_and_resolve(
        cls,
        task: str,
        workspace: Path,
        max_chars_per_file: int = 4000,
    ) -> Tuple[str, List[str]]:
        """Extract file paths from task text, read contents, and append structured references."""
        resolved_files: List[str] = []
        already_seen: Set[Path] = set()
        injected_blocks: List[str] = []

        workspace_resolved = workspace.resolve()

        # Check if the entire task is a single file path (including unquoted paths with spaces)
        clean_task = task.strip().strip("'\"")
        try:
            p_direct = Path(clean_task)
            if not p_direct.is_absolute():
                p_direct = (workspace_resolved / p_direct).resolve()
            if p_direct.is_file():
                content = p_direct.read_text(encoding="utf-8", errors="replace").strip()
                if content:
                    if len(content) > max_chars_per_file:
                        content = (
                            content[:max_chars_per_file] + "\n... [Content Truncated]"
                        )
                    already_seen.add(p_direct)
                    resolved_files.append(str(p_direct))
                    injected_blocks.append(
                        f"[Referenced File: {p_direct.name} ({p_direct})]:\n{content}"
                    )
        except Exception:
            pass

        for pattern in cls.PATH_PATTERNS:
            for match in re.finditer(pattern, task):
                raw_path = match.group(1) if match.groups() else match.group(0)
                raw_path = raw_path.strip(" \t\n\r'\"<>")
                candidate = Path(raw_path)
                target: Path

                if candidate.is_absolute():
                    target = candidate
                else:
                    target = (workspace_resolved / candidate).resolve()

                if target in already_seen:
                    continue

                if target.is_file():
                    try:
                        content = target.read_text(
                            encoding="utf-8", errors="replace"
                        ).strip()
                        if content:
                            if len(content) > max_chars_per_file:
                                content = (
                                    content[:max_chars_per_file]
                                    + "\n... [Content Truncated]"
                                )
                            already_seen.add(target)
                            resolved_files.append(str(target))
                            injected_blocks.append(
                                f"[Referenced File: {target.name} ({target})]:\n{content}"
                            )
                    except Exception:
                        continue

        if not injected_blocks:
            return task, []

        enriched_task = task.strip() + "\n\n" + "\n\n".join(injected_blocks)
        return enriched_task, resolved_files
