# Plan 04: Graph Execution Model

## 1. Objective
Design a visual-ready, resilient Graph Execution Model for ORAGAI. Support directed acyclic graphs (DAGs), cyclic feedback loops (e.g. Developer <-> Tester <-> Reviewer), conditional branching, parallel fan-out/fan-in, human approval gates, error routing, and checkpointed state resumption.

## 2. Current Architecture Involved
- `orchestrator/pipeline/fsm/engine.py` (FSM Runtime)
- `orchestrator/pipeline/state_machine.py`
- `orchestrator/pipeline/checkpoint.py`
- `orchestrator/pipeline/dispatcher.py`

## 3. Problem
Existing execution logic is hardcoded into sequential Python loops (`dev_test_loop.py`, `full_pipeline.py`) or rigid FSM state tables. Introducing dynamic branching, dynamic sub-graphs, or visual drag-and-drop connections is blocked by static orchestration classes.

## 4. Proposed Design

### Graph Specification & Schema

```python
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class NodeExecutionState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"

class EdgeType(str, Enum):
    DATA = "data"           # Transfers port data
    CONTROL = "control"     # Dictates execution sequence
    CONDITIONAL = "conditional" # Executes when condition evaluates to True
    ERROR = "error"         # Executes on node failure

class Connection(BaseModel):
    id: str
    from_node_id: str
    from_port: str
    to_node_id: str
    to_port: str
    edge_type: EdgeType = EdgeType.DATA
    condition_expr: Optional[str] = None  # e.g., "outputs['tests_passed'] == False"

class GraphNode(BaseModel):
    id: str
    component_id: str       # References registered Component ID
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 3, "backoff": 2.0})
    requires_approval: bool = False

class GraphDefinition(BaseModel):
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    entrypoint_node_id: str
    nodes: Dict[str, GraphNode]
    connections: List[Connection]
    max_loop_iterations: int = 25
```

### Graph Execution Dynamics

```text
┌───────────────┐        ┌──────────────┐        ┌──────────────┐
│  Architect    ├───────►│  Developer   ├───────►│    Tester    │
└───────────────┘        └──────▲───────┘        └──────┬───────┘
                                │                       │
                                │   tests_failed == True│
                                └───────────────────────┤ tests_passed == True
                                                        ▼
┌───────────────┐        ┌──────────────┐        ┌──────────────┐
│ Verification  │◄───────┤   Reviewer   │◄───────┤    Audit     │
└───────────────┘        └──────────────┘        └──────────────┘
```

### Advanced Routing & Resilience Features
1. **Conditional Branching**: Evaluates edge conditions against node outputs or global context variables using a sandboxed AST expression evaluator (e.g. `ast.literal_eval` with whitelisted operator tables).
2. **Cyclic Loops & Convergence**: Tracks cycle counts and state delta fingerprints per node pair; enforces `max_loop_iterations` and diff entropy checks to prevent semantic oscillations.
3. **Parallel Execution & Worktree Isolation**: Nodes with satisfied dependencies execute concurrently via `asyncio.gather`. Concurrent file-mutating nodes acquire isolated file/worktree locks managed by `WorkspaceLockManager` to prevent race conditions.
4. **Human Approval Gates**: If `requires_approval` is True, graph execution pauses, persists a deterministic snapshot (with SHA-256 integrity hash), emits a `HUMAN_APPROVAL_REQUESTED` event, and resumes on user response.
5. **Dynamic Failure Routing & Circuit Breaking**: On node error, if an `ERROR` edge exists, execution routes to a remediation node (e.g. self-healing or diagnostic agent); otherwise trips the graph circuit breaker and writes unhandled state to `sentinel_mesh.db`.
6. **Write-Ahead Log (WAL) Checkpointing**: Every node state mutation is recorded in a WAL journal before dispatch. On crash or power failure, `GraphEngine.recover_from_wal()` re-hydrates uncommitted node states and safely replays or resumes the execution pipeline.

## 5. Files/Components Affected
- `orchestrator/engines/graph/models.py`
- `orchestrator/engines/graph/compiler.py`
- `orchestrator/engines/graph/engine.py`
- `orchestrator/engines/graph/evaluator.py`
- `orchestrator/engines/graph/checkpoint.py`

## 6. Interfaces/Contracts
```python
from abc import ABC, abstractmethod

class IGraphEngine(ABC):
    @abstractmethod
    def load_graph(self, definition: GraphDefinition) -> None: ...

    @abstractmethod
    async def run(self, initial_inputs: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    async def step(self) -> NodeExecutionState: ...

    @abstractmethod
    def pause(self) -> str: ...  # Returns checkpoint ID

    @abstractmethod
    async def resume(self, checkpoint_id: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
```

## 7. Data Flow
Graph definition parsed -> Dependency tree validated -> Entrypoint node executed -> Component outputs collected -> Conditional edges evaluated -> Downstream input ports populated -> Next nodes scheduled -> Final graph outputs aggregated.

## 8. State Transitions
Node states: `PENDING -> RUNNING -> WAITING_APPROVAL -> COMPLETED / FAILED / SKIPPED`.
Graph states: `READY -> RUNNING -> PAUSED -> COMPLETED / FAILED`.

## 9. Error Handling
- Graph validation catches cycles without termination conditions, missing port connections, and disconnected subgraphs.
- Runtime node errors trigger retry policies or `ERROR` edge rerouting before escalating to graph abortion.

## 10. Migration Strategy
Transform existing standard pipelines (`dev-test`, `full`, `audit`, `docs`) into default declarative JSON graph templates (`orchestrator/engines/graph/workflows/*.json`).

## 11. Tests
- Cyclic convergence tests.
- Parallel fork-join tests.
- Human-in-the-loop pause/resume checkpoint tests.
- Conditional edge expression evaluation security tests.

## 12. Acceptance Criteria
- Complete declarative graph schema supporting DAG and cyclic topologies.
- Native support for parallel execution, conditional branching, and human-in-the-loop gates.
- 100% test coverage for graph state persistence and recovery.

## 13. Dependencies
Depends on Plan 03 (Component Model). Blocks Plan 07 (Engine Specs) and UI plans.

## 14. Risks
Deadlocks in complex cyclic graphs; mitigated by deterministic cycle detection algorithms and graph-level global execution timeouts.

## 15. Rollback Strategy
Fallback to synchronous FSM runner if graph execution encounters unhandled topological errors.
