"""Agent Blueprint models and declarative schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.core.component import (
    ComponentMetadata,
    ComponentSchema,
    ComponentState,
    ComponentType,
    IComponent,
    PortDefinition,
    PortType,
)


class AgentBlueprint(BaseModel):
    name: str
    display_name: str
    system_prompt: str
    model_provider: str = "mock"
    model_name: str = "default"
    temperature: float = 0.0
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    memory_config: Dict[str, Any] = Field(default_factory=dict)
    governance_policy: str = "default"
    max_turns: int = 30


class AgentComponent(IComponent):
    """Executable Agent Component wrapping a declarative blueprint."""

    def __init__(self, blueprint: AgentBlueprint, container: Any = None) -> None:
        self.blueprint = blueprint
        self.container = container
        self.schema = ComponentSchema(
            metadata=ComponentMetadata(
                id=f"agent-{blueprint.name}",
                name=blueprint.display_name,
                type=ComponentType.AGENT,
                category="agents",
                description=f"Autonomous agent specializing in {blueprint.name}",
            ),
            inputs=[
                PortDefinition(name="task", type=PortType.STRING, description="Task instructions"),
                PortDefinition(name="context", type=PortType.CONTEXT, required=False),
            ],
            outputs=[
                PortDefinition(name="result", type=PortType.OBJECT),
                PortDefinition(name="artifacts", type=PortType.ARRAY),
            ],
        )
        self.state = ComponentState.UNINITIALIZED

    def initialize(self, config: Dict[str, Any]) -> None:
        self.state = ComponentState.INITIALIZED

    async def execute(self, inputs: Dict[str, Any], runtime_context: Any = None) -> Dict[str, Any]:
        self.state = ComponentState.EXECUTING
        task_text = inputs.get("task", "")

        # In unified architecture, execute calls the Execution Engine or Mock Model
        res = {
            "agent": self.blueprint.name,
            "status": "completed",
            "output": f"Executed task: '{task_text}' using model '{self.blueprint.model_name}'",
            "artifacts": ["code_diff.patch"],
        }
        self.state = ComponentState.FINISHED
        return res

    def cleanup(self) -> None:
        self.state = ComponentState.UNMOUNTED
