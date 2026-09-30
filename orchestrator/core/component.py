"""Universal Component Model for ORAGAI."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    AGENT = "agent"
    MODEL = "model"
    TOOL = "tool"
    SKILL = "skill"
    MEMORY = "memory"
    TASK = "task"
    POLICY = "policy"
    GOVERNOR = "governor"
    VERIFIER = "verifier"
    CUSTOM = "custom"


class PortType(str, Enum):
    STRING = "string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    OBJECT = "object"
    ARRAY = "array"
    CONTEXT = "context"
    AGENT = "agent"
    MODEL = "model"
    TOOL = "tool"
    SKILL = "skill"
    MEMORY = "memory"
    EVENT = "event"
    ANY = "any"


class PortDefinition(BaseModel):
    name: str
    type: PortType
    description: str = ""
    required: bool = True
    multiple: bool = False
    default: Optional[Any] = None


class ComponentMetadata(BaseModel):
    id: str
    name: str
    version: str = "1.0.0"
    type: ComponentType
    category: str
    description: str
    author: str = "ORAGAI"
    icon: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ComponentSchema(BaseModel):
    metadata: ComponentMetadata
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    inputs: List[PortDefinition] = Field(default_factory=list)
    outputs: List[PortDefinition] = Field(default_factory=list)


class ComponentState(str, Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    MOUNTED = "mounted"
    EXECUTING = "executing"
    FINISHED = "finished"
    ERROR = "error"
    UNMOUNTED = "unmounted"


class IComponent(ABC):
    """Universal interface for all modular components."""

    schema: ComponentSchema
    state: ComponentState = ComponentState.UNINITIALIZED

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Validate and bind configuration."""
        pass

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], runtime_context: Any = None) -> Dict[str, Any]:
        """Perform component computation."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up allocated resources."""
        pass
