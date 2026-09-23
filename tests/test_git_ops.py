"""Tests for workspace Git operations."""

from pathlib import Path
from orchestrator.utils import GitOps


def test_git_init_and_commit(tmp_path: Path):
    git = GitOps(tmp_path)
    assert git.init_repo() is True
    assert git.is_git_repo() is True

    # Create a dummy file
    (tmp_path / "hello.txt").write_text("Hello Git", encoding="utf-8")
    assert git.has_uncommitted_changes() is True

    # Commit
    commit_hash = git.commit("Initial commit")
    assert commit_hash is not None
    assert len(commit_hash) >= 7
    assert git.has_uncommitted_changes() is False
