"""End-to-End Integration Suite validating all 13 engines operating in concert."""

import pytest
from orchestrator.engines.agents import AgentEngine
from orchestrator.engines.core import CoreEngine
from orchestrator.engines.events import Event, EventEngine
from orchestrator.engines.execution import ExecutionEngine
from orchestrator.engines.governance import GovernanceEngine, GovernanceVerdict
from orchestrator.engines.graph import Connection, GraphDefinition, GraphEngine, GraphNode
from orchestrator.engines.memory import MemoryEngine, MemoryScope
from orchestrator.engines.models import ModelEngine, ModelRequest
from orchestrator.engines.plugins import PluginEngine, PluginManifest
from orchestrator.engines.skills import SkillEngine, SkillManifest
from orchestrator.engines.tasks import SubTask, TaskEngine, TaskStatus
from orchestrator.engines.tools import ToolDescriptor, ToolEngine
from orchestrator.engines.verification import VerificationEngine, VerificationStatus


@pytest.mark.anyio
async def test_full_13_engines_integration_pipeline():
    # 1. Bootstrap Core & Dependency Container
    core = CoreEngine()
    container = await core.bootstrap()
    await core.start()

    # 2. Initialize all 12 satellite engines into the container
    events = EventEngine()
    models = ModelEngine()
    tools = ToolEngine()
    skills = SkillEngine()
    memory = MemoryEngine()
    tasks = TaskEngine()
    agents = AgentEngine()
    execution = ExecutionEngine()
    governance = GovernanceEngine()
    verification = VerificationEngine()
    graph = GraphEngine()
    plugins = PluginEngine()

    all_engines = [
        events, models, tools, skills, memory, tasks,
        agents, execution, governance, verification, graph, plugins
    ]

    for engine in all_engines:
        await engine.initialize(container)
        await engine.start()

    # 3. Verify Container Engine Resolution
    assert container.get_engine(CoreEngine) is core
    assert container.get_engine(EventEngine) is events
    assert container.get_engine(GraphEngine) is graph
    assert container.get_engine(AgentEngine) is agents

    # 4. Set up Event Listener
    event_log = []
    async def capture_event(e: Event):
        event_log.append(e.topic)
    events.subscribe("graph.*", capture_event)

    # 5. Populate Task Engine
    tasks.add_subtask(SubTask(id="sub-1", title="Decompose Feature"))
    tasks.add_subtask(SubTask(id="sub-2", title="Execute Workflow", dependencies=["sub-1"]))
    ready_tasks = tasks.get_ready_tasks()
    assert len(ready_tasks) == 1
    tasks.update_task_status("sub-1", TaskStatus.COMPLETED)

    # 6. Store Project Memory
    await memory.store(MemoryScope.PROJECT, "standards", {"architecture": "Langflow-style Engine Architecture"})

    # 7. Construct and Run Declarative Graph
    workflow = GraphDefinition(
        id="autonomous_dev_verification_flow",
        name="Autonomous Dev & Verification Flow",
        entrypoint_node_id="dev_node",
        nodes={
            "dev_node": GraphNode(id="dev_node", component_name="developer", name="Developer"),
            "test_node": GraphNode(id="test_node", component_name="tester", name="Tester"),
            "rev_node": GraphNode(id="rev_node", component_name="reviewer", name="Reviewer"),
        },
        connections=[
            Connection(id="c1", from_node_id="dev_node", to_node_id="test_node"),
            Connection(id="c2", from_node_id="test_node", to_node_id="rev_node"),
        ],
    )
    graph.load_graph(workflow)

    graph_res = await graph.run_graph("autonomous_dev_verification_flow", {"task": "Implement Modular Engine Platform"})
    assert graph_res["status"] == "completed"
    assert len(event_log) >= 6  # 3 started + 3 completed events

    # 8. Governance Evaluation
    gov_decision = await governance.evaluate_turn("developer", current_tokens=2500, current_cost=0.02, turn_count=3)
    assert gov_decision.verdict == GovernanceVerdict.CONTINUE

    # 9. Verification Evaluation
    verif_report = await verification.verify_evidence("task_final", test_passed=True, diff_present=True, security_clean=True)
    assert verif_report.passed is True
    assert verif_report.status == VerificationStatus.PASSED

    # 10. Update Final Task State
    tasks.update_task_status("sub-2", TaskStatus.COMPLETED, artifacts=["diff.patch"])
    assert tasks.get_progress() == 1.0

    # 11. Teardown
    for engine in all_engines:
        await engine.stop()
    await core.stop()
