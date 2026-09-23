"""Tests for OpenHands skill discovery and assignment."""

from pathlib import Path
from orchestrator.config import SkillManager


def test_discover_skills():
    manager = SkillManager(Path.cwd())
    available = manager.available_skills
    
    # Assert core skills are loaded from .agents/skills
    assert "clean-python-architecture" in available
    assert "pytest-rigorous-testing" in available
    assert "code-review-standards" in available
    assert "architectural-decomposition" in available
    assert "systematic-debugging" in available
    assert "graft-architecture-intelligence" in available


def test_get_skills_for_role():
    manager = SkillManager(Path.cwd())
    dev_skills = manager.get_skills_for_role(["clean-python-architecture", "graft-architecture-intelligence"])
    assert len(dev_skills) == 2
    names = [s.name for s in dev_skills]
    assert "clean-python-architecture" in names
    assert "graft-architecture-intelligence" in names


def test_build_agent_context():
    manager = SkillManager(Path.cwd())
    context = manager.build_agent_context(["pytest-rigorous-testing"])
    assert context is not None
    skill_names = [s.name for s in context.skills]
    assert "pytest-rigorous-testing" in skill_names


def test_openrouter_model_normalization_and_fallback():
    from orchestrator.config import normalize_model_slug, OrchestratorConfig, create_llm_for_role, AgentRoleConfig
    
    assert normalize_model_slug("openrouter/free") == "openrouter/openrouter/free"
    assert normalize_model_slug("free") == "openrouter/openrouter/free"
    assert normalize_model_slug("openrouter/qwen/qwen3.8-27b") == "openrouter/qwen/qwen3.8-27b:free"

    cfg = OrchestratorConfig(openrouter_api_key="sk-test-fake")
    role_cfg = AgentRoleConfig(role="developer", model="openrouter/qwen/qwen3.8-27b:free")
    llm = create_llm_for_role(cfg, role_cfg)
    
    assert llm.model == "openrouter/qwen/qwen3.8-27b:free"
    assert llm.fallback_strategy is not None
    assert len(llm.fallback_strategy._resolved) == 1
    assert llm.fallback_strategy._resolved[0].model == "openrouter/openrouter/free"

    # Test reverse fallback when openrouter/free is the primary model
    role_cfg_free = AgentRoleConfig(role="developer", model="openrouter/free")
    llm_free = create_llm_for_role(cfg, role_cfg_free)
    assert llm_free.model == "openrouter/openrouter/free"
    assert llm_free.fallback_strategy is not None
    assert llm_free.fallback_strategy._resolved[0].model == "openrouter/qwen/qwen3.8-27b:free"


