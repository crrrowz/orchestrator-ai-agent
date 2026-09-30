# ORAGAI — Programmatic API & Architecture Contract

> **Autonomous Multi-Agent Orchestration & Self-Healing Engineering.**

Complete programmatic API and architecture contract for the **ORAGAI** multi-agent framework.

---

## 1. Primary Entrypoint: `Orchestrator`

```python
from orchestrator import Orchestrator, OrchestratorConfig

config = OrchestratorConfig(
    workspace_path="./my-project",
    max_budget_usd=1.00,
    max_iterations=4,
)
orchestrator = Orchestrator(config)
result = orchestrator.run_task(
    task="Implement user profile service with tests",
    mode="dev-test",  # "dev-test" | "full" | "audit" | "audit-fix" | "docs"
)
print(result["status"])  # "SUCCESS" | "FAILED" | "BUDGET_EXHAUSTED"
```

### Methods
- `run_task(task: str, mode: str = "dev-test", workspace_override: Optional[Path] = None, checkpoint: Optional[PipelineCheckpoint] = None) -> dict`
  Executes the selected pipeline mode on the target workspace directory.

---

## 2. Pipeline Execution Engines (`orchestrator.pipeline`)

### `DevTestLoop` (BasePipeline)
Two-agent TDD iteration engine coordinating Developer and Tester agents.
- **Workflow**: Developer initial code generation -> Static Preflight Check -> Tester test creation -> Execution -> Developer fix loop -> Git task branch commit.
- **Zero-Token Optimization**: Tester LLM bypassed on fix iterations > 1; re-verifies developer fixes directly via `pytest`.

### `FullPipeline` (BasePipeline)
Four-agent architectural pipeline.
- **Workflow**: Architect (`PLAN.md`) -> Approval Gate (Optional) -> Milestone DAG Decomposition -> Developer milestone execution -> Tester -> Reviewer (Independent JSON verdict) -> Optional Review Fix Cycle -> Commit.

### `AuditPipeline` (BasePipeline)
Hybrid static + LLM deep codebase audit engine.
- **Workflow**: Phase 0 Metrics & AST validation -> Graft codebase graph query -> Auditor LLM -> Evidence integrity validation -> Generates `docs/AUDIT_REPORT.md` and `docs/audit_findings.json`.

### `AuditFixPipeline` (BasePipeline)
Git-free continuous self-healing loop.
- **Workflow**: Zero-token Ruff pre-fix -> Static & Pytest inspection -> Structured backlog processing -> Developer targeted remediation -> Strict verification convergence -> Generates `docs/AUDIT_FIX_REPORT.md`.

### `DocumentationPipeline` (BasePipeline)
Autonomous technical authoring engine.
- **Workflow**: Codebase inspection -> Generates/updates `README.md`, `CONTRIBUTING.md`, and `docs/API_REFERENCE.md`.

---

## 3. Cognitive Sentinel & SRE Mesh (`orchestrator.sentinel`)

### `CognitiveSentinelSupervisor` (ICognitiveSentinel)
Singleton digital supervisor intercepting file writes, terminal commands, cloud API calls, and runtime anomalies.
- `intercept_file_write(file_path: Path, content: str) -> Tuple[bool, str, Optional[str]]`
  Validates Python AST before disk write; auto-repairs missing imports or syntax colons.
- `intercept_terminal_command(command: str) -> Tuple[bool, str, str]`
  Translates disallowed UNIX commands on Windows (e.g., `ls` -> `dir`, `cat` -> `type`, `grep` -> `findstr`).
- `handle_runtime_error(exc: Exception, context: dict) -> CognitiveIncident`
  Decodes runtime exceptions and triggers automated failovers.
- `get_dashboard_state() -> SentinelDashboardState`
  Generates telemetry snapshot for terminal UI and SRE radar rendering.

### `ASTGuard`
Offline static Python AST validator checking syntax, docstrings, and disallowing empty stubs in strict mode.

### `SelfHealingEngine` (ISelfHealingEngine)
Provides regex, indentation, and AST-level auto-repair algorithms for common code defects and fuzzy whitespace replacements.

### `SentinelDiagnosticsDB`
Thread-safe SQLite WAL incident database persisting all cognitive incidents, cloud latency metrics, and drift checks.

---

## 4. Control Plane & Token Governance (`orchestrator.control`)

### `DynamicTokenGovernor`
Task-aware iteration token allocation engine separating execution into 4 phases:
- `TokenPhase.INVESTIGATION` (Exploration and file reads)
- `TokenPhase.IMPLEMENTATION` (Code writes and edits)
- `TokenPhase.TESTING` (Pytest and verification)
- `TokenPhase.RESERVE` (Contingency buffer)

Enforces investigation circuit breaker when exploration tokens are burned without code edits.

### `BudgetGuard`
Tracks accumulated spending and token consumption against configured monetary (`max_budget_usd`) and token (`max_tokens_budget`) ceilings.

### `ContextBudgetManager`
Evaluates LLM calls pre-flight, clamps tool observations (`MAX_READ_CHARS = 12,000`), and computes dynamic output budgets.

### `HumanInterventionChannel`
Thread-safe human-in-the-loop communication channel supporting interactive approval gates (`after_architect`, `after_developer`, `before_commit`) and permission escalation requests.

---

## 5. Polyglot Project Adapters (`orchestrator.adapters`)

- `PythonAdapter`: Manages AST syntax checks, Ruff zero-token autofix, pytest test runner, and Python codebase metrics.
- `NodeAdapter`: Manages package.json, npm test, eslint, and JS/TS parsing.
- `GenericAdapter`: Fallback adapter for polyglot and generic repositories.
- `detect_adapter(workspace_path: Path) -> ProjectAdapter`: Automatically selects the best matching adapter for the workspace.

---

## 6. Telemetry & Visualizer (`orchestrator.telemetry`, `orchestrator.ui`)

- `TelemetryRecorder`: Records step metrics, token consumption, Progress Efficiency Ratio (PER), and manages FIFO report pruning.
- `SessionLogStore`: Thread-safe project-partitioned execution log store (`diagnostics/logs/<project_slug>/`).
- `OrchestratorLiveVisualizer`: Real-time streaming status panel showing active agent, role, model, elapsed time, token metrics, and Sentinel SRE radar.
- `InteractiveLogExplorer`: Keyboard-driven collapsible TUI log viewer (`uv run python -m orchestrator.main --logs`).

---

## 7. Domain Models (`orchestrator.domain`)

Pure Pydantic domain models with no framework dependencies.

- `TaskTruthGraph`: Requirement-driven task truth model with `RequirementCategory`, `ImplementationState`, `VerificationState`, `AcceptanceCriterion`, `Requirement`, `TaskMilestone`.
- `EvidenceReference`: Cryptographic evidence references with `EvidenceType` (PYTEST_EXECUTION, AST_PREFLIGHT, LINTER_OUTPUT, SECURITY_AUDIT, DIFF_VERIFICATION, USER_SIGN_OFF).
- `VerifiedAuditFinding` / `FindingDAG`: Structured audit findings with `FindingCategory`, `FindingSeverity`.
- `HandoffEnvelope`: Sealed cross-agent context transfer envelopes with `ContextTier` and `HandoffType`.
- `RecoveryDecision` / `VelocityVector`: 4-D progress velocity tracking for stagnation recovery.

---

## 8. Hexagonal Architecture Ports (`orchestrator.ports`)

### Driving Ports (`orchestrator.ports.driving`)
- `CLIControllerPort`: CLI interaction boundary.
- `FSMTriggerPort`: FSM state transition triggers.
- `LifecycleControllerPort`: Pipeline lifecycle control.
- `WorkstreamDispatchPort`: Workstream dispatch interface.

### Driven Ports (`orchestrator.ports.driven`)
- `AgentRuntimePort`: Agent execution abstraction with `AgentExecutionOutcome`.
- `VCSPort`: Version control system operations.
- `ToolExecutionPort`: Tool execution interface.
- `TelemetryStoragePort`: Telemetry persistence.
- `RollbackControllerPort`: Workspace rollback control.

---

## 9. Governance & FSM (`orchestrator.governance`)

### `GuardedFSMEngine`
State machine with guard predicates for pipeline lifecycle orchestration.
- **Legacy FSM States** (`PipelinePhase`, 12 states): INIT, ARCHITECT, DEVELOP, PREFLIGHT, TEST, FIX, REVIEW, HUMAN_GATE, COMMIT, COMPLETED, FAILED, ABORTED.
- **Guarded FSM States** (`FSMState`, 11 states): INIT, PREFLIGHT, PLANNING, IMPLEMENTATION, VERIFICATION, RESOLUTION, REVIEW, BLOCKED, AMBIGUOUS, COMPLETED, FAILED, ABORTED.
- `CompletionGate`: Verification gate with `verify_mandatory_criteria_satisfied()`.
- `SemanticProgressTracker`: Stagnation detection via `ProgressVelocityMetrics` and `OscillationDetector`.
- `RecoveryOrchestrator` / `StrategyMutator`: Adaptive recovery with mutation strategies (PROMPT_SPECIALIZATION, MILESTONE_SPLITTING, PERSONA_REPLACEMENT, HUMAN_ESCALATION).

---

## 10. Workstreams (`orchestrator.workstreams`)

- `MicroTDDLoop`: Red-Green-Blue TDD cycle with `RedPhaseTestGenerator`, `GreenPhaseDispatcher`, `BluePhaseRefactorEngine`.
- `MilestoneDependencyResolver` / `MilestoneDAGDispatcher`: DAG-based milestone decomposition and dispatch.
- `ContextSynthesizer`: Cross-agent context synthesis with `ASTAwareContextClamper`.
- `StaticAnalysisScanner` / `CHICalculator`: Codebase Health Index computation.
- `ReviewerOutputParser` / `DiffVerifier`: Reviewer verdict parsing and diff verification.

---

## 11. Benchmark Engine (`orchestrator.benchmarks`)

- `BenchmarkRunner`: Ephemeral sandbox provisioning for isolated task evaluation.
- `EmpiricalEvaluator`: Metrics: TCR (Task Completion Rate), FCR (False Completion Rate), RCR (Requirement Coverage Rate), PEI (Process Efficiency Index), PER (Progress Efficiency Ratio), CHI_DELTA.
- `BenchmarkCatalog`: Predefined benchmark task specifications with `BenchmarkSuiteType`, `BenchmarkTaskTier`, `BenchmarkDomain`.

---

## 12. Diagnostics (`orchestrator.diagnostics`)

- `DiagnosticsManager`: Unified dashboard aggregating reports, memory, sentinel, and logs.
  - `get_overview() -> Dict`: Aggregated metrics.
  - `render_dashboard()`: Rich CLI dashboard.
  - `search(query)`: Full-text search across diagnostics.
  - `clean(max_retained_reports, max_retained_memories) -> Dict[str, int]`: FIFO pruning.
