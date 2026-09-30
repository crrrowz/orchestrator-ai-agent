# Plan 99: Incremental Migration Strategy

## 1. Objective
Establish a phased, incremental migration roadmap to transform ORAGAI from its current monolithic, pipeline-oriented architecture into the target Langflow-style engine and component platform without breaking existing CLI commands, tests, or workflows.

## 2. Current Architecture Involved
- All 254 source modules across `orchestrator/`.

## 3. Problem
A "big-bang" rewrite would break existing workflows, disrupt current test suites, and introduce severe instability. The migration must preserve system executability at every intermediate milestone.

## 4. Proposed Phased Migration Roadmap

```text
Phase 0: Foundations & Primitives (Core, Events, Components)
   │
   ▼
Phase 1: Subsystem Abstraction (Models, Tools, Skills, Memory)
   │
   ▼
Phase 2: Governance & Verification Consolidation
   │
   ▼
Phase 3: Execution & Graph Engine Implementation
   │
   ▼
Phase 4: Agent & Pipeline Migration to Declarative Graphs
   │
   ▼
Phase 5: Plugin Engine & Visual Studio UI Layer
   │
   ▼
Phase 6: Legacy Deprecation & Cleanup
```

---

### Phase 0: Foundations & Primitives (Core, Events, Component Model)
- **Current State**: Hardcoded initialization in `orchestrator.py`, scattered constants, direct coupling.
- **Target State**: `CoreEngine` runtime container, `EventEngine` async pub/sub bus, `IComponent` and `PortDefinition` base models.
- **Files Affected**:
  - `orchestrator/core/` -> create `orchestrator/engines/core/`, `orchestrator/engines/events/`
  - `orchestrator/core/component.py`
- **Dependencies**: None.
- **Migration Steps**:
  1. Implement `orchestrator/core/component.py` with `ComponentSchema` and `PortDefinition`.
  2. Implement `orchestrator/engines/events/bus.py` with async pub/sub.
  3. Implement `CoreEngine` bootstrap container.
- **Compatibility Strategy**: Legacy code continues to run; `EventEngine` operates in background mode.
- **Tests**: Core DI container tests, Event bus throughput tests, Component schema validation tests.
- **Rollback Strategy**: Revert new core files; legacy imports remain intact.
- **Completion Criteria**: Core container and Event bus pass 100% unit tests.

---

### Phase 1: Subsystem Abstraction (Models, Tools, Skills, Memory)
- **Current State**: Tight coupling to OpenHands SDK tools, hardcoded LLM managers, plain folder skill loaders.
- **Target State**: `ModelEngine`, `ToolEngine`, `SkillEngine`, `MemoryEngine` operating as independent components.
- **Files Affected**:
  - `orchestrator/llm/` -> `orchestrator/engines/models/`
  - `orchestrator/tools/` -> `orchestrator/engines/tools/`
  - `orchestrator/skills/` -> `orchestrator/engines/skills/`
  - `orchestrator/memory/` -> `orchestrator/engines/memory/`
- **Dependencies**: Phase 0.
- **Migration Steps**:
  1. Implement `ModelEngine` with provider adapters (OpenAI, Anthropic, Google, Local).
  2. Implement `ToolEngine` with AST security sandboxing and JSON Schema generators.
  3. Implement `SkillEngine` supporting `skill.yaml` and legacy `SKILL.md`.
  4. Implement `MemoryEngine` with multi-tiered scoping.
  5. Add backward-compatibility facade shims in `orchestrator/llm/manager.py`, `orchestrator/tools/workspace_tools.py`, and `orchestrator/skills/manager.py`.
- **Compatibility Strategy**: Existing factories call the new engines under the hood.
- **Tests**: Provider completion tests, sandboxed tool execution tests, skill compressor tests, memory retrieval tests.
- **Rollback Strategy**: Re-point facade shims back to original implementations.
- **Completion Criteria**: All legacy tests in `tests/test_tools.md`, `tests/test_skills.md`, `tests/test_adapters.md` pass without modification.

---

### Phase 2: Governance & Verification Consolidation
- **Current State**: Governance split between `control/`, `governance/`, and `sentinel/`. Verification split between `ci/` and `analysis/audit/`.
- **Target State**: Consolidated `GovernanceEngine` (deterministic metrics, budget, stagnation, AST guards) and `VerificationEngine` (evidence gates, PyTest/Audit verifiers).
- **Files Affected**:
  - `orchestrator/control/`, `orchestrator/governance/`, `orchestrator/sentinel/` -> `orchestrator/engines/governance/`
  - `orchestrator/ci/`, `orchestrator/analysis/audit/` -> `orchestrator/engines/verification/`
- **Dependencies**: Phase 1.
- **Migration Steps**:
  1. Consolidate token governance, stagnation detectors, and AST guards into `GovernanceEngine`.
  2. Unify CI evidence gates, PyTest parsers, and audit scanners into `VerificationEngine`.
  3. Maintain `SentinelSupervisor` facade delegating to `GovernanceEngine`.
- **Compatibility Strategy**: Expose original function signatures via module aliasing.
- **Tests**: Stagnation velocity tests, token ceiling tests, evidence gate tests, security audit scanner tests.
- **Rollback Strategy**: Restore legacy control/sentinel modules from backup branches.
- **Completion Criteria**: `tests/test_sentinel_mesh.py` and `tests/test_token_governance.py` pass cleanly.

---

### Phase 3: Execution & Graph Engine Implementation
- **Current State**: Pipelines loop through hardcoded state steps in Python.
- **Target State**: `ExecutionEngine` managing agent turns; `GraphEngine` compiling and running DAG/cyclic workflow graphs.
- **Files Affected**:
  - `orchestrator/engines/execution/`
  - `orchestrator/engines/graph/`
  - `orchestrator/engines/tasks/`
- **Dependencies**: Phase 2.
- **Migration Steps**:
  1. Implement `ExecutionEngine` turn loop and OpenHands runtime bridge.
  2. Implement `TaskEngine` for milestone DAG decomposition.
  3. Implement `GraphEngine` (compiler, scheduler, conditional edge evaluator, checkpointing).
- **Compatibility Strategy**: Graph engine runs alongside legacy FSM engine for benchmarking.
- **Tests**: Graph execution DAG tests, cyclic retry convergence tests, execution checkpoint recovery tests.
- **Rollback Strategy**: Keep `FSMRuntimeEngine` as the default execution driver.
- **Completion Criteria**: Graph Engine executes complex multi-node workflows with verified deterministic output.

---

### Phase 4: Agent & Pipeline Migration to Declarative Graphs
- **Current State**: Python agent classes (`DeveloperAgentFactory`), hardcoded pipelines (`DevTestLoop`, `FullPipeline`).
- **Target State**: Declarative Agent YAML blueprints; standard pipelines expressed as declarative Graph JSON templates.
- **Files Affected**:
  - `orchestrator/engines/agents/`
  - `orchestrator/engines/graph/workflows/*.json`
  - `orchestrator/pipeline/dispatcher.py`
  - `orchestrator/orchestrator.py`
- **Dependencies**: Phase 3.
- **Migration Steps**:
  1. Author YAML blueprints for Developer, Tester, Reviewer, Architect, Auditor, Documentation agents.
  2. Author graph workflow definitions for `dev-test`, `full`, `audit`, `audit-fix`, `docs`.
  3. Update `OrchestratorDispatcher` to compile and run declarative graphs.
  4. Update `Orchestrator.run_task()` to dispatch via `GraphEngine`.
- **Compatibility Strategy**: `Orchestrator.run_task(mode="dev-test")` transparently executes `workflows/dev-test.json`.
- **Tests**: End-to-end regression tests across all 5 operational modes.
- **Rollback Strategy**: Set `USE_LEGACY_FSM=true` environment flag to route through legacy `FSMRuntimeEngine`.
- **Completion Criteria**: 100% of existing CLI commands (`oragai run`, `oragai audit`, etc.) function identically using graph execution.

---

### Phase 5: Plugin Engine & Visual Studio UI Layer
- **Current State**: CLI only; no third-party plugin loading or visual builder.
- **Target State**: `PluginEngine` loading external plugins; FastAPI backend and React Flow visual builder UI.
- **Files Affected**:
  - `orchestrator/engines/plugins/`
  - `orchestrator/ui/`
  - `orchestrator/cli/app.py` (add `oragai serve` command)
- **Dependencies**: Phase 4.
- **Migration Steps**:
  1. Implement `PluginEngine` with `plugin.yaml` scanner and loader.
  2. Implement FastAPI server exposing graph, component, and WebSocket event APIs.
  3. Connect visual studio frontend canvas to backend REST/WebSocket endpoints.
- **Compatibility Strategy**: UI is completely additive; CLI remains 100% autonomous and unaffected.
- **Tests**: Plugin hot-reload tests, REST API schema tests, WebSocket live event streaming tests.
- **Rollback Strategy**: Disable `oragai serve` command.
- **Completion Criteria**: Visual Studio loads, edits, runs, and monitors workflows in real time.

---

### Phase 6: Legacy Deprecation & Cleanup
- **Current State**: Dual implementations and backward compatibility shims.
- **Target State**: Clean, unified engine architecture with deprecated code removed.
- **Files Affected**:
  - Deprecate and remove `orchestrator/pipeline/state_machine.py` (legacy).
  - Clean up obsolete shims after 2 minor release cycles.
- **Dependencies**: Phase 5.
- **Migration Steps**:
  1. Add deprecation warnings to legacy module imports.
  2. Verify zero internal references to deprecated modules.
  3. Archive legacy implementations.
- **Compatibility Strategy**: Provide migration guide for external consumers.
- **Tests**: Full repository test suite execution and linting verification.
- **Rollback Strategy**: Revert deprecation commit from git history.
- **Completion Criteria**: Zero legacy duplicate code; 100% test coverage on engine architecture.

---

## 5. Files/Components Affected
All subsystems across `orchestrator/`.

## 6. Interfaces/Contracts
Strict adherence to `IComponent`, `IEngine`, `IGraphEngine`, and `IEventEngine`.

## 7. Data Flow
Progressive transition from linear call stacks to event-driven graph execution.

## 8. State Transitions
`PHASE_0 -> PHASE_1 -> PHASE_2 -> PHASE_3 -> PHASE_4 -> PHASE_5 -> PHASE_6`.

## 9. Error Handling
Feature-flagged fallback shims at every phase boundary to allow instant rollback in production.

## 10. Migration Strategy
As detailed in the 6 phases above.

## 11. Tests
Full end-to-end integration and benchmark suites executed after each phase.

## 12. Acceptance Criteria
- Zero downtime or workflow disruption during all 6 migration phases.
- 100% backward compatibility with existing CLI flags, configs, and `.env` variables.

## 13. Dependencies
Covers the entire transformation sequence.

## 14. Risks
Long migration duration causing merge conflicts; mitigated by keeping phases modular and committing verified engine milestones independently.

## 15. Rollback Strategy
Global feature-flag routing (`ORAGAI_LEGACY_MODE=1`) allowing fallback to original orchestration paths.
