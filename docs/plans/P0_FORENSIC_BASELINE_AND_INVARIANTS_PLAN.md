# P0 — FORENSIC BASELINE & SYSTEM INVARIANTS PLAN

> **Document Type:** Foundational Forensic Systems Engineering & Architecture Baseline  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Software Architect, Forensic Systems Engineer, & Autonomous Agent Orchestration Specialist  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Evaluation Mode:** Forensic Static Code Audit & Dynamic Runtime Baseline (Zero Production Code Modified)

---

# 1. Executive Summary

This forensic baseline establishes an indisputable, evidence-backed characterization of the **ORAGAI** multi-agent software engineering orchestration system prior to any architectural redesign. 

ORAGAI was created to autonomously manage the end-to-end software engineering lifecycle (Requirements $\rightarrow$ Architecture $\rightarrow$ Implementation $\rightarrow$ QA $\rightarrow$ Code Review $\rightarrow$ Audit $\rightarrow$ Git Commit) atop the OpenHands SDK (`openhands-sdk v1.49.4`). 

### Core Forensic Finding
The primary driver of observed system pathologies (such as shallow code generation, superficial audits, investigation starvation, and premature task completion) is **not LLM reasoning weakness or prompt phrasing**. The root cause is a fundamental architectural pathology:

> **The orchestration engine conflates *Resource Safety Governance* with *Work Lifecycle Completion*, enforcing hard micro-step cutoffs and equating binary exit signals (`pytest exit_code == 0`, `ConvRunResult.completed == True`, `diff != None`) with domain goal correctness and requirement coverage.**

The current system operates as a **Defensive Execution Cage**:
1. It assigns agents micro-step budgets (e.g., 5 turns for single-file tasks, 8 for multi-file) regardless of task depth ([token_governance.py:L108-116](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/control/token_governance.py#L108-L116)).
2. It kills agents exploring codebases via `conv.interrupt()` as soon as 28% of turn tokens are consumed without an immediate file edit ([base_pipeline.py:L304-324](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L304-L324)).
3. It clamps file inspection to 250 lines / 12,000 characters per call ([workspace_tools.py:L31-32](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/tools/workspace_tools.py#L31-L32)).
4. It dictates arbitrary prompts mandating audits to finish at step 4-5 after viewing only 2-3 files ([audit_pipeline.py:L158-174](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/audit_pipeline.py#L158-L174)).
5. When OpenHands SDK hits a step ceiling, `ConvRunResult.completed` silently defaults to `True` ([base_pipeline.py:L56](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L56)), registering step exhaustion as successful completion.
6. In development loops, a single pytest execution returning `exit_code == 0` terminates the loop immediately ([dev_test_loop.py:L277-280](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L277-L280)), even if zero functional requirements were tested or implemented.

This document inventories the codebase reality, models all termination and completion mechanisms, categorizes proven root causes, defines inviolable system invariants, specifies baseline metrics, and frames the Change Safety Contract governing all future implementation plans.

---

# 2. Repository Reality vs. Documented Assumptions

Every major claim regarding the system has been cross-examined against source code and test execution.

| Claimed Feature / Behavior | Source Code Reality | Forensic Classification | Confidence | Source Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **"Finite State Machine dynamically governs quality gates."** | `PipelineStateMachine` is a static Python dict lookup (`ALLOWED_TRANSITIONS`) verifying only phase enum legality. It contains **zero guard predicates**, zero evidence checks, and cannot evaluate code artifacts. | **Accidental Defect / Architectural Illusion** | 100% | `orchestrator/pipeline/state_machine.py:L28-93` |
| **"System verifies complete requirement coverage."** | There is **zero data structure or schema** representing user requirements, acceptance criteria, or requirement-to-test traceability. `pytest exit_code == 0` is the sole proxy for success. | **Proven Root Cause (Omission)** | 100% | `orchestrator/pipeline/dev_test_loop.py:L277-280` |
| **"Auditor conducts deep repository-wide analysis."** | Auditor prompt explicitly forces exit at step 4-5 and orders inspecting only 2-3 files. DynamicTokenGovernor step limit overrides config to micro-budgets. | **Proven Root Cause (Intentional Cage)** | 100% | `orchestrator/pipeline/audit_pipeline.py:L158-174`, `orchestrator/control/token_governance.py:L108-116` |
| **"Investigation Circuit Breaker stops infinite loops."** | It trips whenever an agent reads files without writing code after consuming 28% of tokens, aborting legitimate codebase exploration. | **Contributing Factor / False Positive Hazard** | 100% | `orchestrator/control/token_governance.py:L147-151, L237-245` |
| **"BasePipeline detects when an agent conversation completes."** | `ConvRunResult.completed` initializes to `True`. When OpenHands SDK finishes due to step exhaustion, `conv.run()` exits cleanly, and ORAGAI logs success. | **Proven Root Cause (False Success)** | 100% | `orchestrator/pipeline/base_pipeline.py:L56, L353-370` |
| **"Windows Subprocess Execution is fully resilient."** | Command interceptors translate some UNIX commands (`ls`, `cat`, `grep`), but `split_and_validate_command` unconditionally bans all pipe `\|` characters, breaking translated pipelines like `cat \| head`. | **Implementation Contradiction** | 100% | `orchestrator/tools/workspace_tools.py:L817, L835-840` |
| **"Zero-Token Tester Skip saves tokens safely on test re-runs."** | Re-running pytest on iteration $>1$ without LLM Tester works for regression verification, but because Developer is prompted only with test failures, Developer never writes new tests for unaddressed requirements. | **Contributing Factor** | 100% | `orchestrator/pipeline/dev_test_loop.py:L240-272` |
| **"Reviewer provides independent quality approval."** | Reviewer receives only a 4,000-character truncated diff (`GitOps.get_compact_diff`), lacks test suite visibility, and uses relaxed semantic regex matching to parse approvals. | **Contributing Factor** | 100% | `orchestrator/pipeline/full_pipeline.py:L630-654`, `orchestrator/pipeline/reviewer_parser.py:L76-87` |

---

# 3. System Architecture Map

The ORAGAI codebase is organized into distinct subpackages:

```
orchestrator-ai-agent/
├── orchestrator/
│   ├── adapters/          # Polyglot workspace drivers (PythonAdapter, NodeAdapter, GenericAdapter)
│   ├── agents/            # Role Agent Factories (Architect, Developer, Tester, Reviewer, Auditor, Docs)
│   ├── analysis/          # Pytest output parsing, Graft context extraction, finding schemas
│   ├── cli/               # CLI argument parsing, interactive wizard, command handlers
│   ├── config/            # Config schemas (Pydantic v2), cascading JSON/ENV loaders
│   ├── context/           # ContextManager, prompt builder, file resolver, priority injectors
│   ├── control/           # DynamicTokenGovernor, BudgetGuard, CostEstimator, HumanChannel, PipelineController
│   ├── core/              # Constants, typing protocols (ICognitiveSentinel), exception hierarchy
│   ├── diagnostics/       # Diagnostics indexer and catalog manager
│   ├── evolution/         # Codebase self-audit engine
│   ├── guards/            # PreFlightGuard (zero-token py_compile & importability verifier)
│   ├── llm/               # LLMManager, model normalizer, pricing engine, fallback factory
│   ├── memory/            # ConversationMemoryStore with TF-IDF keyword retrieval
│   ├── pipeline/          # 5 Execution Pipelines, PipelineStateMachine, MilestoneDAG, CheckpointManager
│   ├── rendering/         # Rich terminal output (ConsoleOutput), diff renderer, report formatters
│   ├── sentinel/          # CognitiveSentinelSupervisor, ASTGuard, SelfHealingEngine, CloudResilienceMesh
│   ├── skills/            # SkillManager, SkillResolver, SkillCompressor, SkillRegistry
│   ├── tools/             # RBAC WorkspaceFileTool, WorkspaceTerminalTool, RequestPermissionTool
│   ├── ui/                # SessionLogStore, OrchestratorLiveVisualizer, InteractiveLogExplorer
│   └── vcs/               # GitOps workspace isolation, branching, staging, checkpoint commits
├── .agents/skills/        # 9 Modular YAML+Markdown engineering skill specifications
├── tests/                 # 35 test files (244 unit and integration tests, 100% passing)
└── docs/                  # Architectural specs, strategic roadmap, audit reports
```

### Plane Separation Reality
* **Control / Governance Plane (ORAGAI):** CLI, ContextManager, DynamicTokenGovernor, PreFlightGuard, ASTGuard, GitOps, PipelineStateMachine, PytestOutputParser, TelemetryRecorder, Sentinel.
* **Agent Execution Runtime (OpenHands SDK v1.49.4):** Agent instance, Conversation loop (`conv.run()`), LLM client, ToolDefinition / ToolExecutor bindings, Action / Observation serialization.

---

# 4. End-to-End Lifecycle

The complete execution lifecycle across all entry points follows this exact trace:

```
[ User Request / CLI Input ]
            │
            ▼
[ resolve_task_input() ] (Reads embedded files, quotes, absolute paths)
            │
            ▼
[ Orchestrator.run_task(task, mode, workspace) ]
            │
            ▼
[ Pipeline Instantiation ] (DevTestLoop | FullPipeline | AuditPipeline | AuditFixPipeline | DocsPipeline)
            │
            ▼
[ BasePipeline._setup_run() ]
   ├── StateMachine -> INIT
   ├── SkillResolver.resolve() -> Auto-inject skills into role configs
   ├── GitOps.init_repo() & create_task_branch()
   ├── TelemetryRecorder, SessionLogStore, LiveVisualizer initialized
   └── Graft architecture map cached & injected
            │
            ▼
[ Phase-Specific Agent Loop ] (Architect -> Developer -> Tester -> Reviewer / Auditor)
   ├── ContextManager.build_prompt() (Task + Injected Context clamped to token ceiling)
   ├── Conversation(agent, workspace, visualizer)
   ├── Background Monitor Thread starts (1.0s poll for Timeout, Token Ceiling, Investigation Kill, Controller Stop)
   ├── conv.run() (OpenHands SDK agent step cycle)
   ├── Post-run state evaluation & visualizer teardown
   └── Incident / Metric recording
            │
            ▼
[ Verification Gate ]
   ├── PreFlightGuard.check_syntax() & check_importability() (Zero-Token Static Gate)
   └── _execute_tests() -> PytestOutputParser.classify_execution()
            │
            ▼
[ BasePipeline._finalize_pipeline() ]
   ├── StateMachine -> COMMIT / COMPLETED / FAILED
   ├── Telemetry report generated & saved to disk (diagnostics/reports/run_*.json)
   ├── Git auto-commit created on success (if enabled)
   ├── Conversation memory saved (diagnostics/memory/)
   └── SessionLogStore saved & interactive log viewer displayed (if TTY)
```

---

# 5. Pipeline Inventory

ORAGAI contains 5 distinct pipelines with substantial duplicated boilerplate:

| Pipeline | Entry Class | Primary Purpose | Agents Involved | Termination Conditions | Duplicated Boilerplate Areas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dev-Test Loop** | `DevTestLoop` | Fast implementation & unit test iteration (MVP) | Developer, Tester | `pytest exit_code == 0`, max iterations exhausted, circuit breaker trip, budget exhausted, controller abort. | `_setup_run`, `_run_conv`, monitor thread, preflight checks, test execution, checkpointing. |
| **Full Pipeline** | `FullPipeline` | 4-agent waterfall engineering lifecycle | Architect, Developer, Tester, Reviewer | Reviewer approval + tests passing, review cycle limit (2 cycles), budget exhaustion, controller abort. | Same as Dev-Test Loop plus approval gate handling and milestone loop iteration. |
| **Audit Pipeline** | `AuditPipeline` | Static AST + lint + LLM architectural inspection | Auditor (Reviewer LLM) | Auditor writes `AUDIT_REPORT.md` and `audit_findings.json`, max steps (20), budget exhaustion. | Static metrics collection, visualizer setup, telemetry recording, report file normalization. |
| **Audit-Fix Loop** | `AuditFixPipeline` | Automated remediation of audit findings backlog | Developer | Backlog empty, all findings quarantined by circuit breaker, max iterations reached. | Standalone custom loop (1,282 LOC), custom git diffing, custom test execution, custom report rotation. |
| **Documentation Pipeline** | `DocumentationPipeline` | Authoring README, architecture, and API docs | DocumentationAgent | Single conversation pass completion, token exhaustion. | `_setup_run`, conversation execution, telemetry logging, finalization. |

---

# 6. FSM (State Management) Analysis

### Source Inspection
In `orchestrator/pipeline/state_machine.py`:
* `PipelinePhase` defines 12 phases: `INIT`, `ARCHITECT`, `DEVELOP`, `PREFLIGHT`, `TEST`, `FIX`, `REVIEW`, `HUMAN_GATE`, `COMMIT`, `COMPLETED`, `FAILED`, `ABORTED`.
* `ALLOWED_TRANSITIONS` is a static dictionary mapping each phase to a set of allowed destination phases.
* `can_transition(target)` performs `target in self.ALLOWED_TRANSITIONS.get(self._current_phase, set())`.
* `transition_to(target)` raises `ValueError` on invalid transitions and updates `self._current_phase`.

### Architectural Verdict
> **The current FSM does NOT govern lifecycle correctness. It merely acts as a passive navigation validator.**

#### Evidence:
1. **Zero Guard Predicates:** There are no callable guards or assertion rules evaluated during `transition_to()`. The FSM does not check if tests actually passed, if files were written, or if acceptance criteria were satisfied.
2. **Bypass Capability:** A pipeline can call `state_machine.transition_to(PipelinePhase.COMPLETED)` without executing tests or review, provided the transition is structurally listed in `ALLOWED_TRANSITIONS`.
3. **External State Logic:** All real transition decisions are hardcoded in procedural `if/else` statements inside `dev_test_loop.py` and `full_pipeline.py`.

---

# 7. Agent Runtime & Termination Analysis

ORAGAI wraps OpenHands SDK conversations via `BasePipeline._run_conv()` ([base_pipeline.py:L190-540](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L190-L540)).

### Comprehensive Termination Mechanisms Matrix

| Termination Mechanism | Trigger / Root Cause | Detecting Entity | Return Contract State | Interpretation by ORAGAI | False Success Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Natural LLM Completion** | Agent emits message with no tool calls. | OpenHands SDK | `ConvRunResult.completed = True` | Phase finished normally; proceeds to next pipeline step. | **HIGH**: Agent may say "I have designed the plan" without calling tools to write `PLAN.md`. |
| **Step Exhaustion** | Agent reaches `max_iteration_per_run` (5–20 steps). | OpenHands SDK | `ConvRunResult.completed = True` (defaults to True) | Phase marked successful; moves to next phase despite truncated work. | **CRITICAL**: Primary cause of micro-stubs and incomplete implementations. |
| **Investigation Token Exhaustion** | Agent consumes 28% of turn token budget without file edit. | ORAGAI Monitor Thread (`DynamicTokenGovernor`) | `ConvRunResult.completed = False`, `interrupted_by_tokens = True` | Agent halted; conversation ends; pipeline proceeds with whatever partial state exists. | **CRITICAL**: Kills legitimate exploratory reading and dependency analysis. |
| **Hard Turn Token Ceiling** | Agent turn consumes total allocated turn tokens. | ORAGAI Monitor Thread | `ConvRunResult.completed = False`, `interrupted_by_tokens = True` | Agent halted; turn ends; loop proceeds. | **MEDIUM**: Truncates complex edits mid-stream. |
| **Turn Timeout** | Conversation wall-clock time exceeds `timeout_seconds` (default 300s). | ORAGAI Monitor Thread | `ConvRunResult.completed = False`, `interrupted_by_timeout = True` | Agent halted; conversation ends. | **LOW**: Necessary safety stop for hung subprocesses. |
| **Pipeline Controller Abort** | Human operator or external signal stops pipeline. | `PipelineController.check_should_continue()` | `ConvRunResult.completed = False`, `interrupted_by_controller = True` | Pipeline aborts immediately; returns `status: "STOPPED"`. | **ZERO**: Correctly records stop. |
| **Global Dollar Budget Ceiling** | Total session spend reaches `max_budget_usd`. | `BudgetGuard.update_cost()` | Exception / Return `BUDGET_EXHAUSTED` | Halts entire pipeline; generates diagnostic report. | **ZERO**: Proper monetary guard. |
| **Unrecoverable Provider Quota (429)** | Daily free-tier or paid quota exhausted. | `_run_conv()` exception handler | Raises `ProviderQuotaExceededError` | Halts execution cleanly with user remediation advice. | **ZERO**: Accurate error handling. |
| **Runner / Trampoline Crash** | Windows subprocess or launcher fails (e.g. `uv trampoline`). | `PytestOutputParser.is_runner_crash()` | `TestExecutionStatus.INFRASTRUCTURE_ERROR` | Halts loop immediately to prevent damaging code edits; attempts auto-heal. | **ZERO**: Excellent protective guard. |

---

# 8. Resource Governance vs. Work Governance Analysis

A critical architectural flaw in ORAGAI is the entanglement of **Resource Safety Governance** with **Work Lifecycle Governance**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RESOURCE GOVERNANCE (Safety Net)                     │
│  - Total Session Dollar Ceiling (e.g., $0.50)                           │
│  - Maximum Wall-Clock Timeout (e.g., 300s)                              │
│  - Model Context Window Limit (e.g., 8K output tokens)                  │
│  - Memory / Process Isolation                                           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │  CONFLATED & COLLAPSED INTO
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    WORK GOVERNANCE (Domain Progress)                    │
│  - Micro-Step Quotas (5 steps for Developer)                            │
│  - Investigation Token Kill (28% of budget before edit)                 │
│  - Forced Prompt Exits (Step 4-5 forced exit in Audit)                  │
│  - File Read Clamps (250 lines / 12K chars)                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Forensic Distinctions
* **Resource Governance** protects the user's wallet, hardware, and API limits. It should act as an out-of-band asynchronous safety net.
* **Work Governance** ensures that tasks are fully understood, decomposed, implemented, and verified against domain requirements.
* **The Current Failure:** ORAGAI applies micro-resource throttles *as if they were work completion criteria*, choking agent cognitive loops before meaningful software engineering can take place.

---

# 9. Completion Semantics Analysis

### Signals Table

| Completion Signal | Subsystem Source | Actual Code Condition | Actual Operational Meaning | Can It Produce False Success? |
| :--- | :--- | :--- | :--- | :--- |
| `pytest exit_code == 0` | `DevTestLoop` / `FullPipeline` | `test_result.status == TestExecutionStatus.PASSED` | Pytest process exited with 0. | **CRITICAL**: If Developer generated 1 trivial test asserting `True`, or if zero tests were written, it registers complete feature success. |
| `ConvRunResult.completed` | `BasePipeline._run_conv()` | `conv.run()` returned without unhandled Python exception. | OpenHands conversation loop finished (either naturally or via step exhaustion). | **CRITICAL**: OpenHands hitting step limit (e.g., step 5 of 5) returns cleanly, registering `completed=True`. |
| Reviewer Approval | `FullPipeline` | `ReviewerVerdict.approved == True` | Reviewer emitted "APPROVED" in JSON or markdown text. | **HIGH**: Reviewer evaluated a 4,000-char truncated diff without viewing test executions or requirements. |
| Git Working Tree Status | `BasePipeline._finalize_pipeline()` | `self.git.commit(commit_msg)` | Git created a commit object. | **MEDIUM**: Proves files changed, not that the code works. |
| FSM `COMPLETED` | `PipelineStateMachine` | `transition_to(PipelinePhase.COMPLETED)` | FSM reached final enum state. | **HIGH**: Reflects only that the pipeline procedural script reached line 710. |

### Requirement Representation Gap
ORAGAI has **zero formal representation** of:
1. User Requirement Decomposition (Requirement ID, Description, Expected Behavior).
2. Acceptance Criteria.
3. Test-to-Requirement Traceability Matrix.
4. Requirement Verification Evidence.

---

# 10. Progress Detection & Semantic Analysis

### Current Progress Detection Mechanisms
1. **Diff Hash & Error Hash Comparison:** `TelemetryRecorder.check_circuit_breaker()` computes SHA-256 of `git diff` and pytest error text.
2. **Failing Test Set Comparison:** Extracts `FAILED tests/test_*.py::test_name` via regex.
3. **Error Text Similarity Ratio:** `difflib.SequenceMatcher` calculating similarity $\ge 0.88$.
4. **Action Classification:** `DynamicTokenGovernor.classify_action()` classifies tool calls into `INVESTIGATION`, `IMPLEMENTATION`, `TESTING`.

### System Capability Breakdown

| Progress Phenomenon | Can Current ORAGAI Detect? | How It Is Handled | Forensic Evaluation |
| :--- | :--- | :--- | :--- |
| **Real Progress** | Partially | Different diff hash or different test failure signature. | Works when error signatures change. |
| **Semantic No-Op** | No | Agent modifying comments or formatting produces a new diff hash, resetting circuit breaker. | **Vulnerable to loop exploitation.** |
| **Cosmetic Change** | No | Treated as valid new implementation step. | Fails to detect superficial churn. |
| **Regression** | Partially | If previously passing tests fail, classified as `TEST_FAILURE`. | Detected only if test suite runs all tests. |
| **Circular Fix** | Partially | If exact same error repeats after 2 iterations, circuit breaker trips. | Fails if error alternates across 3 states (A $\rightarrow$ B $\rightarrow$ A). |
| **Strategy Change** | No | If agent spends 28% tokens researching a new strategy, `DynamicTokenGovernor` kills it. | **Mistakes deep investigation for stagnation.** |
| **Investigation** | Poorly | Reading files or inspecting AST without edits is penalized after 28% turn budget. | **Primary cause of investigation starvation.** |

---

# 11. Circuit Breakers & Recovery

### Circuit Breakers Inventory

| Breaker Name | Location | Trigger Condition | Action Taken | Recovery Mechanism | False Positive Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Investigation Breaker** | `token_governance.py:L237` | `investigation_consumed >= investigation_budget` (28%) with `has_performed_edit == False` | `conv.interrupt()` halts agent conversation. | None (turn terminates). | **CRITICAL**: Halts agents exploring medium/large codebases. |
| **Semantic Test Breaker** | `telemetry/recorder.py:L236` | 2 consecutive iterations with identical error hash, identical failed test set, or error similarity $\ge 0.88$. | Aborts test/fix loop (`CIRCUIT_BREAKER_ABORT`). | Resets count if diff and error change. | **MEDIUM**: Trips if Developer needs 2 iterations to diagnose a complex multi-stage bug. |
| **Budget Guard** | `control/budget_guard.py` | Accumulated cost $\ge \text{max\_budget\_usd}$ ($0.50). | Aborts pipeline with `BUDGET_EXHAUSTED`. | None (hard monetary ceiling). | **LOW**: Legitimate cost protection. |
| **Finding Breaker** | `pipeline/audit_fix_pipeline.py` | Single audit finding fails remediation 2 times. | Quarantines finding; proceeds to next finding in backlog. | Skips poisoned finding; cleans remaining backlog. | **LOW**: Effective backlog isolation. |

---

# 12. Context & Information Handoffs

### Cross-Agent Information Flow

```
[ User Task ]
      │
      ▼
[ Architect ] ──( Writes PLAN.md )──► [ Disk: PLAN.md ]
                                            │
                                            ▼ (MilestoneParser extracts milestones)
                                      [ Developer ]
                                            │
                                            ▼ (Writes code files)
                                      [ Disk: Code ]
                                            │
                                            ▼ (Inspects code via tools)
                                      [ Tester ]
                                            │
                                            ▼ (Writes tests/test_*.py)
                                      [ Pytest Execution ]
                                            │
                                            ▼ (4,000-char compact diff + git status)
                                      [ Reviewer ]
```

### Context Asymmetries & Truncation Losses
1. **Architect $\rightarrow$ Developer:** If Architect fails to invoke `workspace_file` to write `PLAN.md`, `FullPipeline` falls back to regex event scraping ([full_pipeline.py:L157-185](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L157-L185)). If that fails, Developer receives raw task text with zero architectural design.
2. **Developer $\rightarrow$ Tester:** Tester receives only raw task text and an instruction to inspect code. Tester does *not* receive `PLAN.md` or the Architect's test strategy.
3. **Tester $\rightarrow$ Developer (Fix Loop):** Developer receives only compact pytest failure tracebacks. Developer loses sight of overall task goals and focuses solely on silencing the specific test assertion.
4. **Developer/Tester $\rightarrow$ Reviewer:** Reviewer receives a diff clamped to 4,000 characters ([full_pipeline.py:L630](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L630)). On large features, the majority of the diff is omitted (`[... Diff truncated ...]`), forcing Reviewer to judge based on incomplete information.

---

# 13. Tooling & Context Windows Analysis

### Custom Tool Suite (`orchestrator/tools/workspace_tools.py`)

| Tool / Capability | Declared Safety Goal | Implementation Reality | Engineering Impact |
| :--- | :--- | :--- | :--- |
| **`WorkspaceFileTool.read`** | Prevent token context ballooning | Clamps file reading to 250 LOC and 12,000 characters (~3,000 tokens). | Agents cannot read 400-line files in one pass; must paginate or guess missing lines. |
| **`WorkspaceFileTool.symbol`** | Zero-token AST symbol inspection | Parses AST and extracts exact class/function bounds with line numbers. | **High Value**: Deterministic, zero hallucination, token-efficient. |
| **`WorkspaceFileTool` RBAC** | Prevent unauthorized file modifications | Restricts Developer from writing to `tests/`, restricts Architect to `PLAN.md`, restricts Auditor to `docs/`. | **High Value**: Enforces role boundaries and prevents Developer from deleting failing tests. |
| **`WorkspaceTerminalTool`** | Sandboxed shell execution | Parameterized subprocess execution, environment variable masking, command allowlist. | **High Value**: Blocks command injection and protects secrets. |
| **Command Chaining Ban** | Prevent shell escape & injection | `split_and_validate_command` bans `{";", "&&", "||", "|", "&"}`. | **Defect**: Banned pipe `\|` prevents legit commands like `cat file.py \| head -n 20` even after Sentinel translation. |

---

# 14. Audit Pipeline Analysis

### Forensic Inspection of `AuditPipeline`
In `orchestrator/pipeline/audit_pipeline.py:L158-174`:
```python
"STRICT CONSTRAINTS & INSTRUCTIONS (MANDATORY 2-PHASE WORKFLOW):\n"
"PHASE 1 (Inspection - Max 3-4 steps):\n"
"1. Perform targeted inspection of 2-3 key hotspot files and architecture boundaries. Do NOT run repetitive or unbounded terminal exploration scripts.\n"
"PHASE 2 (Report Generation - MUST EXECUTE AT STEP 4-5):\n"
"2. Produce the exhaustive architectural audit in `docs/AUDIT_REPORT.md` (under `docs/`) and write verified structured findings to `docs/audit_findings.json`...\n"
```

### Forensic Verdict
1. **The 98/100 Flattery Trap:** Because the Auditor is explicitly commanded to inspect only 2-3 files and terminate at step 4-5, it cannot audit a 150-file repository. It outputs a generic praise report declaring "Architecture Health: 98/100" with `findings: []`.
2. **Downstream Starvation:** When `AuditFixPipeline` executes, it reads `docs/audit_findings.json`, finds zero actionable findings, and immediately terminates without performing remediation work.

---

# 15. Testing System Analysis

### What `pytest PASSED` Proves:
* The specific test assertions executed in the test files evaluated to `True`.
* The Python interpreter did not raise an unhandled exception during test execution.
* The test command exited with return code 0.

### What `pytest PASSED` Does NOT Prove:
* That user requirements were satisfied.
* That edge cases were tested.
* That newly added business logic has non-trivial assertions.
* That the implementation is not a hardcoded stub returning a constant value to satisfy a single test.
* That complete code coverage was achieved.

---

# 16. Reviewer System Analysis

### Forensic Audit of Reviewer Agent
* **Model Independence:** `create_reviewer_agent()` warns if Reviewer uses the same model as Developer ([reviewer.py:L54-61](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/agents/reviewer.py#L54-L61)).
* **Input Clamping:** Reviewer receives at most 4,000 characters of diff summary ([full_pipeline.py:L630](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L630)).
* **Verdict Parsing:** `ReviewerVerdict.parse()` attempts JSON parsing, then `ast.literal_eval`, and finally falls back to regex search for approval markers like `VERDICT: APPROVED` ([reviewer_parser.py:L76-88](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/reviewer_parser.py#L76-L88)).
* **Weakness:** Reviewer has no visibility into original user acceptance criteria or test execution outputs, making it purely a superficial code-style checker.

---

# 17. Git & Finalization Analysis

### Git Lifecycle Trace
1. **Branch Isolation:** `BasePipeline._setup_run()` creates an isolated Git branch (`task/<sanitized-title>`).
2. **Auto-Commit:** `BasePipeline._finalize_pipeline()` stages all files (`git add -A`) and commits if `success == True` and `config.auto_commit == True`.
3. **Flaw:** Because `success` is determined solely by `tests_passed` (or `tests_passed and review_approved`), incomplete micro-stubs that pass trivial tests are automatically committed to Git as verified features.

---

# 18. Security & Safety Invariants

The following security controls represent core system assets and **must never be compromised**:

| Security Control | Implementation Mechanism | Invariant Purpose | Classification |
| :--- | :--- | :--- | :--- |
| **Workspace Sandboxing** | `WorkspaceFileAction` path resolution with `target_path.relative_to(workspace_root)` | Prevents path traversal and modification of files outside workspace root. | **MUST PRESERVE** |
| **Sensitive File Masking** | `is_sensitive_file()` blocking `.env`, `id_rsa`, `.pem`, `.key`, `credentials.json` | Prevents agents from reading or modifying API keys and cryptographic secrets. | **MUST PRESERVE** |
| **Credential Sanitization** | `sanitize_output_secrets()` redacting env tokens & regex API keys from stdout/file obs | Prevents LLM context and log leakage of API keys. | **MUST PRESERVE** |
| **Terminal Subprocess Isolation** | `execute_terminal_action()` sanitizing `os.environ` before spawning child processes | Prevents child shell processes from inheriting API keys. | **MUST PRESERVE** |
| **Role-Based Access Control (RBAC)** | `allowed_write_prefixes` & `blocked_write_prefixes` on `WorkspaceFileTool` | Prevents Developer from tampering with tests and Architect from modifying source. | **MUST PRESERVE** |
| **Command Whitelist** | `get_allowed_command_binaries()` verifying argv[0] against approved tool set | Prevents arbitrary binary execution and malicious shell invocations. | **MUST PRESERVE** |
| **Subprocess Timeout Guards** | `timeout_seconds` in `subprocess.run` & Conversation monitor thread | Prevents zombie background processes and infinite execution hangs. | **MUST PRESERVE** |
| **Human Escalation Channel** | `HumanInterventionChannel.request_permission()` for blocked operations | Enables Human-in-the-Loop oversight for security-sensitive operations. | **CAN REFACTOR** |
| **Command Chaining Ban** | `DANGEROUS_CHAINING_TOKENS` blocking `;`, `&&`, `\|\|`, `\|`, `&` | Protects against injection, but blocks valid pipes. Needs intelligent grammar parsing. | **CAN REFACTOR** |

---

# 19. Windows Runtime Analysis

ORAGAI runs natively on Windows NT (PowerShell / CMD).

### Verified Windows Adaptations
1. **UTF-8 Standard Stream Reconfiguration:** `sys.stdout.reconfigure(encoding="utf-8")` in CLI entry points prevents `UnicodeEncodeError` on Windows console.
2. **Python Launcher Resolution:** `BasePipeline._execute_tests()` detects launcher crashes and auto-heals commands (e.g. converting `pytest` $\rightarrow$ `python -m pytest` and fixing `uv trampoline` failures with spaces in paths).
3. **PowerShell Cmdlet Execution:** Windows built-ins and PowerShell cmdlets (`Get-ChildItem`, `Select-String`) are explicitly routed to `powershell.exe -NoProfile -NonInteractive -Command`.
4. **Virtual Environment Script Pathing:** `workspace_tools.py` checks for `.venv/Scripts` on Windows vs `.venv/bin` on POSIX.

---

# 20. Observability & Telemetry Gaps

### Current Capabilities (`TelemetryRecorder`)
* Captures step durations, token consumption (prompt/completion/total), and estimated cost in USD.
* Records discrete incidents (`preflight_error`, `test_failure`, `circuit_breaker`, `budget_exceeded`).
* Computes Progress Efficiency Ratio (PER).
* Saves structured JSON diagnostic reports to `diagnostics/reports/run_*.json`.

### Critical Missing Telemetry Signals
* Requirement Satisfaction Rate (percentage of requirements verified).
* Test Assertion Quality & Test Count Delta (tracking whether new tests were actually written).
* Context Truncation Events (recording when prompts, diffs, or file reads were clamped).
* Agent Termination Reason (explicitly logging whether conversation ended naturally vs step exhaustion vs token kill).

---

# 21. Root Cause Classification Matrix

| Finding / Pathology | Classification | Evidence & Impact |
| :--- | :--- | :--- |
| **Equating `pytest exit_code == 0` with complete task success** | **PROVEN ROOT CAUSE** | Directly causes premature termination and micro-stub commits when 0 or 1 trivial test passes. |
| **Step Exhaustion defaulting to `completed = True`** | **PROVEN ROOT CAUSE** | OpenHands step cutoffs are interpreted as successful work completion. |
| **Investigation Circuit Breaker killing agents at 28% tokens** | **PROVEN ROOT CAUSE** | Directly prevents agents from reading codebases and exploring dependencies before editing. |
| **Auditor prompt mandating step 4-5 exit and 2-3 files limit** | **PROVEN ROOT CAUSE** | Directly causes the 98/100 flattery trap and 0 actionable findings in audits. |
| **FSM lacking guard predicates and evidence validation** | **CONTRIBUTING FACTOR** | FSM cannot reject invalid stage transitions or enforce quality prerequisites. |
| **Reviewer diff truncation to 4,000 characters** | **CONTRIBUTING FACTOR** | Forces Reviewer to rubber-stamp changes without seeing the complete implementation. |
| **Zero-Token Tester Skip on iteration $>1$ without requirement verification** | **CONTRIBUTING FACTOR** | Prevents the creation of new tests for unaddressed requirements during fix cycles. |
| **File read clamping to 250 LOC / 12,000 characters** | **CONTRIBUTING FACTOR** | Creates context fragmentation on large source files. |
| **Command chaining ban blocking shell pipes (`\|`)** | **CONTRIBUTING FACTOR** | Causes legitimate translated inspection commands to fail. |
| **Shallow code implementations & stub methods** | **SYMPTOM** | Observable result of micro-step budgets and premature pytest loop exit. |
| **0 actionable findings in audit reports** | **SYMPTOM** | Observable result of forced step 4-5 exit prompt and 2-3 file inspection limit. |
| **OpenHands SDK background thread polling overhead** | **UNVERIFIED HYPOTHESIS** | Hypothesized to introduce latency; requires benchmark profiling against synchronous hooks. |

---

# 22. Proven vs. Unverified Findings

### Proven Facts (Validated by Code & Test Execution)
1. **FACT:** `PipelineStateMachine` enforces only transition name legality and performs zero quality or artifact verification (`tests/test_phase5_improvements.py`).
2. **FACT:** `DynamicTokenGovernor` sets `max_agent_steps = 5` for single-file tasks and halts exploration if 28% budget is consumed without edits (`tests/test_token_governance.py`).
3. **FACT:** `DevTestLoop` breaks out of the iteration loop on the very first occurrence of `TestExecutionStatus.PASSED` without inspecting test counts or requirements (`dev_test_loop.py:L277-280`).
4. **FACT:** `WorkspaceFileTool` enforces strict sandboxing, RBAC write scopes, and secret masking (`tests/test_tools.py`, `tests/test_permission_escalation.py`).
5. **FACT:** The test suite contains 244 passing tests that execute deterministically in ~22.5 seconds.

### Unverified Hypotheses (Requiring Future Runtime Experiments)
1. **HYPOTHESIS:** Removing the 28% investigation token kill will increase task completion depth without causing runaway token loops if bounded by an evidence-based progress detector. (*Requires controlled benchmark experiment*).
2. **HYPOTHESIS:** Providing the Reviewer with full AST symbol diffs and test logs instead of a 4K truncated text diff will increase defect detection accuracy by $>50\%$. (*Requires benchmark experiment*).

---

# 23. System Invariants

Future architectural redesigns **MUST NEVER VIOLATE** these core system invariants:

### 1. Workspace Isolation Invariant
* **Statement:** No agent or tool action shall read, write, or delete files outside the configured workspace directory root.
* **Why it matters:** Prevents accidental modification or destruction of host system files and repository source code.
* **Current Implementation:** `target_path.relative_to(workspace_root)` validation in `orchestrator/tools/workspace_tools.py`.
* **Tests Protecting It:** `tests/test_tools.py::test_file_tool_path_traversal_blocked`.
* **What could break it:** Introducing un-sandboxed file tools or naive string concatenation for path resolution.

### 2. Secret & Credential Protection Invariant
* **Statement:** Sensitive environment files (`.env*`), private keys, and credential tokens must never be readable by agents, passed to child subprocesses, or leaked into LLM prompts/logs.
* **Why it matters:** Prevents leakage and unauthorized use of LLM provider keys and system credentials.
* **Current Implementation:** `is_sensitive_file()`, `sanitize_output_secrets()`, and `env` sanitization in `workspace_tools.py`.
* **Tests Protecting It:** `tests/test_tools.py::test_sensitive_file_protection`, `tests/test_phase20_round11_hardening.py::test_subprocess_env_masks_sensitive_api_keys`.
* **What could break it:** Passing raw `os.environ` to subprocesses or relaxing file read filters.

### 3. Role-Based Access Control (RBAC) Invariant
* **Statement:** Agent roles must strictly adhere to their assigned write boundaries (Architect $\rightarrow$ `PLAN.md`; Developer $\rightarrow$ source files, blocked from `tests/` in dev-test mode; Tester $\rightarrow$ `tests/`; Auditor $\rightarrow$ `docs/`; Reviewer $\rightarrow$ read-only).
* **Why it matters:** Prevents Developer agents from altering test assertions to create artificial test passes, and prevents Architects/Auditors from making unverified code changes.
* **Current Implementation:** `allowed_write_prefixes` and `blocked_write_prefixes` in `WorkspaceFileTool`.
* **Tests Protecting It:** `tests/test_permission_escalation.py`, `tests/test_tools.py::test_rbac_file_restrictions`.
* **What could break it:** Granting universal write permissions to all agent roles.

### 4. Monetary & Execution Safety Invariant
* **Statement:** Every execution run must be strictly bounded by a global dollar budget ceiling (`max_budget_usd`) and wall-clock timeout.
* **Why it matters:** Protects users against infinite loops and catastrophic API spend.
* **Current Implementation:** `BudgetGuard` in `orchestrator/control/budget_guard.py` and timeout monitors in `base_pipeline.py`.
* **Tests Protecting It:** `tests/test_phase1_improvements.py::test_telemetry_recorder_token_tracking_and_budget_guard`, `tests/test_phase5_improvements.py::test_pipeline_controller_and_budget_guard`.
* **What could break it:** Bypassing `BudgetGuard` checks in newly introduced execution pipelines.

### 5. Deterministic Zero-Token Verification Invariant
* **Statement:** Syntax compilation, AST verification, and unit test execution on fix iterations $>1$ must execute deterministically via local tools without consuming LLM tokens.
* **Why it matters:** Prevents wasteful token burn and hallucinations on deterministic operations.
* **Current Implementation:** `PreFlightGuard.check_syntax()` and `DevTestLoop` Zero-Token Tester Skip.
* **Tests Protecting It:** `tests/test_phase2_improvements.py::test_preflight_guard_detects_syntax_errors`.
* **What could break it:** Invoking LLM agents to evaluate simple syntax errors or re-run existing tests.

---

# 24. Baseline Metrics Specification

Before implementing any architectural changes, the following baseline metrics must be tracked:

| Metric Name | Measurement Unit | Current State in Repository | Planned Forensic Target |
| :--- | :--- | :--- | :--- |
| **Task Completion Rate** | Percentage (%) | NOT CURRENTLY MEASURED | Track true requirement satisfaction. |
| **False Completion Rate** | Percentage (%) | NOT CURRENTLY MEASURED | Measure cases where tests pass but requirements are unmet. |
| **Requirement Coverage** | Ratio (Met / Total) | NOT CURRENTLY MEASURED | Track formal requirement coverage. |
| **Agent Steps per Task** | Integer count | Measured in Telemetry (`StepMetric`) | Measure turn consumption by role. |
| **Total LLM Tokens** | Integer count | Measured in Telemetry (`DiagnosticReport`) | Track prompt vs completion tokens. |
| **Total Cost** | USD ($) | Measured in Telemetry (`total_cost_usd`) | Track monetary cost per task. |
| **Execution Duration** | Seconds (s) | Measured in Telemetry (`total_duration_seconds`) | Track wall-clock execution time. |
| **Tool Calls by Type** | Count per tool | NOT CURRENTLY MEASURED (Aggregated only) | Track file vs terminal vs AST calls. |
| **Files Inspected vs Modified** | Count | Partial (`diff_size_bytes`) | Track exploration depth vs edit scope. |
| **Tests Generated & Passed** | Count | Extracted via Pytest regex | Track test count delta across iterations. |
| **Reviewer Rejection Rate** | Percentage (%) | Measured in Telemetry (`StepMetric.success`) | Track critique vs approval frequency. |
| **Circuit Breaker Triggers** | Count | Measured in Telemetry (`circuit_breaker_triggered`) | Track false positive vs true stall triggers. |
| **Investigation Kills** | Count | Logged to console warnings | Formally measure investigation starvation. |

---

# 25. Benchmark Specification

To evaluate ORAGAI and prevent regressions during redesign, a standard benchmark of 8 representative tasks is defined:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       ORAGAI EVALUATION BENCHMARK                       │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. BM-01: Single-File Bug Fix (Systematic Debugging)                   │
│ 2. BM-02: Multi-File Feature Implementation (Milestone DAG)             │
│ 3. BM-03: Architectural Refactoring & Boundary Decoupling               │
│ 4. BM-04: Deep Codebase Security & Bug Audit (100+ Files)               │
│ 5. BM-05: Autonomous Audit-Fix Remediation Loop                         │
│ 6. BM-06: New Subsystem Design & Delivery (Full Pipeline)               │
│ 7. BM-07: Cross-Platform (Windows/POSIX) CLI Tool Implementation        │
│ 8. BM-08: Stagnation & Failure Recovery (Circuit Breaker Resilience)    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Benchmark Task Definitions

#### BM-01: Single-File Bug Fix
* **Task:** Fix an edge-case concurrency race condition in a thread-safe token bucket rate limiter.
* **Requirements:** Preserve public API; handle zero and negative refill rates; enforce atomic thread safety.
* **Acceptance Criteria:** Rate limiter passes all edge-case concurrency tests with 100 concurrent threads.
* **Expected Evidence:** Unit tests with assertions covering concurrent refills and exhausted tokens.
* **Detection Goal:** Verify that Developer does not generate a shallow stub or exit without concurrency tests.

#### BM-02: Multi-File Feature Implementation
* **Task:** Implement an in-memory caching engine with LRU eviction, TTL expiration, and disk persistence.
* **Requirements:** 3 distinct modules (`cache_store.py`, `eviction_policy.py`, `persistence.py`).
* **Acceptance Criteria:** All 3 modules fully implemented with type hints; zero `# TODO` or placeholder methods.
* **Expected Evidence:** Comprehensive unit tests for TTL expiry and eviction order; runnable `demo.py`.
* **Detection Goal:** Verify that Developer executes all milestones and does not terminate after writing only 1 file.

#### BM-04: Deep Codebase Security & Bug Audit
* **Task:** Conduct a full architecture and security audit of a 50+ file Python repository.
* **Requirements:** Inspect module boundaries, secret leaks, subprocess injections, and DRY violations.
* **Acceptance Criteria:** Generates `docs/AUDIT_REPORT.md` and structured `docs/audit_findings.json` with verifiable line-level evidence.
* **Expected Evidence:** At least 5 verified findings with concrete code snippets; no flattery scores.
* **Detection Goal:** Detect and eliminate the 98/100 Flattery Trap and step 4-5 forced exit mandate.

---

# 26. Future Change Safety Contract

All future design and implementation plans (P1, P2, P3, etc.) **MUST COMPLY** with these mandatory rules:

1. **No Production Modification Without Plan Approval:** No Python source file in `orchestrator/` shall be modified without an approved design specification.
2. **No Weakening of Security Invariants:** Workspace sandboxing, secret masking, RBAC write scopes, and command allowlists must remain strictly intact or be replaced only with strictly superior controls.
3. **No Unconstrained Limit Increases:** Token budgets and step limits shall not be increased globally without attaching evidence-based progress monitoring and cost ceilings.
4. **Separation of Concerns Mandate:** Resource safety governance (out-of-band circuit breakers) must be kept strictly decoupled from work lifecycle completion (requirement verification).
5. **No False Completion Signals:** A pipeline stage must never register `SUCCESS` based solely on process exit codes or conversation step exhaustion without validating evidence and artifacts.
6. **Behavioral Parity Testing:** Any consolidation or refactoring of pipelines must pass all 244 existing tests with zero regressions.

---

# 27. Dependencies for P1

The upcoming **P1 — Architectural Redesign & Unification Plan** will depend upon the following verified outputs from P0:

1. **The Verified Responsibility Matrix:** ORAGAI acts as the Quality/Governance Plane; OpenHands SDK acts as the Agent Execution Runtime.
2. **The FSM Diagnosis:** The FSM must be evolved from a passive enum router into a true **Guarded Evidence-Driven State Machine**.
3. **The Termination Reality:** OpenHands SDK step limit completion semantics must be wrapped with explicit exit-status classifiers to eliminate silent false success.
4. **The Tooling Baseline:** `WorkspaceFileTool` and `WorkspaceTerminalTool` are proven enterprise assets that must be preserved and enhanced with grammar-based command validation.
5. **The Benchmark Framework:** All P1 architectural proposals will be measured against the 8 benchmark task classes defined in Section 25.

---

# 28. Open Questions

1. **OpenHands SDK Event Hooks:** Does OpenHands SDK v1.49.4 support synchronous step event listeners, or must ORAGAI continue using the background polling thread for real-time turn monitoring?
2. **MCP Service Extraction Boundary:** Should codebase intelligence (`Graft`) and static AST auditing be extracted into a standalone MCP server (`oragai-sre-mcp`) during P2, or maintained as in-process services?
3. **Dynamic Step Sizing:** What is the optimal mathematical formulation for dynamically allocating agent turns based on AST dependency depth rather than fixed file-count tiers?

---

# P0 EXIT CRITERIA

```text
[x] Current architecture is mapped.
[x] All termination paths are identified.
[x] All completion signals are identified.
[x] Resource governance is separated conceptually from work governance.
[x] Current root causes are classified.
[x] Unverified hypotheses are explicitly marked.
[x] Security and architectural invariants are documented.
[x] Baseline metrics are defined.
[x] Benchmark structure is defined.
[x] Future change safety rules are defined.
[x] No production code was modified.
```

---

# INPUT CONTRACT FOR P1

The P1 Architectural Redesign phase is authorized to assume the following verified facts from P0:
* The test suite contains 244 passing tests across 35 test files that must remain passing.
* The 5 existing procedural pipelines (`DevTestLoop`, `FullPipeline`, `AuditPipeline`, `AuditFixPipeline`, `DocumentationPipeline`) share extensive duplicate logic and should be unified under a single Guarded FSM Engine.
* The 98/100 flattery trap in audits and premature completion in dev loops are proven defects rooted in micro-step limits, forced-exit prompts, and binary exit code proxies.
* All security invariants detailed in Section 18 and Section 23 are inviolable constraints.
