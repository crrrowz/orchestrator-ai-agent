# Engine Plan 08: Task Engine

## 1. Objective
Design an autonomous Task Engine capable of hierarchical task decomposition, Milestone DAG dependency tracking, priority queue dispatching, progress monitoring, and dynamic replanning.

## 2. Current Architecture Involved
- `orchestrator/pipeline/task_queue.py`
- `orchestrator/pipeline/milestone_dag.py`
- `orchestrator/workstreams/milestone_dag/` (`resolver.py`, `dispatcher.py`)

## 3. Problem
Task management is split across linear queues (`task_queue.py`) and custom milestone dispatchers. It lacks dynamic runtime decomposition, real-time progress percentage calculation, and automated replanning triggers when dependencies fail.

## 4. Proposed Design
Implement `TaskEngine`:
- **Task Decomposition**: Breaks complex engineering objectives into an actionable, dependency-ordered Milestone DAG.
- **Dependency Resolver**: Computes ready tasks via topological sort and detects blocked dependencies.
- **Dynamic Replanner**: Automatically reorganizes downstream subtasks or injects diagnostic tasks when an execution branch fails.
- **Progress & Milestone Tracker**: Maintains live progress metrics, completion percentages, and milestone achievement verification.

## 5. Files/Components Affected
- `orchestrator/engines/tasks/engine.py`
- `orchestrator/engines/tasks/models.py`
- `orchestrator/engines/tasks/decomposer.py`
- `orchestrator/engines/tasks/dag.py`
- `orchestrator/engines/tasks/replanner.py`

## 6. Interfaces/Contracts
```python
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"

class SubTask(BaseModel):
    id: str
    title: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    assigned_role: Optional[str] = None
    output_artifacts: List[str] = Field(default_factory=list)

class ITaskEngine(IEngine):
    async def decompose_goal(self, goal: str, context: Dict[str, Any]) -> List[SubTask]: ...
    def get_ready_tasks(self) -> List[SubTask]: ...
    def update_task_status(self, task_id: str, status: TaskStatus, artifacts: Optional[List[str]] = None) -> None: ...
    async def replan_on_failure(self, failed_task_id: str, failure_reason: str) -> List[SubTask]: ...
    def get_progress(self) -> float: ...
```

## 7. Data Flow
User submits goal -> Task Engine decomposes into Milestone DAG -> Ready subtasks queued -> Dispatched to Graph/Execution Engine -> Results update status -> If task fails, Replanner recalculates DAG -> Remaining tasks execute until completion.

## 8. State Transitions
SubTask states: `PENDING -> READY -> IN_PROGRESS -> COMPLETED / FAILED / BLOCKED`.

## 9. Error Handling
Cyclic dependencies in subtasks are detected and rejected at decomposition time. Failed subtasks trigger replanning up to a configured threshold before aborting.

## 10. Migration Strategy
Replace `SequentialTaskQueue` and `MilestoneDAG` with `TaskEngine` models, retaining compatibility methods for legacy callers.

## 11. Tests
- Decomposition generation tests.
- Topological execution order tests with multi-level dependencies.
- Dynamic replanning tests validating replacement of failed subtasks.

## 12. Acceptance Criteria
- Full support for DAG-based subtask scheduling.
- Real-time progress metric calculation.
- Automated replanning integration.

## 13. Dependencies
Depends on Core Engine, Event Engine. Blocks Graph Engine.

## 14. Risks
Over-decomposition leading to excessive small tasks and token waste; mitigated by max-depth constraints and batching heuristics.

## 15. Rollback Strategy
Fallback to `orchestrator/pipeline/task_queue.py`.
