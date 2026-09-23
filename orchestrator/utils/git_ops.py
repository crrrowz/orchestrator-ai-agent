"""Git operations utility for managing workspace commits and branches."""

import subprocess
from pathlib import Path
from typing import Optional


class GitOps:
    """Provides high-level Git operations for the multi-agent workspace."""

    def __init__(self, workspace_path: Path | str):
        p = Path(workspace_path).resolve()
        self.workspace_path = p.parent if p.is_file() else p

    def _run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=str(self.workspace_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def is_git_repo(self) -> bool:
        """Check if workspace is a valid Git repository."""
        proc = self._run_git("rev-parse", "--is-inside-work-tree")
        return proc.returncode == 0 and proc.stdout.strip() == "true"

    def init_repo(self) -> bool:
        """Initialize a new Git repository if not already initialized."""
        if not self.is_git_repo():
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            res = self._run_git("init")
            return res.returncode == 0
        return True

    init_if_needed = init_repo

    def get_status(self) -> str:
        """Get git status output (porcelain format)."""
        proc = self._run_git("status", "--porcelain")
        return proc.stdout

    def has_uncommitted_changes(self) -> bool:
        """Check if there are modified, staged, or untracked files."""
        return bool(self.get_status().strip())

    is_dirty = has_uncommitted_changes

    def get_diff(self, staged: bool = False) -> str:
        """Get git diff of working directory or staged changes."""
        args = ["diff", "--cached"] if staged else ["diff"]
        proc = self._run_git(*args)
        return proc.stdout

    def get_compact_diff(
        self,
        max_lines_per_file: int = 50,
        max_chars: int = 4000,
        staged: bool = False,
    ) -> str:
        """Generate compact diff with --stat summary and per-file truncation to prevent context blowup."""
        stat_args = ["diff", "--cached", "--stat"] if staged else ["diff", "--stat"]
        stat_proc = self._run_git(*stat_args)
        stat_summary = stat_proc.stdout.strip()

        diff_args = (
            ["diff", "--cached", "--unified=3"] if staged else ["diff", "--unified=3"]
        )
        diff_proc = self._run_git(*diff_args)
        diff_text = diff_proc.stdout.strip()

        if not diff_text:
            return stat_summary or self.get_status().strip()

        lines = diff_text.splitlines()
        truncated_lines: list[str] = []
        file_line_count = 0
        in_file = False

        for line in lines:
            if line.startswith("diff --git"):
                in_file = True
                file_line_count = 0
                truncated_lines.append(line)
            elif in_file:
                file_line_count += 1
                if file_line_count <= max_lines_per_file:
                    truncated_lines.append(line)
                elif file_line_count == max_lines_per_file + 1:
                    truncated_lines.append("  [... diff truncated for this file ...]")
            else:
                truncated_lines.append(line)

        result = "\n".join(truncated_lines).strip()
        if len(result) > max_chars:
            omitted = len(result) - max_chars
            result = (
                result[:max_chars]
                + f"\n\n[... Diff truncated: {omitted} characters omitted to save tokens ...]"
            )

        return (
            f"Diff Summary:\n{stat_summary}\n\nDetailed Changes:\n{result}".strip()
            if stat_summary
            else result
        )

    def stage_all(self) -> bool:
        """Stage all changes in the workspace."""
        proc = self._run_git("add", "-A")
        return proc.returncode == 0

    def commit(
        self,
        message: str,
        author_name: str = "Agent Orchestrator",
        author_email: str = "agent@orchestrator.local",
    ) -> Optional[str]:
        """Stage all changes and create a commit. Returns commit hash or None."""
        if not self.has_uncommitted_changes():
            return None

        self.stage_all()
        proc = self._run_git(
            "-c",
            f"user.name={author_name}",
            "-c",
            f"user.email={author_email}",
            "commit",
            "-m",
            message,
        )
        if proc.returncode == 0:
            head = self._run_git("rev-parse", "HEAD")
            return head.stdout.strip()
        return None

    def get_log(self, max_count: int = 5) -> str:
        """Get recent commit logs."""
        proc = self._run_git("log", f"-n{max_count}", "--oneline")
        return proc.stdout.strip()

    def create_task_branch(self, task_name: str) -> Optional[str]:
        """Create and switch to an isolated task branch slug."""
        if not self.is_git_repo():
            self.init_repo()

        import re
        import time

        clean_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", task_name.strip().lower()).strip(
            "-"
        )[:25]
        if not clean_slug:
            clean_slug = "task"
        timestamp = int(time.time())
        branch_name = f"agent/{clean_slug}-{timestamp}"

        proc = self._run_git("checkout", "-b", branch_name)
        if proc.returncode == 0:
            return branch_name

        proc_switch = self._run_git("switch", "-c", branch_name)
        if proc_switch.returncode == 0:
            return branch_name

        return None

    create_and_checkout_branch = create_task_branch

    def get_current_branch(self) -> Optional[str]:
        """Return the active git branch name."""
        proc = self._run_git("branch", "--show-current")
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
        proc_head = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        if proc_head.returncode == 0 and proc_head.stdout.strip():
            return proc_head.stdout.strip()
        return None
