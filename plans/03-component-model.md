# Plan 03: Unified Component Model

## 1. Objective
Design a universal, typed Component Contract inspired by Langflow and modern visual workflow architectures. Ensure every functional unit (Agents, Models, Tools, Skills, Memories, Tasks, Policies, Governors, Verifiers) shares a predictable metadata, I/O port, configuration, and lifecycle interface.

## 2. Current Architecture Involved
- `orchestrator/agents/base.py`
- `orchestrator/tools/workspace_tools.py`
- `orchestrator/skills/manager.py`
- `orchestrator/llm/manager.py`
- `orchestrator/control/adaptive/governor.py`
- `orchestrator/ci/verifier.py`

## 3. Problem
Currently, each domain uses disparate signatures, instantiation patterns, and configuration schemas. Agents expect `OrchestratorConfig`, tools are constructed as raw function wrappers or OpenHands tool objects, skills are directory strings, and verifiers are standalone procedural scripts. This makes visual composition and dynamic node connections impossible.

## 4. Proposed Design

### Universal Component Specification

Every component in ORAGAI implements the base `Component` contract:

```python
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
```

### Component Types & Port Contracts

| Component Type | Canonical Inputs | Canonical Outputs | Key Configuration Fields |
| :--- | :--- | :--- | :--- |
| **Agent** | `model` (MODEL), `skills` (SKILL[]), `tools` (TOOL[]), `memory` (MEMORY), `task` (STRING) | `agent` (AGENT), `result` (OBJECT), `artifacts` (ARRAY) | `role_name`, `system_prompt`, `max_turns`, `temperature` |
| **Model** | `prompt` (STRING/CONTEXT) | `completion` (STRING), `tool_calls` (ARRAY), `usage` (OBJECT) | `provider`, `model_name`, `api_key_env`, `temperature`, `max_tokens` |
| **Tool** | `params` (OBJECT) | `result` (ANY), `error` (STRING) | `tool_name`, `sandbox_mode`, `timeout_seconds`, `allowed_paths` |
| **Skill** | `task_context` (CONTEXT) | `instructions` (STRING), `examples` (ARRAY), `skill_ref` (SKILL) | `skill_dir`, `compression_level`, `auto_activate` |
| **Memory** | `query` (STRING), `item_to_store` (OBJECT) | `retrieved_context` (CONTEXT), `history` (ARRAY) | `backend`, `embedding_model`, `max_context_tokens`, `ttl` |
| **Task** | `goal` (STRING), `dependencies` (ARRAY) | `subtasks` (ARRAY), `current_task` (OBJECT) | `decomposition_strategy`, `max_subtasks`, `priority` |
| **Policy** | `event` (EVENT), `state` (OBJECT) | `action` (STRING), `params` (OBJECT) | `rules`, `severity_threshold`, `enforcement_mode` |
| **Governor** | `telemetry` (OBJECT), `turn_count` (INTEGER) | `verdict` (STRING), `budget_adjustment` (OBJECT) | `max_budget`, `stagnation_threshold`, `chaos_limit` |
| **Verifier** | `evidence` (OBJECT), `task_spec` (OBJECT) | `passed` (BOOLEAN), `feedback` (STRING), `defects` (ARRAY) | `verification_type` (pytest/audit/lint), `strict_mode` |

### Lifecycle Hooks
Each component lifecycle executes predictable hooks:
1. `on_init(config)`: Validate and bind configuration.
2. `on_mount(context)`: Bind to the active execution context and event bus.
3. `execute(inputs) -> outputs`: Primary functional computation.
4. `on_unmount()`: Clean up resources, connections, sandboxes, and file handles.

## 5. Files/Components Affected
- `orchestrator/core/component.py` (New base classes)
- `orchestrator/engines/*/component.py` (Domain component wrappers)

## 6. Interfaces/Contracts
```python
from abc import ABC, abstractmethod

class IComponent(ABC):
    schema: ComponentSchema

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None: ...

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], runtime_context: Any) -> Dict[str, Any]: ...

    @abstractmethod
    def cleanup(self) -> None: ...
```

## 7. Data Flow
Inputs validated against `PortDefinition` -> Component `execute()` runs -> Outputs validated against output `PortDefinition` -> Emitted to connected downstream ports.

## 8. State Transitions
`UNINITIALIZED -> INITIALIZED -> MOUNTED -> EXECUTING -> FINISHED / ERROR -> UNMOUNTED`.

## 9. Error Handling
Type mismatches on ports raise `PortTypeMismatchError`. Execution exceptions are captured into a standardized `ComponentExecutionError` container carrying input payload snapshots for debugging.

## 10. Migration Strategy
Wrap existing agent factories, tools, and managers in Component adapter shims during Migration Phase 2.

## 11. Tests
Unit tests verifying component schema generation, port validation, lifecycle transitions, and error trapping.

## 12. Acceptance Criteria
- Complete, typed Pydantic schema for components and ports.
- Canonical port definitions for all 9 primary component types.
- 100% decoupling from specific runtime frameworks.

## 13. Dependencies
Depends on Plan 02 (Target Architecture). Blocks Plan 04 (Graph Execution Model) and Plan 05 (Plugin System).

## 14. Risks
Overhead of port serialization; mitigated by allowing in-memory object references for local execution while enforcing Pydantic serialization at network boundaries.

## 15. Rollback Strategy
Component wrappers act as non-breaking decorators around existing classes.
