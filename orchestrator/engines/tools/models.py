"""Tool models, descriptors, and execution results."""

from typing import Any, Callable, Coroutine, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolDescriptor(BaseModel):
    name: str
    description: str
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    category: str = "general"
    is_safe: bool = True
    timeout_seconds: int = 60
    required_permissions: List[str] = Field(default_factory=list)


class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: float = 0.0
    command_executed: Optional[str] = None


ToolHandler = Callable[[Dict[str, Any], Dict[str, Any]], Coroutine[Any, Any, Any]]
