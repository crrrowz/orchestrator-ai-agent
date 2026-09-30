"""Model engine data models and adapter contracts."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelRequest(BaseModel):
    messages: List[Dict[str, Any]]
    tools: Optional[List[Dict[str, Any]]] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    structured_output_schema: Optional[Dict[str, Any]] = None


class ModelResponse(BaseModel):
    content: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    provider: str = "mock"
    model_name: str = "mock-model"


class IModelAdapter(ABC):
    """Abstract adapter for LLM providers."""

    provider_name: str

    @abstractmethod
    async def complete(self, request: ModelRequest, model_name: str) -> ModelResponse:
        pass

    @abstractmethod
    async def stream(self, request: ModelRequest, model_name: str) -> AsyncIterator[str]:
        pass
