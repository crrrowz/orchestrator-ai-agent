# Plugin Plan 03: Provider-Agnostic Model System

## 1. Objective
Design the Provider-Agnostic Model Plugin System, allowing seamless addition and configuration of model providers (OpenAI, Anthropic, Google, DeepSeek, Local Ollama/vLLM, OpenRouter) with standardized tool-calling, token counting, and structured outputs.

## 2. Current Architecture Involved
- `orchestrator/llm/manager.py`
- `orchestrator/llm/factory.py`
- `orchestrator/llm/normalize.py`

## 3. Problem
LLM instantiation is coupled to fixed internal provider wrappers. Adding new providers or switching between reasoning models and standard models requires editing core codebase modules.

## 4. Proposed Design
Implement a modular Model Provider Plugin architecture:

### Provider Plugin Manifest (`provider.yaml`)
```yaml
name: "deepseek-provider"
version: "1.0.0"
author: "AI Infra"
description: "DeepSeek V3 and R1 reasoning model provider adapter"
entrypoint: "deepseek_plugin.adapter:DeepSeekModelAdapter"
supported_models:
  - id: "deepseek-chat"
    context_window: 64000
    cost_per_1k_input: 0.00014
    cost_per_1k_output: 0.00028
    supports_tools: true
  - id: "deepseek-reasoner"
    context_window: 64000
    cost_per_1k_input: 0.00055
    cost_per_1k_output: 0.00219
    supports_tools: false
```

### Standardized Adapter Interface
```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from orchestrator.engines.models.adapter import IModelAdapter, ModelRequest, ModelResponse

class BaseProviderPlugin(IModelAdapter, ABC):
    provider_id: str
    
    @abstractmethod
    async def complete(self, request: ModelRequest) -> ModelResponse: ...
    
    @abstractmethod
    async def stream(self, request: ModelRequest) -> AsyncIterator[str]: ...
```

## 5. Files/Components Affected
- `orchestrator/engines/models/plugins/`
- `orchestrator/plugins/models/`

## 6. Interfaces/Contracts
```python
from typing import Dict, List
from pydantic import BaseModel

class ModelCapability(BaseModel):
    model_id: str
    context_window: int
    supports_tools: bool
    supports_streaming: bool
    supports_vision: bool
    supports_reasoning: bool
```

## 7. Data Flow
Model Engine loads Provider Plugins -> Registers supported models in catalog -> Agent specifies model ID -> Provider adapter executes API call -> Normalizes response into universal `ModelResponse`.

## 8. State Transitions
`REGISTERED -> AUTHENTICATING -> READY -> COMPLETING -> STREAMING -> SHUTDOWN`.

## 9. Error Handling
Unified mapping of provider-specific errors (e.g. OpenAI `RateLimitError`, Anthropic `OverloadedError`, Google `ResourceExhausted`) into standard `ORAGAIModelError` exceptions.

## 10. Migration Strategy
Port existing OpenAI, Anthropic, and Google factories in `orchestrator/llm/` to standard built-in provider plugins.

## 11. Tests
- Cross-provider response normalization parity tests.
- Function calling schema translation tests.
- Streaming token generator tests.

## 12. Acceptance Criteria
- Complete isolation of third-party SDK dependencies.
- Ability to add new LLM providers via standalone plugin packages.

## 13. Dependencies
Depends on Model Engine, Core Engine.

## 14. Risks
Differences in function calling formats across providers; mitigated by unified JSON Schema normalization layer.

## 15. Rollback Strategy
Fallback to `orchestrator/llm/manager.py`.
