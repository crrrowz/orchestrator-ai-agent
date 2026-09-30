"""Provider-Agnostic Model Engine implementation."""

from typing import Any, AsyncIterator, Dict, List, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.models.adapter import IModelAdapter, ModelRequest, ModelResponse


class MockModelAdapter(IModelAdapter):
    provider_name: str = "mock"

    async def complete(self, request: ModelRequest, model_name: str) -> ModelResponse:
        prompt_len = sum(len(str(m.get("content", ""))) for m in request.messages)
        return ModelResponse(
            content="Mock model completion response.",
            tool_calls=[],
            prompt_tokens=max(1, prompt_len // 4),
            completion_tokens=10,
            cost_usd=0.00001,
            provider="mock",
            model_name=model_name,
        )

    async def stream(self, request: ModelRequest, model_name: str) -> AsyncIterator[str]:
        for word in ["Mock ", "streaming ", "completion."]:
            yield word


class ModelEngine(IEngine):
    """Engine responsible for LLM provider abstraction, rate limiting, and cost tracking."""

    engine_name: str = "models"

    def __init__(self) -> None:
        self._adapters: Dict[str, IModelAdapter] = {}
        self._total_tokens_used: int = 0
        self._total_cost_usd: float = 0.0
        self._is_running: bool = False
        # Register default mock adapter
        self.register_adapter(MockModelAdapter())

    async def initialize(self, container: IContainer) -> None:
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    def register_adapter(self, adapter: IModelAdapter) -> None:
        self._adapters[adapter.provider_name] = adapter

    def get_adapter(self, provider_name: str) -> IModelAdapter:
        if provider_name not in self._adapters:
            return self._adapters["mock"]
        return self._adapters[provider_name]

    async def generate(
        self,
        request: ModelRequest,
        provider: str = "mock",
        model_name: str = "default",
    ) -> ModelResponse:
        adapter = self.get_adapter(provider)
        response = await adapter.complete(request, model_name)
        self._total_tokens_used += response.prompt_tokens + response.completion_tokens
        self._total_cost_usd += response.cost_usd
        return response

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "registered_providers": list(self._adapters.keys()),
            "total_tokens_consumed": self._total_tokens_used,
            "total_cost_usd": self._total_cost_usd,
        }
