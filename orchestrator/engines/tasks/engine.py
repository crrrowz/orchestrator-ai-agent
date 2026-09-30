"""Autonomous Task Engine for decomposition, DAG scheduling, and replanning."""

from typing import Any, Dict, List, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.tasks.models import SubTask, TaskStatus


class TaskEngine(IEngine):
    """Engine responsible for hierarchical task decomposition and milestone dependency management."""

    engine_name: str = "tasks"

    def __init__(self) -> None:
        self._tasks: Dict[str, SubTask] = {}
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    def add_subtask(self, subtask: SubTask) -> None:
        self._tasks[subtask.id] = subtask

    def get_subtask(self, task_id: str) -> Optional[SubTask]:
        return self._tasks.get(task_id)

    def list_subtasks(self) -> List[SubTask]:
        return list(self._tasks.values())

    def get_ready_tasks(self) -> List[SubTask]:
        """Return all tasks whose dependencies have been completed."""
        completed_ids = {t.id for t in self._tasks.values() if t.status == TaskStatus.COMPLETED}
        ready: List[SubTask] = []
        for task in self._tasks.values():
            if task.status == TaskStatus.PENDING:
                if all(dep in completed_ids for dep in task.dependencies):
                    task.status = TaskStatus.READY
                    ready.append(task)
            elif task.status == TaskStatus.READY:
                ready.append(task)
        return ready

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        artifacts: Optional[List[str]] = None,
    ) -> Optional[SubTask]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = status
        if artifacts:
            task.output_artifacts.extend(artifacts)
        return task

    def get_progress(self) -> float:
        if not self._tasks:
            return 1.0
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        return completed / len(self._tasks)

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "total_tasks": len(self._tasks),
            "progress": self.get_progress(),
        }
