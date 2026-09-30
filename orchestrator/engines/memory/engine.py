"""Multi-tiered Memory Engine supporting 5 distinct scopes and handoff synthesis."""

from typing import Any, Dict, List, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.memory.models import MemoryItem, MemoryScope


class MemoryEngine(IEngine):
    """Engine providing 5-tier memory storage, context retrieval, and cross-agent handoffs."""

    engine_name: str = "memory"

    def __init__(self) -> None:
        self._stores: Dict[MemoryScope, Dict[str, MemoryItem]] = {
            scope: {} for scope in MemoryScope
        }
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    async def store(
        self,
        scope: MemoryScope,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        item = MemoryItem(
            scope=scope,
            key=key,
            value=value,
            metadata=metadata or {},
        )
        self._stores[scope][key] = item
        return item

    async def get(self, scope: MemoryScope, key: str) -> Optional[MemoryItem]:
        return self._stores[scope].get(key)

    async def list_scope(self, scope: MemoryScope) -> List[MemoryItem]:
        return list(self._stores[scope].values())

    async def create_handoff(
        self,
        from_agent: str,
        to_agent: str,
        summary: str,
        artifacts: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        key = f"handoff_{from_agent}_to_{to_agent}"
        value = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "summary": summary,
            "artifacts": artifacts or {},
        }
        return await self.store(MemoryScope.TASK, key, value)

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "items_per_scope": {
                scope.value: len(items) for scope, items in self._stores.items()
            },
        }
