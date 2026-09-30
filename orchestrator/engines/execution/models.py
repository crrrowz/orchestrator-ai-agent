"""Execution Engine models and turn results."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionTurnResult(BaseModel):
    turn_index: int
    agent_name: str
    action_taken: str = ""
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0
    is_terminal: bool = False
    error: Optional[str] = None
