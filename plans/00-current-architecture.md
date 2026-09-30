# Plan 00: Current Architecture Audit

## 1. Objective
Establish a comprehensive baseline audit of the existing ORAGAI codebase. Document the current orchestration topology, finite state machines (FSM), agent implementations, execution loops, budget management, context handoffs, tools, skills, telemetry, Sentinel guards, and identify legacy/duplicated subsystems.

## 2. Current Architecture Involved
- **Main Entrypoints**: `orchestrator/orchestrator.py`, `orchestrator/main.py`, `orchestrator/cli/app.py`
- **Pipelines & FSM**: `orchestrator/pipeline/` (`dev_test_loop.py`, `full_pipeline.py`, `audit_pipeline.py`, `audit_fix_pipeline.py`, `documentation_pipeline.py`, `dispatcher.py`, `fsm/engine.py`, `state_machine.py`)
- **Agents**: `orchestrator/agents/` (`base.py`, `developer.py`, `tester.py`, `reviewer.py`, `architect.py`, `auditor.py`, `documentation.py`)
- **Execution Bridge**: `orchestrator/engine/openhands_bridge.py`
- **Governance & Sentinel**: `orchestrator/control/` (`token_governance.py`, `budget_guard.py`, `context_budget_manager.py`, `adaptive/`), `orchestrator/sentinel/` (`supervisor.py`, `self_healing.py`, `ast_guard.py`, `command_interceptor.py`, `cloud_mesh.py`)
- **Skills & Tools**: `orchestrator/skills/` (`manager.py`, `resolver.py`, `registry.py`, `compressor.py`), `orchestrator/tools/` (`workspace_tools.py`, `hardened/`)
- **Context & Memory**: `orchestrator/context/` (`manager.py`, `prompt_builder.py`, `handoff/`), `orchestrator/memory/` (`conversation_store.py`)
- **Analysis & CI**: `orchestrator/analysis/` (`audit/`, `pr_gate.py`, `pytest_parser.py`), `orchestrator/ci/` (`verifier.py`, `analyzer.py`, `root_cause.py`)
- **Adapters & Ports**: `orchestrator/adapters/` (`vcs/`), `orchestrator/ports/` (`driving/`)

## 3. Problem
1. **Monolithic Orchestration**: `Orchestrator` (`orchestrator.py`) and `OrchestratorDispatcher` directly branch across hard-coded string modes (`"dev-test"`, `"full"`, `"audit"`, `"audit-fix"`, `"docs"`).
2. **Dual State Machine Duplication**: Two parallel state machine implementations exist: `orchestrator/pipeline/state_machine.py` (legacy simple FSM) and `orchestrator/pipeline/fsm/engine.py` (hierarchical profile-based FSM).
3. **Rigid Agent Specialization**: Agents inherit from `BaseAgentFactory` but are hardcoded classes with static system prompts and hardwired tool/skill associations rather than composable entity configurations.
4. **Scattered Governance & Guards**: Governance is split across `orchestrator/control/token_governance.py`, `orchestrator/control/adaptive/`, `orchestrator/governance/`, and `orchestrator/sentinel/`.
5. **Coupled Runtime Engine**: Agents directly instantiate OpenHands SDK objects (`openhands.sdk.Agent`, `LLM`) without an intermediate, provider-agnostic component and execution graph layer.

## 4. Proposed Design
Transition the audited architecture into a composable Langflow-style engine-and-component hierarchy:
- Replace static mode dispatchers with a declarative Graph Execution Engine.
- Unify dual FSM implementations into a Graph Node State Machine.
- Abstract Agent instantiation into a Component-based dynamic Agent Engine.
- Centralize Sentinel, Adaptive Governance, and Budget Guards into an Adaptive Governance Engine.
- Decouple OpenHands SDK dependencies behind an extensible Execution Engine.

## 5. Files/Components Affected
- `orchestrator/orchestrator.py`
- `orchestrator/pipeline/*`
- `orchestrator/agents/*`
- `orchestrator/control/*`
- `orchestrator/sentinel/*`
- `orchestrator/skills/*`
- `orchestrator/tools/*`
- `orchestrator/llm/*`
- `orchestrator/context/*`

## 6. Interfaces/Contracts
Currently, pipelines implement implicit contracts:
```python
class BasePipeline:
    def run(self, task: str) -> Dict[str, Any]: ...
```
And agents expose:
```python
class BaseAgentFactory:
    @classmethod
    def create(cls, config: OrchestratorConfig, skill_manager: SkillManager, workspace_path: Optional[Path] = None, **kwargs) -> Agent: ...
```
These will be mapped to unified `Component` and `Node` lifecycle protocols in target plans.

## 7. Data Flow
1. User Task String -> CLI/API -> `Orchestrator.run_task()`
2. `OrchestratorDispatcher.dispatch()` instantiates `FSMRuntimeEngine` with profile (e.g. `FullPipelineProfile`).
3. `FSMRuntimeEngine` steps through discrete states (`DEV`, `TEST`, `REVIEW`, `AUDIT`).
4. At each state, `BaseAgentFactory.create()` creates an OpenHands Agent.
5. `OpenHandsExecutionBridge` executes agent turns, intercepted by Sentinel hooks.
6. Execution results update `IterationState` and emit telemetry.

## 8. State Transitions
Current FSM profiles define explicit transitions:
- `DEV` -> `TEST` on code generation
- `TEST` -> `REVIEW` on test success / `TEST` -> `DEV` on test failure
- `REVIEW` -> `AUDIT` on review approval / `REVIEW` -> `DEV` on rejection
- `AUDIT` -> `COMPLETE` on clean audit / `AUDIT` -> `DEV` on issues found

## 9. Error Handling
- Sentinel interceptor catches blocked shell commands.
- Circuit breaker triggers in `orchestrator/control/recovery/circuit_breaker.py` on repeated failures.
- Diagnostic DB (`sentinel_mesh.db`) logs anomalies and recovery strategies.

## 10. Migration Strategy
Preserve existing `Orchestrator.run_task` API as a legacy facade while routing internally to graph workflows during Phase 17.

## 11. Tests
Audit verified existing test suites in `tests/`:
- `tests/test_fsm_engine.py`
- `tests/test_agents.py`
- `tests/test_token_governance.py`
- `tests/test_sentinel_mesh.py`
- `tests/test_audit_pipeline.py`

## 12. Acceptance Criteria
- Complete architectural inventory documented.
- All 254 source modules mapped to functional domains.
- Legacy duplicates identified for deprecation.

## 13. Dependencies
None (baseline audit document).

## 14. Risks
High complexity in backward compatibility if legacy pipeline classes are referenced directly in external consumer scripts.

## 15. Rollback Strategy
Read-only documentation artifact; changes to this plan do not mutate active runtime code.
