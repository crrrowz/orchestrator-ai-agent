"""Round 11 Ultra-Tier Hardening & Security Isolation Test Suite.

Verifies:
1. ContextManager token bounding with massive task specifications.
2. Subprocess environment secret masking in WorkspaceTerminalTool.
3. SessionLogStore project slugification and session path isolation.
4. PromptBuilder section chaining and directive precedence.
"""

from pathlib import Path
import os
from unittest.mock import patch
import pytest

from orchestrator.config import OrchestratorConfig
from orchestrator.context.manager import ContextManager
from orchestrator.context.prompt_builder import PromptBuilder
from orchestrator.ui.session_store import SessionLogStore
from orchestrator.tools.workspace_tools import (
    WorkspaceTerminalAction,
    execute_terminal_action,
)


class TestRound11Hardening:
    """Tests for Round 11 security isolation and context governance."""

    def test_context_manager_bounds_massive_task_specification(self, tmp_path: Path):
        cfg = OrchestratorConfig(workspace_path=tmp_path)
        mgr = ContextManager(cfg)

        massive_task = "A" * 50_000
        prompt = mgr.build_prompt(
            task=massive_task,
            role="developer",
            workspace=tmp_path,
            max_tokens=2000,  # ~8000 chars limit
        )

        assert len(prompt) <= 9000
        assert "... [Task specification truncated to token ceiling]" in prompt

    def test_session_log_store_slugification_sanitizes_special_characters(self, tmp_path: Path):
        special_ws = tmp_path / "My Project (v2.0) [Prod] #1"
        special_ws.mkdir(parents=True, exist_ok=True)

        store = SessionLogStore(workspace_path=special_ws)
        assert "/" not in store.project_slug
        assert "\\" not in store.project_slug
        assert " " not in store.project_slug
        assert store.project_slug.startswith("my_project")

    def test_subprocess_env_masks_sensitive_api_keys(self, tmp_path: Path):
        action = WorkspaceTerminalAction(
            command="python -c \"import os; print(os.environ.get('OPENROUTER_API_KEY', 'MASKED'))\""
        )

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-secret-12345"}):
            obs = execute_terminal_action(action, base_dir=tmp_path)
            assert obs.is_error is False
            # Secret key must not be passed into child environment
            assert "sk-secret-12345" not in obs.stdout
            assert "MASKED" in obs.stdout

    def test_prompt_builder_directive_precedence(self, tmp_path: Path):
        builder = PromptBuilder("developer")
        builder.add_directive("CRITICAL: Adhere to clean architecture.")
        builder.add_section("Database Specs", "Use PostgreSQL with asyncpg.")

        prompt = builder.build(
            task="Build order microservice",
            workspace=tmp_path,
            max_tokens=1000,
        )

        assert "CRITICAL: Adhere to clean architecture." in prompt
        assert "### Database Specs" in prompt
        assert "Build order microservice" in prompt
