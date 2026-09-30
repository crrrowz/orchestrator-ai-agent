"""Graph execution models, connections, and schemas."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeExecutionState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class EdgeType(str, Enum):
    DATA = "data"
    CONTROL = "control"
    CONDITIONAL = "conditional"
    ERROR = "error"


class Connection(BaseModel):
    id: str
    from_node_id: str
    from_port: str = "result"
    to_node_id: str
    to_port: str = "context"
    edge_type: EdgeType = EdgeType.CONTROL
    condition_expr: Optional[str] = None


class GraphNode(BaseModel):
    id: str
    component_name: str
    name: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})


class GraphDefinition(BaseModel):
    id: str
    name: str
    description: str = ""
    entrypoint_node_id: str
    nodes: Dict[str, GraphNode]
    connections: List[Connection]
    max_loop_iterations: int = 20
