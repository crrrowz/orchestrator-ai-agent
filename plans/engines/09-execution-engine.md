# Engine Plan 09: Execution Engine

## 1. Objective
Design a unified, pluggable Execution Engine responsible for managing agent-environment execution loops, turn orchestration, action dispatching, tool result routing, and runtime abstraction.

## 2. Current Architecture Involved
- `orchestrator/engine/openhands_bridge.py`
- `orchestrator/pipeline/dev_test_loop.py`
- `orchestrator/pipeline/iteration_state.py`

## 3. Problem
Execution loop logic is hardcoded inside individual pipeline classes (`dev_test_loop.py`, `full_pipeline.py`) and coupled to the OpenHands runtime SDK. Switching runtimes, running multiple agents in parallel isolated containers, or intercepting execution turns requires modifying core loop logic.

## 4. Proposed Design
Implement `ExecutionEngine`:
- **Pluggable Execution Runtimes**: Supports Native Async Python Runtime, OpenHands SDK Bridge, and Isolated Docker Container Runtimes.
- **Turn-by-Turn Orchestration**: Standardized step loop: `Prompt Assembly -> Model Inference -> Tool Call Extraction -> Tool Execution -> Result Injection -> Event Emission`.
- **Iteration & State Tracker**: Real-time tracking of turns, cost, duration, and artifact generation.
- **Execution Interceptors**: Pluggable before/after turn hooks for governance checks, AST validation, and telemetry recording.

## 5. Files/Components Affected
- `orchestrator/engines/execution/engine.py`
- `orchestrator/engines/execution/runtimes/` (`native.py`, `openhands.py`, `docker.py`)
- `orchestrator/engines/execution/loop.py`
- `orchestrator/engines/execution/state.py`
- `orchestrator/engines/execution/interceptors.py`

## 6. Interfaces/Contracts
```python
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class ExecutionTurnResult(BaseModel):
    turn_index: int
    agent_name: str
    action_taken: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int
    cost_usd: float
    is_terminal: bool = False
    error: Optional[str] = None
    fingerprint_hash: Optional[str] = None  # SHA-256 hash of turn output to detect loop stagnation

class WorkerLease(BaseModel):
    lease_id: str
    worker_id: str
    node_id: str
    lease_ttl_seconds: float = 60.0
    last_heartbeat: float

class IExecutionRuntime(ABC):
    @abstractmethod
    async def run_turn(self, agent: Any, instruction: str, context: Dict[str, Any]) -> ExecutionTurnResult: ...

    @abstractmethod
    async def heartbeat(self, lease_id: str) -> bool: ...

class IExecutionEngine(IEngine):
    async def execute_agent_loop(self, agent: Any, task: str, max_turns: int = 30) -> Dict[str, Any]: ...
    def register_interceptor(self, interceptor: Any) -> None: ...
    async def reclaim_zombie_workers(self) -> List[str]: ...
```

## 7. Data Flow
Graph Engine schedules Agent Node -> Execution Engine initializes turn loop -> Injects prompt -> Runtime calls Model Engine -> Extracts tool calls -> Tool Engine executes tools -> Interceptors evaluate output -> Result fed back into agent context -> Emits `TURN_COMPLETED` event -> Repeats until terminal condition or max turns.

## 8. State Transitions
`IDLE -> INITIALIZING_LOOP -> TURN_START -> INFERENCE -> TOOL_EXECUTION -> TURN_EVALUATED -> LOOP_COMPLETED / HALTED_BY_GOVERNOR / MAX_TURNS_EXCEEDED`.

## 9. Error Handling
Runtime crashes or unhandled tool exceptions are captured per turn, updating the execution state without crashing the host process, allowing the Graph Engine to route to failure recovery nodes.

## 10. Migration Strategy
Wrap existing `OpenHandsExecutionBridge` as the default `openhands.py` runtime provider under `ExecutionEngine`.

## 11. Tests
- Mock runtime step loop tests.
- Execution interceptor veto/continuation tests.
- Parallel multi-agent execution concurrency tests.

## 12. Acceptance Criteria
- Complete abstraction over underlying agent execution SDKs.
- Zero coupling between pipeline flow and runtime execution loops.

## 13. Dependencies
Depends on Core Engine, Agent Engine, Tool Engine, Model Engine, Event Engine. Blocks Graph Engine.

## 14. Risks
Overhead of interceptor pipeline; mitigated by async non-blocking event dispatches.

## 15. Rollback Strategy
Fallback to `orchestrator/engine/openhands_bridge.py`.
