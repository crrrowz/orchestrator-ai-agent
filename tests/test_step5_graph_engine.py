"""Tests for Step 5: Graph Execution Model and Graph Engine."""

import pytest
from orchestrator.engines.agents import AgentEngine
from orchestrator.engines.core import ServiceContainer
from orchestrator.engines.events import EventEngine
from orchestrator.engines.graph import (
    Connection,
    EdgeType,
    GraphDefinition,
    GraphEngine,
    GraphNode,
    NodeExecutionState,
)


@pytest.mark.anyio
async def test_graph_engine_sequential_execution():
    container = ServiceContainer()
    event_engine = EventEngine()
    agent_engine = AgentEngine()
    graph_engine = GraphEngine()

    await event_engine.initialize(container)
    await agent_engine.initialize(container)
    await graph_engine.initialize(container)

    await event_engine.start()
    await agent_engine.start()
    await graph_engine.start()

    # Define a 3-node graph: Developer -> Tester -> Reviewer
    graph_def = GraphDefinition(
        id="dev_test_review_pipeline",
        name="Standard Dev-Test-Review Graph",
        entrypoint_node_id="node_dev",
        nodes={
            "node_dev": GraphNode(id="node_dev", component_name="developer", name="Developer"),
            "node_test": GraphNode(id="node_test", component_name="tester", name="Tester"),
            "node_rev": GraphNode(id="node_rev", component_name="reviewer", name="Reviewer"),
        },
        connections=[
            Connection(id="c1", from_node_id="node_dev", to_node_id="node_test"),
            Connection(id="c2", from_node_id="node_test", to_node_id="node_rev"),
        ],
    )

    graph_engine.load_graph(graph_def)
    result = await graph_engine.run_graph("dev_test_review_pipeline", {"task": "Implement feature Y"})

    assert result["status"] == "completed"
    assert result["total_iterations"] == 3
    assert result["node_states"]["node_dev"] == NodeExecutionState.COMPLETED.value
    assert result["node_states"]["node_test"] == NodeExecutionState.COMPLETED.value
    assert result["node_states"]["node_rev"] == NodeExecutionState.COMPLETED.value
