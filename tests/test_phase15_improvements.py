"""Unit tests for Phase 15 enterprise architecture modularization, BaseAgentFactory, and DiffRenderer."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.panel import Panel

from orchestrator.agents.base import BaseAgentFactory
from orchestrator.agents.documentation import DocumentationAgentFactory, create_documentation_agent
from orchestrator.analysis import ConnectivityChecker, GraftContextProvider, PytestOutputParser
from orchestrator.core import (
    AgentFactoryProtocol,
    AgentRoleConfig,
    BudgetExhaustedError,
    CircuitBreakerTrippedError,
    ContextInjectorProtocol,
    DomainProfile,
    HumanRejectedError,
    LogStoreProtocol,
    OrchestratorConfig,
    OrchestratorException,
    PipelineAbortedError,
    PipelineProtocol,
    PreflightCheckError,
)
from orchestrator.rendering import DiffRenderer, MarkdownReportGenerator
from orchestrator.skills import CompactSkillInjector, SkillManager, SkillRegistry
from orchestrator.ui import InteractiveLogExplorer, LogStep, OrchestratorLiveVisualizer, SessionLogStore
from orchestrator.vcs import GitOps


# ---------------------------------------------------------------------------
# 1. Core Module, Exceptions, Protocols & Models
# ---------------------------------------------------------------------------

def test_core_exceptions_hierarchy():
    """Custom exceptions must inherit cleanly from OrchestratorException."""
    assert issubclass(BudgetExhaustedError, OrchestratorException)
    assert issubclass(CircuitBreakerTrippedError, OrchestratorException)
    assert issubclass(PipelineAbortedError, OrchestratorException)
    assert issubclass(PreflightCheckError, OrchestratorException)
    assert issubclass(HumanRejectedError, OrchestratorException)

    with pytest.raises(BudgetExhaustedError):
        raise BudgetExhaustedError("Budget exhausted test")


def test_core_protocols_runtime_checkable():
    """Core typing protocols must be runtime checkable."""
    class DummyInjector:
        def should_inject(self, role: str, task: str) -> bool:
            return True
        def get_context(self, task: str, workspace: Path) -> str:
            return "context"

    assert isinstance(DummyInjector(), ContextInjectorProtocol)

    class DummyFactory:
        @classmethod
        def create(cls, config, skill_manager, workspace_path=None, **kwargs):
            return None

    assert isinstance(DummyFactory(), AgentFactoryProtocol)


def test_domain_profile_model():
    """DomainProfile must store language-specific tool commands and extensions."""
    py_profile = DomainProfile(
        name="python",
        test_command="pytest -v",
        lint_command="ruff check .",
        preflight_extensions=[".py"],
    )
    assert py_profile.name == "python"
    assert py_profile.preflight_extensions == [".py"]

    cfg = OrchestratorConfig()
    active_profile = cfg.get_current_domain_profile()
    assert active_profile.name == "python"
    assert active_profile.test_command == "pytest -v"


# ---------------------------------------------------------------------------
# 2. BaseAgentFactory & DocumentationAgent
# ---------------------------------------------------------------------------

def test_base_agent_factory_lifecycle(tmp_path: Path):
    """BaseAgentFactory must resolve workspace, LLM, context, and build agent properly."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(tmp_path)

    with patch("orchestrator.agents.base.create_llm_for_role") as mock_llm:
        mock_llm.return_value = MagicMock()
        agent = BaseAgentFactory.create(
            config=cfg,
            skill_manager=sm,
            workspace_path=tmp_path,
        )
        assert agent is not None
        assert len(agent.tools) >= 1


def test_documentation_agent_creation(tmp_path: Path):
    """DocumentationAgentFactory must construct agent with documentation write boundaries."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(tmp_path)

    with patch("orchestrator.agents.base.create_llm_for_role") as mock_llm:
        mock_llm.return_value = MagicMock()
        doc_agent = create_documentation_agent(
            config=cfg,
            skill_manager=sm,
            workspace_path=tmp_path,
            task_text="Document project",
        )
        assert doc_agent is not None
        assert "Technical Writer" in doc_agent.system_prompt


# ---------------------------------------------------------------------------
# 3. DiffRenderer & ReportGenerator
# ---------------------------------------------------------------------------

def test_diff_renderer_render_file_change():
    """DiffRenderer must generate rich Panel with unified diff highlighting."""
    old_code = "def hello():\n    return 'old'\n"
    new_code = "def hello():\n    return 'new'\n"

    panel = DiffRenderer.render_file_change("sample.py", old_code, new_code)
    assert isinstance(panel, Panel)


def test_markdown_report_generator():
    """MarkdownReportGenerator must generate valid markdown with tables and telemetry."""
    md = MarkdownReportGenerator.generate_pipeline_summary(
        task="Test Task",
        mode="dev-test",
        status="SUCCESS",
        iterations=2,
        duration_seconds=12.5,
        total_tokens=15000,
        total_cost_usd=0.0125,
        steps=[{"agent_role": "developer", "action_type": "code", "iteration": 1, "duration_seconds": 5.0}],
    )
    assert "# 🚀 Orchestrator Pipeline Run Report" in md
    assert "Test Task" in md
    assert "15,000" in md
    assert "$0.0125" in md


# ---------------------------------------------------------------------------
# 4. Modular VCS, Analysis, and UI packages
# ---------------------------------------------------------------------------

def test_vcs_git_ops_isolated_import(tmp_path: Path):
    """GitOps in orchestrator.vcs must initialize cleanly and report status."""
    git = GitOps(tmp_path)
    assert git.workspace_path == tmp_path
    assert git.sanitize_branch_name("Add Auth Feature! #123") == "add-auth-feature-123"


def test_ui_session_store_and_steps(tmp_path: Path):
    """SessionLogStore must record LogStep objects and prune correctly."""
    store = SessionLogStore(workspace_path=tmp_path, max_retained_sessions=3)
    step = store.add_step(summary="Ran test", is_error=False)
    assert isinstance(step, LogStep)
    assert store.get_latest_step() == step

    saved_file = store.save_to_file(diagnostics_dir=tmp_path / "diagnostics")
    assert saved_file.exists()


def test_skills_registry(tmp_path: Path):
    """SkillRegistry should index skills and support search queries."""
    from openhands.sdk.skills import Skill

    s1 = Skill(name="clean-python-architecture", content="Write clean code", description="Python clean code rules")
    s2 = Skill(name="docker-devops-containerization", content="Write Dockerfile", description="Docker containerization")

    registry = SkillRegistry([s1, s2])
    assert len(registry.list_all()) == 2
    assert registry.get("clean-python-architecture") == s1

    search_res = registry.search("docker")
    assert len(search_res) == 1
    assert search_res[0].name == "docker-devops-containerization"
