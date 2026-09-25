"""Tests for OpenHands skill discovery, path-based role hierarchy, and token compression."""

from pathlib import Path
from orchestrator.config import SkillManager
from orchestrator.skills.resolver import SkillResolver
from orchestrator.skills.compressor import CompactSkillInjector


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
    dev_skills = manager.get_skills_for_role(
        ["clean-python-architecture", "graft-architecture-intelligence"]
    )
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


def test_path_based_role_discovery_and_dynamic_registration(tmp_path: Path):
    """Verify that SkillResolver and SkillManager dynamically discover skills organized by role hierarchy."""
    skills_root = tmp_path / ".agents" / "skills"
    
    # Setup custom role hierarchy
    (skills_root / "security_analyst" / "penetration-testing").mkdir(parents=True)
    (skills_root / "security_analyst" / "penetration-testing" / "SKILL.md").write_text(
        "---\nname: penetration-testing\ndescription: Automated vulnerability assessment\n---\n# Penetration Testing\n",
        encoding="utf-8",
    )

    (skills_root / "developer" / "async-optimization").mkdir(parents=True)
    (skills_root / "developer" / "async-optimization" / "SKILL.md").write_text(
        "---\nname: async-optimization\ndescription: Asyncio concurrency rules\n---\n# Async Optimization\n",
        encoding="utf-8",
    )

    # 1. SkillResolver role-path discovery
    role_skills = SkillResolver.discover_role_skills("security_analyst", skills_root=skills_root)
    assert role_skills == ["penetration-testing"]

    all_roles = SkillResolver.discover_all_skills_by_role(skills_root=skills_root)
    assert "security_analyst" in all_roles
    assert "developer" in all_roles
    assert all_roles["developer"] == ["async-optimization"]

    # 2. SkillManager path-based instantiation
    sm = SkillManager(tmp_path)
    assert "penetration-testing" in sm.available_skills
    assert "async-optimization" in sm.available_skills
    assert "security_analyst" in sm.available_roles

    # Dynamic role resolution via string role name
    sec_skills = sm.get_skills_for_role("security_analyst")
    assert len(sec_skills) == 1
    assert sec_skills[0].name == "penetration-testing"

    # Context building using role name
    ctx = sm.build_agent_context("security_analyst")
    assert len(ctx.skills) == 1
    assert ctx.skills[0].name == "penetration-testing"


def test_persona_rbac_and_compression_invariants():
    """Verify persona RBAC rules and token efficiency in authoritative role skills."""
    manager = SkillManager(Path.cwd())

    # Developer skill: must enforce Zero-Stub and forbid editing tests/
    dev_skill = manager.get_skill("clean-python-architecture")
    assert dev_skill is not None
    content_lower = dev_skill.content.lower()
    assert "zero-stub" in content_lower or "zero stubs" in content_lower
    assert "tests/" in content_lower

    # Tester skill: must enforce AAA and forbid editing production source code
    tester_skill = manager.get_skill("pytest-rigorous-testing")
    assert tester_skill is not None
    t_content_lower = tester_skill.content.lower()
    assert "aaa" in t_content_lower
    assert "production" in t_content_lower or "src/" in t_content_lower

    # Architect skill: must enforce graft discovery
    arch_skill = manager.get_skill("architectural-decomposition")
    assert arch_skill is not None
    a_content_lower = arch_skill.content.lower()
    assert "graft" in a_content_lower

    # Auditor skill: must enforce graft discovery and unification
    audit_skill = manager.get_skill("system-unification-audit")
    assert audit_skill is not None
    aud_content_lower = audit_skill.content.lower()
    assert "graft" in aud_content_lower

    # Verify character/token reduction
    for skill_name in manager.available_skills:
        skill = manager.get_skill(skill_name)
        assert skill is not None
        compact = CompactSkillInjector.create_compact_skill(skill)
        assert len(compact.content) <= 1200


def test_openrouter_model_normalization_and_fallback():
    from orchestrator.config import (
        normalize_model_slug,
        OrchestratorConfig,
        create_llm_for_role,
        AgentRoleConfig,
    )

    assert normalize_model_slug("openrouter/free") == "openrouter/openrouter/free"
    assert normalize_model_slug("free") == "openrouter/openrouter/free"
    assert (
        normalize_model_slug("openrouter/qwen/qwen3.8-27b")
        == "openrouter/qwen/qwen3.8-27b:free"
    )

    cfg = OrchestratorConfig(openrouter_api_key="sk-test-fake")
    role_cfg = AgentRoleConfig(
        role="developer", model="openrouter/qwen/qwen3.8-27b:free"
    )
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
    assert (
        llm_free.fallback_strategy._resolved[0].model
        == "openrouter/qwen/qwen3.8-27b:free"
    )

