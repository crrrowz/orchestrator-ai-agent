"""Memory item models and scoped storage structures."""

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryScope(str, Enum):
    CONVERSATION = "conversation"
    TASK = "task"
    PROJECT = "project"
    AGENT = "agent"
    LONG_TERM = "long_term"


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scope: MemoryScope
    key: str
    value: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
