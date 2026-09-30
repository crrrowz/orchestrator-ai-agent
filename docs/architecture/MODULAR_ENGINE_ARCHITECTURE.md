# 🧩 Langflow-Style Modular Engine Architecture

## 1. Architectural Overview

ORAGAI has evolved from a monolithic orchestration system into a **composable, visual, engine-based autonomous AI platform**. Inspired by the architectural elegance of Langflow, every capability in ORAGAI is modeled as an independent **Component** connected through an asynchronous **Graph Execution Engine** and coordinated via a unified **Event Bus**.

```text
                               ┌─────────────────────────────────────────┐
                               │       Visual Studio / UI Client         │
                               └────────────────────┬────────────────────┘
                                                    │ REST / WebSocket
                               ┌────────────────────▼────────────────────┐
                               │           ORAGAI Core Engine            │
                               └──────┬───────────────────────────┬──────┘
                                      │                           │
                   ┌──────────────────▼───────────┐   ┌───────────▼──────────────────┐
                   │         Graph Engine         │   │         Plugin Engine        │
                   └──────────┬───────────────────┘   └───────────┬──────────────────┘
                              │                                   │
       ┌──────────────────────┼───────────────────────────────────┼──────────────────────┐
       │                      │                                   │                      │
┌──────▼──────┐        ┌──────▼──────┐                     ┌──────▼──────┐        ┌──────▼──────┐
│Agent Engine │        │Task Engine  │                     │Model Engine │        │Skill Engine │
└──────┬──────┘        └──────┬──────┘                     └──────┬──────┘        └──────┬──────┘
       │                      │                                   │                      │
       │               ┌──────▼──────────────┐                    │               ┌──────▼──────┐
       ├──────────────►│  Execution Engine   │◄───────────────────┴──────────────►│ Tool Engine  │
       │               └──────┬──────────────┘                                    └─────────────┘
       │                      │
┌──────▼──────┐        ┌──────▼──────────────┐                     ┌─────────────┐
│Memory Engine│        │  Governance Engine  │◄────────────────────┤Event Engine │
└─────────────┘        └──────┬──────────────┘                     └──────┬──────┘
                              │                                           │
                       ┌──────▼──────────────┐                            │
                       │ Verification Engine │◄───────────────────────────┘
                       └─────────────────────┘
```

---

## 2. The 13 Autonomous Engines

| Engine | Package Location | Primary Responsibility |
| :--- | :--- | :--- |
| **Core Engine** | `orchestrator/engines/core/` | Runtime container, dependency injection, and global lifecycle management. |
| **Graph Engine** | `orchestrator/engines/graph/` | Compilation, cyclic loop scheduling, and edge execution for workflow graphs. |
| **Agent Engine** | `orchestrator/engines/agents/` | Dynamic declarative agent blueprint registration and instance composition. |
| **Model Engine** | `orchestrator/engines/models/` | Provider-agnostic LLM interface, token counting, and live cost calculation. |
| **Tool Engine** | `orchestrator/engines/tools/` | Sandboxed tool execution, parameter schema validation, and AST security inspection. |
| **Skill Engine** | `orchestrator/engines/skills/` | Skill packaging (`skill.yaml`), dependency resolution, and token compression. |
| **Memory Engine** | `orchestrator/engines/memory/` | 5-tier memory scoping (`Conversation`, `Task`, `Project`, `Agent`, `LongTerm`). |
| **Task Engine** | `orchestrator/engines/tasks/` | Hierarchical task decomposition, Milestone DAG scheduling, and progress tracking. |
| **Execution Engine** | `orchestrator/engines/execution/` | Turn-by-turn agent loop orchestration and runtime abstraction. |
| **Governance Engine** | `orchestrator/engines/governance/` | Deterministic token budgeting, stagnation detection, and command safety interception. |
| **Verification Engine** | `orchestrator/engines/verification/` | Independent evidence-based completion gates and structured defect reports. |
| **Event Engine** | `orchestrator/engines/events/` | Asynchronous pub/sub event bus with wildcard pattern matching. |
| **Plugin Engine** | `orchestrator/engines/plugins/` | Dynamic third-party plugin discovery, validation, and lifecycle isolation. |

---

## 3. Universal Component & Port Contract

Every functional unit implements `IComponent` from `orchestrator/core/component.py`:

```python
class ComponentSchema(BaseModel):
    metadata: ComponentMetadata
    config_schema: Dict[str, Any]
    inputs: List[PortDefinition]
    outputs: List[PortDefinition]
```

### Supported Port Types
- `STRING`, `BOOLEAN`, `INTEGER`, `FLOAT`, `OBJECT`, `ARRAY`
- `CONTEXT`, `AGENT`, `MODEL`, `TOOL`, `SKILL`, `MEMORY`, `EVENT`, `ANY`

---

## 4. Visual Studio & FastAPI Integration

ORAGAI provides a decoupled FastAPI server in `orchestrator/ui/server/app.py`:
- `GET /api/v1/health`: Returns health status across all active engines.
- `POST /api/v1/graphs`: Validates and registers visual workflow DAGs.
- `POST /api/v1/execution/run`: Dispatches asynchronous workflow execution.

---

## 5. Master Plan & Implementation Map

The complete architectural plan suite is documented under `plans/`:
- `plans/00-plan-index.md`: Master dependency graph and traceability matrix.
- `plans/00-current-architecture.md`: Full codebase audit.
- `plans/01-architecture-gap-analysis.md`: 8-category architectural classification.
- `plans/02-target-architecture.md`: Detailed subsystem boundaries and specifications.
- `plans/03-component-model.md`: Universal component specifications.
- `plans/04-graph-execution-model.md`: Cyclic and DAG execution model.
- `plans/engines/01-13`: Discrete specifications for all 13 engines.
- `plans/agents/01-agent-composition.md`: Declarative agent YAML templates.
- `plans/plugins/01-03`: Skill, Tool, and Model plugin specifications.
- `plans/ui/01-visual-builder.md`: Visual Studio React Flow client design.
- `plans/99-migration-plan.md`: 6-phase non-breaking migration strategy.
