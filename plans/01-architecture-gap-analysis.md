# Plan 01: Architectural Gap Analysis

## 1. Objective
Perform a rigorous gap analysis comparing the current monolithic, pipeline-oriented ORAGAI architecture with the target Langflow-style composable, visual, engine-based autonomous AI platform. Classify every major subsystem into KEEP, REUSE, MOVE, MERGE, REPLACE, DEPRECATE, REMOVE, or CREATE.

## 2. Current Architecture Involved
- Subsystems across `orchestrator/pipeline/`, `orchestrator/agents/`, `orchestrator/control/`, `orchestrator/sentinel/`, `orchestrator/tools/`, `orchestrator/skills/`, `orchestrator/llm/`, `orchestrator/memory/`, `orchestrator/analysis/`, and `orchestrator/ci/`.

## 3. Problem
The current system binds agent roles, model invocation, tools, and execution sequences into fixed Python classes and hardcoded pipeline classes (`DevTestLoop`, `FullPipeline`, `AuditPipeline`), making dynamic runtime graph composition, visual workflow editing, and flexible plugin integration impossible without modifying core orchestrator source code.

## 4. Proposed Design
Decompose the monolith into 13 autonomous engines adhering to a unified Component-Connection-Execution paradigm.

### Comprehensive Action Classification Table

| Subsystem / Component | Current Location | Architectural Action | Target Location / Engine | Justification |
| :--- | :--- | :--- | :--- | :--- |
| **AST Guard & Hardened Tools** | `orchestrator/sentinel/ast_guard.py`, `tools/hardened/` | **REUSE & MOVE** | `orchestrator/engines/governance/guards/`, `engines/tools/` | Core security logic is robust; needs decoupling from sentinel monolith into Tool/Governance engines. |
| **Skill Registry & Compression** | `orchestrator/skills/` | **MOVE & REUSE** | `orchestrator/engines/skills/` | High-value domain capability; abstract into a standard Plugin/Skill Engine component. |
| **Token & Context Budgeting** | `orchestrator/control/token_governance.py`, `context_budget_manager.py` | **MERGE & MOVE** | `orchestrator/engines/governance/budget/` | Unify token tracking, rate limiting, and context budgeting into cohesive Governance Engine. |
| **Adaptive Governor & Clamper** | `orchestrator/control/adaptive/` | **REUSE & MOVE** | `orchestrator/engines/governance/adaptive/` | Dynamic iteration and budget adjustment logic is production-grade and fits directly into Governance. |
| **Legacy Pipelines** | `orchestrator/pipeline/dev_test_loop.py`, `full_pipeline.py`, etc. | **REPLACE & DEPRECATE** | `orchestrator/engines/graph/workflows/` (declarative graphs) | Replace hardcoded Python loops with declarative DAG execution graphs. |
| **Dual FSM Engines** | `orchestrator/pipeline/state_machine.py` vs `fsm/engine.py` | **MERGE & REPLACE** | `orchestrator/engines/graph/state_machine.py` | Eliminate legacy `state_machine.py`; adapt `fsm/engine.py` to drive Graph Engine execution. |
| **Static Agent Classes** | `orchestrator/agents/developer.py`, `tester.py`, etc. | **REPLACE** | `orchestrator/engines/agents/` (Declarative Agent Component) | Agents become schema-defined compositions (Model + Skills + Tools + Memory + Governance). |
| **OpenHands Bridge** | `orchestrator/engine/openhands_bridge.py` | **MOVE & REUSE** | `orchestrator/engines/execution/providers/openhands.py` | Retain as an execution runtime provider behind the unified Execution Engine interface. |
| **Sentinel Supervisor** | `orchestrator/sentinel/supervisor.py` | **MERGE** | `orchestrator/engines/governance/sentinel_supervisor.py` | Integrate with the Event Engine and Governance Engine for unified lifecycle telemetry. |
| **CI Evidence & Root Cause** | `orchestrator/ci/` | **MOVE & REUSE** | `orchestrator/engines/verification/ci/` | Foundational for evidence-based completion; integrate into Verification Engine. |
| **Audit Engine & Scanner** | `orchestrator/analysis/audit/` | **MOVE & REUSE** | `orchestrator/engines/verification/audit/` | Move into Verification Engine as an independent audit verifier node. |
| **Conversation Store** | `orchestrator/memory/conversation_store.py` | **MOVE & EXPAND** | `orchestrator/engines/memory/` | Expand beyond simple conversation store to support Project, Task, Agent, and Long-Term Memory. |
| **Graph Execution Engine** | N/A | **CREATE** | `orchestrator/engines/graph/` | Core missing capability: supports DAG/cyclic execution, conditional branching, and node handoffs. |
| **Plugin Engine** | N/A | **CREATE** | `orchestrator/engines/plugins/` | Core missing capability: allows dynamic discovery and lifecycle management of 3rd party components. |
| **Event Engine** | N/A | **CREATE** | `orchestrator/engines/events/` | Core missing capability: event-driven pub/sub bus to decouple inter-engine communication. |
| **Visual Studio / UI API** | N/A | **CREATE** | `orchestrator/ui/` | Backend REST/WebSocket API and visual workflow schema translator. |

## 5. Files/Components Affected
All subsystems across `orchestrator/` as outlined in Section 4.

## 6. Interfaces/Contracts
Unified abstraction contracts:
- `IComponent`: Base protocol for all modular components.
- `IEngine`: Base protocol for all 13 core engines.
- `IGraphNode`: Protocol for nodes executing within the Graph Engine.
- `IEventBus`: Protocol for event publishing and subscription.

## 7. Data Flow
Transformation from synchronous call stacks:
`Orchestrator -> Dispatcher -> FSM -> Agent -> OpenHands`
to event-driven, graph-governed execution:
`Graph Engine -> Execution Engine -> Component (Agent/Tool/Skill) -> Event Bus -> Governance & Verification Engines`.

## 8. State Transitions
Transition states migrate from pipeline-specific enumerations (`DevTestState`, `FullPipelineState`) to node-level lifecycle states (`IDLE`, `CONFIGURED`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`, `ROLLED_BACK`).

## 9. Error Handling
Fault isolation shifts from top-level `try-except` blocks in `orchestrator.py` to localized Node Error Handlers and Sentinel Circuit Breakers within the Graph Engine.

## 10. Migration Strategy
Dual-mode execution architecture: Legacy pipelines will construct Graph Engine DAG representations on-the-fly to guarantee 100% backward compatibility during migration.

## 11. Tests
- Comparative parity tests validating that graph-based workflows produce identical outputs to legacy pipelines.
- Unit tests for new `IComponent` contracts and engine interfaces.

## 12. Acceptance Criteria
- Explicit categorization for every file in the repository.
- Clear architectural rationale for all 8 action categories (KEEP, REUSE, MOVE, MERGE, REPLACE, DEPRECATE, REMOVE, CREATE).
- Zero ambiguity on target destination for legacy logic.

## 13. Dependencies
Depends on Plan 00 (Current Architecture Audit). Blocks all subsequent Engine and Component plans.

## 14. Risks
Scope creep during component separation; mitigated by strict adherence to declarative interfaces without altering underlying algorithmic logic.

## 15. Rollback Strategy
Non-destructive planning document; baseline code remains unmodified.
