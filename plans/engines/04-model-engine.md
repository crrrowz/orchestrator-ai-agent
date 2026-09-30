# Engine Plan 04: Model Engine

## 1. Objective
Design a provider-independent, pluggable Model Engine that abstracts LLM interactions across OpenAI, Anthropic, Google Gemini, local models (Ollama, vLLM), and OpenRouter.

## 2. Current Architecture Involved
- `orchestrator/llm/manager.py`
- `orchestrator/llm/factory.py`
- `orchestrator/llm/normalize.py`
- `orchestrator/llm/pricing.py`

## 3. Problem
LLM management is coupled to specific SDK wrappers and config models (`orchestrator.core.config.AgentRoleConfig`), making dynamic switching of model providers at runtime or embedding custom local inference backends rigid and brittle.

## 4. Proposed Design
Implement `ModelEngine`:
- **Provider Abstraction Layer**: Unified protocol for synchronous, streaming, and tool-calling LLM invocations.
- **Dynamic Provider Adapters**: Pluggable adapters for OpenAI, Anthropic, Google, OpenRouter, and Local OpenAI-compatible endpoints.
- **Token Estimation & Cost Telemetry**: Live token counting, cost calculation, and budget alert hooks.
- **Resilience & Rate-Limiting**: Token-bucket rate limiting, exponential backoff on HTTP 429/503, and automatic fallback provider cascades.

## 5. Files/Components Affected
- `orchestrator/engines/models/engine.py`
- `orchestrator/engines/models/adapter.py`
- `orchestrator/engines/models/providers/` (`openai.py`, `anthropic.py`, `google.py`, `local.py`, `openrouter.py`)
- `orchestrator/engines/models/cost.py`
- `orchestrator/engines/models/rate_limiter.py`

## 6. Interfaces/Contracts
```python
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class ModelRequest(BaseModel):
    messages: List[Dict[str, Any]]
    tools: Optional[List[Dict[str, Any]]] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    structured_output_schema: Optional[Dict[str, Any]] = None

class ModelResponse(BaseModel):
    content: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    provider: str
    model_name: str

class IModelAdapter(ABC):
    @abstractmethod
    async def complete(self, request: ModelRequest) -> ModelResponse: ...

    @abstractmethod
    async def stream(self, request: ModelRequest) -> AsyncIterator[str]: ...

class IModelEngine(IEngine):
    def register_provider(self, name: str, adapter: IModelAdapter) -> None: ...
    async def generate(self, model_id: str, request: ModelRequest) -> ModelResponse: ...
```

## 7. Data Flow
Agent/Execution Engine calls `ModelEngine.generate()` -> Rate limiter verifies token quota -> Selected Provider Adapter invokes API -> Response normalized into `ModelResponse` -> Token and cost metrics published to Event Engine -> Response returned to Agent.

## 8. State Transitions
`PROVIDER_REGISTERED -> READY -> IN_FLIGHT -> RATE_LIMITED (Wait) -> COMPLETED / FAILED_RETRY / FALLBACK_DISPATCHED`.

## 9. Error Handling
- Rate limit errors (429) trigger automatic backoff and retry.
- Persistent provider outages trigger configured fallback provider (e.g. Anthropic Claude -> Google Gemini).

## 10. Migration Strategy
`LLMManager.get_llm()` will delegate internally to `ModelEngine.get_adapter()` or wrap `ModelEngine` instances.

## 11. Tests
- Multi-provider mock completion tests.
- Streaming chunk parser tests.
- Automatic rate limit backoff and fallback cascade tests.
- Precise cost calculation tests against the pricing catalog.

## 12. Acceptance Criteria
- Complete decoupling from OpenHands SDK LLM internals.
- Clean support for OpenAI, Anthropic, Google, and Local endpoints.
- Zero-downtime provider fallback routing.

## 13. Dependencies
Depends on Core Engine, Event Engine. Blocks Agent Engine and Execution Engine.

## 14. Risks
Provider API divergence on structured outputs and tool calling; mitigated by standardized JSON Schema tool normalization.

## 15. Rollback Strategy
Fallback to `orchestrator/llm/manager.py` implementations.
