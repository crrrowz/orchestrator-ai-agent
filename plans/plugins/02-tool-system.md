# Plugin Plan 02: Unified Tool System

## 1. Objective
Design the unified Tool Plugin System in ORAGAI, defining standard tool packaging, schema generation, permissions, execution hooks, and telemetry isolation.

## 2. Current Architecture Involved
- `orchestrator/tools/workspace_tools.py`
- `orchestrator/tools/hardened/manager.py`
- `orchestrator/tools/hardened/sandbox.py`

## 3. Problem
Tools are currently coupled to OpenHands SDK function signatures and lack declarative permission manifests, standalone packaging, and visual inspector compatibility.

## 4. Proposed Design
Standardize the Tool Plugin architecture:

### Tool Plugin Declaration
```python
from typing import Any, Dict
from pydantic import BaseModel, Field

class BaseToolPlugin:
    name: str = "custom_tool"
    description: str = "Tool description"
    parameters_schema: Dict[str, Any] = {}
    required_permissions: List[str] = []
    timeout_seconds: int = 60

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Any:
        raise NotImplementedError
```

### Declarative Tool Manifest (`tool.yaml`)
```yaml
name: "git_advanced_ops"
version: "1.0.0"
author: "VCS Team"
description: "Advanced Git branch, rebase, and diff verification tools"
entrypoint: "git_plugin.tools:GitAdvancedTool"
permissions:
  - "terminal.execute"
  - "git.read"
  - "git.write"
parameters:
  type: "object"
  properties:
    command:
      type: "string"
      description: "Git sub-command to execute"
    target_branch:
      type: "string"
      description: "Target branch name"
  required:
    - "command"
```

## 5. Files/Components Affected
- `orchestrator/engines/tools/plugin_base.py`
- `orchestrator/engines/tools/builtins/`
- `orchestrator/plugins/tools/`

## 6. Interfaces/Contracts
```python
from abc import ABC, abstractmethod

class IToolPlugin(ABC):
    @abstractmethod
    def get_descriptor(self) -> ToolDescriptor: ...

    @abstractmethod
    async def run(self, arguments: Dict[str, Any], runtime_context: Any) -> ToolExecutionResult: ...
```

## 7. Data Flow
Agent emits tool call -> Tool Engine resolves `IToolPlugin` -> Verifies permissions against security sandbox -> Executes `run()` -> Returns sanitized `ToolExecutionResult`.

## 8. State Transitions
`UNLOADED -> REGISTERED -> PERMISSION_CHECK -> EXECUTING -> RETURNED`.

## 9. Error Handling
Runtime tool exceptions are encapsulated into structured JSON errors returned to the LLM agent rather than throwing unhandled process exceptions.

## 10. Migration Strategy
Wrap existing `create_workspace_file_tool` and `create_workspace_terminal_tool` as built-in `IToolPlugin` implementations.

## 11. Tests
- Tool parameter validation against JSON schema tests.
- Tool permission enforcement tests.
- Sandboxed error encapsulation tests.

## 12. Acceptance Criteria
- 100% decoupling from OpenHands tool primitives.
- Dynamic tool registration and schema export.

## 13. Dependencies
Depends on Tool Engine, Core Engine.

## 14. Risks
Permission escalation bypass; mitigated by running tools within strict OS-level sandbox boundaries.

## 15. Rollback Strategy
Fallback to `orchestrator/tools/workspace_tools.py`.
