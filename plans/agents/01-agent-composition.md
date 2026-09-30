# Agent Plan 01: Declarative Agent Composition

## 1. Objective
Specify the declarative Agent Composition framework in ORAGAI, enabling the instantiation of specialized agents (Architect, Developer, Tester, Reviewer, Auditor, Researcher, etc.) as pure configurations combining Model, Skills, Tools, Memory, and Governance without code duplication.

## 2. Current Architecture Involved
- `orchestrator/agents/base.py`
- `orchestrator/agents/developer.py`
- `orchestrator/agents/tester.py`
- `orchestrator/agents/reviewer.py`
- `orchestrator/agents/architect.py`
- `orchestrator/agents/auditor.py`
- `orchestrator/agents/documentation.py`

## 3. Problem
Each agent in the existing codebase is an independent Python class repeating boilerplate factory methods (`resolve_workspace`, `resolve_role_config`, `resolve_tools`, `create`). Adding or modifying agent roles requires writing Python code rather than composing reusable component primitives.

## 4. Proposed Design

### Declarative Agent Assembly

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Declarative Agent Entity                     │
├─────────────────────────────────────────────────────────────────┤
│ Identity: Developer Agent                                       │
├─────────────────┬─────────────────────────────┬─────────────────┤
│ Model           │ Google Gemini 2.5 Flash     │ (Model Engine)  │
├─────────────────┼─────────────────────────────┼─────────────────┤
│ Skills          │ clean-python-architecture   │ (Skill Engine)  │
│                 │ api-design-guide, git-ops   │                 │
├─────────────────┼─────────────────────────────┼─────────────────┤
│ Tools           │ filesystem_tool             │ (Tool Engine)   │
│                 │ terminal_tool, git_tool     │                 │
├─────────────────┼─────────────────────────────┼─────────────────┤
│ Memory          │ project_scope_memory        │ (Memory Engine) │
│                 │ task_context_store          │                 │
├─────────────────┼─────────────────────────────┼─────────────────┤
│ Governance      │ adaptive_developer_policy   │ (Gov Engine)    │
└─────────────────┴─────────────────────────────┴─────────────────┘
```

### Standard Declarative Role Specifications

```yaml
# templates/developer.yaml
agent:
  name: "developer"
  display_name: "Lead Software Developer"
  system_prompt: |
    You are an expert autonomous software engineer.
    Implement code changes, adhere to clean architecture, run unit tests, and resolve defects.
  model:
    provider: "google"
    model_name: "gemini-2.5-flash"
    temperature: 0.2
  skills:
    - "clean-python-architecture"
    - "api-design-guide"
    - "systematic-debugging"
  tools:
    - "workspace_filesystem"
    - "workspace_terminal"
    - "git_ops"
  memory:
    conversation: true
    project_ast: true
    task_history: true
  governance:
    policy: "adaptive_execution"
    max_turns: 35
    stagnation_detection: true

---
# templates/tester.yaml
agent:
  name: "tester"
  display_name: "Senior QA & Test Engineer"
  system_prompt: |
    You are an autonomous quality assurance specialist.
    Write rigorous unit and integration tests, verify edge cases, and execute pytest suites.
  model:
    provider: "anthropic"
    model_name: "claude-3-7-sonnet"
    temperature: 0.0
  skills:
    - "pytest-rigorous-testing"
    - "api-contract-audit"
  tools:
    - "workspace_filesystem"
    - "workspace_terminal"
  memory:
    conversation: true
    task_history: true
  governance:
    policy: "strict_verification"
    max_turns: 20

---
# templates/reviewer.yaml
agent:
  name: "reviewer"
  display_name: "Security & Architectural Reviewer"
  system_prompt: |
    You are a principal engineer conducting code reviews and security audits.
    Enforce zero-stub policy, verify OWASP compliance, and review diffs critically.
  model:
    provider: "openai"
    model_name: "gpt-4o"
    temperature: 0.0
  skills:
    - "code-review-standards"
    - "security-audit-hardening"
  tools:
    - "workspace_filesystem" # Read-only
  memory:
    project_ast: true
    diff_history: true
  governance:
    policy: "read_only_governance"
    max_turns: 10
```

## 5. Files/Components Affected
- `orchestrator/engines/agents/models.py`
- `orchestrator/engines/agents/composer.py`
- `orchestrator/engines/agents/templates/*.yaml`
- `orchestrator/agents/` (Legacy shims)

## 6. Interfaces/Contracts
```python
from typing import Any, Dict
from pydantic import BaseModel

class AgentBlueprint(BaseModel):
    name: str
    display_name: str
    system_prompt: str
    model: Dict[str, Any]
    skills: List[str]
    tools: List[str]
    memory: Dict[str, Any]
    governance: Dict[str, Any]

class AgentComposer:
    @staticmethod
    def compose(blueprint: AgentBlueprint, engine_container: Any) -> Any: ...
```

## 7. Data Flow
Blueprint loaded from YAML/UI -> AgentComposer fetches Model adapter from Model Engine, Skills from Skill Engine, Tools from Tool Engine, Memory handles from Memory Engine, Governance rules from Governance Engine -> Assembles cohesive Agent Component -> Dispatches to Graph execution.

## 8. State Transitions
`BLUEPRINT_VALIDATED -> COMPONENTS_BOUND -> RUNTIME_INSTANTIATED -> EXECUTING -> DISPOSED`.

## 9. Error Handling
Invalid blueprint configurations (e.g. referencing an unregistered skill or tool) fail with clear structural validation errors prior to runtime execution.

## 10. Migration Strategy
Legacy factory classes (`DeveloperAgentFactory`, `TesterAgentFactory`, etc.) load their respective YAML blueprint and call `AgentComposer.compose()`.

## 11. Tests
- Schema validation tests across all YAML blueprints.
- Agent composition integration tests verifying correct tool and skill attachments.
- Zero-leakage multi-agent context tests.

## 12. Acceptance Criteria
- 100% of agent definitions migrated to declarative YAML blueprints.
- Ability to create custom ad-hoc agents at runtime without Python code modification.

## 13. Dependencies
Depends on Model, Skill, Tool, Memory, and Governance engines.

## 14. Risks
Runtime resolution latency; mitigated by caching composed agent blueprints in memory.

## 15. Rollback Strategy
Fallback to `orchestrator/agents/base.py` class hierarchies.
