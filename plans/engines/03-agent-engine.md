# Engine Plan 03: Agent Engine

## 1. Objective
Design the Agent Engine responsible for dynamically composing, instantiating, executing, and managing autonomous AI agent entities without hardcoded role classes.

## 2. Current Architecture Involved
- `orchestrator/agents/base.py`
- `orchestrator/agents/developer.py`
- `orchestrator/agents/tester.py`
- `orchestrator/agents/reviewer.py`
- `orchestrator/agents/architect.py`
- `orchestrator/agents/auditor.py`
- `orchestrator/agents/documentation.py`

## 3. Problem
Currently, each agent role is a hardcoded Python class subclassing `BaseAgentFactory`. Customizing an agent's skills, tools, model, or prompts requires editing Python code. Agents cannot be composed or customized dynamically at runtime or via a visual canvas.

## 4. Proposed Design
Implement `AgentEngine` based on dynamic composition:
- **Declarative Agent Specification**: Defines an agent entity purely via configuration (Name, Persona, System Prompt Template, Model Reference, Skill References, Tool References, Memory Policy, Governance Policy).
- **Agent Factory & Registry**: Dynamically constructs executable agent instances from specifications.
- **Role Templates**: Pre-packaged templates for Architect, Developer, Tester, Reviewer, Auditor, and Documentation agents defined as YAML/JSON descriptors.
- **Dynamic Persona & Context Injection**: Injects project context, skill summaries, and runtime guidelines into the agent's prompt during initialization.

## 5. Files/Components Affected
- `orchestrator/engines/agents/engine.py`
- `orchestrator/engines/agents/models.py`
- `orchestrator/engines/agents/factory.py`
- `orchestrator/engines/agents/registry.py`
- `orchestrator/engines/agents/templates/*.yaml`

## 6. Interfaces/Contracts
```python
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class AgentConfig(BaseModel):
    name: str
    role: str
    system_prompt: str
    model_component_id: str
    skill_ids: List[str] = Field(default_factory=list)
    tool_ids: List[str] = Field(default_factory=list)
    memory_config: Dict[str, Any] = Field(default_factory=dict)
    governance_policy_id: str = "default_governance"
    temperature: float = 0.0
    max_turns: int = 30

class IAgentEngine(IEngine):
    async def create_agent(self, config: AgentConfig) -> Any: ...
    def register_template(self, template_name: str, config: AgentConfig) -> None: ...
    def get_template(self, template_name: str) -> AgentConfig: ...
```

## 7. Data Flow
Graph Node triggers Agent Component -> Agent Engine resolves configured Model, Skills, Tools, and Memory -> Synthesizes consolidated system prompt -> Creates runtime Agent entity -> Dispatches to Execution Engine -> Returns execution outcome.

## 8. State Transitions
`CONFIGURED -> INSTANTIATED -> BOUND_TO_RUNTIME -> ACTIVE_TURN -> COMPLETED / TURN_LIMIT_REACHED`.

## 9. Error Handling
Missing tool or skill references raise `AgentCompositionError`. Unresponsive models or malformed prompts trigger agent-level fallback policies.

## 10. Migration Strategy
Legacy classes (`DeveloperAgentFactory`, etc.) become thin wrapper functions calling `AgentEngine.create_from_template("developer")`.

## 11. Tests
- Dynamic composition tests verifying prompt injection and tool binding.
- Template inheritance and override tests.
- Multi-agent isolation tests ensuring zero context leakage across agent instances.

## 12. Acceptance Criteria
- Complete elimination of hardcoded agent Python classes.
- Full parity with existing agent behaviors via YAML template definitions.

## 13. Dependencies
Depends on Core Engine, Model Engine, Skill Engine, Tool Engine, Memory Engine. Blocks Graph Engine workflow execution.

## 14. Risks
Prompt template regressions when moving from Python f-strings to declarative templates; mitigated by strict unit test golden prompt assertions.

## 15. Rollback Strategy
Keep `orchestrator/agents/base.py` as an active fallback factory during migration.
