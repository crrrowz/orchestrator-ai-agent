"""Tests for workspace Git operations."""

from pathlib import Path
from orchestrator.vcs.git_ops import GitOps


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
    assert git.has_uncommitted_changes() is False


def test_git_branch_sanitization_and_creation(tmp_path: Path):
    git = GitOps(tmp_path)
    git.init_repo()

    # Sanitize test
    assert (
        GitOps.sanitize_branch_name("Fix: /special & symbols! (now)")
        == "fix-special-symbols-now"
    )
    assert GitOps.sanitize_branch_name("   ") == "task"

    # Branch creation
    branch = git.create_task_branch("Implement User Auth")
    assert branch is not None
    assert branch.startswith("agent/implement-user-auth-")
    assert git.get_current_branch() == branch
