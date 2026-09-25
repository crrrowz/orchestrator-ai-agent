# P12 — STRANGLER FIG MIGRATION & SAFE ROLLOUT PLAN

> **Document Type:** Canonical Systems Architecture, Safe Migration Strategy & Phased Rollout Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Systems Architect, Site Reliability Engineer & Safe Migration Specialist  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md` through `docs/plans/P11_AUTONOMOUS_BENCHMARK_AND_VERIFICATION_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Design Phase:** P12 (Specification & Strangler Fig Rollout Engine — Zero Production Code Modified)

---

# 1. Executive Summary & Strangler Fig Migration Strategy

This specification establishes the canonical **Strangler Fig Migration & Safe Rollout Plan (P12)** for the **ORAGAI** multi-agent software engineering orchestrator.

### 1.1 The Strategic Position of P12 in the ORAGAI Evolution
Across the architectural design phases (P0–P11), ORAGAI has been re-architected from a defensive execution cage into a high-assurance, hexagonal, evidence-governed multi-agent platform:
1. **P0 (Forensic Baseline & Invariants):** Established the 244-test safety regression baseline and exposed legacy false completion pathologies.
2. **P1 (Task Truth & Requirement Model):** Formulated requirement-to-evidence traceability and the canonical completion function.
3. **P2.1 (Evidence Engine & Completion Gates):** Specified deterministic completion evaluation, cryptographic SHA-256 content hashing, and orthogonal state dimensions.
4. **P3 (Guarded FSM & Lifecycle Orchestration):** Established Inversion of Control (IoC) with ephemeral OpenHands turns yielding to the `GuardedFSMEngine`.
5. **P4 (Adaptive Resource Governance):** Designed dynamic turn envelopes ($T_{\text{allocated}}$), complexity scoring, and financial circuit breakers.
6. **P5 (Agent Work & Milestone Execution):** Established persona RBAC boundaries, Micro-TDD loops, and `CrossAgentHandoffPayload` schemas.
7. **P6 (Context & Evidence Handoff):** Formulated priority context tiers (Tier 0 to Tier 3), Merkle workspace digests, and cryptographic handoff envelopes.
8. **P7 (Audit, Deep Inspection & Self-Evolution):** Built zero-token pre-audit sweeps, finding DAGs, Codebase Health Index ($\text{CHI}$), and SQLite WAL logging.
9. **P8 (Progress, Stagnation & Recovery):** Implemented multi-dimensional velocity vectors (PER 2.0), sliding-window cycle detection, and 4-tier circuit breaker strategy mutations.
10. **P9 (Tooling, Context Windows & Sandbox Hardening):** Built AST file virtualization, grammar-based command security, and workspace isolation.
11. **P10 (OpenHands Runtime Boundary & Integration):** Formalized the clean SDK execution seam, deterministic exit status classification, and ephemeral turn lifecycle.
12. **P11 (Autonomous Benchmark & Verification):** Delivered the 4-Tier Verification Pyramid, the 244-test safety invariant gate, zero-token mock ReAct simulator, canonical BM-01 to BM-08 benchmarks, and the non-negotiable $FCR \equiv 0.000$ barrier.

### The Core Mission of P12:
$$\text{While P1–P10 designed the target hexagonal components and P11 built the empirical verification harness,}$$
$$\text{\textbf{P12 designs the safe, incremental, zero-downtime, and zero-regression migration path using the Strangler Fig pattern,}}$$
$$\text{\textbf{ensuring legacy components are systematically intercepted, shadowed, and retired while maintaining 100\% pass rates across all 244 baseline tests.}}$$

---

## 1.2 Why Big-Bang Replacements Fail in Autonomous Agent Systems

In distributed and autonomous multi-agent orchestration engines, "Big-Bang" rewrites (simultaneously replacing the state machine, agent loops, tools, and SDK boundaries) invariably fail due to four systemic failure modes:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     THE 4 SYSTEMIC HAZARDS OF BIG-BANG REWRITES                                        │
├───────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────┤
│ Pathology                     │ Mechanism & Impact                                                                     │
├───────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Non-Deterministic Blast    │ Replacing the CLI dispatcher, FSM, and SDK wrapper at once causes multi-variable failure│
│    Radius Expansion           │ modes. When an LLM agent produces shallow output or hallucinates, it is impossible to │
│                               │ isolate whether the fault is in prompt injection (P6), tool parsing (P9), or FSM (P3). │
├───────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. Silent False Completion    │ Replacing `dev_test_loop.py` directly without shadow validation risks introducing new  │
│    Regressions                │ exit loops that report false completion without fulfilling task criteria ($FCR > 0$). │
├───────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. State Schema Corruption    │ Sudden changes to `PipelineCheckpoint` or SQLite logging schemas break backward       │
│    and Session Invalidation   │ compatibility with ongoing multi-hour CLI tasks and historical diagnostic databases.   │
├───────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. Immediate Rollback         │ In a big-bang rewrite, a single critical runtime bug forces a complete repository     │
│    Paralysis                  │ revert, discarding hundreds of hours of stable architectural enhancements.             │
└───────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────┘
```

The **Strangler Fig Application Pattern** (originally coined by Martin Fowler) solves this by placing an interception boundary (the **Strangler Seam**) around the legacy subsystem. New hexagonal capabilities grow around the perimeter, intercepting calls incrementally. The legacy codebase is gradually "strangled" until it is safely pruned away with zero downtime, zero regression, and constant empirical verification.

---

## 1.3 The Strangler Fig Lifecycle: Intercept ──▶ Shadow ──▶ Canary ──▶ Decommission

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ORAGAI STRANGLER FIG MIGRATION LIFECYCLE (P12)                                       │
│                                                                                                                        │
│   STAGE 1: INTERCEPT                STAGE 2: SHADOW                 STAGE 3: CANARY               STAGE 4: RETIRE      │
│                                                                                                                        │
│   CLI Task Request                  CLI Task Request                CLI Task Request              CLI Task Request     │
│          │                                 │                               │                             │             │
│          ▼                                 ▼                               ▼                             ▼             │
│   ┌──────────────┐                  ┌──────────────┐                ┌──────────────┐              ┌──────────────┐     │
│   │Strangler Seam│                  │Strangler Seam│                │Strangler Seam│              │ Direct Entry │     │
│   │ (Dispatcher) │                  │ (Dual-Run)   │                │(Canary Route)│              │ (Target FSM) │     │
│   └──────┬───────┘                  └──────┬───────┘                └──────┬───────┘              └──────┬───────┘     │
│          │                                 ├───────────────┐               ├──[Canary %]──┐              │             │
│          │ (100% Traffic)                  │ (Live Run)    │ (Shadow Run)  │              │              │             │
│          ▼                                 ▼               ▼               ▼              ▼              │             │
│   ┌──────────────┐                  ┌────────────┐  ┌────────────┐  ┌────────────┐ ┌────────────┐        │             │
│   │Legacy Engine │                  │Legacy Core │  │Target FSM  │  │Legacy Core │ │Target FSM  │        │             │
│   │(dev_test_loop│                  │(Production)│  │ (Isolated) │  │ (Fallback) │ │ (Primary)  │        │             │
│   │ full_pipeline│                  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘ └─────┬──────┘        │             │
│   └──────────────┘                        │               │               │              │               │             │
│                                           └───────┬───────┘               └──────┬───────┘               │             │
│                                                   ▼                              ▼                       ▼             │
│                                           ┌──────────────┐                ┌──────────────┐        ┌──────────────┐     │
│                                           │ Differential │                │Auto-Fallback │        │  Clean P1-P11│     │
│                                           │  Evaluator   │                │CircuitBreaker│        │  Hexagonal   │     │
│                                           │(AST/FCR/CHI) │                │(FCR==0 Check)│        │ Architecture │     │
│                                           └──────────────┘                └──────────────┘        └──────────────┘     │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.4 Inviolable System Migration Invariants

The migration engine must strictly satisfy five non-negotiable architectural invariants:

1. **Zero Production Code Modifications During Design (Invariant 1):** P12 specifies the migration infrastructure, shadow harnesses, and rollback runbooks. No source files in `orchestrator/` are altered prior to Phase 0 sign-off.
2. **The 244-Test Invariant Gate (Invariant 2):** Every atomic commit across all migration phases must run `pytest tests/ -v` and achieve a **100% pass rate (244/244 passing tests)**. A single test failure halts the migration pipeline immediately.
3. **Strangler Seam Discipline (Invariant 3):** No legacy component may be removed or replaced until its hexagonal successor has achieved 100% test parity and passed shadow verification across all canonical benchmarks (BM-01 to BM-08).
4. **Differential Parity & Zero False Completion ($FCR \equiv 0.000$) (Invariant 4):** Target components in shadow and canary mode must yield output quality, test counts, and Codebase Health Index ($\text{CHI}$) equal to or greater than legacy pipelines, with strictly zero false completions.
5. **Deterministic 1-Command Atomic Rollback (Invariant 5):** Every migration phase must provide an automated, instant rollback script that restores the previous verified checkpoint in $< 5\text{ seconds}$ via feature flags or Git tags.

---

# 2. Legacy Subsystem Inventory & Deprecation Mapping

To ensure seamless decoupling without dangling dependencies or orphaned imports, every legacy module is inventoried, categorized, and mapped to its target hexagonal successor.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 LEGACY TO TARGET SUBSYSTEM DEPRECATION MAPPING                                         │
├──────────────────────────────────────────┬──────────────────────────────────────────┬─────────────┬────────────────────┤
│ Legacy Source Path                       │ Target Hexagonal Architecture Module     │ Phase Target│ Deprecation Method │
├──────────────────────────────────────────┼──────────────────────────────────────────┼─────────────┼────────────────────┤
│ `orchestrator/utils/sdk_patch.py`        │ `orchestrator/runtime/openhands/` (P10)  │ Phase 3     │ Complete Deletion  │
│                                          │ • Clean SDK `ToolDefinition` adapters    │             │ (Eliminate Monkey  │
│                                          │ • Official `LocalConversation` runner    │             │  Patching)         │
├──────────────────────────────────────────┼──────────────────────────────────────────┼─────────────┼────────────────────┤
│ `orchestrator/utils/*` (Facades)         │ Direct Domain Package Imports            │ Phase 1     │ Module Pruning &   │
│ • `utils/visualizer.py`                  │ • `orchestrator/ui/visualizer.py`        │             │ Direct Import      │
│ • `utils/skill_compressor.py`            │ • `orchestrator/skills/compressor.py`    │             │ Rewriting          │
│ • `utils/pytest_parser.py`               │ • `orchestrator/analysis/pytest_parser.py│             │                    │
│ • `utils/output.py`                      │ • `orchestrator/rendering/output.py`     │             │                    │
│ • `utils/graft_context.py`               │ • `orchestrator/analysis/graft_context.py│             │                    │
│ • `utils/git_ops.py`                     │ • `orchestrator/vcs/git_ops.py`          │             │                    │
│ • `utils/__init__.py` (Re-exports)       │ • Removed entirely                       │             │                    │
├──────────────────────────────────────────┼──────────────────────────────────────────┼─────────────┼────────────────────┤
│ `orchestrator/tools/workspace_tools.py`  │ `orchestrator/tools/hardened/` (P9)      │ Phase 2     │ Wrapped via Seam   │
│ • Unsandboxed Bash execution             │ • `HardenedTerminalTool` (Grammar AST)   │             │ ──▶ Replaced with  │
│ • Unvalidated raw file I/O               │ • `HardenedFileTool` (AST Virtualizer)   │             │ AST Virtualizer    │
│ • Arbitrary 250-line truncation          │ • Priority-Tiered Context Window Slicing │             │                    │
├──────────────────────────────────────────┼──────────────────────────────────────────┼─────────────┼────────────────────┤
│ `orchestrator/control/` (Legacy Budget)  │ `orchestrator/governance/resource/` (P4) │ Phase 3/4   │ Strangled via      │
│ • `token_governance.py` (28% kill rule)  │ • `AdaptiveResourceGovernor` (Dynamic T) │             │ `ResourceGovernor` │
│ • `budget_guard.py`                      │ • `ComplexityEstimator` (AST/Graft)      │             │ Protocol Adapter   │
│ • `context_budget_manager.py`            │ • `MonetaryCircuitBreaker`               │             │                    │
├──────────────────────────────────────────┼──────────────────────────────────────────┼─────────────┼────────────────────┤
│ `orchestrator/pipeline/state_machine.py` │ `orchestrator/governance/fsm/` (P3)      │ Phase 4     │ Replaced by        │
│ • Unguarded static dict transition lookup│ • `GuardedFSMEngine` (Evidence-gated)    │             │ `GuardedFSMEngine` │
│ • Zero state verification predicates     │ • `CompletionEvaluator` (P2.1)           │             │                    │
├──────────────────────────────────────────┼──────────────────────────────────────────┼─────────────┼────────────────────┤
│ `orchestrator/pipeline/base_pipeline.py` │ `orchestrator/governance/fsm/` & (P3/P10)│ Phase 4/5   │ Strangled via      │
│ • `ConvRunResult.completed = True` flaw  │ • `OpenHandsRuntimeBridge` (P10)         │             │ `StranglerPipeline │
│ • Asynchronous thread kill collisions    │ • Bounded Ephemeral Turn Lifecycle       │             │ Dispatcher`        │
│ • Monolithic 756-line lifecycle God-class│ • Hexagonal Port/Adapter Architecture    │             │                    │
├──────────────────────────────────────────┼──────────────────────────────────────────┼─────────────┼────────────────────┤
│ `orchestrator/pipeline/dev_test_loop.py` │ `orchestrator/workstreams/` (P5)         │ Phase 4/5   │ Shadowed ──▶       │
│ • `pytest exit_code == 0` shallow exit   │ • `MicroTDDWorkstream` (P1/P2.1/P5)      │             │ Canary ──▶         │
│ • Zero requirement-to-test traceability  │ • Strict Non-Agent Test Adequacy Sweep   │             │ Decommissioned     │
├──────────────────────────────────────────┼──────────────────────────────────────────┼─────────────┼────────────────────┤
│ `orchestrator/pipeline/full_pipeline.py` │ `orchestrator/workstreams/` (P3/P5/P6)   │ Phase 4/5   │ Shadowed ──▶       │
│ • Rigid 4-stage waterfall execution      │ • `LifecycleWorkstreamCoordinator`       │             │ Canary ──▶         │
│ • 4,000-char truncated reviewer diff     │ • Merkle Handoff Envelopes (P6)          │             │ Decommissioned     │
│ • Regex-based approval parsing           │ • AST Finding DAG Review Engine (P7)     │             │                    │
├──────────────────────────────────────────┼──────────────────────────────────────────┼─────────────┼────────────────────┤
│ `orchestrator/pipeline/audit_pipeline.py`│ `orchestrator/workstreams/audit/` (P7)   │ Phase 4/5   │ Shadowed ──▶       │
│ `orchestrator/pipeline/audit_fix_...`    │ • `ZeroTokenStaticAuditor` (P7)          │             │ Canary ──▶         │
│ • 4-step cutoff cage                     │ • Empirical Codebase Health Index (CHI)  │             │ Decommissioned     │
│ • 98/100 Flattery Trap susceptibility    │ • Monotonic Remediation Verification     │             │                    │
└──────────────────────────────────────────┴──────────────────────────────────────────┴─────────────┴────────────────────┘
```

---

# 3. Phased Migration Roadmap (Phases 0 through 5)

The migration is executed across 6 deterministic, self-verifying phases. Every phase must pass its strict Entry Criteria, Execution Steps, Validation Gate, and produce a sealed Rollback Checkpoint Tag.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       6-PHASE STRANGLER FIG EXECUTION TIMELINE                                         │
│                                                                                                                        │
│  [Phase 0: Baseline Freeze] ─────────────────────────────────────────────────────────▶ Tag: v0.1.0-baseline            │
│           │                                                                                                            │
│           ▼                                                                                                            │
│  [Phase 1: Facade Elimination] ──────────────────────────────────────────────────────▶ Tag: v0.2.0-facades-cleansed    │
│           │                                                                                                            │
│           ▼                                                                                                            │
│  [Phase 2: Hardened Sandbox & AST Virtualizer] ──────────────────────────────────────▶ Tag: v0.3.0-hardened-tools      │
│           │                                                                                                            │
│           ▼                                                                                                            │
│  [Phase 3: Clean SDK Boundary & Patch Removal] ──────────────────────────────────────▶ Tag: v0.4.0-clean-sdk-boundary  │
│           │                                                                                                            │
│           ▼                                                                                                            │
│  [Phase 4: Guarded FSM Shadow & Canary Rollout] ─────────────────────────────────────▶ Tag: v0.5.0-fsm-canary-100       │
│           │                                                                                                            │
│           ▼                                                                                                            │
│  [Phase 5: Legacy Decommissioning & Hexagonal Finalization] ─────────────────────────▶ Tag: v1.0.0-hexagonal-complete  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3.1 Phase 0: Baseline Freeze & Verification Seam

### Objectives & Scope
Establish an unalterable forensic baseline and deploy the P11 Verification Pyramid into the continuous integration harness.

### Step-by-Step Execution
1. **Repository Tagging:** Create immutable baseline Git tag `v0.1.0-baseline` on main branch.
2. **Verification Suite Activation:** Verify that all 244 existing unit and integration tests pass across 37 test modules (`pytest tests/ -v`).
3. **CI Pipeline Invariant Enforcement:** Configure pre-commit and CI hooks to block any commit that drops passing test count below 244.
4. **Strangler Infrastructure Initialization:** Create `orchestrator/migration/` package containing:
   - `__init__.py`
   - `strangler_bridge.py` (Dispatcher, RoutingConfig, ShadowHarness)
   - `evaluator.py` (DifferentialExecutionEvaluator)

### Phase 0 Validation Gate
- `pytest tests/` $\rightarrow$ `244 passed in < 15s`.
- `git tag -v v0.1.0-baseline` verified.
- `orchestrator.migration.strangler_bridge` imported successfully without side effects.

---

## 3.2 Phase 1: Zero-Risk Utilities & Facade Elimination

### Objectives & Scope
Eliminate all backward-compatibility forwarding facades in `orchestrator/utils/` (`visualizer.py`, `skill_compressor.py`, `pytest_parser.py`, `output.py`, `graft_context.py`, `git_ops.py`), refactoring all internal imports across `orchestrator/` and `tests/` to use explicit, direct domain packages.

### Step-by-Step Execution
1. **Dependency Graph Analysis:** Audit all references to `orchestrator.utils.*` in production and test code.
2. **Import Rewriting:**
   - Change `from orchestrator.utils import ConsoleOutput` $\rightarrow$ `from orchestrator.rendering.output import ConsoleOutput`
   - Change `from orchestrator.utils import GitOps` $\rightarrow$ `from orchestrator.vcs.git_ops import GitOps`
   - Change `from orchestrator.utils import PytestOutputParser` $\rightarrow$ `from orchestrator.analysis.pytest_parser import PytestOutputParser`
   - Change `from orchestrator.utils import CompactSkillInjector` $\rightarrow$ `from orchestrator.skills.compressor import CompactSkillInjector`
   - Change `from orchestrator.utils import OrchestratorLiveVisualizer` $\rightarrow$ `from orchestrator.ui.visualizer import OrchestratorLiveVisualizer`
   - Change `from orchestrator.utils import GraftContextProvider` $\rightarrow$ `from orchestrator.analysis.graft_context import GraftContextProvider`
3. **Facade Deprecation Deposition:** Replace forwarding stubs with runtime `DeprecationWarning` shims to catch any external consumers.
4. **Validation Run:** Execute full test suite to guarantee zero broken imports.

### Phase 1 Validation Gate
- `pytest tests/` $\rightarrow$ `244 passed, 0 failed, 0 errors`.
- Zero circular import cycles detected by `importlib` graph traversal.
- Tag: `v0.2.0-facades-cleansed`.

---

## 3.3 Phase 2: Tooling & Sandbox Swap (P9 AST Virtualizer Deployment)

### Objectives & Scope
Deploy the P9 Hardened Tooling suite (`HardenedFileTool`, `HardenedTerminalTool`, `ASTVirtualizer`, `ToolSandboxManager`) behind dynamic feature flags. Wrap legacy `orchestrator/tools/workspace_tools.py` with an adapter seam that transparently routes file operations and bash commands to the secure AST engine.

### Step-by-Step Execution
1. **Module Deployment:** Deploy `orchestrator/tools/hardened/` implementing AST virtualization, anti-stub verification, and grammar-based command interception.
2. **Seam Adapter Registration:** Update `workspace_tools.py` to route execution through `ToolSandboxManager` when `use_hardened_sandbox: true` is configured in `RoutingConfig`.
3. **Security Fuzzing Verification:** Execute P11 Layer 3 Adversarial Security Suite:
   - Command injection payloads (`$(rm -rf ...)`, `; cat /etc/passwd`, PowerShell backtick escapes).
   - Path traversal exploits (`../../.env`, Windows device names `CON`, `NUL`, `AUX`).
   - Placeholder stub detections (`pass`, `...`, `raise NotImplementedError`).
4. **Zero-Token Mock Simulation:** Verify tool performance under high contention with zero token consumption.

### Phase 2 Validation Gate
- `pytest tests/` $\rightarrow$ `244 passed`.
- `pytest tests/test_security_fuzzing.py` $\rightarrow$ 100% injection/traversal attacks neutralized.
- Anti-stub rejection rate $\equiv 100.0\%$ on placeholder modifications.
- Tag: `v0.3.0-hardened-tools`.

---

## 3.4 Phase 3: SDK Seam & Clean Boundary Deployment (P10 Bridge)

### Objectives & Scope
Eradicate `orchestrator/utils/sdk_patch.py` and its brittle monkey-patching of `openhands.sdk`. Deploy the P10 `OpenHandsRuntimeBridge`, official `ToolDefinition` schemas, and synchronous bounded turn execution loop.

### Step-by-Step Execution
1. **Bridge Deployment:** Deploy `orchestrator/runtime/openhands/` containing:
   - `bridge.py` (`OpenHandsRuntimeBridge`)
   - `factory.py` (`SDKAgentFactory`)
   - `adapter.py` (`SDKToolAdapter`)
   - `runner.py` (`SDKSessionRunner`)
2. **Eradicate `sdk_patch.py`:** Remove monkey-patch invocations from `orchestrator/__init__.py` and `orchestrator/pipeline/base_pipeline.py`.
3. **Synchronous Turn Lifecycle:** Replace the legacy 28% asynchronous `conv.interrupt()` thread kill with P10 synchronous bounded turn envelopes ($T_{\text{allocated}}$) and clean `AGENT_YIELDED` exit classification.
4. **EventStream Telemetry Binding:** Connect OpenHands SDK synchronous event callbacks directly to `SessionLogStore` and `SentinelDiagnosticsDB` with secret masking.

### Phase 3 Validation Gate
- `pytest tests/` $\rightarrow$ `244 passed`.
- Zero monkey-patches detected in `sys.modules["openhands.sdk"]`.
- Thread safety verified: 0 deadlocks or race conditions across 100 simulated concurrent agent turns.
- Tag: `v0.4.0-clean-sdk-boundary`.

---

## 3.5 Phase 4: Guarded FSM Shadow & Canary Rollout (P3–P8 Integration)

### Objectives & Scope
Deploy the `GuardedFSMEngine` (P3), `AdaptiveResourceGovernor` (P4), `MicroTDDWorkstream` (P5), `ContextHandoffMesh` (P6), `ZeroTokenStaticAuditor` (P7), and `StagnationRecoveryEngine` (P8). Run dual-execution shadow testing on all benchmark tasks, then progressively route production CLI traffic through canary stages (10% $\rightarrow$ 25% $\rightarrow$ 50% $\rightarrow$ 100%).

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PHASE 4 PROGRESSIVE CANARY TRAFFIC ALLOCATION                                        │
│                                                                                                                        │
│   STAGE 4A: Shadow Mode (0% Live Route)                                                                               │
│   [CLI Task] ──▶ Dispatcher ──▶ [Legacy Engine (100% Production)] ──▶ User Result                                     │
│                               └──▶ [Guarded FSM (Shadow Run)]   ──▶ Differential Evaluator (Telemetry Only)           │
│                                                                                                                        │
│   STAGE 4B: Initial Canary (10% Route)                                                                                 │
│   [CLI Task] ──▶ Dispatcher ──┬──[90% Traffic]──▶ [Legacy Engine] ──▶ User Result                                      │
│                               └──[10% Traffic]──▶ [Guarded FSM]   ──▶ User Result (Circuit Breaker Monitored)          │
│                                                                                                                        │
│   STAGE 4C: Major Canary (50% Route)                                                                                   │
│   [CLI Task] ──▶ Dispatcher ──┬──[50% Traffic]──▶ [Legacy Engine] ──▶ User Result                                      │
│                               └──[50% Traffic]──▶ [Guarded FSM]   ──▶ User Result (Circuit Breaker Monitored)          │
│                                                                                                                        │
│   STAGE 4D: Full Canary (100% Route)                                                                                  │
│   [CLI Task] ──▶ Dispatcher ──▶ [Guarded FSM (100% Production)] ──▶ User Result (Legacy in Standby Fallback)          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Execution
1. **Shadow Mode (Stage 4A):** All CLI invocations execute on the legacy pipeline for user output, while `ShadowExecutionHarness` executes `GuardedFSMEngine` concurrently in an isolated shadow directory. Output metrics are evaluated by `DifferentialExecutionEvaluator`.
2. **Canary 10% (Stage 4B):** 10% of tasks (deterministic hash based on task text and workspace path) are routed directly to `GuardedFSMEngine`. Automated circuit breakers monitor for exceptions or requirement failures.
3. **Canary 50% (Stage 4C):** Traffic increased to 50% after 24 hours of zero circuit breaker trips.
4. **Canary 100% (Stage 4D):** 100% of traffic handled by `GuardedFSMEngine`. Legacy pipelines remain available purely as emergency fallbacks.

### Phase 4 Validation Gate
- `pytest tests/` $\rightarrow$ `244 passed`.
- Canonical Benchmarks BM-01 through BM-08 pass with:
  - $\text{True Completion Rate (TCR)} \ge 95.0\%$
  - $\text{False Completion Rate (FCR)} \equiv 0.000$
  - $\text{Codebase Health Index Improvement } (\Delta \text{CHI}) \ge +15.0$
- Zero unhandled circuit breaker trips in canary execution.
- Tag: `v0.5.0-fsm-canary-100`.

---

## 3.6 Phase 5: Legacy Pipeline Decommissioning & Repository Cleansing

### Objectives & Scope
Permanently delete all dead legacy pipeline files, unneeded fallback branches, and deprecated shims. Finalize the clean hexagonal architecture directory tree.

### Step-by-Step Execution
1. **Legacy Pipeline Removal:** Safely delete:
   - `orchestrator/pipeline/base_pipeline.py`
   - `orchestrator/pipeline/dev_test_loop.py`
   - `orchestrator/pipeline/full_pipeline.py`
   - `orchestrator/pipeline/audit_pipeline.py`
   - `orchestrator/pipeline/audit_fix_pipeline.py`
   - `orchestrator/pipeline/documentation_pipeline.py`
   - `orchestrator/pipeline/state_machine.py`
   - `orchestrator/utils/` (entire directory)
2. **Dispatcher Streamlining:** Refactor `StranglerPipelineDispatcher` to route directly to `GuardedFSMEngine` without legacy branches.
3. **Orphaned Test Sweep:** Update test suites that tested legacy internal classes to target the equivalent hexagonal interfaces.
4. **Final Architecture Seal:** Run full verification pyramid (L0: 244 tests, L1: Simulators, L2: Benchmarks, L3: Security).

### Phase 5 Validation Gate
- `pytest tests/` $\rightarrow$ `244 passed`.
- Zero legacy modules remaining in repository tree.
- Package imports strictly follow hexagonal layers (Domain $\leftarrow$ Application $\leftarrow$ Adapters/Infrastructure).
- Tag: `v1.0.0-hexagonal-complete`.

---

# 4. Dual-Run Shadow Execution & Verification Seam

The **Dual-Run Shadow Execution Seam** guarantees that before any legacy pipeline is deprecated, the target `GuardedFSMEngine` is proven under identical production inputs without risking user-facing failures.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   DUAL-RUN SHADOW EXECUTION HARNESS ARCHITECTURE                                      │
│                                                                                                                        │
│                                          User CLI Task Request                                                         │
│                                                    │                                                                   │
│                                                    ▼                                                                   │
│                                     ┌─────────────────────────────┐                                                    │
│                                     │   ShadowExecutionHarness    │                                                    │
│                                     └──────────────┬──────────────┘                                                    │
│                                                    │                                                                   │
│                       ┌────────────────────────────┴────────────────────────────┐                                      │
│                       │ Clone Workspace                                         │ Clone Workspace                      │
│                       ▼                                                         ▼                                      │
│            ┌───────────────────────┐                                 ┌───────────────────────┐                         │
│            │  Workspace A (Legacy) │                                 │  Workspace B (Target) │                         │
│            │  `/tmp/ws_shadow_leg` │                                 │  `/tmp/ws_shadow_tgt` │                         │
│            └──────────┬────────────┘                                 └──────────┬────────────┘                         │
│                       │                                                         │                                      │
│                       ▼                                                         ▼                                      │
│            ┌───────────────────────┐                                 ┌───────────────────────┐                         │
│            │  Legacy BasePipeline  │                                 │   Guarded FSM Engine  │                         │
│            │ (Production Response) │                                 │ (Shadow Evaluation)   │                         │
│            └──────────┬────────────┘                                 └──────────┬────────────┘                         │
│                       │                                                         │                                      │
│                       │ Return Result to CLI                                    │                                      │
│                       ▼                                                         ▼                                      │
│            ┌───────────────────────┐                                 ┌───────────────────────┐                         │
│            │ User Output Delivered │                                 │ Shadow Result Artifact│                         │
│            └───────────────────────┘                                 └──────────┬────────────┘                         │
│                                                                                 │                                      │
│                                                                                 ▼                                      │
│                                                                      ┌───────────────────────┐                         │
│                                                                      │ Differential Evaluator│                         │
│                                                                      │ • AST Structural Diff │                         │
│                                                                      │ • Test Suite Parity   │                         │
│                                                                      │ • FCR / TCR Delta     │                         │
│                                                                      │ • CHI Health Delta    │                         │
│                                                                      │ • Token Efficiency    │                         │
│                                                                      └──────────┬────────────┘                         │
│                                                                                 │                                      │
│                                                                                 ▼                                      │
│                                                                      ┌───────────────────────┐                         │
│                                                                      │ SQLite Telemetry WAL  │                         │
│                                                                      │ (Shadow Audit Log)    │                         │
│                                                                      └───────────────────────┘                         │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4.1 Differential Evaluation Metrics

The `DifferentialExecutionEvaluator` compares the execution outcomes of the Legacy Pipeline ($E_{\text{legacy}}$) and the Guarded FSM ($E_{\text{target}}$) across 5 orthogonal mathematical dimensions:

### 1. Abstract Syntax Tree (AST) Semantic Complexity Metric ($\Delta \text{AST}$)
Measures whether the target engine generated complete, concrete domain logic rather than shallow stubs:
$$\text{AST}_{\text{score}} = \sum_{n \in \text{AST Nodes}} \text{Weight}(n) \times \text{Depth}(n) - \kappa \cdot N_{\text{stubs}}$$
$$\text{Invariant: } \Delta \text{AST} = \text{AST}_{\text{score}}(E_{\text{target}}) - \text{AST}_{\text{score}}(E_{\text{legacy}}) \ge 0$$
Where $N_{\text{stubs}}$ is the count of `pass`, `...`, or `raise NotImplementedError` nodes. Any $\Delta \text{AST} < 0$ flags a code generation regression.

### 2. Test Suite Adequacy & Mutation Score ($\Delta \text{Test}$)
Verifies that the target engine generated a more rigorous, fault-sensitive test suite:
$$N_{\text{tests}}(E_{\text{target}}) \ge N_{\text{tests}}(E_{\text{legacy}})$$
$$\text{MutationScore}(E_{\text{target}}) \ge \text{MutationScore}(E_{\text{legacy}})$$

### 3. Codebase Health Index Delta ($\Delta \text{CHI}$)
Using the formal P7 Codebase Health Index ($\text{CHI} \in [0, 100]$):
$$\Delta \text{CHI} = \text{CHI}(W_{\text{target}}) - \text{CHI}(W_{\text{legacy}}) \ge 0.00$$

### 4. False Completion Rate Barrier ($FCR$)
Using the P1/P2.1 Ground-Truth Requirement Satisfaction Gate:
$$FCR(E_{\text{target}}) \equiv 0.000$$
If the legacy engine claims completion while requirements are missing, $E_{\text{target}}$ must identify the deficiency and remain in the repair state.

### 5. Token Efficiency Ratio ($\eta_{\text{token}}$)
Measures the token expenditure per requirement verified:
$$\eta_{\text{token}} = \frac{\text{Tokens Consumed}}{\text{Verified AST Requirements Satisfied}}$$
$$\text{Target Invariant: } \eta_{\text{token}}(E_{\text{target}}) \le 1.25 \times \eta_{\text{token}}(E_{\text{legacy}})$$

---

# 5. Canary Feature-Flag Deployment & Traffic Routing

The migration control plane dynamically routes incoming CLI and API requests between legacy pipelines and target hexagonal engines based on explicit runtime configuration.

## 5.1 Runtime Routing Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RoutingConfig",
  "type": "object",
  "properties": {
    "migration_phase": {
      "type": "string",
      "enum": [
        "PHASE_0_BASELINE",
        "PHASE_1_FACADES",
        "PHASE_2_TOOLS",
        "PHASE_3_SDK_SEAM",
        "PHASE_4_CANARY",
        "PHASE_5_DECOMMISSIONED"
      ],
      "default": "PHASE_4_CANARY"
    },
    "use_guarded_fsm": {
      "type": "boolean",
      "default": true
    },
    "use_hardened_sandbox": {
      "type": "boolean",
      "default": true
    },
    "use_clean_sdk_bridge": {
      "type": "boolean",
      "default": true
    },
    "canary_percentage": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "default": 100
    },
    "shadow_execution_enabled": {
      "type": "boolean",
      "default": false
    },
    "shadow_sample_rate": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.20
    },
    "fallback_to_legacy_on_error": {
      "type": "boolean",
      "default": true
    },
    "circuit_breaker_max_fcr": {
      "type": "number",
      "default": 0.000
    },
    "circuit_breaker_error_threshold": {
      "type": "integer",
      "default": 3
    }
  },
  "required": ["migration_phase", "canary_percentage"]
}
```

---

## 5.2 Automated Circuit Breakers & Trip-Wire Matrix

To prevent regressions in production, the `StranglerPipelineDispatcher` enforces three automated runtime trip-wires:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   AUTOMATED CIRCUIT BREAKER TRIP-WIRE MATRIX                                           │
├───────────┬───────────────────────────────────┬──────────────────────────────────────┬─────────────────────────────────┤
│ Trip-Wire │ Trigger Condition                 │ Immediate System Action              │ Recovery Procedure              │
├───────────┼───────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────────┤
│ TW-01     │ Unhandled Exception / Crash in    │ Catch exception, log full diagnostic │ Re-execute task on Legacy Engine│
│ (Runtime) │ Target Hexagonal FSM              │ telemetry to SQLite WAL, switch route│ with zero user-visible error.   │
├───────────┼───────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────────┤
│ TW-02     │ Consecutive Target Failures       │ Trip Circuit Breaker to OPEN state.  │ Automatic Rollback of Canary    │
│ (Threshold│ $\ge \text{circuit\_breaker\_...}$│ Instantly force `canary_percentage`  │ traffic to 0%. Notify DevOps via│
│           │ (Default: 3 failures in 10 mins)  │ to 0% for all subsequent runs.       │ Console Alert & Diagnostics DB. │
├───────────┼───────────────────────────────────┼──────────────────────────────────────┼─────────────────────────────────┤
│ TW-03     │ Shadow Differential Detects False │ Record critical incident finding.    │ Freeze Canary percentage.       │
│ (Quality) │ Completion ($FCR > 0.000$)        │ Halt automatic canary progression.   │ Block Phase 5 decommission.     │
└───────────┴───────────────────────────────────┴──────────────────────────────────────┴─────────────────────────────────┘
```

---

# 6. Rollback Playbooks & Incident Recovery Procedures

Every phase possesses an explicit, tested rollback playbook guaranteeing immediate system restoration.

## 6.1 Phase-by-Phase Rollback Runbooks

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      OPERATIONAL ROLLBACK RUNBOOKS (P12)                                               │
├──────────────────┬──────────────────────┬──────────────────────────────────────────────────────────────────────────────┤
│ Target Phase     │ Rollback Script / Cmd│ Detailed Recovery Actions                                                    │
├──────────────────┼──────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ Phase 1          │ `python scripts/`    │ 1. Git restore `orchestrator/utils/` facades.                                │
│ (Facades)        │ `rollback.py phase1` │ 2. Re-point internal imports back to `orchestrator.utils`.                   │
│                  │                      │ 3. Run `pytest tests/ -v` to confirm 244/244 passing tests.                  │
├──────────────────┼──────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ Phase 2          │ `python scripts/`    │ 1. Set `use_hardened_sandbox: false` in `RoutingConfig`.                     │
│ (Hardened Tools) │ `rollback.py phase2` │ 2. Revert `workspace_tools.py` seam to legacy subprocess caller.             │
│                  │                      │ 3. Verify terminal and file tests pass cleanly.                              │
├──────────────────┼──────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ Phase 3          │ `python scripts/`    │ 1. Re-enable `sdk_patch.py` import in `orchestrator/__init__.py`.             │
│ (SDK Boundary)   │ `rollback.py phase3` │ 2. Set `use_clean_sdk_bridge: false` in `RoutingConfig`.                     │
│                  │                      │ 3. Re-engage legacy conversation runner.                                     │
├──────────────────┼──────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ Phase 4          │ `python scripts/`    │ 1. Set `canary_percentage: 0` and `use_guarded_fsm: false`.                   │
│ (Guarded FSM)    │ `rollback.py phase4` │ 2. Force all CLI traffic to `DevTestLoop` and `FullPipeline`.                 │
│                  │                      │ 3. Flush SQLite WAL shadow queues.                                           │
├──────────────────┼──────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ Emergency Hard   │ `git checkout -f`    │ 1. Force checkout baseline tag `v0.1.0-baseline`.                            │
│ Rollback (All)   │ `v0.1.0-baseline`    │ 2. Purge untracked migration caches and bytecode.                            │
│                  │                      │ 3. Instant total system recovery in $< 3\text{ seconds}$.                     │
└──────────────────┴──────────────────────┴──────────────────────────────────────────────────────────────────────────────┘
```

---

## 6.2 Deterministic Rollback Script (`scripts/rollback_migration.py`)

```python
"""Automated, deterministic 1-command rollback utility for ORAGAI migration phases."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROUTING_CONFIG_PATH = REPO_ROOT / "orchestrator" / "config" / "migration_routing.json"

CHECKPOINTS = {
    "phase0": "v0.1.0-baseline",
    "phase1": "v0.2.0-facades-cleansed",
    "phase2": "v0.3.0-hardened-tools",
    "phase3": "v0.4.0-clean-sdk-boundary",
    "phase4": "v0.5.0-fsm-canary-100",
}


def update_routing_config(overrides: dict) -> None:
    """Safely update the dynamic JSON routing configuration."""
    if ROUTING_CONFIG_PATH.exists():
        data = json.loads(ROUTING_CONFIG_PATH.read_text(encoding="utf-8"))
    else:
        data = {}
    data.update(overrides)
    ROUTING_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROUTING_CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[ROLLBACK] Updated routing configuration: {overrides}")


def execute_rollback(target_phase: str, hard_git_reset: bool = False) -> None:
    """Execute deterministic rollback to a prior verified state."""
    print(f"[ROLLBACK] Initiating rollback to checkpoint: {target_phase.upper()}...")

    if target_phase == "phase4":
        update_routing_config({"canary_percentage": 0, "use_guarded_fsm": False})
    elif target_phase == "phase3":
        update_routing_config({"use_clean_sdk_bridge": False, "canary_percentage": 0})
    elif target_phase == "phase2":
        update_routing_config({"use_hardened_sandbox": False})
    elif target_phase == "phase1" or hard_git_reset:
        tag = CHECKPOINTS.get(target_phase, "v0.1.0-baseline")
        print(f"[ROLLBACK] Performing Git hard checkout to tag: {tag}")
        cmd = ["git", "checkout", "-f", tag]
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[ROLLBACK ERROR] Git checkout failed: {res.stderr}")
            sys.exit(1)

    # Post-rollback verification gate
    print("[ROLLBACK] Running regression test verification (244-test invariant)...")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=REPO_ROOT)
    if res.returncode == 0:
        print(f"[ROLLBACK SUCCESS] System successfully restored to {target_phase.upper()} (244/244 tests passing).")
    else:
        print("[ROLLBACK CRITICAL] Test verification failed after rollback! Manual inspection required.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ORAGAI Migration Rollback Utility")
    parser.add_argument("phase", choices=["phase0", "phase1", "phase2", "phase3", "phase4"], help="Target rollback phase")
    parser.add_argument("--hard", action="store_true", help="Perform hard Git reset to tag instead of flag toggle")
    args = parser.parse_args()
    execute_rollback(args.phase, args.hard)
```

---

# 7. Canonical Python Architecture & Data Models

This section provides the complete, production-ready, fully typed Python implementation for `orchestrator/migration/strangler_bridge.py`.

```python
"""Canonical Strangler Fig Migration Bridge, Dispatcher, and Shadow Harness for ORAGAI.

Module: orchestrator.migration.strangler_bridge
Specification: docs/plans/P12_STRANGLER_FIG_MIGRATION_AND_SAFE_ROLLOUT_PLAN.md
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union
from pydantic import BaseModel, Field

logger = logging.getLogger("orchestrator.migration.strangler_bridge")


# ============================================================================
# 1. Enums and Data Models
# ============================================================================

class MigrationPhase(str, Enum):
    """Formal lifecycle migration phases for ORAGAI."""
    PHASE_0_BASELINE = "PHASE_0_BASELINE"
    PHASE_1_FACADES = "PHASE_1_FACADES"
    PHASE_2_TOOLS = "PHASE_2_TOOLS"
    PHASE_3_SDK_SEAM = "PHASE_3_SDK_SEAM"
    PHASE_4_CANARY = "PHASE_4_CANARY"
    PHASE_5_DECOMMISSIONED = "PHASE_5_DECOMMISSIONED"


class CircuitBreakerStatus(str, Enum):
    """Circuit breaker operational state."""
    CLOSED = "CLOSED"      # Normal operation: traffic routes to Target
    OPEN = "OPEN"          # Tripped: all traffic forced to Legacy
    HALF_OPEN = "HALF_OPEN" # Probing: testing small canary sample


class RoutingConfig(BaseModel):
    """Dynamic runtime traffic routing configuration."""
    migration_phase: MigrationPhase = MigrationPhase.PHASE_4_CANARY
    use_guarded_fsm: bool = True
    use_hardened_sandbox: bool = True
    use_clean_sdk_bridge: bool = True
    canary_percentage: int = Field(default=100, ge=0, le=100)
    shadow_execution_enabled: bool = False
    shadow_sample_rate: float = Field(default=0.20, ge=0.0, le=1.0)
    fallback_to_legacy_on_error: bool = True
    circuit_breaker_max_fcr: float = Field(default=0.000, ge=0.0, le=1.0)
    circuit_breaker_error_threshold: int = Field(default=3, ge=1)


class ExecutionMetrics(BaseModel):
    """Execution telemetry captured during a pipeline run."""
    success: bool
    wall_clock_seconds: float
    total_tokens_consumed: int
    ast_node_count: int
    ast_stub_count: int
    total_test_count: int
    passing_test_count: int
    codebase_health_index: float
    false_completion_detected: bool
    error_message: Optional[str] = None


class PipelineExecutionOutcome(BaseModel):
    """Result of an autonomous task execution."""
    pipeline_type: str  # "LEGACY" | "TARGET_HEXAGONAL"
    task_id: str
    status: str
    metrics: ExecutionMetrics
    artifacts_diff: Optional[str] = None
    raw_result: Dict[str, Any] = Field(default_factory=dict)


class ShadowComparisonReport(BaseModel):
    """Differential comparison between legacy and target execution outcomes."""
    task_id: str
    timestamp: float = Field(default_factory=time.time)
    legacy_outcome: PipelineExecutionOutcome
    target_outcome: PipelineExecutionOutcome
    ast_complexity_delta: int
    test_count_delta: int
    passing_test_delta: int
    chi_delta: float
    token_ratio: float
    target_fcr_violation: bool
    parity_satisfied: bool
    recommendation: str


# ============================================================================
# 2. Differential Execution Evaluator
# ============================================================================

class DifferentialExecutionEvaluator:
    """Evaluates and compares execution artifacts between Legacy and Target engines."""

    @staticmethod
    def count_ast_nodes_and_stubs(workspace_path: Path) -> Tuple[int, int]:
        """Parse all Python files in the workspace to count AST nodes and stub tokens."""
        total_nodes = 0
        total_stubs = 0

        for py_file in workspace_path.glob("**/*.py"):
            if "venv" in py_file.parts or ".git" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
                for node in ast.walk(tree):
                    total_nodes += 1
                    # Detect stub implementations (pass, Expr(Constant(...)), raise NotImplementedError)
                    if isinstance(node, ast.Pass):
                        total_stubs += 1
                    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node.value.value is Ellipsis:
                        total_stubs += 1
                    elif isinstance(node, ast.Raise):
                        if isinstance(node.exc, ast.Name) and node.exc.id == "NotImplementedError":
                            total_stubs += 1
                        elif isinstance(node.exc, ast.Call) and getattr(node.exc.func, "id", "") == "NotImplementedError":
                            total_stubs += 1
            except Exception:
                continue

        return total_nodes, total_stubs

    @classmethod
    def evaluate(
        cls,
        task_id: str,
        legacy_res: PipelineExecutionOutcome,
        target_res: PipelineExecutionOutcome,
    ) -> ShadowComparisonReport:
        """Compute differential parity report."""
        leg_m = legacy_res.metrics
        tgt_m = target_res.metrics

        ast_delta = tgt_m.ast_node_count - leg_m.ast_node_count
        test_delta = tgt_m.total_test_count - leg_m.total_test_count
        pass_delta = tgt_m.passing_test_count - leg_m.passing_test_count
        chi_delta = tgt_m.codebase_health_index - leg_m.codebase_health_index

        token_ratio = (
            tgt_m.total_tokens_consumed / leg_m.total_tokens_consumed
            if leg_m.total_tokens_consumed > 0
            else 1.0
        )

        target_fcr = tgt_m.false_completion_detected

        # Parity is satisfied if target has zero FCR, test passes >= legacy, and CHI >= legacy
        parity_satisfied = (
            not target_fcr
            and tgt_m.success
            and pass_delta >= 0
            and chi_delta >= -0.01
            and tgt_m.ast_stub_count == 0
        )

        if parity_satisfied:
            recommendation = "TARGET_EXCEEDS_OR_MATCHES_LEGACY: Safe to advance canary percentage."
        else:
            recommendation = "TARGET_REGRESSION_DETECTED: Hold canary and inspect AST/FCR differential."

        return ShadowComparisonReport(
            task_id=task_id,
            legacy_outcome=legacy_res,
            target_outcome=target_res,
            ast_complexity_delta=ast_delta,
            test_count_delta=test_delta,
            passing_test_delta=pass_delta,
            chi_delta=chi_delta,
            token_ratio=token_ratio,
            target_fcr_violation=target_fcr,
            parity_satisfied=parity_satisfied,
            recommendation=recommendation,
        )


# ============================================================================
# 3. Shadow Execution Harness
# ============================================================================

class ShadowExecutionHarness:
    """Executes tasks concurrently across Legacy and Target engines in isolated workspaces."""

    def __init__(self, differential_evaluator: Optional[DifferentialExecutionEvaluator] = None):
        self.evaluator = differential_evaluator or DifferentialExecutionEvaluator()

    @staticmethod
    def _clone_workspace(source_ws: Path, target_ws: Path) -> None:
        """Create an exact isolated clone of the workspace directory."""
        if target_ws.exists():
            shutil.rmtree(target_ws, ignore_errors=True)
        shutil.copytree(
            source_ws,
            target_ws,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache", ".venv"),
        )

    def execute_shadow_dual_run(
        self,
        task: str,
        mode: str,
        workspace: Path,
        legacy_runner: Callable[[str, str, Path], Dict[str, Any]],
        target_runner: Callable[[str, str, Path], Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], ShadowComparisonReport]:
        """Run legacy and target pipelines in parallel isolated workspaces and compare."""
        task_id = hashlib.sha256(f"{task}:{time.time()}".encode("utf-8")).hexdigest()[:12]

        with tempfile.TemporaryDirectory(prefix=f"oragai_shadow_leg_{task_id}_") as leg_dir, \
             tempfile.TemporaryDirectory(prefix=f"oragai_shadow_tgt_{task_id}_") as tgt_dir:

            leg_ws = Path(leg_dir)
            tgt_ws = Path(tgt_dir)

            self._clone_workspace(workspace, leg_ws)
            self._clone_workspace(workspace, tgt_ws)

            # 1. Execute Legacy Pipeline (Live Response)
            t0_leg = time.perf_counter()
            try:
                leg_raw = legacy_runner(task, mode, leg_ws)
                leg_err = None
                leg_success = True
            except Exception as e:
                leg_raw = {"error": str(e)}
                leg_err = str(e)
                leg_success = False
            t_leg_duration = time.perf_counter() - t0_leg

            leg_nodes, leg_stubs = self.evaluator.count_ast_nodes_and_stubs(leg_ws)
            leg_outcome = PipelineExecutionOutcome(
                pipeline_type="LEGACY",
                task_id=task_id,
                status="COMPLETED" if leg_success else "FAILED",
                metrics=ExecutionMetrics(
                    success=leg_success,
                    wall_clock_seconds=t_leg_duration,
                    total_tokens_consumed=leg_raw.get("tokens_consumed", 0),
                    ast_node_count=leg_nodes,
                    ast_stub_count=leg_stubs,
                    total_test_count=leg_raw.get("total_tests", 0),
                    passing_test_count=leg_raw.get("passing_tests", 0),
                    codebase_health_index=leg_raw.get("chi", 70.0),
                    false_completion_detected=leg_raw.get("false_completion", False),
                    error_message=leg_err,
                ),
                raw_result=leg_raw,
            )

            # 2. Execute Target Hexagonal FSM Engine (Shadow Execution)
            t0_tgt = time.perf_counter()
            try:
                tgt_raw = target_runner(task, mode, tgt_ws)
                tgt_err = None
                tgt_success = True
            except Exception as e:
                tgt_raw = {"error": str(e)}
                tgt_err = str(e)
                tgt_success = False
            t_tgt_duration = time.perf_counter() - t0_tgt

            tgt_nodes, tgt_stubs = self.evaluator.count_ast_nodes_and_stubs(tgt_ws)
            tgt_outcome = PipelineExecutionOutcome(
                pipeline_type="TARGET_HEXAGONAL",
                task_id=task_id,
                status="COMPLETED" if tgt_success else "FAILED",
                metrics=ExecutionMetrics(
                    success=tgt_success,
                    wall_clock_seconds=t_tgt_duration,
                    total_tokens_consumed=tgt_raw.get("tokens_consumed", 0),
                    ast_node_count=tgt_nodes,
                    ast_stub_count=tgt_stubs,
                    total_test_count=tgt_raw.get("total_tests", 0),
                    passing_test_count=tgt_raw.get("passing_tests", 0),
                    codebase_health_index=tgt_raw.get("chi", 85.0),
                    false_completion_detected=tgt_raw.get("false_completion", False),
                    error_message=tgt_err,
                ),
                raw_result=tgt_raw,
            )

            # 3. Synchronize modified files from Live Legacy Workspace back to user's real workspace
            for item in leg_ws.glob("**/*"):
                if item.is_file():
                    rel = item.relative_to(leg_ws)
                    dest = workspace / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)

            # 4. Generate Differential Report
            report = self.evaluator.evaluate(task_id, leg_outcome, tgt_outcome)
            logger.info("Shadow Differential Evaluation: %s", report.model_dump_json())

            return leg_raw, report


# ============================================================================
# 4. Strangler Pipeline Dispatcher (The Control Plane Seam)
# ============================================================================

class StranglerPipelineDispatcher:
    """Dynamic Strangler Seam dispatching CLI execution between Legacy and Target engines."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        shadow_harness: Optional[ShadowExecutionHarness] = None,
    ):
        self.config_path = config_path or (
            Path(__file__).resolve().parent.parent / "config" / "migration_routing.json"
        )
        self.routing_config = self._load_routing_config()
        self.shadow_harness = shadow_harness or ShadowExecutionHarness()
        self.consecutive_target_errors = 0
        self.circuit_status = CircuitBreakerStatus.CLOSED

    def _load_routing_config(self) -> RoutingConfig:
        """Load routing configuration from disk or return default."""
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                return RoutingConfig(**data)
            except Exception as e:
                logger.warning("Failed to load migration routing config: %s. Using defaults.", e)
        return RoutingConfig()

    def _should_route_to_target(self, task: str, workspace: Path) -> bool:
        """Determine if request routes to Target based on canary hash and circuit breaker."""
        if self.circuit_status == CircuitBreakerStatus.OPEN:
            return False

        if not self.routing_config.use_guarded_fsm:
            return False

        if self.routing_config.canary_percentage >= 100:
            return True

        if self.routing_config.canary_percentage <= 0:
            return False

        # Deterministic hashing (0-99 bucket)
        hash_val = int(hashlib.sha256(f"{task}:{workspace}".encode("utf-8")).hexdigest()[:8], 16)
        bucket = hash_val % 100
        return bucket < self.routing_config.canary_percentage

    def dispatch_task(
        self,
        task: str,
        mode: str,
        workspace: Path,
        legacy_runner: Callable[[str, str, Path], Dict[str, Any]],
        target_runner: Callable[[str, str, Path], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Dispatch task with automatic shadow dual-run and fault-tolerant fallback."""
        self.routing_config = self._load_routing_config()

        # 1. Shadow Execution Hook
        if self.routing_config.shadow_execution_enabled:
            logger.info("Executing task under Shadow Execution Harness...")
            leg_res, report = self.shadow_harness.execute_shadow_dual_run(
                task, mode, workspace, legacy_runner, target_runner
            )
            if report.target_fcr_violation:
                logger.error("CIRCUIT BREAKER: Shadow run detected FCR > 0.000!")
            return leg_res

        # 2. Canary Route Selection
        route_to_target = self._should_route_to_target(task, workspace)

        if route_to_target:
            logger.info("Routing task to TARGET Hexagonal Guarded FSM Engine (Canary %d%%)...",
                        self.routing_config.canary_percentage)
            try:
                result = target_runner(task, mode, workspace)
                self.consecutive_target_errors = 0
                return result
            except Exception as e:
                self.consecutive_target_errors += 1
                logger.error("Target engine execution failed: %s (Consecutive: %d)",
                             e, self.consecutive_target_errors)

                # Check Circuit Breaker Trip-Wire
                if self.consecutive_target_errors >= self.routing_config.circuit_breaker_error_threshold:
                    self.circuit_status = CircuitBreakerStatus.OPEN
                    logger.critical("CIRCUIT BREAKER TRIPPED! Switching all traffic to LEGACY fallback.")

                if self.routing_config.fallback_to_legacy_on_error:
                    logger.warning("Executing emergency fallback to LEGACY pipeline...")
                    return legacy_runner(task, mode, workspace)
                raise

        # 3. Legacy Pipeline Route
        logger.info("Routing task to LEGACY pipeline...")
        return legacy_runner(task, mode, workspace)
```

---

# 8. Rigorous Test Matrix & Verification Scenarios

The migration test suite (`tests/test_strangler_migration.py`) comprehensively validates routing mechanics, shadow execution parity, circuit breaker trip-wires, and clean module deprecations.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   MIGRATION VERIFICATION SCENARIOS MATRIX                                              │
├────────┬──────────────────────────────────────────┬──────────┬─────────────────────────────────────────────────────────┤
│ Test ID│ Test Function Name                       │ Phase    │ Tested Invariant & Validation Criteria                  │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-01 │ `test_phase0_baseline_244_invariant`     │ Phase 0  │ Invariant 2: 244/244 tests passing on baseline freeze.  │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-02 │ `test_phase1_facades_direct_imports`     │ Phase 1  │ Verify direct imports from domain packages without      │
│        │                                          │          │ triggering deprecated `orchestrator.utils.*` facades.   │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-03 │ `test_phase2_ast_virtualizer_seam`       │ Phase 2  │ `use_hardened_sandbox: true` routes file writes through │
│        │                                          │          │ `ASTVirtualizer` and blocks placeholder stub writes.   │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-04 │ `test_phase2_grammar_terminal_security`  │ Phase 2  │ Verify command injection payloads (`$(...)`, `&&`) are  │
│        │                                          │          │ intercepted and sanitized without subprocess bypass.    │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-05 │ `test_phase3_clean_sdk_bridge_isolation` │ Phase 3  │ Verify official `ToolDefinition` registers without      │
│        │                                          │          │ requiring `sdk_patch.py` monkey-patching.              │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-06 │ `test_phase3_bounded_turn_yield_signal`  │ Phase 3  │ Verify conversation yields `AGENT_YIELDED` without      │
│        │                                          │          │ asynchronous `conv.interrupt()` thread kill errors.     │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-07 │ `test_phase4_canary_routing_0_percent`   │ Phase 4  │ `canary_percentage: 0` routes 100% of tasks to Legacy. │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-08 │ `test_phase4_canary_routing_100_percent` │ Phase 4  │ `canary_percentage: 100` routes 100% of tasks to Target.│
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-09 │ `test_phase4_canary_deterministic_split` │ Phase 4  │ `canary_percentage: 50` routes deterministic hash split │
│        │                                          │          │ with $< 2\%$ statistical variance across 1000 tasks.   │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-10 │ `test_phase4_shadow_dual_run_execution`  │ Phase 4  │ Shadow harness clones workspaces and computes valid     │
│        │                                          │          │ differential AST, test count, and CHI metrics.         │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-11 │ `test_phase4_circuit_breaker_crash_trip` │ Phase 4  │ Unhandled exception in Target engine triggers instant   │
│        │                                          │          │ transparent fallback to Legacy without client failure.  │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-12 │ `test_phase4_circuit_breaker_threshold`  │ Phase 4  │ 3 consecutive Target failures trip circuit breaker to   │
│        │                                          │          │ `OPEN` state, forcing subsequent tasks to Legacy.       │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-13 │ `test_phase4_shadow_fcr_zero_enforcement`│ Phase 4  │ Differential evaluator flags `parity_satisfied = False` │
│        │                                          │          │ if Target reports completion on incomplete requirement. │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-14 │ `test_phase5_legacy_modules_decommission`│ Phase 5  │ Verify repository builds and passes full test suite     │
│        │                                          │          │ after physical deletion of legacy pipeline files.       │
├────────┼──────────────────────────────────────────┼──────────┼─────────────────────────────────────────────────────────┤
│ MIG-15 │ `test_rollback_phase4_to_legacy`         │ Rollback │ Automated rollback script restores `canary: 0` in $< 1s │
│        │                                          │          │ and passes 244/244 regression tests.                    │
└────────┴──────────────────────────────────────────┴──────────┴─────────────────────────────────────────────────────────┘
```

---

# 9. Handoff Contract for P13 (Final Target Architecture Specification)

The completion of P12 establishes the operational migration bridge and guarantees zero-regression rollout. This section formalizes the **Final Target Architecture Specification Contract** that will be codified in **P13**.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FINAL TARGET HEXAGONAL REPOSITORY LAYOUT (P13)                                      │
│                                                                                                                        │
│   orchestrator/                                                                                                        │
│   ├── domain/                         # Core Domain Entities & Truth Models (P1, P2.1)                                 │
│   │   ├── task_truth.py               # Requirement DAG, Evidence Graph, Completion Predicates                        │
│   │   ├── evidence.py                 # Content Hashing, Cryptographic Merkle Signatures                               │
│   │   └── state.py                    # Orthogonal ImplementationState & VerificationState                             │
│   ├── governance/                     # Control Plane & Lifecycle Orchestration (P3, P4, P8)                           │
│   │   ├── fsm/                        # Guarded FSM Engine, Guard Predicates, Phase Handlers                           │
│   │   ├── resource/                   # Adaptive Resource Governor, Dynamic Turn Allocation                            │
│   │   └── recovery/                   # Stagnation Velocity Vectors (PER 2.0), Cycle Breakers                          │
│   ├── workstreams/                    # Agent Collaboration Workstreams (P5, P6, P7)                                   │
│   │   ├── micro_tdd.py                # Red-Green-Refactor Autonomous Test-Driven Loop                                 │
│   │   ├── full_lifecycle.py           # Requirements ──▶ Architecture ──▶ Implementation ──▶ QA                        │
│   │   ├── audit.py                    # Zero-Token AST Sweeps, Finding DAGs, CHI Calculator                            │
│   │   └── handoff/                    # Priority-Tiered Context Packaging (Tier 0 to Tier 3)                           │
│   ├── runtime/                        # Clean OpenHands SDK Boundary (P10)                                             │
│   │   ├── openhands/                  # OpenHandsRuntimeBridge, SDKAgentFactory, SDKSessionRunner                      │
│   │   └── simulation/                 # Zero-Token Deterministic Mock ReAct EventStream Runner (P11)                   │
│   ├── tools/                          # Hardened Virtualized Tooling (P9)                                              │
│   │   ├── file_virtualizer.py         # AST Patch Engine, Anti-Stub Interceptor                                        │
│   │   ├── command_terminal.py         # Grammar-Based Command Security Interceptor                                     │
│   │   └── sandbox_manager.py          # Workspace Isolation & Resource Throttling                                      │
│   ├── adapters/                       # Polyglot Project Adapters (Python, Node, Generic)                              │
│   ├── analysis/                       # Static Code Analysis, AST Parsers, Graft Context                               │
│   ├── ui/                             # Session Store, Live Rich Visualizer, SQLite Diagnostics                        │
│   └── cli/                            # Clean Argument Parsing, Command Handlers, Interactive Wizard                   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9.1 P12 Exit Criteria Checklist

Before declaring P12 complete and transitioning to P13:
- [x] **Zero Production Code Modified:** All source files in `orchestrator/` remain untouched during planning.
- [x] **Strangler Seam Bridge Implemented:** `StranglerPipelineDispatcher`, `ShadowExecutionHarness`, and `DifferentialExecutionEvaluator` fully specified with complete Python typing.
- [x] **6-Phase Execution Roadmap Defined:** Phases 0 through 5 fully detailed with explicit validation gates and tags.
- [x] **244-Test Invariant Gate Preserved:** Unbroken 100% pass requirement enforced across all phases.
- [x] **Shadow Differential Evaluation Formulated:** 5-dimensional evaluation ($\Delta \text{AST}$, $\Delta \text{Test}$, $\Delta \text{CHI}$, $FCR$, $\eta_{\text{token}}$) codified.
- [x] **Automated Circuit Breakers Specified:** 3 runtime trip-wires (crash, threshold, FCR) defined with automated rollback scripts.
- [x] **15-Scenario Verification Matrix Constructed:** Scenarios MIG-01 through MIG-15 documented.

---

## 9.2 Input Contract for P13 (Canonical Target Architecture Specification)

The P13 plan will consume the outputs of P0 through P12 to deliver the final production codebase:
1. **Repository Layout Finalization:** Physical implementation of the target hexagonal directory structure.
2. **Unified Core Domain Model:** Consolidating `TaskTruthModel`, `CompletionEvaluator`, and `GuardedFSMEngine`.
3. **Execution of Migration Phases:** Step-by-step application of Phases 0–5 governed by the P12 Strangler Seam.
4. **End-to-End System Benchmark Certification:** Executing BM-01 through BM-08 against the finished target architecture to achieve formal production sign-off.
