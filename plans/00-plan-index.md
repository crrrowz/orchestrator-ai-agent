# Master Plan Index & Dependency Graph

## Executive Summary
This document defines the master plan index, dependency graph, execution sequence, and traceability matrix for transforming ORAGAI into a modular, visual, engine-based autonomous AI platform inspired by Langflow-style composability.

---

## 1. Master Dependency Graph

```text
                               ┌─────────────────────────────┐
                               │  00-current-architecture    │
                               └──────────────┬──────────────┘
                                              │
                               ┌──────────────▼──────────────┐
                               │ 01-architecture-gap-analysis│
                               └──────────────┬──────────────┘
                                              │
                               ┌──────────────▼──────────────┐
                               │    02-target-architecture   │
                               └──────────────┬──────────────┘
                                              │
                               ┌──────────────▼──────────────┐
                               │     03-component-model      │
                               └──────────────┬──────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                             │
        ┌──────────────▼──────────────┐               ┌──────────────▼──────────────┐
        │   engines/01-core-engine    │               │   engines/12-event-engine   │
        └──────────────┬──────────────┘               └──────────────┬──────────────┘
                       │                                             │
                       └──────────────────────┬──────────────────────┘
                                              │
     ┌───────────────────┬────────────────────┼───────────────────┬───────────────────┐
     │                   │                    │                   │                   │
┌────▼─────────────┐┌────▼─────────────┐ ┌────▼─────────────┐┌────▼─────────────┐┌────▼─────────────┐
│engines/04-model  ││engines/05-tool   │ │engines/06-skill  ││engines/07-memory ││engines/08-task   │
│plugins/03-model  ││plugins/02-tool   │ │plugins/01-skill  ││  (Memory Engine) ││  (Task Engine)   │
└────┬─────────────┘└────┬─────────────┘ └────┬─────────────┘└────┬─────────────┘└────┬─────────────┘
     │                   │                    │                   │                   │
     └───────────────────┼────────────────────┴───────────────────┘                   │
                         │                                                            │
                  ┌──────▼────────────────────────────────┐                           │
                  │       engines/03-agent-engine         │                           │
                  │     agents/01-agent-composition       │                           │
                  └──────┬────────────────────────────────┘                           │
                         │                                                            │
                         ├────────────────────────────────────────────────────────────┘
                         │
                  ┌──────▼────────────────────────────────┐
                  │      engines/09-execution-engine      │
                  └──────┬────────────────────────────────┘
                         │
     ┌───────────────────┴────────────────────┐
     │                                        │
┌────▼─────────────────────────┐       ┌──────▼────────────────────────┐
│ engines/10-governance-engine │       │ engines/11-verification-engine│
└────┬─────────────────────────┘       └──────┬────────────────────────┘
     │                                        │
     └───────────────────┬────────────────────┘
                         │
                  ┌──────▼────────────────────────────────┐
                  │       04-graph-execution-model        │
                  │       engines/02-graph-engine         │
                  └──────┬────────────────────────────────┘
                         │
     ┌───────────────────┴────────────────────┐
     │                                        │
┌────▼─────────────────────────┐       ┌──────▼────────────────────────┐
│  engines/13-plugin-engine    │       │     ui/01-visual-builder      │
└────┬─────────────────────────┘       └──────┬────────────────────────┘
     │                                        │
     └───────────────────┬────────────────────┘
                         │
                  ┌──────▼────────────────────────────────┐
                  │          99-migration-plan            │
                  └───────────────────────────────────────┘
```

---

## 2. Complete Plan Manifest & Traceability Matrix

| Plan Path | Title | Depends On | Blocks | Parallel With |
| :--- | :--- | :--- | :--- | :--- |
| `plans/00-current-architecture.md` | Current Architecture Audit | None | `01-gap-analysis` | None |
| `plans/completeness-matrix.md` | Architecture Completeness Matrix | `00-current-architecture` | All Plans | Continuous |
| `plans/01-architecture-gap-analysis.md` | Architecture Gap Analysis | `00-current-architecture` | `02-target-architecture` | None |
| `plans/02-target-architecture.md` | Target Architecture Specification | `01-gap-analysis` | `03-component-model` | None |
| `plans/03-component-model.md` | Unified Component Model | `02-target-architecture` | `engines/01-core`, `engines/12-event` | None |
| `plans/04-graph-execution-model.md` | Graph Execution Model | `engines/09-execution`, `engines/10-governance` | `engines/02-graph`, `ui/01-visual` | `engines/11-verification` |
| `plans/engines/01-core-engine.md` | Core Engine Specification | `03-component-model` | All Engines | `engines/12-event` |
| `plans/engines/02-graph-engine.md` | Graph Engine Implementation | `04-graph-execution-model` | `ui/01-visual`, `99-migration` | `engines/13-plugin` |
| `plans/engines/03-agent-engine.md` | Agent Engine Specification | `engines/04-model`, `engines/05-tool`, `engines/06-skill`, `engines/07-memory` | `engines/09-execution` | `agents/01-agent-composition` |
| `plans/engines/04-model-engine.md` | Model Engine Specification | `engines/01-core`, `engines/12-event` | `engines/03-agent` | `engines/05-tool`, `engines/06-skill`, `engines/07-memory` |
| `plans/engines/05-tool-engine.md` | Tool Engine Specification | `engines/01-core`, `engines/12-event` | `engines/03-agent` | `engines/04-model`, `engines/06-skill`, `engines/07-memory` |
| `plans/engines/06-skill-engine.md` | Skill Engine Specification | `engines/01-core`, `engines/07-memory` | `engines/03-agent` | `engines/04-model`, `engines/05-tool` |
| `plans/engines/07-memory-engine.md` | Memory Engine Specification | `engines/01-core`, `engines/12-event` | `engines/03-agent` | `engines/04-model`, `engines/05-tool`, `engines/06-skill` |
| `plans/engines/08-task-engine.md` | Task Engine Specification | `engines/01-core`, `engines/12-event` | `engines/09-execution` | `engines/03-agent` |
| `plans/engines/09-execution-engine.md` | Execution Engine Specification | `engines/03-agent`, `engines/08-task` | `04-graph-execution-model` | `engines/10-governance` |
| `plans/engines/10-governance-engine.md` | Adaptive Governance Engine | `engines/01-core`, `engines/12-event` | `04-graph-execution-model` | `engines/11-verification` |
| `plans/engines/11-verification-engine.md` | Verification Engine Specification | `engines/01-core`, `engines/05-tool`, `engines/12-event` | `04-graph-execution-model` | `engines/10-governance` |
| `plans/engines/12-event-engine.md` | Event Engine Specification | `03-component-model` | All Engines | `engines/01-core` |
| `plans/engines/13-plugin-engine.md` | Plugin Engine Specification | `engines/01-core`, `03-component-model` | `ui/01-visual`, `99-migration` | `engines/02-graph` |
| `plans/agents/01-agent-composition.md` | Declarative Agent Composition | `engines/03-agent` | `engines/09-execution` | `engines/03-agent` |
| `plans/plugins/01-skill-system.md` | Skill Package & Plugin System | `engines/06-skill` | `engines/03-agent` | `plugins/02-tool`, `plugins/03-model` |
| `plans/plugins/02-tool-system.md` | Unified Tool System | `engines/05-tool` | `engines/03-agent` | `plugins/01-skill`, `plugins/03-model` |
| `plans/plugins/03-model-system.md` | Provider-Agnostic Model System | `engines/04-model` | `engines/03-agent` | `plugins/01-skill`, `plugins/02-tool` |
| `plans/ui/01-visual-builder.md` | Visual Studio & Workflow Builder | `engines/02-graph`, `engines/12-event`, `engines/13-plugin` | `99-migration` | None |
| `plans/99-migration-plan.md` | Incremental Migration Strategy | All preceding plans | Final Release | None |

---

## 3. Recommended Execution Order for Autonomous Implementation Agents

When executing this roadmap, implementation agents MUST follow this sequence:

1. **Step 1**: Execute `plans/engines/01-core-engine.md`, `plans/03-component-model.md`, and `plans/engines/12-event-engine.md`.
2. **Step 2**: Concurrently execute `plans/engines/04-model-engine.md` (and `plugins/03`), `plans/engines/05-tool-engine.md` (and `plugins/02`), `plans/engines/06-skill-engine.md` (and `plugins/01`), and `plans/engines/07-memory-engine.md`.
3. **Step 3**: Execute `plans/engines/08-task-engine.md`, `plans/engines/03-agent-engine.md`, and `plans/agents/01-agent-composition.md`.
4. **Step 4**: Execute `plans/engines/09-execution-engine.md`, `plans/engines/10-governance-engine.md`, and `plans/engines/11-verification-engine.md`.
5. **Step 5**: Execute `plans/04-graph-execution-model.md` and `plans/engines/02-graph-engine.md`.
6. **Step 6**: Execute `plans/engines/13-plugin-engine.md` and `plans/ui/01-visual-builder.md`.
7. **Step 7**: Execute `plans/99-migration-plan.md` to complete end-to-end integration and deprecated code cleanup.
