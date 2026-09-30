# Engine Plan 05: Tool Engine

## 1. Objective
Design a hardened, secure, and extensible Tool Engine supporting dynamic tool discovery, AST security inspection, path-scoped sandboxing, parameter validation, and execution telemetry.

## 2. Current Architecture Involved
- `orchestrator/tools/workspace_tools.py`
- `orchestrator/tools/hardened/` (`manager.py`, `sandbox.py`, `security.py`, `grammar.py`, `virtualizer.py`)
- `orchestrator/sentinel/ast_guard.py`
- `orchestrator/sentinel/command_interceptor.py`

## 3. Problem
Tool definitions and security guards are currently fragmented between `tools/hardened/`, `tools/workspace_tools.py`, and `sentinel/`. Tools cannot be visually inspected or dynamically attached to agents without manual code modifications.

## 4. Proposed Design
Implement `ToolEngine`:
- **Tool Registry**: Dynamic registry indexing tools by category (Filesystem, Terminal, VCS, Web, Analysis, Custom).
- **Hardened Execution Sandbox**: Strict process sandboxing, execution timeouts, working directory isolation, and path-traversal prevention.
- **AST & Command Security Guard**: Embedded AST inspection for Python scripts and regex/grammar interceptors for shell commands to prevent dangerous or destructive operations.
- **JSON Schema Tool Definition**: Automatic generation of OpenAI/Anthropic/Google function-calling schemas from Python type annotations or JSON definitions.

## 5. Files/Components Affected
- `orchestrator/engines/tools/engine.py`
- `orchestrator/engines/tools/registry.py`
- `orchestrator/engines/tools/sandbox.py`
- `orchestrator/engines/tools/guard.py`
- `orchestrator/engines/tools/builtins/` (`filesystem.py`, `terminal.py`, `git.py`, `web.py`)

## 6. Interfaces/Contracts
```python
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class ToolDescriptor(BaseModel):
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    category: str
    is_safe: bool = True
    timeout_seconds: int = 60
    required_permissions: List[str] = Field(default_factory=list)

class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: float
    command_executed: Optional[str] = None

class IToolEngine(IEngine):
    def register_tool(self, descriptor: ToolDescriptor, handler: Callable[..., Any]) -> None: ...
    async def execute_tool(self, name: str, params: Dict[str, Any], context: Dict[str, Any]) -> ToolExecutionResult: ...
    def get_tool_schemas(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]: ...
```

## 7. Data Flow
Agent invokes tool -> Tool Engine checks permissions & AST Guard -> Sandbox prepares isolated environment -> Tool handler executes with timeout -> Output sanitized and truncated if oversized -> Telemetry emitted to Event Engine -> Result returned to Agent.

## 8. State Transitions
`REGISTERED -> VALIDATING_INPUT -> SECURITY_CHECK -> EXECUTING -> OUTPUT_SANITIZATION -> RETURNED / BLOCKED_SECURITY / TIMEOUT`.

## 9. Error Handling
- Blocked commands (e.g. `rm -rf /`, unsafe network calls) trigger `SecurityViolationError` and log to Sentinel DB.
- Process timeouts gracefully kill the spawned subprocess tree without hanging the runtime.

## 10. Migration Strategy
Port existing functions in `workspace_tools.py` and `tools/hardened/manager.py` into native builtin tool plugins in `engines/tools/builtins/`.

## 11. Tests
- Sandboxed file path escape prevention tests (e.g. `../../etc/passwd`).
- Terminal command injection and AST guard AST-traversal rejection tests.
- Tool timeout and process termination tests.

## 12. Acceptance Criteria
- Zero-trust execution boundary around shell and filesystem operations.
- 100% compatibility with standard OpenAPI/JSON Schema function calling.

## 13. Dependencies
Depends on Core Engine, Event Engine. Blocks Agent Engine and Execution Engine.

## 14. Risks
Overly restrictive command interceptors blocking legitimate development scripts; mitigated by fine-grained rule whitelisting and user confirmation prompts.

## 15. Rollback Strategy
Fallback to `orchestrator/tools/workspace_tools.py`.
