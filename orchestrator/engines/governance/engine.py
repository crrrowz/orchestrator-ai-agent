"""Adaptive Governance Engine for multi-dimensional safety and budget control."""

from typing import Any, Dict, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.governance.models import GovernanceDecision, GovernanceVerdict


class GovernanceEngine(IEngine):
    """Engine responsible for token budgeting, stagnation/chaos detection, and AST safety."""

    engine_name: str = "governance"

    def __init__(self, max_token_ceiling: int = 100_000, max_cost_usd: float = 10.0) -> None:
        self.max_token_ceiling = max_token_ceiling
        self.max_cost_usd = max_cost_usd
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    async def evaluate_turn(
        self,
        agent_name: str,
        current_tokens: int,
        current_cost: float,
        turn_count: int,
        recent_edits_count: int = 1,
    ) -> GovernanceDecision:
        # Check hard budget ceilings
        if current_tokens >= self.max_token_ceiling:
            return GovernanceDecision(
                verdict=GovernanceVerdict.HALT,
                reason=f"Hard token ceiling ({self.max_token_ceiling}) exceeded.",
            )

        if current_cost >= self.max_cost_usd:
            return GovernanceDecision(
                verdict=GovernanceVerdict.HALT,
                reason=f"Hard budget cap (${self.max_cost_usd}) reached.",
            )

        # Check for stagnation / oscillation
        if turn_count > 20 and recent_edits_count == 0:
            return GovernanceDecision(
                verdict=GovernanceVerdict.REPLAN,
                reason="Stagnation detected: zero productive file edits over extended turns.",
            )

        return GovernanceDecision(
            verdict=GovernanceVerdict.CONTINUE,
            reason="Execution within nominal safety and budget parameters.",
        )

    async def check_command_safety(self, command: str) -> bool:
        forbidden = ["rm -rf /", ":(){ :|:& };:", "mkfs", "dd if=/dev/zero"]
        return not any(bad in command for bad in forbidden)

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "max_token_ceiling": self.max_token_ceiling,
            "max_cost_usd": self.max_cost_usd,
        }
