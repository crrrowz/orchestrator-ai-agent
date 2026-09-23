"""Git operations utility for managing workspace commits and branches."""

import subprocess
from pathlib import Path
from typing import Optional


class GitOps:
    """Provides high-level Git operations for the multi-agent workspace."""

    def __init__(self, workspace_path: Path | str):
        self.workspace_path = Path(workspace_path).resolve()

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

    def get_status(self) -> str:
        """Get git status output (porcelain format)."""
        proc = self._run_git("status", "--porcelain")
        return proc.stdout

    def has_uncommitted_changes(self) -> bool:
        """Check if there are modified, staged, or untracked files."""
        return bool(self.get_status().strip())

    def get_diff(self, staged: bool = False) -> str:
        """Get git diff of working directory or staged changes."""
        args = ["diff", "--cached"] if staged else ["diff"]
        proc = self._run_git(*args)
        return proc.stdout

    def stage_all(self) -> bool:
        """Stage all changes in the workspace."""
        proc = self._run_git("add", "-A")
        return proc.returncode == 0

    def commit(self, message: str, author_name: str = "Agent Orchestrator", author_email: str = "agent@orchestrator.local") -> Optional[str]:
        """Stage all changes and create a commit. Returns commit hash or None."""
        if not self.has_uncommitted_changes():
            return None

        self.stage_all()
        proc = self._run_git(
            "-c", f"user.name={author_name}",
            "-c", f"user.email={author_email}",
            "commit", "-m", message
        )
        if proc.returncode == 0:
            head = self._run_git("rev-parse", "HEAD")
            return head.stdout.strip()
        return None

    def get_log(self, max_count: int = 5) -> str:
        """Get recent commit logs."""
        proc = self._run_git("log", f"-n{max_count}", "--oneline")
        return proc.stdout.strip()
