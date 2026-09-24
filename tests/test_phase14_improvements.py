"""Unit tests for Phase 14 ContextManager, LLMManager, SkillResolver, and FilePathResolver."""

from pathlib import Path
from unittest.mock import MagicMock, patch


from orchestrator.config import OrchestratorConfig
from orchestrator.context import (
    ContextInjector,
    ContextManager,
    FilePathResolver,
    PromptBuilder,
)
from orchestrator.llm import (
    LLMManager,
    get_pricing_rates,
)
from orchestrator.skills import SkillResolver


# ---------------------------------------------------------------------------
# 1. SkillResolver Tests
# ---------------------------------------------------------------------------


def test_skill_resolver_semantic_matching():
    """SkillResolver must match keyword patterns in task specifications to relevant skills."""
    available = [
        "clean-python-architecture",
        "pytest-rigorous-testing",
        "docker-devops-containerization",
        "security-audit-hardening",
        "api-design-contract",
        "architectural-decomposition",
        "systematic-debugging",
        "code-review-standards",
        "graft-architecture-intelligence",
    ]

    # Task requiring containerization & testing
    task_docker_test = (
        "Build a Dockerfile and docker-compose setup, then run pytest test coverage."
    )
    resolved = SkillResolver.resolve(task_docker_test, available)
    assert "docker-devops-containerization" in resolved
    assert "pytest-rigorous-testing" in resolved
    assert "clean-python-architecture" in resolved

    # Task requiring security & API
    task_security_api = (
        "Implement OAuth2 JWT authentication for the FastAPI rest endpoint."
    )
    resolved = SkillResolver.resolve(task_security_api, available)
    assert "security-audit-hardening" in resolved
    assert "api-design-contract" in resolved

    # Task with no special keywords defaults to base skills
    task_generic = "Sort a list of strings alphabetically."
    resolved = SkillResolver.resolve(task_generic, available)
    assert resolved == ["clean-python-architecture"]


# ---------------------------------------------------------------------------
# 2. FilePathResolver Tests
# ---------------------------------------------------------------------------


def test_file_path_resolver_embedded_extraction(tmp_path: Path):
    """FilePathResolver should detect relative and absolute file paths in text and inline their content."""
    spec_file = tmp_path / "auth_spec.md"
    spec_file.write_text(
        "# Authentication Specification\nMust use JWT bearer tokens.", encoding="utf-8"
    )

    task = (
        f"Please implement feature according to {spec_file.name} and ensure compliance."
    )
    enriched_task, resolved_paths = FilePathResolver.extract_and_resolve(
        task, workspace=tmp_path
    )

    assert len(resolved_paths) == 1
    assert str(spec_file.resolve()) in resolved_paths[0]
    assert "[Referenced File: auth_spec.md" in enriched_task
    assert "Must use JWT bearer tokens." in enriched_task


def test_file_path_resolver_nonexistent_and_truncation(tmp_path: Path):
    """FilePathResolver should ignore missing files and truncate excessively large files."""
    large_file = tmp_path / "large_dataset.txt"
    large_file.write_text("X" * 10000, encoding="utf-8")

    task = f"Analyze {large_file.name} and nonexistent/missing_spec.md"
    enriched_task, resolved_paths = FilePathResolver.extract_and_resolve(
        task, workspace=tmp_path, max_chars_per_file=500
    )

    assert len(resolved_paths) == 1
    assert "[Referenced File: missing_spec.md" not in enriched_task
    assert "[Referenced File: large_dataset.txt" in enriched_task
    assert "... [Content Truncated]" in enriched_task


# ---------------------------------------------------------------------------
# 3. ContextManager & Injectors Tests
# ---------------------------------------------------------------------------


class CustomTestInjector(ContextInjector):
    def __init__(self, tag: str):
        self.tag = tag

    def should_inject(self, role: str, task: str) -> bool:
        return True

    def get_context(self, task: str, workspace: Path) -> str:
        return f"[Custom Block: {self.tag}]"


def test_context_manager_assembly_and_priority(tmp_path: Path):
    """ContextManager should order injectors by priority and assemble clean prompt."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    mgr = ContextManager(cfg)

    # Register out of order
    mgr.register(CustomTestInjector("PRIORITY_80"), priority=80)
    mgr.register(CustomTestInjector("PRIORITY_10"), priority=10)

    prompt = mgr.build_prompt(
        task="Build an authentication microservice",
        role="developer",
        workspace=tmp_path,
        max_tokens=2000,
    )

    pos_10 = prompt.find("[Custom Block: PRIORITY_10]")
    pos_80 = prompt.find("[Custom Block: PRIORITY_80]")
    assert pos_10 != -1 and pos_80 != -1
    assert pos_10 < pos_80, (
        "Higher priority (lower integer) must precede lower priority blocks"
    )


def test_context_manager_token_budget_truncation(tmp_path: Path):
    """ContextManager should stop adding blocks when token budget ceiling is reached."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    mgr = ContextManager(cfg)

    mgr.register(CustomTestInjector("A" * 500), priority=10)
    mgr.register(CustomTestInjector("B" * 500), priority=20)
    mgr.register(CustomTestInjector("C" * 500), priority=30)

    # Very small budget (approx 50 tokens ~= 200 chars)
    prompt = mgr.build_prompt(
        task="Do task",
        role="developer",
        workspace=tmp_path,
        max_tokens=60,
    )

    # Should contain first block truncated or truncated marker, but not third block
    assert "PRIORITY" not in prompt


def test_prompt_builder_fluent_api(tmp_path: Path):
    """PromptBuilder should fluently combine directives and sections with ContextManager."""
    pb = PromptBuilder(role="developer")
    pb.add_directive("Adhere strictly to clean-python-architecture.")
    pb.add_section(
        "Requirements", "1. Unit test coverage > 90%\n2. Full type annotations"
    )

    prompt = pb.build(task="Create billing endpoint", workspace=tmp_path)
    assert "Adhere strictly to clean-python-architecture." in prompt
    assert "### Requirements" in prompt
    assert "Task Specification:\nCreate billing endpoint" in prompt


# ---------------------------------------------------------------------------
# 4. LLMManager Tests
# ---------------------------------------------------------------------------


def test_llm_manager_singleton_and_pool():
    """LLMManager must act as a singleton and pool LLM instances per role."""
    LLMManager.reset_instance()
    mgr1 = LLMManager.get_instance()
    mgr2 = LLMManager.get_instance()
    assert mgr1 is mgr2

    with patch("orchestrator.llm.manager.create_llm_for_role") as mock_create:
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm

        llm_dev = mgr1.get_llm("developer")
        assert llm_dev is mock_llm
        assert mock_create.call_count == 1

        # Second call should reuse pooled instance without re-creating
        llm_dev_cached = mgr1.get_llm("developer")
        assert llm_dev_cached is mock_llm
        assert mock_create.call_count == 1

        # Swapping model should invalidate pool entry and re-create
        mgr1.swap_model("developer", "openrouter/openai/gpt-4o")
        assert mock_create.call_count == 2


def test_pricing_rates_computation():
    """get_pricing_rates should return accurate input and output rates per 1M tokens."""
    # Free tier
    assert get_pricing_rates("openrouter/qwen/qwen3.8-27b:free") == (0.0, 0.0)
    assert get_pricing_rates("openrouter/free") == (0.0, 0.0)

    # Commercial tiers
    in_rate, out_rate = get_pricing_rates("anthropic/claude-sonnet-4-5-20250929")
    assert in_rate == 3.0 and out_rate == 15.0

    in_rate, out_rate = get_pricing_rates("openai/gpt-4o-mini")
    assert in_rate == 0.15 and out_rate == 0.60
