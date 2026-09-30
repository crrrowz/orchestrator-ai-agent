"""Core Engine implementation for bootstrapping and lifecycle orchestration."""

import asyncio
from typing import Any, Dict, Optional
from orchestrator.core.config import OrchestratorConfig
from orchestrator.engines.core.container import IContainer, IEngine, ServiceContainer


class CoreEngine(IEngine):
    """Central Core Engine for ORAGAI runtime."""

    engine_name: str = "core"

    def __init__(self, config: Optional[OrchestratorConfig] = None) -> None:
        self.config = config or OrchestratorConfig()
        self.container: IContainer = ServiceContainer()
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        self.container = container
        self.container.register_engine(self)

    async def bootstrap(self) -> IContainer:
        """Bootstrap the runtime container and register core services."""
        await self.initialize(self.container)
        return self.container

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "engine": self.engine_name,
            "workspace": str(self.config.workspace_path),
        }
