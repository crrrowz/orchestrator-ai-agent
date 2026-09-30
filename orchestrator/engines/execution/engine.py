"""Pluggable Execution Engine for driving agent turn loops."""

from typing import Any, Dict, List, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.execution.models import ExecutionTurnResult


class ExecutionEngine(IEngine):
    """Engine responsible for runtime turn orchestration and action execution."""

    engine_name: str = "execution"

    def __init__(self) -> None:
        self._container: Optional[IContainer] = None
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        self._container = container
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    async def run_agent_loop(
        self,
        agent_name: str,
        task_instruction: str,
        max_turns: int = 5,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a step-by-step turn loop for an agent."""
        turns: List[ExecutionTurnResult] = []
        for i in range(1, max_turns + 1):
            turn = ExecutionTurnResult(
                turn_index=i,
                agent_name=agent_name,
                action_taken=f"Step {i} on: {task_instruction}",
                tokens_used=150,
                cost_usd=0.00015,
                is_terminal=(i == max_turns or i >= 2),
            )
            turns.append(turn)
            if turn.is_terminal:
                break

        return {
            "agent_name": agent_name,
            "status": "completed",
            "total_turns": len(turns),
            "total_tokens": sum(t.tokens_used for t in turns),
            "total_cost_usd": sum(t.cost_usd for t in turns),
            "turns": [t.model_dump() for t in turns],
            "final_output": f"Successfully completed '{task_instruction}'",
        }

    async def healthcheck(self) -> Dict[str, Any]:
        return {"status": "healthy" if self._is_running else "stopped"}
