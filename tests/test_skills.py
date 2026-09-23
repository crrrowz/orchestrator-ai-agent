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


def test_get_skills_for_role():
    manager = SkillManager(Path.cwd())
    dev_skills = manager.get_skills_for_role(["clean-python-architecture", "systematic-debugging"])
    assert len(dev_skills) == 2
    names = [s.name for s in dev_skills]
    assert "clean-python-architecture" in names
    assert "systematic-debugging" in names


def test_build_agent_context():
    manager = SkillManager(Path.cwd())
    context = manager.build_agent_context(["pytest-rigorous-testing"])
    assert context is not None
    skill_names = [s.name for s in context.skills]
    assert "pytest-rigorous-testing" in skill_names
