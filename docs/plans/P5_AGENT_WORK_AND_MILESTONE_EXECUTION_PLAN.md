# P5 — AGENT WORK & MILESTONE EXECUTION PLAN

> **Document Type:** Canonical Systems Architecture, Agent Workstream & Milestone Execution Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Systems Architect, Multi-Agent Coordination Engineer & Agent Workstream Specialist  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md`, `docs/plans/P1_TASK_TRUTH_AND_REQUIREMENT_MODEL_PLAN.md`, `docs/plans/P2_EVIDENCE_AND_COMPLETION_GATES_PLAN.md`, `docs/plans/P3_GUARDED_FSM_AND_LIFECYCLE_ORCHESTRATION_PLAN.md`, `docs/plans/P4_ADAPTIVE_RESOURCE_GOVERNANCE_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Design Phase:** P5 (Specification & Agent Workstream Engine — Zero Production Code Modified)

---

# 1. Executive Summary & Theoretical Framework

This specification establishes the canonical **Agent Work & Milestone Execution Plan (P5)** for the **ORAGAI** autonomous multi-agent software engineering orchestrator.

### 1.1 The Strategic Position of P5 in the ORAGAI Stack
To date, the architectural redesign of ORAGAI has established:
1. **P0 (Forensic Baseline & Invariants):** Identified the fatal conflation of *Resource Governance* with *Work Completion*, micro-turn cages (5 steps), premature 28% investigation aborts, and passive FSM dictionary lookups.
2. **P1 (Task Truth & Requirement Model):** Established the deterministic entity graph: $\text{Task} \to \text{Requirements} \to \text{Acceptance Criteria} \to \text{Milestones}$.
3. **P2.1 (Evidence Engine & Completion Gates):** Formulated cryptographic content identity (composite SHA-256), orthogonal state dimensions (`ImplementationState`, `VerificationState`, `BlockingState`), and the 14-step deterministic Completion Gate (`TaskTruthSemanticQueries`).
4. **P3 (Guarded FSM & Lifecycle Orchestration):** Inverted the execution loop from procedural scripts to an event-driven `GuardedFSMEngine` that delegates bounded, ephemeral agent turns via Inversion of Control (IoC).
5. **P4 (Adaptive Resource Governance):** Replaced hard micro-caps with dynamic complexity-based turn allocation ($T_{\text{allocated}}$), AST-aware context folding (`ASTAwareContextClamper`), and non-intrusive financial circuit breakers ($5.00 default).

### The Core Mission of P5:
$$\text{While P3 defines the state transitions and P4 computes the bounded turn envelope,}$$
$$\text{\textbf{P5 defines how specialized agent personas operate within those bounded turns}}$$
$$\text{\textbf{to iteratively execute and verify the MilestoneDAG.}}$$

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ORAGAI ARCHITECTURE                                    │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          Guarded FSM Engine (P3)                               │   │
│   └───────────────────────┬────────────────────────────────┬───────────────────────┘   │
│                           │                                │                           │
│     State Transitions     │                                │  Pre-Dispatch Budget      │
│     & Evidence Queries    │                                │  & Context Folding        │
│                           ▼                                ▼                           │
│   ┌───────────────────────────────┐        ┌───────────────────────────────┐           │
│   │  Task Truth & Evidence Engine │        │ Adaptive Resource Governance  │           │
│   │            (P2.1)             │        │             (P4)              │           │
│   │                               │        │                               │           │
│   │ • TaskTruthGraph (P1)         │        │ • AdaptiveBudgetAllocator     │           │
│   │ • CriterionEvidencePolicies   │        │ • ASTAwareContextClamper      │           │
│   │ • SHA-256 Identity Hash       │        │ • MonetaryCircuitBreaker      │           │
│   │ • CompletionGate              │        │ • Turn Envelope (T_allocated) │           │
│   └───────────────────────┬───────┘        └───────────────┬───────────────┘           │
│                           │                                │                           │
│                           └────────────────┬───────────────┘                           │
│                                            │                                           │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                    Agent Workstream & Milestone Engine (P5)                    │   │
│   │                                                                                │   │
│   │  • Persona Role-Based Access Control (RBAC) & Tool Sandboxing                  │   │
│   │  • Anti-Stub, Anti-Hallucination Production System Prompts                     │   │
│   │  • MilestoneDAG Topological Ingestion & Dispatch                               │   │
│   │  • Micro-TDD Authoring Loop (Red -> Green -> Refactor)                         │   │
│   │  • Structured Intra-Turn Cognitive Action Budget (Orient -> Act -> Preflight)  │   │
│   │  • Typed Cross-Agent Handoff Contracts (JSON/Markdown)                         │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │ Ephemeral Bounded Execution               │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        OpenHands SDK Runtime (v1.49.4)                         │   │
│   │                                                                                │   │
│   │   [Architect]   [Developer]   [Tester]   [Reviewer]   [Auditor]   [Remediator] │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.2 The Inversion of Control (IoC) Runtime Contract
In legacy ORAGAI (`base_pipeline.py`, `dev_test_loop.py`), agents were long-lived procedural loops that attempted to run entire workflows end-to-end, leading to state corruption, uncontrolled memory growth, and uncoordinated file mutations.

Under P5's **Inversion of Control (IoC)** architecture:
1. **Agents are Ephemeral Workers:** An agent persona is instantiated solely for the duration of a single bounded FSM turn ($T_{\text{allocated}}$). It possesses no persistent in-memory state across FSM state cycles.
2. **Context is Reconstituted Deterministically:** At the start of every turn, the agent's context is synthesized fresh from:
   - The active `TaskMilestone` slice from `TaskTruthGraph` (P1).
   - The exact diff and AST symbol index of the workspace (P4).
   - The upstream `CrossAgentHandoffPayload` from the preceding persona.
3. **Execution is Constrained by RBAC:** Agents are granted only the minimum tool capabilities and workspace write permissions required for their specific role.
4. **Turns Yield Bounded Artifacts:** Agents do not declare phase transitions or mutate global state. Instead, they emit structured handoff artifacts (diffs, test traces, critique rubrics) and yield control back to the FSM.

---

### 1.3 Inviolable System Invariants
P5 strictly preserves five system-wide architectural invariants:

1. **Zero Production Code Modifications During Planning:** P5 is an architectural specification and design contract. No files in `orchestrator/` are altered during this planning phase.
2. **Ephemeral Agent Invocations:** Agent sessions are stateless across FSM transitions. All cross-phase truth is persisted via `TaskTruthGraph` on disk and Git commits.
3. **Zero Agent Self-Certification:** No persona can mutate `VerificationState` or declare its own work `VERIFIED`. `Developer` records `ImplementationState = IMPLEMENTED`; `Tester` emits raw test execution traces; `VerificationState = VERIFIED` is computed exclusively by deterministic engines (`CompletionGate`) and independent `Reviewer` consensus.
4. **Strict RBAC Sandboxing:** Path-level file permissions and command execution rules are strictly enforced at the tool boundary. Attempted violations fail immediately with security errors.
5. **Zero Stub Invariant:** Developer and Remediation personas are strictly prohibited from generating `# TODO`, `pass`, or `NotImplementedError` stubs in public interfaces. Syntactic and AST guards reject partial implementations before FSM acceptance.

---

# 2. Agent Persona Taxonomy & System Prompt Architecture

ORAGAI defines six specialized, highly disciplined agent personas. Each persona is configured with an explicit operational scope, strict Role-Based Access Control (RBAC) rules, a production-grade system prompt, and deterministic turn yield triggers.

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                PERSONA RBAC & TOOL MATRIX                                 │
├───────────────┬──────────────────────────┬─────────────────────────────┬──────────────────┤
│ Persona       │ Allowed File Operations  │ Allowed Terminal Commands   │ Primary Output   │
├───────────────┼──────────────────────────┼─────────────────────────────┼──────────────────┤
│ Architect     │ Write: `PLAN.md` only    │ `graft map`, `graft skel`,  │ `PLAN.md`,       │
│               │ Read: Full Workspace     │ `graft callers`, `git log`  │ Milestone DAG    │
├───────────────┼──────────────────────────┼─────────────────────────────┼──────────────────┤
│ Developer     │ Write: Source files      │ `python -m py_compile`,     │ Source Code,     │
│               │ Blocked: `tests/`        │ `git diff`, `git status`    │ Implemented ASTs │
├───────────────┼──────────────────────────┼─────────────────────────────┼──────────────────┤
│ Tester        │ Write: `tests/` only     │ `pytest -v`, `pytest -k`,   │ Pytest Suites,   │
│               │ Read: Full Workspace     │ `python -m pytest`          │ Test Node Traces │
├───────────────┼──────────────────────────┼─────────────────────────────┼──────────────────┤
│ Reviewer      │ Read: Full Workspace     │ `git diff`, `git log -p`,   │ Structured JSON  │
│               │ Write: None (Read-Only)  │ `graft map`                 │ Critique Rubric  │
├───────────────┼──────────────────────────┼─────────────────────────────┼──────────────────┤
│ Auditor       │ Write: `docs/` only      │ `graft map`, `git grep`,    │ Audit Reports,   │
│               │ Read: Full Workspace     │ `python -m py_compile`      │ Vulnerability DB │
├───────────────┼──────────────────────────┼─────────────────────────────┼──────────────────┤
│ Remediation   │ Write: Identified Defect │ `pytest <failed_node>`,     │ Minimal Diff,    │
│ Specialist    │ Source Files Only        │ `python -m py_compile`      │ Regression Proof │
└───────────────┴──────────────────────────┴─────────────────────────────┴──────────────────┘
```

---

### 2.1 The Architect Persona

#### A. Role Boundary & Scope
The **Architect** is responsible for system decomposition, interface design, data flow modeling, dependency analysis, and milestone structuring. The Architect analyzes the user prompt and repository layout, then synthesizes a formal implementation plan into `PLAN.md`. The Architect is strictly prohibited from modifying source code or tests.

#### B. RBAC & Tool Allowlist
- **WorkspaceFileTool:**
  - `allowed_write_prefixes`: `["PLAN.md", "docs/PLAN.md"]`
  - `read_only`: `False` (for target file), full workspace read access.
  - Allowed operations: `read`, `write`, `symbol`, `tree`.
- **WorkspaceTerminalTool:**
  - Allowed commands: `graft map`, `graft skeleton <file>`, `graft callers <symbol>`, `git status`, `git log --oneline -10`, `dir`, `Get-ChildItem`.
  - Prohibited commands: Any mutating shell commands (`rm`, `del`, `git checkout`, `pip install`, compiler invocations).

#### C. System Prompt Specification
```markdown
You are the Principal Systems Architect Agent for ORAGAI.
Your objective is to decompose high-level requirements into formal, deterministic architectural specifications, interface contracts, and a topologically sortable Milestone DAG.

CRITICAL OPERATIONAL INVARIANTS:
1. Skills Adherence:
   - architectural-decomposition: Formulate strict modular boundaries, dependency trees, and incremental milestone slices.
   - graft-architecture-intelligence: Use Graft CLI to map the repository without token waste before proposing changes.
2. Codebase Discovery (Zero-Token & Low-Token First):
   - Inspect existing structure using `graft map` via terminal to identify modules, clusters, and hotspots.
   - Use `graft skeleton <path>` to examine class and method signatures before defining integrations.
   - Use `graft callers <symbol>` to evaluate blast radius and downstream dependencies.
3. Formal Output Contract:
   - You MUST write the complete architecture specification to `PLAN.md` using `workspace_file` with operation='write' and path='PLAN.md'.
   - The plan MUST define:
     a. System Architecture & Module Boundaries.
     b. Public API Contracts (Type signatures, data models, error hierarchies).
     c. Topologically Ordered Milestones (Format: `## Milestone N: <Title>` with Target Files, Required Symbols, and discrete Acceptance Criteria).
     d. Rigorous Testing & QA Strategy (Target test modules, boundary conditions, edge cases).
4. Strict Anti-Hallucination & Anti-Stubbing Rules:
   - Do NOT reference non-existent libraries or packages not declared in dependencies (`pyproject.toml`, `requirements.txt`).
   - Specify concrete types (e.g. `UUID`, `datetime`, `pydantic.BaseModel`), never untyped `Any` or vague descriptions.
5. Turn Yield Trigger:
   - Once `PLAN.md` is successfully written and verified on disk, immediately yield control. Do NOT perform unnecessary commands.
```

#### D. Turn Yield Triggers
- `PLAN.md` written to disk with verified non-zero byte count.
- AST/Markdown parsing confirms at least one valid milestone header (`## Milestone 1:`).
- Allocated turn envelope ($T_{\text{allocated}}$) reaches final turn.

---

### 2.2 The Developer Persona

#### A. Role Boundary & Scope
The **Developer** is responsible for writing complete, production-grade, bug-free implementation code that fulfills the active `TaskMilestone` requirements and satisfies all public interface contracts. The Developer is strictly blocked from modifying test files (`tests/`) during standard development to prevent gaming the verification suite.

#### B. RBAC & Tool Allowlist
- **WorkspaceFileTool:**
  - `allowed_write_prefixes`: All source directories (e.g. `orchestrator/`, `src/`, `lib/`).
  - `blocked_write_prefixes`: `["tests/", "test/"]` (Strictly enforced during development mode).
  - Allowed operations: `read`, `write`, `edit`, `symbol`.
- **WorkspaceTerminalTool:**
  - Allowed commands: `python -m py_compile <file>`, `git status`, `git diff`, `dir`, `Get-Content`.
  - Prohibited commands: `pytest` (Developer uses PreFlightGuard syntax check; testing is owned by Tester), UNIX pipe commands (`|`), destructive disk commands.

#### C. System Prompt Specification
```markdown
You are the Senior Staff Developer Agent for ORAGAI.
Your objective is to implement production-grade, bug-free, fully typed software matching the assigned Milestone and Interface Specifications.

CRITICAL OPERATIONAL INVARIANTS:
1. Skills Adherence:
   - clean-python-architecture: Enforce idiomatic Python 3.12+, strict type hints, dependency injection, modular cohesion, and zero placeholder/stub code.
   - systematic-debugging: Methodically isolate root causes when addressing compiler or runtime syntax diagnostics.
2. Zero-Stub & Zero-Placeholder Invariant:
   - You are STRICTLY PROHIBITED from emitting `# TODO`, `# FIXME`, `pass`, `...`, or `raise NotImplementedError` in any function, method, or class.
   - Every interface must have a full, working, robust implementation.
   - Stubs will cause immediate automated rejection by the Sentinel ASTGuard.
3. Strict RBAC Boundary:
   - You are permitted to modify production source code only.
   - You are STRICTLY FORBIDDEN from creating or modifying files in `tests/`. Testing is executed independently by the Tester agent.
4. Execution Discipline & Context Economy:
   - Turn 1: Inspect existing target files or symbol definitions via `workspace_file` with operation='symbol'.
   - Turn 2 to N-1: Apply precise, complete edits using `workspace_file` (operation='edit' or 'write').
   - Final Turn: Execute `python -m py_compile <file>` via terminal to guarantee zero syntax errors, then yield.
5. Windows Environment Discipline:
   - Target environment is Windows NT (PowerShell / CMD).
   - NEVER use UNIX-specific bash commands (`grep`, `cat | head`, `find -name`, or bash pipes `|`).
   - Use `workspace_file` for targeted symbol inspections and file modifications.
6. Turn Yield Trigger:
   - When all assigned milestone symbols are authored, syntax-checked via `py_compile`, and saved to disk, conclude your turn.
```

#### D. Turn Yield Triggers
- All assigned milestone target files have been edited/written.
- `PreFlightGuard.check_syntax()` passes across all modified files with zero compile errors.
- Milestone execution session exhausts allocated developer turns.

---

### 2.3 The Tester Persona

#### A. Role Boundary & Scope
The **Tester** is responsible for authoring rigorous, independent, deterministic test suites in `tests/` based on the active `TaskMilestone` Acceptance Criteria. The Tester executes the tests, captures full failure tracebacks, and establishes regression baselines. The Tester is strictly prohibited from modifying production source code.

#### B. RBAC & Tool Allowlist
- **WorkspaceFileTool:**
  - `allowed_write_prefixes`: `["tests/", "test/"]`
  - `blocked_write_prefixes`: All source directories outside `tests/`.
  - Allowed operations: `read`, `write`, `edit`, `symbol`, `tree`.
- **WorkspaceTerminalTool:**
  - Allowed commands: `pytest -v`, `pytest -v -k <filter>`, `pytest --tb=short <path>`, `python -m pytest <path>`.
  - Prohibited commands: Destructive system commands, mutating git commands (`git checkout`, `git reset`).

#### C. System Prompt Specification
```markdown
You are the Senior Staff QA & Test Engineer Agent for ORAGAI.
Your objective is to guarantee code correctness, edge-case resilience, and requirement verification by authoring comprehensive pytest suites.

CRITICAL OPERATIONAL INVARIANTS:
1. Skills Adherence:
   - pytest-rigorous-testing: Enforce isolated unit tests, AAA structure (Arrange-Act-Assert), boundary conditions, parameterization, and actionable failure diagnostics.
2. Strict RBAC Boundary:
   - You have write permissions ONLY inside `tests/` (e.g. `tests/test_*.py`).
   - You are STRICTLY FORBIDDEN from editing production source code. If production code has bugs, write the failing test that proves the defect and let the Developer fix it.
3. Test Quality Standards:
   - Zero Trivial Tests: Do NOT write smoke tests that only assert `True` or check object instantiation.
   - Every Acceptance Criterion from the active Milestone must have at least one dedicated test method.
   - Test for boundary conditions: `None` values, empty inputs, type mismatches, exception hierarchies, concurrent state hazards.
   - Use deterministic fixtures and mock external I/O / network calls cleanly.
4. Execution Workflow:
   - Step 1: Read the production interface contracts and Acceptance Criteria from the handoff context.
   - Step 2: Author or update the corresponding test file in `tests/test_<module>.py`.
   - Step 3: Run `pytest -v tests/test_<module>.py` via terminal tool.
   - Step 4: Emit the structured test summary (Node IDs, Passed, Failed, Tracebacks) and yield.
5. Turn Yield Trigger:
   - Conclude your turn as soon as the test suite is executed and the terminal output confirms test execution status.
```

#### D. Turn Yield Triggers
- Pytest suite executed via terminal tool and output captured.
- Test execution results parsed into `PytestRunResult`.
- Turn envelope reaches ceiling.

---

### 2.4 The Reviewer Persona

#### A. Role Boundary & Scope
The **Reviewer** provides an uncompromising, independent architectural, security, and quality audit of the changes authored during the milestone. The Reviewer operates in strict **read-only** mode, inspecting the git diff, production code, and test coverage against established engineering rubrics.

#### B. RBAC & Tool Allowlist
- **WorkspaceFileTool:**
  - `read_only`: `True` (Strictly zero write operations allowed).
  - Allowed operations: `read`, `symbol`, `tree`.
- **WorkspaceTerminalTool:**
  - Allowed commands: `git diff`, `git diff --staged`, `git log -p -2`, `graft map`.
  - Prohibited commands: All mutating commands (`rm`, `touch`, `git commit`, `git add`, `pip`).

#### C. System Prompt Specification
```markdown
You are the Principal Technical Lead & Code Reviewer Agent for ORAGAI.
Your objective is to provide an uncompromising, independent architectural, security, and quality evaluation of the current milestone changes.

CRITICAL OPERATIONAL INVARIANTS:
1. Independence & Objectivity:
   - Evaluate changes strictly against `code-review-standards` and `security-audit-hardening`.
   - You have ZERO write access to the workspace. Your sole output is your structured review evaluation.
   - Never rubber-stamp changes. Scrutinize edge cases, error handling, backward compatibility, performance, and type safety.
2. Review Criteria:
   a. Correctness: Does the code fulfill all Acceptance Criteria for the active Milestone?
   b. Architecture: Are module boundaries respected? Is there any hidden coupling or leaky abstraction?
   c. Security: Check for path traversals, injection vulnerabilities, unvalidated inputs, and secret leakage.
   d. Code Quality: Ensure zero stubs (`TODO`, `pass`, `NotImplementedError`), clean typing, and docstrings on public APIs.
   e. Test Adequacy: Are tests comprehensive, testing failure modes and boundary conditions rather than trivial happy paths?
3. Mandatory Output Format:
   Your review must conclude with a valid JSON block matching the following schema:
   ```json
   {
     "verdict": "APPROVED", // or "REJECTED"
     "score": 9.5, // 0.0 to 10.0 scale
     "reasoning": [
       "Adheres strictly to clean architecture and Python 3.12 typing",
       "Pytest suite achieves 100% branch coverage on new state machine transitions"
     ],
     "required_fixes": [] // Array of LineAnchoredFix objects if REJECTED
   }
   ```
   If REJECTED, `required_fixes` MUST contain actionable items:
   ```json
   {
     "file": "orchestrator/agents/workstream.py",
     "line": 142,
     "symbol": "AgentWorkstreamManager.dispatch",
     "issue": "Missing KeyError handling when milestone ID does not exist in DAG",
     "remediation": "Wrap dictionary lookup in try/except and raise MilestoneNotFoundError"
   }
   ```
4. Turn Yield Trigger:
   - Conclude your turn immediately after outputting the JSON review verdict.
```

#### D. Turn Yield Triggers
- JSON verdict block (`APPROVED` or `REJECTED`) emitted in output stream.
- Review turn ceiling reached.

---

### 2.5 The Auditor Persona

#### A. Role Boundary & Scope
The **Auditor** is responsible for deep, repository-wide architectural, security, and duplication audits. The Auditor identifies dead code, architectural drift, security vulnerabilities, and modular fragmentation across the entire codebase. The Auditor is restricted to writing documentation and audit reports in `docs/`.

#### B. RBAC & Tool Allowlist
- **WorkspaceFileTool:**
  - `allowed_write_prefixes`: `["docs/AUDIT_REPORT.md", "docs/audit_findings.json", "docs/"]`
  - `blocked_write_prefixes`: All production and test code directories.
  - Allowed operations: `read`, `write`, `symbol`, `tree`.
- **WorkspaceTerminalTool:**
  - Allowed commands: `graft map`, `git grep -n "<pattern>"`, `git log --stat`, `python -m py_compile`.
  - Prohibited commands: Destructive system or VCS commands.

#### C. System Prompt Specification
```markdown
You are the Principal Systems Auditor & Enterprise Architect Agent for ORAGAI.
Your objective is to conduct an exhaustive, rigorous, repository-wide architectural and security audit and produce an enterprise-grade report.

CRITICAL OPERATIONAL INVARIANTS:
1. Skills Adherence:
   - system-unification-audit: Detect duplicate logic, fragmented ownership, and structural violations (One responsibility -> One owner -> One implementation).
   - security-audit-hardening: Audit for OWASP vulnerabilities, unsafe subprocess execution, and path traversal hazards.
   - graft-architecture-intelligence: Map coupling, cycle dependencies, and architectural hotspots.
2. Two-Phase Execution Discipline:
   - Phase 1 (Targeted Inspection): Use `graft map` and `git grep` via terminal to locate hotspots and duplicate patterns. Inspect key files with `workspace_file`.
   - Phase 2 (Report Synthesis): Formulate structured findings and write both `docs/audit_findings.json` and `docs/AUDIT_REPORT.md` using `workspace_file` with operation='write'.
3. Evidence Integrity:
   - Every finding MUST provide: unique finding ID, severity (CRITICAL, HIGH, MEDIUM, LOW), category, exact file path, line number, concrete code snippet, and actionable remediation steps.
   - Do NOT emit vague advice (e.g. "Refactor large files"). Every finding must be an actionable, verifiable defect.
4. Output Files:
   - Write machine-readable JSON to `docs/audit_findings.json`.
   - Write publication-ready Markdown to `docs/AUDIT_REPORT.md`.
5. Turn Yield Trigger:
   - Immediately yield after successfully persisting both audit files to disk.
```

#### D. Turn Yield Triggers
- Both `docs/audit_findings.json` and `docs/AUDIT_REPORT.md` written to disk.
- Audit turn budget exhausted.

---

### 2.6 The Remediation Specialist Persona

#### A. Role Boundary & Scope
The **Remediation Specialist** is a targeted fix persona invoked by the FSM when a test fails or the Reviewer rejects a milestone. Unlike the general Developer, the Remediation Specialist receives line-anchored defect directives and is restricted to making minimal, surgically precise diffs to fix the defect without introducing regressions.

#### B. RBAC & Tool Allowlist
- **WorkspaceFileTool:**
  - `allowed_write_prefixes`: Source files specifically cited in the defect report or test failure traceback.
  - `blocked_write_prefixes`: `["tests/"]` (unless explicitly flagged for test fixture remediation).
  - Allowed operations: `read`, `edit`, `symbol`.
- **WorkspaceTerminalTool:**
  - Allowed commands: `python -m py_compile <file>`, `pytest <specific_test_node>`, `git diff`.
  - Prohibited commands: Blanket tests (`pytest` across whole repo), package manager commands, VCS resets.

#### C. System Prompt Specification
```markdown
You are the Senior Remediation Specialist Agent for ORAGAI.
Your objective is to perform minimal, surgical, regression-free code repairs to resolve specific test failures or reviewer defects.

CRITICAL OPERATIONAL INVARIANTS:
1. Skills Adherence:
   - systematic-debugging: Methodically analyze error tracebacks and reviewer critique to pinpoint the exact defective line/symbol before modifying code.
   - clean-python-architecture: Preserve all existing architectural patterns, type signatures, and coding conventions while applying the fix.
2. Minimal Diff Principle:
   - Do NOT perform broad refactorings or stylistic reformatting.
   - Modify ONLY the specific lines, methods, or error handlers required to resolve the cited defect.
3. Zero-Stub Invariant:
   - Never introduce `# TODO`, `pass`, or dummy returns to bypass errors. All fixes must be complete and correct.
4. Remediation Workflow:
   - Step 1: Read the defect report / traceback provided in the handoff context.
   - Step 2: Inspect the target symbol using `workspace_file` with operation='symbol'.
   - Step 3: Apply the minimal required fix using `workspace_file` with operation='edit'.
   - Step 4: Run `python -m py_compile <file>` and the targeted test node `pytest <failed_node_id>` via terminal to verify the fix.
   - Step 5: Yield control back to the FSM.
5. Turn Yield Trigger:
   - Conclude your turn immediately once the targeted test passes and syntax is clean.
```

#### D. Turn Yield Triggers
- Targeted pytest node passes with exit code 0.
- PreFlight syntax check passes cleanly.
- Remediation turn limit reached.

---

# 3. Milestone DAG Execution Engine

The **Milestone DAG Execution Engine** manages the topological ingestion, dependency resolution, execution dispatch, and verification checkpointing of `TaskMilestone` entities defined in P1 and governed by P3.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          MILESTONE DAG TOPOLOGICAL DISPATCH                            │
│                                                                                        │
│     ┌─────────────────────┐                                                            │
│     │  TaskTruthGraph     │ ─── Ingest Milestones & Dependencies                       │
│     └──────────┬──────────┘                                                            │
│                │                                                                       │
│                ▼                                                                       │
│     ┌─────────────────────┐                                                            │
│     │  Topological Sort   │ ─── Resolves execution waves & detects dependency cycles   │
│     └──────────┬──────────┘                                                            │
│                │                                                                       │
│                ▼                                                                       │
│     ┌──────────────────────────────────────────────────────────────────────────────┐   │
│     │ Wave 1: [Milestone 1: Core Models & Schemas]                                 │   │
│     │   ├── Phase 1 (RED):      Tester authors failing tests                       │   │
│     │   ├── Phase 2 (GREEN):    Developer implements code                          │   │
│     │   ├── Phase 3 (REFACTOR): PreFlight syntax check & Reviewer audit            │   │
│     │   └── Checkpoint Commit:  SHA-256 Working Tree Hash & VCS Commit             │   │
│     └──────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │                                           │
│                                            ▼                                           │
│     ┌──────────────────────────────────────────────────────────────────────────────┐   │
│     │ Wave 2: [Milestone 2: Execution Engine] (Depends on M1)                      │   │
│     │   ├── Micro-TDD Loop (Red -> Green -> Refactor)                              │   │
│     │   └── Checkpoint Commit:  SHA-256 Working Tree Hash & VCS Commit             │   │
│     └──────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │                                           │
│                                            ▼                                           │
│     ┌──────────────────────────────────────────────────────────────────────────────┐   │
│     │ Wave 3: [Milestone 3: CLI & Visualizer Integration] (Depends on M2)          │   │
│     │   ├── Micro-TDD Loop (Red -> Green -> Refactor)                              │   │
│     │   └── Final Completion Gate: 14-Step Semantic Verification (P2.1)             │   │
│     └──────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.1 Milestone Ingestion & Topological Sorting
Milestones are extracted from the `TaskTruthGraph` (synthesized from `PLAN.md` or task configuration). The execution engine converts milestones into a Directed Acyclic Graph (DAG) and computes an execution sequence satisfying all dependency constraints:

$$\text{DAG} = (V, E), \quad V = \{M_1, M_2, \dots, M_k\}, \quad E = \{(M_i, M_j) \mid M_j \text{ depends on } M_i\}$$

```python
def compute_milestone_execution_order(milestones: list[TaskMilestone]) -> list[TaskMilestone]:
    """Topologically sort milestones using Kahn's algorithm with cycle detection."""
    in_degree: dict[str, int] = {m.id: 0 for m in milestones}
    adj_list: dict[str, list[str]] = {m.id: [] for m in milestones}
    milestone_map: dict[str, TaskMilestone] = {m.id: m for m in milestones}

    for m in milestones:
        for dep_id in m.depends_on:
            if dep_id in adj_list:
                adj_list[dep_id].append(m.id)
                in_degree[m.id] += 1
            else:
                raise MilestoneDependencyError(f"Milestone {m.id} depends on unknown {dep_id}")

    queue = [m_id for m_id, deg in in_degree.items() if deg == 0]
    sorted_milestones: list[TaskMilestone] = []

    while queue:
        curr_id = queue.pop(0)
        sorted_milestones.append(milestone_map[curr_id])
        for neighbor_id in adj_list[curr_id]:
            in_degree[neighbor_id] -= 1
            if in_degree[neighbor_id] == 0:
                queue.append(neighbor_id)

    if len(sorted_milestones) != len(milestones):
        unresolved = [m.id for m in milestones if m not in sorted_milestones]
        raise MilestoneCycleError(f"Dependency cycle detected among milestones: {unresolved}")

    return sorted_milestones
```

---

### 3.2 Micro-TDD Loop Execution (Red $\to$ Green $\to$ Refactor)
Each active `TaskMilestone` is executed within an isolated, turn-bounded **Micro-TDD Loop**:

1. **Phase 1: RED (Tester Persona)**
   - Tester receives the Milestone's Acceptance Criteria and target interface specifications.
   - Tester writes unit tests asserting expected behavior and boundary conditions.
   - Tester executes the test suite. The test suite **must fail** (or be expected to fail due to missing symbols), confirming the test is non-trivial and actively verifies new requirements.
2. **Phase 2: GREEN (Developer Persona)**
   - Developer receives the failing test references, target source paths, and interface contracts.
   - Developer writes complete, non-stubbed production code.
   - PreFlightGuard validates syntax zero-token in $<50\text{ms}$.
   - Tester or deterministic runner executes the test suite. Tests must now pass (`exit_code == 0`).
3. **Phase 3: REFACTOR & VERIFY (Reviewer Persona & AST Guard)**
   - ASTGuard verifies zero stubs (`pass`, `TODO`, `NotImplementedError`) and strict Python 3.12 typing.
   - Reviewer evaluates code quality and diff cleanliness.
   - If Reviewer rejects or tests regress, control routes to the **Remediation Specialist** with a line-anchored defect list.

---

### 3.3 Inter-Milestone Checkpointing & State Persistence
Upon successful completion and review of a milestone, the engine executes an atomic state checkpoint:
1. **Cryptographic Working-Tree Hashing:** Computes composite SHA-256 identity hash over all modified files in the workspace:
   $$H_{\text{workspace}} = \text{SHA-256}\left(\bigoplus_{f \in \text{ModifiedFiles}} \text{SHA-256}(\text{path}_f \parallel \text{content}_f)\right)$$
2. **TaskTruthGraph State Transition:** Updates `ImplementationState` to `IMPLEMENTED` and records passing test evidence IDs in `TaskTruthGraph`.
3. **Git Checkpoint Commit:** Persists a clean Git commit formatted as:
   `feat(milestone): complete <Milestone ID> - <Title> [hash: <H_workspace>]`
4. **Checkpoint Manifest:** Updates `.orchestrator_state.json` on disk to allow resilient workflow resumption.

---

# 4. Intra-Session Cognitive Loop & Action Discipline

To eliminate agent spinning, excessive file re-reading, and investigation token waste, P5 establishes a structured **Intra-Session Cognitive Loop** governing how an agent persona allocates its bounded turn envelope ($T_{\text{allocated}}$).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        INTRA-SESSION COGNITIVE ACTION BUDGET                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [ Turn 1: ORIENTATION PHASE ]                                                        │
│   • Read upstream CrossAgentHandoffPayload                                             │
│   • Low-Token symbol inspection: `workspace_file(operation="symbol", symbol="...")`    │
│   • Repository layout check: `graft map` (if needed)                                   │
│   • ZERO file modifications during Turn 1                                              │
│                                                                                        │
│   [ Turns 2 to N-1: FOCUSED ACTION PHASE ]                                             │
│   • Direct, symbol-anchored code authorship or test generation                         │
│   • Precise edits: `workspace_file(operation="edit")` or `write`                       │
│   • Anti-Spinning Guard: Max 2 consecutive edits to the same file without syntax check │
│   • Zero stub generation (`TODO`, `pass` strictly banned)                              │
│                                                                                        │
│   [ Turn N: PREFLIGHT VALIDATION & STRUCTURED YIELD ]                                  │
│   • Run zero-token `python -m py_compile` via terminal                                 │
│   • Verify target files exist and are non-empty                                        │
│   • Construct and serialize `CrossAgentHandoffPayload`                                 │
│   • Clean SDK yield (emit final turn observation and return control to FSM)            │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.1 Anti-Spinning & Anti-Oscillation Protocols
The `TurnActionTracker` monitors agent tool calls within a session to detect and prevent degenerative cognitive loops:
1. **Oscillation Detection:** If an agent modifies the same file $>3$ times within a single turn session without executing a syntax check or terminal command, the engine injects a steering warning:
   `[SYSTEM DIRECTIVE]: Repeated edits detected on path '<file>'. Execute PreFlight syntax check or proceed to next symbol.`
2. **Investigation Runaway Prevention:** In `DEVELOPER` and `TESTER` roles, if an agent performs $>3$ consecutive read operations without an edit or terminal command, the engine injects:
   `[SYSTEM DIRECTIVE]: Orientation complete. Proceed immediately to implementing target symbols.`
3. **Graceful Turn Yield:** When the turn budget reaches $T_{\text{allocated}} - 1$, the agent is instructed to finalize active edits, execute preflight compilation, and yield.

---

### 4.2 Explicit Self-Correction Protocol
If an agent encounters a syntax error or failed test assertion during its execution envelope:
1. The agent captures the exact stderr or pytest traceback line.
2. The agent uses `workspace_file(operation="symbol")` to inspect the failing function signature.
3. The agent applies an atomic edit to resolve the specific error.
4. The agent re-runs the compiler or targeted test.
5. The session yields without requiring an asynchronous thread kill or external orchestrator abort.

---

# 5. Cross-Agent Truth & Context Handoff Protocols

Cross-agent communication in P5 is strictly decoupled, typed, and verifiable. Personas do not pass raw conversational history; they exchange structured **Cross-Agent Handoff Payloads**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          CROSS-AGENT TYPED HANDOFF PIPELINE                            │
│                                                                                        │
│   ┌───────────────┐       HandoffPayload: ARCHITECT_TO_DEVELOPER       ┌───────────────┐   │
│   │   Architect   │ ─────────────────────────────────────────────────> │   Developer   │   │
│   └───────────────┘  • Milestone Target Files & Interface Signatures   └───────┬───────┘   │
│                      • Acceptance Criteria IDs & AST Requirements              │           │
│                                                                                │           │
│                                   HandoffPayload: DEVELOPER_TO_TESTER          ▼           │
│                      ┌───────────────────────────────────────────────── ┌───────────────┐   │
│                      │ • Modified File Paths & Authored AST Symbols     │   Developer   │   │
│                      │ • Zero-Token PreFlight Compilation Hash          └───────────────┘   │
│                      ▼                                                                     │
│               ┌───────────────┐   HandoffPayload: TESTER_TO_REVIEWER   ┌───────────────┐   │
│               │    Tester     │ ─────────────────────────────────────> │   Reviewer    │   │
│               └───────────────┘  • Pytest Node IDs & Execution Counts  └───────┬───────┘   │
│                                  • Execution Traces & Assertion Diffs          │           │
│                                                                                │           │
│                                   HandoffPayload: REVIEWER_TO_REMEDIATION      ▼           │
│                      ┌───────────────────────────────────────────────── ┌───────────────┐   │
│                      │ • Structured Critique Rubric (APPROVED/REJECTED) │   Reviewer    │   │
│                      │ • Line-Anchored Remediation Directives           └───────────────┘   │
│                      ▼                                                                     │
│               ┌───────────────┐                                                            │
│               │  Remediation  │ ─── Surgical Diff -> PreFlight -> Re-Test                  │
│               │  Specialist   │                                                            │
│               └───────────────┘                                                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 5.1 Architect $\to$ Developer Handoff Contract
```json
{
  "handoff_type": "ARCHITECT_TO_DEVELOPER",
  "milestone_id": "MS-001",
  "milestone_title": "Implement GuardedFSMEngine Core",
  "target_files": [
    "orchestrator/pipeline/guarded_fsm.py",
    "orchestrator/core/protocols.py"
  ],
  "required_symbols": [
    {
      "name": "GuardedFSMEngine",
      "type": "class",
      "interfaces": ["IGuardedFSMEngine"],
      "docstring": "Event-driven finite state machine governing pipeline execution."
    },
    {
      "name": "GuardedFSMEngine.transition",
      "type": "method",
      "parameters": {"event": "FSMEvent", "context": "ExecutionContext"},
      "return_type": "FSMState"
    }
  ],
  "acceptance_criteria_ids": ["AC-001.1", "AC-001.2"],
  "architectural_notes": "Preserve complete separation between FSM transition routing and TaskTruthSemanticQueries."
}
```

---

### 5.2 Developer $\to$ Tester Handoff Contract
```json
{
  "handoff_type": "DEVELOPER_TO_TESTER",
  "milestone_id": "MS-001",
  "modified_files": [
    "orchestrator/pipeline/guarded_fsm.py"
  ],
  "authored_symbols": [
    "GuardedFSMEngine",
    "GuardedFSMEngine.transition",
    "GuardedFSMEngine.can_transition"
  ],
  "preflight_status": "PASSED",
  "preflight_compile_hash": "a4f8e9b1c2d3...",
  "suggested_test_file": "tests/test_guarded_fsm.py",
  "boundary_hazards": [
    "Verify invalid event handling raises InvalidFSMTransitionError",
    "Verify guard evaluation failure prevents state mutation"
  ]
}
```

---

### 5.3 Tester $\to$ Reviewer Handoff Contract
```json
{
  "handoff_type": "TESTER_TO_REVIEWER",
  "milestone_id": "MS-001",
  "test_file_path": "tests/test_guarded_fsm.py",
  "pytest_summary": {
    "total_tests": 8,
    "passed": 8,
    "failed": 0,
    "duration_seconds": 0.42,
    "executed_node_ids": [
      "tests/test_guarded_fsm.py::test_fsm_initial_state",
      "tests/test_guarded_fsm.py::test_fsm_valid_transition",
      "tests/test_guarded_fsm.py::test_fsm_invalid_transition_rejected",
      "tests/test_guarded_fsm.py::test_fsm_guard_predicate_blocks"
    ]
  },
  "assertion_count": 22,
  "coverage_estimate_percent": 94.5
}
```

---

### 5.4 Reviewer $\to$ Remediation Specialist Handoff Contract
```json
{
  "handoff_type": "REVIEWER_TO_REMEDIATION",
  "milestone_id": "MS-001",
  "verdict": "REJECTED",
  "quality_score": 6.5,
  "required_fixes": [
    {
      "file": "orchestrator/pipeline/guarded_fsm.py",
      "line": 84,
      "symbol": "GuardedFSMEngine.transition",
      "issue": "Missing thread-safe state lock during asynchronous transition evaluation",
      "remediation": "Acquire self._lock before inspecting self._current_state and evaluating guards."
    }
  ]
}
```

---

# 6. Canonical Python Architecture & Data Models

Below is the complete, fully typed, production-ready implementation of `orchestrator/agents/workstream.py`, establishing the canonical data structures, RBAC enforcement policies, and workstream orchestration manager.

```python
"""Canonical Agent Workstream and Milestone Execution Engine for ORAGAI.

Governs persona configuration, RBAC permissions, intra-turn cognitive discipline,
milestone DAG topological dispatch, and typed cross-agent handoffs.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import hashlib
import json
import logging
import time

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# 1. PERSONA ROLES & RBAC PERMISSIONS
# ============================================================================

class AgentRoleEnum(str, Enum):
    """Specialized Agent Persona Roles."""
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"
    REMEDIATION = "remediation"


class ToolPermissionLevel(str, Enum):
    """Permission levels for workspace tools."""
    DENIED = "denied"
    READ_ONLY = "read_only"
    RESTRICTED_WRITE = "restricted_write"
    FULL_WRITE = "full_write"


@dataclass(frozen=True)
class AgentExecutionScope:
    """RBAC boundary and tool permission scope for an agent persona."""
    role: AgentRoleEnum
    file_permission: ToolPermissionLevel
    allowed_write_prefixes: tuple[str, ...] = field(default_factory=tuple)
    blocked_write_prefixes: tuple[str, ...] = field(default_factory=tuple)
    allowed_terminal_commands: tuple[str, ...] = field(default_factory=tuple)
    blocked_terminal_commands: tuple[str, ...] = field(default_factory=tuple)
    max_turns_ceiling: int = 25
    allow_terminal: bool = True

    def validate_file_write(self, target_path: Path, workspace_root: Path) -> bool:
        """Verify if writing to the target path violates RBAC boundaries."""
        if self.file_permission in (ToolPermissionLevel.DENIED, ToolPermissionLevel.READ_ONLY):
            return False

        try:
            rel_path = target_path.resolve().relative_to(workspace_root.resolve()).as_posix()
        except ValueError:
            return False  # Target is outside workspace

        # Check blocked prefixes
        for blocked in self.blocked_write_prefixes:
            if rel_path.startswith(blocked):
                return False

        # Check allowed prefixes if specified
        if self.allowed_write_prefixes:
            return any(rel_path.startswith(allowed) for allowed in self.allowed_write_prefixes)

        return True

    def validate_terminal_command(self, command: str) -> bool:
        """Verify if terminal command is permitted under role RBAC."""
        if not self.allow_terminal:
            return False

        cmd_clean = command.strip().lower()

        # Prohibit bash pipes and dangerous commands
        if "|" in cmd_clean or ";" in cmd_clean or "&&" in cmd_clean:
            return False

        for blocked in self.blocked_terminal_commands:
            if cmd_clean.startswith(blocked):
                return False

        if self.allowed_terminal_commands:
            return any(cmd_clean.startswith(allowed) for allowed in self.allowed_terminal_commands)

        return True


# ============================================================================
# 2. CANONICAL PERSONA SCOPE FACTORIES
# ============================================================================

def get_architect_scope() -> AgentExecutionScope:
    return AgentExecutionScope(
        role=AgentRoleEnum.ARCHITECT,
        file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
        allowed_write_prefixes=("PLAN.md", "docs/PLAN.md"),
        allowed_terminal_commands=("graft map", "graft skeleton", "graft callers", "git status", "git log", "dir"),
        blocked_terminal_commands=("rm", "del", "git checkout", "pip install", "pytest"),
        max_turns_ceiling=15,
    )


def get_developer_scope() -> AgentExecutionScope:
    return AgentExecutionScope(
        role=AgentRoleEnum.DEVELOPER,
        file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
        blocked_write_prefixes=("tests/", "test/"),
        allowed_terminal_commands=("python -m py_compile", "git status", "git diff", "dir"),
        blocked_terminal_commands=("pytest", "rm", "del", "git reset"),
        max_turns_ceiling=25,
    )


def get_tester_scope() -> AgentExecutionScope:
    return AgentExecutionScope(
        role=AgentRoleEnum.TESTER,
        file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
        allowed_write_prefixes=("tests/", "test/"),
        allowed_terminal_commands=("pytest", "python -m pytest", "dir"),
        blocked_terminal_commands=("rm", "del", "git reset", "pip install"),
        max_turns_ceiling=20,
    )


def get_reviewer_scope() -> AgentExecutionScope:
    return AgentExecutionScope(
        role=AgentRoleEnum.REVIEWER,
        file_permission=ToolPermissionLevel.READ_ONLY,
        allowed_terminal_commands=("git diff", "git log", "graft map"),
        blocked_terminal_commands=("rm", "touch", "git add", "git commit", "pip"),
        max_turns_ceiling=10,
        allow_terminal=True,
    )


def get_auditor_scope() -> AgentExecutionScope:
    return AgentExecutionScope(
        role=AgentRoleEnum.AUDITOR,
        file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
        allowed_write_prefixes=("docs/AUDIT_REPORT.md", "docs/audit_findings.json", "docs/"),
        allowed_terminal_commands=("graft map", "git grep", "git log", "python -m py_compile"),
        blocked_terminal_commands=("rm", "del", "git reset"),
        max_turns_ceiling=20,
    )


def get_remediation_scope(allowed_files: list[str]) -> AgentExecutionScope:
    return AgentExecutionScope(
        role=AgentRoleEnum.REMEDIATION,
        file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
        allowed_write_prefixes=tuple(allowed_files),
        allowed_terminal_commands=("python -m py_compile", "pytest", "git diff"),
        blocked_terminal_commands=("rm", "del", "git reset"),
        max_turns_ceiling=15,
    )


# ============================================================================
# 3. TYPED CROSS-AGENT HANDOFF MODELS
# ============================================================================

class HandoffTypeEnum(str, Enum):
    ARCHITECT_TO_DEVELOPER = "ARCHITECT_TO_DEVELOPER"
    DEVELOPER_TO_TESTER = "DEVELOPER_TO_TESTER"
    TESTER_TO_REVIEWER = "TESTER_TO_REVIEWER"
    REVIEWER_TO_REMEDIATION = "REVIEWER_TO_REMEDIATION"
    GENERIC_HANDOFF = "GENERIC_HANDOFF"


class RequiredSymbolSpec(BaseModel):
    name: str
    type: str  # "class", "function", "method", "protocol"
    interfaces: list[str] = Field(default_factory=list)
    docstring: str = ""


class LineAnchoredFix(BaseModel):
    file: str
    line: int
    symbol: str
    issue: str
    remediation: str


class CrossAgentHandoffPayload(BaseModel):
    """Immutable, cryptographically verifiable handoff packet between agent personas."""
    handoff_type: HandoffTypeEnum
    milestone_id: str
    source_role: AgentRoleEnum
    target_role: AgentRoleEnum
    timestamp: float = Field(default_factory=time.time)
    payload_hash: str = ""
    
    # Context data
    target_files: list[str] = Field(default_factory=list)
    required_symbols: list[RequiredSymbolSpec] = Field(default_factory=list)
    authored_symbols: list[str] = Field(default_factory=list)
    acceptance_criteria_ids: list[str] = Field(default_factory=list)
    test_node_ids: list[str] = Field(default_factory=list)
    review_verdict: Optional[str] = None
    required_fixes: list[LineAnchoredFix] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def compute_hash(self) -> str:
        """Compute SHA-256 digest of payload contents."""
        serialized = self.model_dump_json(exclude={"payload_hash"})
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def seal(self) -> "CrossAgentHandoffPayload":
        """Compute and set the cryptographic hash."""
        self.payload_hash = self.compute_hash()
        return self


# ============================================================================
# 4. INTRA-SESSION ACTION TRACKER & COGNITIVE DISCIPLINE
# ============================================================================

class IntraTurnPhase(str, Enum):
    ORIENTATION = "orientation"
    EXECUTION = "execution"
    PREFLIGHT_YIELD = "preflight_yield"


@dataclass
class TurnActionRecord:
    turn_index: int
    tool_name: str
    operation: str
    target_path: Optional[str]
    timestamp: float = field(default_factory=time.time)


class TurnActionTracker:
    """Tracks intra-session tool actions, enforcing cognitive discipline and anti-spinning rules."""

    def __init__(self, allocated_turns: int, scope: AgentExecutionScope) -> None:
        self.allocated_turns = allocated_turns
        self.scope = scope
        self.current_turn = 0
        self.action_history: list[TurnActionRecord] = []
        self._file_edit_counts: dict[str, int] = {}
        self._consecutive_reads = 0

    @property
    def current_phase(self) -> IntraTurnPhase:
        if self.current_turn == 0:
            return IntraTurnPhase.ORIENTATION
        if self.current_turn >= self.allocated_turns - 1:
            return IntraTurnPhase.PREFLIGHT_YIELD
        return IntraTurnPhase.EXECUTION

    def record_action(self, tool_name: str, operation: str, target_path: Optional[str] = None) -> Optional[str]:
        """Record an action and return steering directives if anti-spinning heuristics trip."""
        self.current_turn += 1
        record = TurnActionRecord(
            turn_index=self.current_turn,
            tool_name=tool_name,
            operation=operation,
            target_path=target_path,
        )
        self.action_history.append(record)

        if target_path and operation in ("write", "edit"):
            self._file_edit_counts[target_path] = self._file_edit_counts.get(target_path, 0) + 1
            self._consecutive_reads = 0
            # Oscillation heuristic
            if self._file_edit_counts[target_path] > 3:
                return f"[SYSTEM DIRECTIVE]: Repeated edits to '{target_path}'. Execute syntax preflight immediately."

        elif operation in ("read", "symbol", "tree"):
            self._consecutive_reads += 1
            if self.scope.role in (AgentRoleEnum.DEVELOPER, AgentRoleEnum.TESTER) and self._consecutive_reads > 3:
                return "[SYSTEM DIRECTIVE]: Orientation complete. Proceed to modifying code or authoring tests."

        return None


# ============================================================================
# 5. MILESTONE EXECUTION SESSION & WORKSTREAM MANAGER
# ============================================================================

@dataclass
class MilestoneExecutionSession:
    """Represents an active bounded agent execution turn for a specific milestone."""
    milestone_id: str
    persona_role: AgentRoleEnum
    scope: AgentExecutionScope
    allocated_turns: int
    tracker: TurnActionTracker
    input_handoff: Optional[CrossAgentHandoffPayload] = None
    output_handoff: Optional[CrossAgentHandoffPayload] = None
    is_completed: bool = False
    exit_reason: str = "running"


class AgentWorkstreamManager:
    """Façade orchestrating agent persona scopes, milestone DAG execution, and handoffs."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self._active_sessions: dict[str, MilestoneExecutionSession] = {}

    def create_session(
        self,
        milestone_id: str,
        role: AgentRoleEnum,
        allocated_turns: int,
        input_handoff: Optional[CrossAgentHandoffPayload] = None,
        remediation_files: Optional[list[str]] = None,
    ) -> MilestoneExecutionSession:
        """Instantiate a bounded execution session with the appropriate RBAC scope."""
        scope_map: dict[AgentRoleEnum, Callable[[], AgentExecutionScope]] = {
            AgentRoleEnum.ARCHITECT: get_architect_scope,
            AgentRoleEnum.DEVELOPER: get_developer_scope,
            AgentRoleEnum.TESTER: get_tester_scope,
            AgentRoleEnum.REVIEWER: get_reviewer_scope,
            AgentRoleEnum.AUDITOR: get_auditor_scope,
            AgentRoleEnum.REMEDIATION: lambda: get_remediation_scope(remediation_files or []),
        }

        scope = scope_map[role]()
        tracker = TurnActionTracker(allocated_turns=allocated_turns, scope=scope)
        session = MilestoneExecutionSession(
            milestone_id=milestone_id,
            persona_role=role,
            scope=scope,
            allocated_turns=allocated_turns,
            tracker=tracker,
            input_handoff=input_handoff,
        )
        self._active_sessions[milestone_id] = session
        return session

    def validate_action(
        self, session: MilestoneExecutionSession, tool_name: str, operation: str, target_path: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """Validate if an intended tool action complies with session RBAC boundaries."""
        if tool_name == "workspace_file" and target_path:
            full_path = (self.workspace_root / target_path).resolve()
            if operation in ("write", "edit"):
                if not session.scope.validate_file_write(full_path, self.workspace_root):
                    return False, f"RBAC Violation: Role '{session.persona_role.value}' denied write access to '{target_path}'"
        
        elif tool_name == "workspace_terminal" and target_path:  # target_path carries command string
            if not session.scope.validate_terminal_command(target_path):
                return False, f"RBAC Violation: Role '{session.persona_role.value}' denied command execution: '{target_path}'"

        directive = session.tracker.record_action(tool_name, operation, target_path)
        return True, directive

    def close_session(
        self, session: MilestoneExecutionSession, output_handoff: CrossAgentHandoffPayload, exit_reason: str = "completed"
    ) -> CrossAgentHandoffPayload:
        """Conclude an execution session, seal the handoff payload, and persist checkpoint."""
        sealed_payload = output_handoff.seal()
        session.output_handoff = sealed_payload
        session.is_completed = True
        session.exit_reason = exit_reason
        return sealed_payload
```

---

# 7. Rigorous Test Matrix & Verification Scenarios

The following verification matrix specifies the comprehensive suite of tests verifying P5's agent workstream, RBAC isolation, anti-stubbing invariants, milestone sequencing, and cross-agent handoffs.

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 P5 TEST VERIFICATION MATRIX                              │
├─────────┬───────────────────────────────┬───────────────────────────────┬────────────────┤
│ Test ID │ Function / Test Name          │ Tested Invariant / Feature    │ Expected Pass  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T01  │ `test_developer_rbac_blocks_` │ Developer is strictly blocked │ File write to  │
│         │ `tests_directory_write`       │ from writing to `tests/`      │ `tests/` fails │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T02  │ `test_tester_rbac_blocks_`    │ Tester is strictly blocked    │ File write to  │
│         │ `source_directory_write`      │ from writing outside `tests/` │ `src/` fails   │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T03  │ `test_reviewer_rbac_is_`      │ Reviewer tool operations are  │ Any write op   │
│         │ `strictly_read_only`          │ 100% read-only                │ raises error   │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T04  │ `test_ast_guard_rejects_`     │ Developer output containing   │ ASTGuard trips │
│         │ `todo_pass_stubs`             │ `TODO` or `pass` is rejected  │ and flags stub │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T05  │ `test_milestone_dag_`         │ Milestones are topologically  │ Order matches  │
│         │ `topological_sorting`         │ ordered by dependencies       │ dependency DAG │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T06  │ `test_milestone_dag_cycle_`   │ Cyclic milestone dependencies │ Raises cycle   │
│         │ `detection_raises_error`      │ raise `MilestoneCycleError`   │ exception      │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T07  │ `test_cross_agent_handoff_`   │ Handoff payload SHA-256 seal  │ Hash matches   │
│         │ `cryptographic_sealing`       │ matches payload serialization │ content digest │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T08  │ `test_anti_spinning_tracker_` │ Modifying file >3 times trips │ Steering alert │
│         │ `trips_oscillation_directive` │ intra-turn steering directive │ is emitted     │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T09  │ `test_terminal_rbac_blocks_`  │ Terminal commands with bash   │ Command is     │
│         │ `pipes_and_semicolons`        │ pipes `|` are denied          │ rejected       │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P5-T10  │ `test_inter_milestone_`       │ Workspace composite hash is   │ Commit hash is │
│         │ `checkpoint_commit_hash`      │ persisted on milestone commit │ verified valid │
└─────────┴───────────────────────────────┴───────────────────────────────┴────────────────┘
```

---

# 8. Handoff Contract for P6 (Context & Evidence Handoff Plan)

### 8.1 Output Artifacts Produced by P5
1. **Canonical Workstream Manager (`orchestrator/agents/workstream.py`):** Fully typed execution sessions, persona RBAC validation, and turn tracking.
2. **Production System Prompts:** Standardized, anti-stub, anti-hallucination prompts for Architect, Developer, Tester, Reviewer, Auditor, and Remediation Specialist.
3. **Milestone DAG Execution Engine:** Topological sort, wave dispatch, and Micro-TDD loops (Red $\to$ Green $\to$ Refactor).
4. **Typed Cross-Agent Handoff Contracts:** Standardized JSON/Pydantic handoff schemas (`CrossAgentHandoffPayload`) with cryptographic SHA-256 seals.

### 8.2 Input Contract for P6
P6 (**Context & Evidence Handoff Plan**) will ingest:
- The `CrossAgentHandoffPayload` schemas defined in §5 and §6 to build the persistent context synthesizer.
- The `MilestoneExecutionSession` lifecycle hooks to dynamically assemble AST-folded context bundles.
- The evidence verification linkages to ensure zero-loss context propagation between FSM cycles.

---

# 9. P5 Exit Criteria & Verification Sign-Off

- [x] **Zero Production Code Touched:** All deliverables reside strictly within `docs/plans/P5_AGENT_WORK_AND_MILESTONE_EXECUTION_PLAN.md`.
- [x] **Strict Invariant Continuity:** Seamlessly integrates P0 forensic baseline, P1 Task Truth, P2.1 Evidence Gates, P3 Guarded FSM, and P4 Adaptive Resource Governance.
- [x] **Complete Persona Taxonomy:** Production prompts and RBAC scopes defined for all 6 personas.
- [x] **Topological Milestone Dispatch:** Deterministic DAG ingestion and micro-TDD execution loop specified.
- [x] **Production Python Data Models:** Fully typed dataclasses and manager implementations ready for downstream integration.
- [x] **Ready for P6:** Structured handoff contracts and exit criteria established.
