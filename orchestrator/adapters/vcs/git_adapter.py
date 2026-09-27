"""GitOps Adapter (Atomic Commits, Merkle Workspace Scanning).

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Optional
from orchestrator.vcs.git_ops import GitOps


class GitOpsAdapter:
    """Outbound driven adapter implementing VCSPort via GitOps."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.git = GitOps(workspace_path)

    def create_atomic_checkpoint(self, milestone_id: str, message: str) -> str:
        commit_msg = f"[ORAGAI-VERIFIED] Milestone {milestone_id}: {message}"
        self.git.init_if_needed()
        self.git.stage_all()
        sha = self.git.commit(commit_msg)
        return sha if sha else "0000000000000000000000000000000000000000"

    def rollback_to_checkpoint(self, commit_sha: str) -> bool:
        res = self.git._run_git("reset", "--hard", commit_sha)
        return res.returncode == 0

    def get_workspace_merkle_root(self) -> str:
        hasher = hashlib.sha256()
        for p in sorted(self.workspace_path.rglob("*")):
            if not p.is_file():
                continue
            if (
                ".git" in p.parts
                or ".venv" in p.parts
                or "__pycache__" in p.parts
            ):
                continue
            try:
                hasher.update(p.read_bytes())
            except Exception:
                continue
        return hasher.hexdigest()
