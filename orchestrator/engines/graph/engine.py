"""Graph Engine for compiling, executing, and monitoring DAG/Cyclic workflows."""

from typing import Any, Dict, List, Optional
from orchestrator.engines.agents.engine import AgentEngine
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.events.engine import EventEngine
from orchestrator.engines.graph.models import Connection, GraphDefinition, NodeExecutionState


class GraphEngine(IEngine):
    """Engine responsible for declarative graph compilation and execution."""

    engine_name: str = "graph"

    def __init__(self) -> None:
        self._graphs: Dict[str, GraphDefinition] = {}
        self._container: Optional[IContainer] = None
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        self._container = container
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    def load_graph(self, graph_def: GraphDefinition) -> None:
        self._graphs[graph_def.id] = graph_def

    async def run_graph(
        self,
        graph_id: str,
        initial_inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a graph from its entrypoint following connections."""
        graph = self._graphs.get(graph_id)
        if not graph:
            raise KeyError(f"Graph '{graph_id}' not loaded in GraphEngine.")

        node_states: Dict[str, NodeExecutionState] = {
            nid: NodeExecutionState.PENDING for nid in graph.nodes
        }
        node_outputs: Dict[str, Any] = {}

        current_node_id = graph.entrypoint_node_id
        iterations = 0
        agent_engine: Optional[AgentEngine] = (
            self._container.get_engine(AgentEngine) if self._container else None
        )
        event_engine: Optional[EventEngine] = (
            self._container.get_engine(EventEngine) if self._container else None
        )

        while current_node_id and iterations < graph.max_loop_iterations:
            iterations += 1
            node = graph.nodes[current_node_id]
            node_states[current_node_id] = NodeExecutionState.RUNNING

            if event_engine:
                await event_engine.publish(
                    "graph.node.started",
                    {"graph_id": graph_id, "node_id": current_node_id, "node_name": node.name},
                    source="graph",
                )

            # Execute component via AgentEngine or direct computation
            if agent_engine:
                agent_comp = agent_engine.create_agent_component(node.component_name)
                if agent_comp:
                    agent_comp.initialize(node.config)
                    out = await agent_comp.execute(initial_inputs)
                    node_outputs[current_node_id] = out
                else:
                    node_outputs[current_node_id] = {"output": f"Executed {node.name}"}
            else:
                node_outputs[current_node_id] = {"output": f"Executed {node.name}"}

            node_states[current_node_id] = NodeExecutionState.COMPLETED

            if event_engine:
                await event_engine.publish(
                    "graph.node.completed",
                    {"graph_id": graph_id, "node_id": current_node_id, "output": node_outputs[current_node_id]},
                    source="graph",
                )

            # Determine next node from outgoing connections
            outgoing = [c for c in graph.connections if c.from_node_id == current_node_id]
            if outgoing:
                current_node_id = outgoing[0].to_node_id
            else:
                current_node_id = None  # Graph termination

        return {
            "graph_id": graph_id,
            "status": "completed",
            "total_iterations": iterations,
            "node_states": {k: v.value for k, v in node_states.items()},
            "node_outputs": node_outputs,
        }

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "loaded_graphs_count": len(self._graphs),
        }
