"""Dynamic Agent Engine for declarative blueprint registration and composition."""

from typing import Any, Dict, List, Optional
from orchestrator.engines.agents.models import AgentBlueprint, AgentComponent
from orchestrator.engines.core.container import IContainer, IEngine


class AgentEngine(IEngine):
    """Engine responsible for declarative agent registration and dynamic instance composition."""

    engine_name: str = "agents"

    def __init__(self) -> None:
        self._blueprints: Dict[str, AgentBlueprint] = {}
        self._container: Optional[IContainer] = None
        self._is_running: bool = False
        self._register_default_blueprints()

    async def initialize(self, container: IContainer) -> None:
        self._container = container
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    def register_blueprint(self, blueprint: AgentBlueprint) -> None:
        self._blueprints[blueprint.name] = blueprint

    def get_blueprint(self, name: str) -> Optional[AgentBlueprint]:
        return self._blueprints.get(name)

    def list_blueprints(self) -> List[AgentBlueprint]:
        return list(self._blueprints.values())

    def create_agent_component(self, name: str) -> Optional[AgentComponent]:
        blueprint = self._blueprints.get(name)
        if not blueprint:
            return None
        return AgentComponent(blueprint, self._container)

    def _register_default_blueprints(self) -> None:
        self.register_blueprint(
            AgentBlueprint(
                name="developer",
                display_name="Lead Developer",
                system_prompt="You are an autonomous software developer.",
                skills=["clean-python-architecture"],
                tools=["echo"],
            )
        )
        self.register_blueprint(
            AgentBlueprint(
                name="tester",
                display_name="Senior QA Tester",
                system_prompt="You are a quality assurance specialist.",
                skills=["pytest-rigorous-testing"],
                tools=["echo"],
            )
        )
        self.register_blueprint(
            AgentBlueprint(
                name="reviewer",
                display_name="Code Reviewer",
                system_prompt="You are a senior security and code reviewer.",
                skills=["code-review-standards"],
                tools=["echo"],
            )
        )

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "registered_blueprints_count": len(self._blueprints),
            "blueprint_names": list(self._blueprints.keys()),
        }
