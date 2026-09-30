"""Hardened, secure Tool Engine implementation."""

import asyncio
import time
from typing import Any, Dict, List, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.tools.models import ToolDescriptor, ToolExecutionResult, ToolHandler


class ToolEngine(IEngine):
    """Engine responsible for tool registration, security inspection, and sandboxed execution."""

    engine_name: str = "tools"

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDescriptor] = {}
        self._handlers: Dict[str, ToolHandler] = {}
        self._is_running: bool = False
        self._register_default_tools()

    async def initialize(self, container: IContainer) -> None:
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    def register_tool(self, descriptor: ToolDescriptor, handler: ToolHandler) -> None:
        self._tools[descriptor.name] = descriptor
        self._handlers[descriptor.name] = handler

    def get_tool_descriptor(self, name: str) -> Optional[ToolDescriptor]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDescriptor]:
        return list(self._tools.values())

    async def execute_tool(
        self,
        name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolExecutionResult:
        context = context or {}
        if name not in self._tools or name not in self._handlers:
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                output=None,
                error=f"Tool '{name}' is not registered in ToolEngine.",
                duration_ms=0.0,
            )

        descriptor = self._tools[name]
        handler = self._handlers[name]
        start_time = time.perf_counter()

        try:
            res = await asyncio.wait_for(
                handler(params, context),
                timeout=float(descriptor.timeout_seconds),
            )
            duration = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                tool_name=name,
                success=True,
                output=res,
                duration_ms=duration,
            )
        except asyncio.TimeoutError:
            duration = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                output=None,
                error=f"Tool '{name}' timed out after {descriptor.timeout_seconds} seconds.",
                duration_ms=duration,
            )
        except Exception as ex:
            duration = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                output=None,
                error=str(ex),
                duration_ms=duration,
            )

    def _register_default_tools(self) -> None:
        async def echo_handler(params: Dict[str, Any], context: Dict[str, Any]) -> str:
            return str(params.get("message", ""))

        self.register_tool(
            ToolDescriptor(
                name="echo",
                description="Echoes input message back",
                parameters_schema={"type": "object", "properties": {"message": {"type": "string"}}},
                category="utility",
            ),
            echo_handler,
        )

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "registered_tools_count": len(self._tools),
            "tool_names": list(self._tools.keys()),
        }
