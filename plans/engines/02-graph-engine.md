# Engine Plan 02: Graph Engine

## 1. Objective
Specify the Graph Engine responsible for parsing, compiling, optimizing, executing, and monitoring visual and declarative workflow graphs.

## 2. Current Architecture Involved
- `orchestrator/pipeline/fsm/engine.py`
- `orchestrator/pipeline/dispatcher.py`
- `orchestrator/pipeline/checkpoint.py`

## 3. Problem
Static state machines in `fsm/engine.py` cannot dynamically insert nodes, handle parallel branches, evaluate runtime edge predicates, or serialize execution graphs for frontend visual editors.

## 4. Proposed Design
Implement `GraphEngine`:
- **Graph Compiler**: Converts JSON/YAML graph specifications into an optimized executable topological execution structure.
- **Scheduler & Worker Pool**: Dispatches independent nodes concurrently via `asyncio`.
- **Edge Predicate Evaluator**: Safely evaluates boolean expressions and output matching on conditional edges.
- **Loop & Oscillation Controller**: Tracks iteration depth and convergence metrics on cyclic edges.
- **State Checkpointer**: Takes periodic snapshots of graph state and node outputs to SQLite or disk for crash recovery.

## 5. Files/Components Affected
- `orchestrator/engines/graph/engine.py`
- `orchestrator/engines/graph/compiler.py`
- `orchestrator/engines/graph/scheduler.py`
- `orchestrator/engines/graph/predicates.py`
- `orchestrator/engines/graph/checkpoint.py`
- `orchestrator/engines/graph/models.py`

## 6. Interfaces/Contracts
```python
from typing import Any, Dict, List, Optional
from orchestrator.engines.core.engine import IEngine
from orchestrator.engines.graph.models import GraphDefinition, NodeExecutionState

class IGraphEngine(IEngine):
    async def compile_and_load(self, graph_def: GraphDefinition) -> str: ...
    async def execute_graph(self, graph_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]: ...
    async def get_node_status(self, graph_id: str, node_id: str) -> NodeExecutionState: ...
    async def inject_human_response(self, graph_id: str, node_id: str, response: Dict[str, Any]) -> None: ...
```

## 7. Data Flow
Graph definition received -> Compiler validates acyclic/cyclic properties -> Nodes queued in Scheduler -> Node execution delegated to Execution Engine -> Node output stored in Graph State -> Dependent edges evaluated -> Downstream nodes queued -> Completion event published.

## 8. State Transitions
`GRAPH_LOADED -> GRAPH_VALIDATED -> EXECUTING -> NODE_RUNNING -> NODE_EVALUATED -> GRAPH_COMPLETED / GRAPH_PAUSED / GRAPH_FAILED`.

## 9. Error Handling
Nodes failing without recovery edges trigger the Graph Error Handler, recording the call stack into `sentinel_mesh.db` and publishing a `GRAPH_EXECUTION_FAILED` event.

## 10. Migration Strategy
Legacy FSM profiles (`FullPipelineProfile`, `DevTestProfile`) are mapped into static `GraphDefinition` templates.

## 11. Tests
- Parallel diamond graph execution tests (`A -> (B, C) -> D`).
- Cyclic retry loop tests with edge counter limits.
- Human approval pause/resume state tests.

## 12. Acceptance Criteria
- Full support for DAG and cyclic execution topologies.
- Sub-millisecond edge evaluation latency.
- Deterministic checkpoint recovery.

## 13. Dependencies
Depends on Core Engine, Component Model, and Event Engine. Blocks Agent Engine execution workflows.

## 14. Risks
Memory leaks from accumulating node output buffers in large graphs; mitigated by configurable port buffer eviction policies.

## 15. Rollback Strategy
Fallback to `orchestrator.pipeline.fsm.engine.FSMRuntimeEngine`.
