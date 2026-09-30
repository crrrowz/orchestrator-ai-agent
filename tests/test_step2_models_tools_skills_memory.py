"""Tests for Step 2: Model Engine, Tool Engine, Skill Engine, and Memory Engine."""

import pytest
from orchestrator.engines.core import ServiceContainer
from orchestrator.engines.memory import MemoryEngine, MemoryScope
from orchestrator.engines.models import ModelEngine, ModelRequest
from orchestrator.engines.skills import SkillEngine, SkillManifest
from orchestrator.engines.tools import ToolDescriptor, ToolEngine


@pytest.mark.anyio
async def test_models_and_tools_engine():
    container = ServiceContainer()
    model_engine = ModelEngine()
    tool_engine = ToolEngine()
    await model_engine.initialize(container)
    await tool_engine.initialize(container)
    await model_engine.start()
    await tool_engine.start()

    # Test Model Completion
    req = ModelRequest(messages=[{"role": "user", "content": "Hello AI"}])
    res = await model_engine.generate(req)
    assert res.content == "Mock model completion response."
    assert res.prompt_tokens > 0

    # Test Tool Execution
    tool_res = await tool_engine.execute_tool("echo", {"message": "test_echo"})
    assert tool_res.success is True
    assert tool_res.output == "test_echo"

    # Test Unregistered Tool
    bad_res = await tool_engine.execute_tool("unknown_tool", {})
    assert bad_res.success is False
    assert "not registered" in bad_res.error


@pytest.mark.anyio
async def test_skills_and_memory_engine():
    container = ServiceContainer()
    skill_engine = SkillEngine()
    memory_engine = MemoryEngine()
    await skill_engine.initialize(container)
    await memory_engine.initialize(container)
    await skill_engine.start()
    await memory_engine.start()

    # Test Skill Dependency Resolution & Prompt Building
    skill_engine.register_skill(
        SkillManifest(
            name="base-skill",
            system_prompt_snippet="Base rules.",
        )
    )
    skill_engine.register_skill(
        SkillManifest(
            name="python-skill",
            dependencies=["base-skill"],
            system_prompt_snippet="Python rules.",
        )
    )

    prompt = skill_engine.build_skill_prompt(["python-skill"])
    assert "Base rules." in prompt
    assert "Python rules." in prompt

    # Test Memory Scoping and Handoff
    await memory_engine.store(MemoryScope.PROJECT, "architecture", {"pattern": "modular"})
    item = await memory_engine.get(MemoryScope.PROJECT, "architecture")
    assert item is not None
    assert item.value["pattern"] == "modular"

    handoff = await memory_engine.create_handoff(
        from_agent="developer",
        to_agent="tester",
        summary="Implemented feature X",
    )
    assert handoff.scope == MemoryScope.TASK
    assert handoff.value["from_agent"] == "developer"
