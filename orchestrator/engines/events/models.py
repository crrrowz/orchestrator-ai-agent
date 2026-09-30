"""Event models and schemas for Event Engine."""

import time
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    source_engine: str = "core"
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
