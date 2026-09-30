"""Tests for Step 3: Task Engine and Agent Engine."""

import pytest
from orchestrator.engines.agents import AgentBlueprint, AgentEngine
from orchestrator.engines.core import ServiceContainer
from orchestrator.engines.tasks import SubTask, TaskEngine, TaskStatus


@pytest.mark.anyio
async def test_task_engine_dag_scheduling():
    container = ServiceContainer()
    task_engine = TaskEngine()
    await task_engine.initialize(container)
    await task_engine.start()

    t1 = SubTask(id="task-1", title="Write Architecture")
    t2 = SubTask(id="task-2", title="Implement Code", dependencies=["task-1"])
    t3 = SubTask(id="task-3", title="Write Tests", dependencies=["task-2"])

    task_engine.add_subtask(t1)
    task_engine.add_subtask(t2)
    task_engine.add_subtask(t3)

    ready = task_engine.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == "task-1"
    assert task_engine.get_progress() == 0.0

    task_engine.update_task_status("task-1", TaskStatus.COMPLETED)
    ready = task_engine.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == "task-2"

    task_engine.update_task_status("task-2", TaskStatus.COMPLETED)
    ready = task_engine.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == "task-3"

    task_engine.update_task_status("task-3", TaskStatus.COMPLETED)
    assert task_engine.get_progress() == 1.0


@pytest.mark.anyio
async def test_agent_engine_composition():
    container = ServiceContainer()
    agent_engine = AgentEngine()
    await agent_engine.initialize(container)
    await agent_engine.start()

    # Check default blueprints
    dev_bp = agent_engine.get_blueprint("developer")
    assert dev_bp is not None
    assert dev_bp.name == "developer"

    # Instantiate Agent Component
    comp = agent_engine.create_agent_component("developer")
    assert comp is not None
    assert comp.schema.metadata.id == "agent-developer"

    comp.initialize({})
    res = await comp.execute({"task": "Refactor auth logic"})
    assert res["status"] == "completed"
    assert "Refactor auth logic" in res["output"]
