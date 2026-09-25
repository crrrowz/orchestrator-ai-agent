# P1 — TASK TRUTH & REQUIREMENT MODEL PLAN

> **Document Type:** Foundational Systems Architecture & Requirements Engineering Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Software Architect, Requirements Engineering Specialist, & Autonomous Agent Systems Architect  
> **Baseline Reference:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1`  
> **Design Phase:** P1 (Specification & Canonical Representation — Zero Production Code Modified)

---

# 1. Executive Summary

This specification establishes the canonical, machine-readable **Task Truth & Requirement Model** for the **ORAGAI** autonomous multi-agent software engineering orchestrator.

ORAGAI orchestrates specialized LLM agent personas (Architect, Developer, Tester, Reviewer, Auditor, Documentation) atop the OpenHands SDK (`openhands-sdk v1.49.4`). The primary defect identified in the P0 Forensic Baseline is the complete conflation of **Resource Safety Governance** with **Work Lifecycle Completion**. 

Prior to P1, ORAGAI evaluated task conclusion based entirely on procedural side-effects and resource limits:
- `pytest exit_code == 0` was treated as mathematical proof of feature completeness.
- `conv.run()` returning cleanly upon micro-step exhaustion was registered as successful agent execution (`ConvRunResult.completed = True`).
- Truncated git diff inspection with regex-matched keywords (`"APPROVED"`) was accepted as independent architectural review.
- The system possessed **zero data structures** representing what the user requested, how requirements were decomposed, what acceptance criteria governed them, what evidence substantiated them, or what remained unverified.

P1 resolves this foundational omission by defining a deterministic, normalized, and immutable-by-default **Task Truth Model**. This model decouples the domain reality of the work (*"What must be true for the software to meet specifications?"*) from transient execution mechanics (*"Did the agent run out of tokens or steps?"*). It provides the formal conceptual substrate upon which future Evidence Gates (P2), Dynamic Lifecycles (P3), and Governance Controls (P4+) will operate without semantic ambiguity.

---

# 2. P0 Baseline Summary

The forensic baseline established in `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md` proved that ORAGAI suffered from severe architectural pathologies rooted in an absence of work truth representation:

1. **Procedural Completion Illusions:**
   - Single-assertion test passes (`pytest == 0`) prematurely terminated the execution loop ([dev_test_loop.py:L277-280](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L277-L280)).
   - OpenHands conversation loops defaulting `ConvRunResult.completed = True` masked step limit truncation as success ([base_pipeline.py:L56](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L56)).
2. **Context & Intent Disintegration:**
   - If the Architect agent failed to write `PLAN.md`, the pipeline silently fell back to passing the raw user string to the Developer ([full_pipeline.py:L256-258](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L256-L258)).
   - The Tester never received the Architect's test strategy or decomposition, writing arbitrary smoke tests ([full_pipeline.py:L471-474](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L471-L474)).
   - The Reviewer received a 4,000-character truncated diff without access to the requirements or test results ([full_pipeline.py:L630-636](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L630-L636)).
3. **Investigation Starvation:**
   - `DynamicTokenGovernor` interrupted agents via `conv.interrupt()` if 28% of turn tokens were consumed without a file write, penalizing essential codebase analysis ([base_pipeline.py:L304-324](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L304-L324)).
4. **Passive FSM Illusion:**
   - `PipelineStateMachine` verified only phase enum transitions in a dictionary lookup without any guard predicates or evidence checks ([state_machine.py:L28-93](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/state_machine.py#L28-L93)).

P1 directly addresses these deficiencies by establishing the canonical chain of truth:
$$\text{User Task} \longrightarrow \text{Requirements} \longrightarrow \text{Acceptance Criteria} \longrightarrow \text{Evidence} \longrightarrow \text{Verified Completion}$$

---

# 3. Current-State Requirement Representation

A rigorous audit of the repository reveals the exact locations, structures, and limitations of existing task and requirement handling:

| Concern | Current Repository Location | Current Representation | Current Strength | Architectural Problem & Pathology | Migration Need |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **User Task** | `orchestrator/cli/handlers.py:L17-79` | Unstructured `str` from CLI or referenced file content. | Resolves embedded file paths and raw markdown input. | Treated as an opaque string; no parsing of goals, boundaries, or constraints. | Normalize into structured `Task` entity with immutable request preservation. |
| **Architect Output** | `orchestrator/agents/architect.py:L13-32` | Freeform markdown written to `PLAN.md` on disk. | Prompt requests milestones, interface contracts, and test strategy. | Non-deterministic structure; often missed or formatted arbitrarily. | Parse into formal `Requirement`, `Milestone`, and `Constraint` models. |
| **Milestones / Plan** | `orchestrator/pipeline/milestone_dag.py:L8-16, L63-115` | `SubtaskMilestone` Pydantic model parsed via regex header matching (`## Milestone N:`). | Extracts title, body, target files, and numeric dependency ordering. | Milestones represent execution chunks, not requirement verification contracts; no acceptance criteria. | Link `Milestone` directly to discrete `Requirement` IDs and evidence targets. |
| **Requirements & Criteria** | *None* (Missing) | Implicitly embedded inside natural language prompts. | Zero | Zero data structure; agents guess what constitutes completeness. | Create first-class `Requirement` and `AcceptanceCriterion` entities. |
| **Tests & QA** | `orchestrator/pipeline/dev_test_loop.py:L240-272` | Pytest files in `tests/test_*.py` generated on iteration 1. | Zero-token test execution skip on subsequent fix iterations. | Tester tests whatever it invents; zero traceability to user requirements. | Create `VerificationMethod` and `TestReference` linking tests to ACs. |
| **Reviewer Verdict** | `orchestrator/pipeline/reviewer_parser.py:L9-16, L58-88` | `ReviewerVerdict` dataclass parsed from JSON or fuzzy regex. | Parses `APPROVED`/`REJECTED`, reasonings, and required fixes. | Evaluates 4KB truncated diff; blind to requirement satisfaction and test outcomes. | Reviewer must evaluate evidence bundle against canonical requirement criteria. |
| **Audit Findings** | `orchestrator/analysis/schemas.py:L21-45` | `AuditFinding` Pydantic model with severity, file, line, and evidence. | Highly structured, validated with finding-level circuit breakers. | Disconnected from general engineering task requirements; used only in audit pipeline. | Generalize finding schema to integrate with requirement defect tracking. |
| **Execution State** | `orchestrator/pipeline/base_pipeline.py:L53-62` | `ConvRunResult` dataclass (`completed`, `interrupted_by_*`). | Captures token/timeout interrupts cleanly. | `completed=True` default conflates clean loop exit with requirement satisfaction. | Strict separation: `ConvRunResult` denotes execution state; Task Truth denotes work state. |
| **Pipeline Checkpoint** | `orchestrator/pipeline/checkpoint.py:L9-21` | `PipelineCheckpoint` (`.orchestrator_state.json`) with phase list. | Basic resume across agent phases. | Tracks completed phase names (`"architect"`, `"developer"`) rather than verified requirements. | Checkpoint must persist the full `TaskTruthState` graph. |
| **Telemetry & Report** | `orchestrator/telemetry/schemas.py:L34-52` | `DiagnosticReport` recording tokens, costs, durations, and incidents. | Comprehensive post-mortem telemetry. | Evaluates binary `completed_successfully: bool` based on final exit status. | Report requirement verification breakdown and evidence audit trail. |

---

# 4. Architectural Gap Analysis

The architectural gap between ORAGAI's current execution engine and a truth-driven autonomous system spans five dimensions:

```
CURRENT (PROCEDURAL TERMINATION)                  TARGET (TASK TRUTH & VERIFICATION)
┌──────────────────────────────────────┐          ┌──────────────────────────────────────┐
│  User Task: "Add JWT Authentication" │          │  Task: TASK-001                      │
│                                      │          │  ├── REQ-001 (Explicit Functional)   │
│  Architect -> PLAN.md (unstructured) │          │  │   └── AC-001.1 (Given/When/Then)  │
│  Developer -> writes code            │          │  │       └── EVID-101 (pytest pass)  │
│  Tester    -> writes 1 assert True   │          │  ├── REQ-002 (System Invariant)      │
│  Pytest    -> Exit Code 0            │          │  │   └── AC-002.1 (AST Guard clean)  │
│                                      │          │  │       └── EVID-102 (AST verified) │
│  RESULT: PIPELINE SUCCESS            │          │  └── REQ-003 (Security Constraint)   │
│  (Code is broken/incomplete)         │          │      └── AC-003.1 (No secrets logged)│
│                                      │          │          └── EVID-103 (Static Audit) │
│                                      │          │                                      │
│                                      │          │  RESULT: VERIFIED COMPLETION         │
│                                      │          │  (All criteria backed by evidence)   │
└──────────────────────────────────────┘          └──────────────────────────────────────┘
```

1. **Semantic Vacuum:** The orchestrator manages processes, threads, files, and tokens, but possesses no schema representing domain truth. It is blind to whether code fulfills intent or merely avoids syntax crashes.
2. **Asymmetric Knowledge Loss:** Context degrades monotonically across agent boundaries. The Architect formulates intent; the Developer receives a markdown snippet; the Tester receives a prompt to "write tests"; the Reviewer receives a truncated diff. Domain requirements are lost at every handoff.
3. **Absence of Traceability:** There is no bidirectional graph linking a test in `tests/test_auth.py` back to a user requirement. The system cannot answer: *"Which requirement does this test verify?"* or *"Which requirements have zero tests?"*
4. **False Equivalence of Resource Limits:** Running out of turns is classified as agent completion, while hitting token ceilings is treated as task failure rather than partial progress awaiting resumption.
5. **Vulnerability to Agent Hallucination:** Agents can fabricate requirements, claim completion without proof, or silently drop complex constraints, with no central authority to validate assertions.

---

# 5. Design Goals

The Task Truth Model must achieve the following engineering goals:

1. **Authoritative Work Truth:** Serve as the single, immutable source of truth for what was requested, what was planned, what was implemented, and what was proven.
2. **Machine-Readable & Deterministic:** Every entity (Task, Requirement, Acceptance Criterion, Constraint, Invariant, Evidence Reference) must have a globally unique, deterministic identifier and a strict Pydantic/JSON schema.
3. **Explicit Provenance:** Rigorously distinguish between explicit user commands, derived requirements, agent-proposed enhancements, environmental constraints, and system security invariants.
4. **Rigorous Verification Semantics:** Enforce that $\text{IMPLEMENTED} \neq \text{VERIFIED}$. An agent cannot declare a requirement verified; verification is an objective property derived from valid evidence.
5. **Resource-vs-Work Decoupling:** Execution state (step exhaustion, token ceiling, timeout) must never mutate requirement truth status into false success.
6. **Zero-Token Static Traceability:** Provide deterministic lookup between requirements, acceptance criteria, test files, and evidence artifacts without requiring LLM inference.
7. **Graceful Coexistence & Migration:** Integrate cleanly with existing ORAGAI subsystems (`GitOps`, `ContextManager`, `SessionLogStore`, `TelemetryRecorder`) via adapters and projections.

---

# 6. Non-Goals

To maintain strict architectural focus, P1 explicitly excludes:

1. **No Production Code Modifications:** P1 is a design specification. No production files in `orchestrator/` or tests in `tests/` will be altered during this phase.
2. **No Evidence Gate Engine Implementation (P2):** P1 defines evidence relationships and schemas, but does not build the runtime evidence collection, evaluation engine, or dynamic gate hooks.
3. **No FSM or Pipeline Redesign (P3):** P1 specifies the contracts that pipelines will consume, but does not refactor `PipelineStateMachine`, `BasePipeline`, or `DevTestLoop`.
4. **No Token Governor or Circuit Breaker Modifications (P4):** P1 defines how resource exhaustion is represented, but does not alter token thresholds or rate-limiting heuristics.
5. **No OpenHands SDK Patching:** P1 operates strictly within the existing OpenHands SDK conversation abstractions.
6. **No External Database or Enterprise BPM Infrastructure:** The model must remain lean, file-serializable (JSON/YAML), and embedded directly within the project workspace and diagnostics store.

---

# 7. Canonical Task Truth Model

The canonical Task Truth Model organizes work into a formal hierarchical and relational graph:

```
                           ┌──────────────────────────────┐
                           │          USER TASK           │
                           │   (Immutable Root Request)   │
                           └──────────────┬───────────────┘
                                          │
                                          ▼
                           ┌──────────────────────────────┐
                           │      TASK TRUTH GRAPH        │
                           │  (Canonical State Container) │
                           └──────────────┬───────────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
 ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
 │     REQUIREMENTS     │      │     CONSTRAINTS      │      │      INVARIANTS      │
 │ (Functional/Behavior)│      │(Environment/Platform)│      │  (Security/RBAC/AST) │
 └──────────┬───────────┘      └──────────┬───────────┘      └──────────┬───────────┘
            │                             │                             │
            ▼                             ▼                             ▼
 ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
 │ ACCEPTANCE CRITERIA  │      │  GUARD RESTRICTIONS  │      │ INVIOLABLE PROTOCOLS │
 │ (Given / When / Then)│      │  (Tool/Command Bans) │      │ (Zero Stub / Safety) │
 └──────────┬───────────┘      └──────────┬───────────┘      └──────────┬───────────┘
            │                             │                             │
            └─────────────────────────────┼─────────────────────────────┘
                                          │
                                          ▼
                           ┌──────────────────────────────┐
                           │          MILESTONES          │
                           │    (Execution DAG Chunks)    │
                           └──────────────┬───────────────┘
                                          │
                                          ▼
                           ┌──────────────────────────────┐
                           │      EVIDENCE BUNDLE         │
                           │  (Test/AST/Diff/Audit Proof) │
                           └──────────────┬───────────────┘
                                          │
                                          ▼
                           ┌──────────────────────────────┐
                           │     VERIFICATION ENGINE      │
                           │    (Evaluates Truth State)   │
                           └──────────────┬───────────────┘
                                          │
                                          ▼
                           ┌──────────────────────────────┐
                           │      FINAL TASK STATUS       │
                           │   (VERIFIED / INCOMPLETE)    │
                           └──────────────────────────────┘
```

---

# 8. Entity Model

The Task Truth Model is composed of twelve normalized entities:

```
+-----------------------------------------------------------------------------------+
|                                  ENTITY TAXONOMY                                  |
+-----------------------------------------------------------------------------------+
|  1. Task               |  5. Invariant          |   9. EvidenceReference          |
|  2. Requirement        |  6. Milestone          |  10. VerificationResult         |
|  3. AcceptanceCriterion|  7. ArtifactReference |  11. RequirementMutationRecord  |
|  4. Constraint         |  8. TestReference      |  12. TaskTruthGraph (Container) |
+-----------------------------------------------------------------------------------+
```

### Detailed Entity Specifications

#### 1. `Task`
- **Why it exists:** Represents the overarching unit of work requested by the user or upstream orchestrator.
- **Problem solved:** Eliminates string-passing ambiguity and preserves the original, unaltered user prompt.
- **Why not a simple field:** Requires metadata (timestamps, workspace root, creator, priority, overall status).
- **Author:** Created by Intake / CLI Handler during initialization.
- **Mutators:** Status updated by Pipeline Controller / Verification Gate.

#### 2. `Requirement`
- **Why it exists:** Represents an atomic, independently verifiable functional, behavioral, or architectural obligation.
- **Problem solved:** Decomposes complex tasks into discrete units that can be assigned, tracked, and proven.
- **Why not a simple field:** Must maintain its own status, priority, provenance, dependencies, acceptance criteria, and evidence links.
- **Author:** Architect Agent (decomposed from task) or Intake System.
- **Mutators:** Architect Agent (during replanning); Status mutated only by Verification Engine.

#### 3. `AcceptanceCriterion`
- **Why it exists:** Defines the objective, unambiguous condition under which a requirement is satisfied.
- **Problem solved:** Eliminates vague hand-waving (*"code works well"*) by requiring verifiable propositions (Given/When/Then, exit code assertions, structural AST checks).
- **Why not a simple field:** A single requirement may have multiple distinct criteria evaluated through different verification methods.
- **Author:** Architect Agent (initial specification) and Tester Agent (executable test binding).
- **Mutators:** Immutable once planned unless formal mutation cycle is triggered.

#### 4. `Constraint`
- **Why it exists:** Encapsulates environmental, platform, tooling, or operational boundaries (e.g., Windows OS, Python 3.12+, no UNIX pipe characters).
- **Problem solved:** Prevents agents from attempting invalid commands or using unsupported libraries.
- **Why not a simple field:** Constraints apply globally or to specific requirement subsets and enforce guard predicates.
- **Author:** System Configuration / Intake / Architect.
- **Mutators:** Read-only for agents.

#### 5. `Invariant`
- **Why it exists:** Represents non-negotiable security, architectural, and safety laws that must never be violated (e.g., zero placeholders/stubs, workspace isolation, secret sanitization, AST validity).
- **Problem solved:** Ensures that functional implementations do not compromise system integrity.
- **Why not a simple field:** Invariants must be continuously verified across all pipeline transitions.
- **Author:** System Core / Security Governance.
- **Mutators:** Inviolable and immutable.

#### 6. `Milestone`
- **Why it exists:** Represents an ordered, executable work package in a Dependency Acyclic Graph (DAG) for developer implementation.
- **Problem solved:** Bridges high-level requirements with iterative developer token budgets and execution steps.
- **Why not a simple field:** Tracks implementation progress, target file sets, and prerequisite relationships.
- **Author:** Architect Agent (via `MilestoneParser`).
- **Mutators:** Pipeline runner (tracks active/completed milestones).

#### 7. `ArtifactReference`
- **Why it exists:** Tracks files created, modified, or referenced during task execution with hash and size metadata.
- **Problem solved:** Links requirements and acceptance criteria to concrete codebase modifications.
- **Why not a simple field:** Requires path normalization, change type classification, and SHA-256 integrity verification.
- **Author:** GitOps / Workspace Tools.
- **Mutators:** Automatically recorded by telemetry upon file operations.

#### 8. `TestReference`
- **Why it exists:** Points to a concrete, executable test file and test function (e.g., `tests/test_auth.py::test_jwt_expiration`).
- **Problem solved:** Establishes explicit traceability between acceptance criteria and automated test suites.
- **Why not a simple field:** Contains runner type, execution flags, and expected assertions.
- **Author:** Tester Agent.
- **Mutators:** Tester Agent during test authoring.

#### 9. `EvidenceReference`
- **Why it exists:** Links an acceptance criterion to a concrete piece of empirical verification data (test run result, AST check, static lint, reviewer report).
- **Problem solved:** Decouples the assertion of completion from the proof of completion.
- **Why not a simple field:** Must record evidence type, artifact URI, timestamp, producer role, and cryptographic/hash integrity.
- **Author:** Verification Runners (Pytest, PreFlightGuard, Reviewer).
- **Mutators:** Append-only.

#### 10. `VerificationResult`
- **Why it exists:** Captures the deterministic evaluation of an Acceptance Criterion against its associated Evidence.
- **Problem solved:** Replaces subjective agent claims with boolean/structured verification records.
- **Why not a simple field:** Records evaluator, evaluation timestamp, pass/fail status, and diagnostic messages.
- **Author:** Verification Engine (P2 Gate).
- **Mutators:** Immutable once evaluated for a specific run iteration.

#### 11. `RequirementMutationRecord`
- **Why it exists:** Tracks any addition, deprecation, revision, or waiver of a requirement during the execution lifecycle.
- **Problem solved:** Prevents silent scope drift and ensures auditability when requirements evolve.
- **Why not a simple field:** Requires versioning, author attribution, rationale, and diff tracking.
- **Author:** Architect / User / System Controller.
- **Mutators:** Append-only history.

#### 12. `TaskTruthGraph`
- **Why it exists:** The authoritative top-level container holding the complete normalized graph of all entities above.
- **Problem solved:** Provides a single, serializable, queryable data structure representing the entire state of task truth.
- **Author:** Orchestrator Runtime.
- **Mutators:** Managed through formal transition methods.

---

# 9. Requirement Taxonomy

To enable precise agent reasoning without taxonomy bloat, ORAGAI adopts a concise, 8-category controlled vocabulary:

```
+-----------------------------------------------------------------------------------+
|                              REQUIREMENT TAXONOMY                                 |
+-----------------------------------------------------------------------------------+
|  1. FUNCTIONAL       | Core business logic, APIs, CLI commands, and features.      |
|  2. BEHAVIORAL       | Error handling, boundary conditions, edge cases, timeouts. |
|  3. ARCHITECTURAL    | Modularity, interface contracts, coupling, clean patterns. |
|  4. SECURITY         | Auth, RBAC, input sanitization, secret masking, injection. |
|  5. PERFORMANCE      | Latency limits, token efficiency, memory bounds, caching.  |
|  6. COMPATIBILITY    | Windows OS support, Python 3.12 syntax, tool restrictions. |
|  7. QUALITY_ASSURANCE| Pytest suite coverage, deterministic fixtures, mocks.      |
|  8. DOCUMENTATION    | README, API references, docstrings, runnable demo scripts. |
+-----------------------------------------------------------------------------------+
```

---

# 10. Requirement Provenance Model

Provenance defines the origin and authority of each requirement. This prevents agents from inventing unauthorized requirements or treating suggestions as user mandates:

```
                                PROVENANCE HIERARCHY
                                
      ┌──────────────────────────────────────────────────────────────┐
      │                   SYSTEM_INVARIANT (Root)                    │
      │      (Inviolable security, AST, and safety invariants)       │
      └──────────────────────────────┬───────────────────────────────┘
                                     │
      ┌──────────────────────────────▼───────────────────────────────┐
      │                      EXPLICIT_USER                           │
      │         (Directly specified in original user task)           │
      └──────────────────────────────┬───────────────────────────────┘
                                     │
      ┌──────────────────────────────▼───────────────────────────────┐
      │                   ENVIRONMENTAL_CONSTRAINT                   │
      │       (Windows OS, Python version, tool permission rules)    │
      └──────────────────────────────┬───────────────────────────────┘
                                     │
      ┌──────────────────────────────▼───────────────────────────────┐
      │                         DERIVED                              │
      │  (Logically required implementation details derived from user│
      │   request, e.g. schema models, database helper methods)      │
      └──────────────────────────────┬───────────────────────────────┘
                                     │
      ┌──────────────────────────────▼───────────────────────────────┐
      │                     AGENT_PROPOSED                           │
      │   (Suggested enhancements, optimizations, or extra features  │
      │    proposed by Architect/Auditor - Non-blocking by default)  │
      └──────────────────────────────────────────────────────────────┘
```

### Provenance Rules:
1. **`EXPLICIT_USER`:** Mandatory. Cannot be deleted or waived without user/controller intervention.
2. **`SYSTEM_INVARIANT`:** Mandatory and non-negotiable. Always active regardless of task description.
3. **`ENVIRONMENTAL_CONSTRAINT`:** Mandatory. Automatically populated by project adapters and host detection.
4. **`DERIVED`:** Mandatory once accepted by Architect. Must link to at least one parent `EXPLICIT_USER` requirement.
5. **`AGENT_PROPOSED`:** Optional/Advisory. **Cannot block task completion** unless explicitly promoted to `DERIVED` or approved via human approval gate.

---

# 11. Acceptance Criteria Model

Acceptance Criteria transform abstract requirements into deterministic verification targets. Every `AcceptanceCriterion` must specify a concrete `VerificationType`:

```
+-----------------------------------------------------------------------------------+
|                             VERIFICATION TYPES                                    |
+-----------------------------------------------------------------------------------+
|  1. AUTOMATED_TEST   | Execution of pytest unit/integration test functions.       |
|  2. STATIC_AST       | Zero-token AST parsing, symbol existence, type checking.  |
|  3. FILE_ASSERTION   | File existence, non-emptiness, path placement.             |
|  4. COMMAND_EXEC     | Standalone subprocess command execution (e.g. demo script).|
|  5. STATIC_LINT      | Ruff linter / PreFlight syntax compilation.                |
|  6. REVIEWER_RUBRIC  | Independent Reviewer evaluation against code standards.   |
|  7. AUDIT_VERIFY     | Absence of high/critical audit defects in target files.    |
+-----------------------------------------------------------------------------------+
```

### Structured Structure:
Each criterion is expressed using structured Given/When/Then semantics combined with machine-actionable targets:

```yaml
id: AC-001.1
requirement_id: REQ-001
description: "JWT token validation rejects expired tokens with HTTP 401"
verification_type: AUTOMATED_TEST
given: "An expired JWT token signed with valid secret"
when: "Invoking verify_token() endpoint"
then: "Raises TokenExpiredException and returns 401 status"
target_test: "tests/test_auth.py::test_expired_token_rejection"
target_files:
  - "orchestrator/auth/jwt.py"
is_mandatory: true
```

---

# 12. Evidence Relationship Contract

Evidence constitutes the empirical proof that an Acceptance Criterion has been satisfied. 

```
┌───────────────────────────┐         ┌───────────────────────────┐
│        REQUIREMENT        │ 1     * │    ACCEPTANCE CRITERION   │
│         (REQ-001)         ├─────────┤         (AC-001.1)        │
└───────────────────────────┘         └─────────────┬─────────────┘
                                                    │ 1
                                                    │
                                                    │ *
                                      ┌─────────────▼─────────────┐
                                      │     EVIDENCE REFERENCE    │
                                      │         (EVID-101)        │
                                      └─────────────┬─────────────┘
                                                    │
                                                    ▼
                                      ┌───────────────────────────┐
                                      │      RAW EVIDENCE DATA    │
                                      │  - Pytest Execution Run   │
                                      │  - PreFlight AST Check    │
                                      │  - Reviewer Verdict JSON  │
                                      │  - Git Diff Snapshot      │
                                      └───────────────────────────┘
```

### Cardinality & Integrity Rules:
1. **One-to-Many Requirement to Criteria:** A Requirement may contain 1 to $N$ Acceptance Criteria.
2. **One-to-Many Criterion to Evidence:** A single Criterion may require multiple pieces of Evidence (e.g., automated test pass + zero-token AST syntax pass).
3. **Many-to-One Evidence Reuse:** A single Evidence item (e.g., a full pytest suite execution report) may provide verification data for multiple Acceptance Criteria simultaneously.
4. **Evidence Freshness:** Evidence is valid only if generated **after** the latest file modification to target files (`evidence.timestamp >= max(artifact.modified_at)`). Any subsequent code edit invalidates existing evidence and resets verification state.
5. **Producer Attribution:** Every evidence record must identify the producing tool/agent (`producer_role`: `"tester"`, `"preflight"`, `"reviewer"`, `"ast_guard"`).

---

# 13. Requirement Status Semantics

The lifecycle of a Requirement is strictly governed by a deterministic state machine:

```
                             REQUIREMENT LIFECYCLE
                             
 ┌───────────────┐
 │   PROPOSED    │ ◄── Intake / Agent suggestion
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │   PLANNED     │ ◄── Decomposed by Architect into Acceptance Criteria
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │  IN_PROGRESS  │ ◄── Assigned to Developer Milestone
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │  IMPLEMENTED  │ ◄── Developer completed edits (Code exists on disk)
 └───────┬───────┘
         │
         ▼
 ┌───────────────────────┐
 │ VERIFICATION_PENDING  │ ◄── Tests authored; awaiting test/gate execution
 └───────┬───────────────┘
         │
         ├────────────────────────────────┐
         ▼                                ▼
 ┌───────────────┐                ┌───────────────┐
 │   VERIFIED    │                │    FAILED     │ ◄── Evidence shows failure
 └───────────────┘                └───────┬───────┘
                                          │
                                          ▼
                                  (Routes to FIX phase)
```

### Additional States:
- **`BLOCKED`:** Requirement cannot proceed due to unmet dependencies, missing environment tools, or upstream failures.
- **`WAIVED`:** Explicitly marked non-mandatory by human operator or controller (strictly prohibited for `EXPLICIT_USER` and `SYSTEM_INVARIANT` requirements).

### Core Semantic Invariants:
1. **$\text{IMPLEMENTED} \neq \text{VERIFIED}$:** A Developer agent writing code transitions a requirement to `IMPLEMENTED`. Only the independent Verification Engine evaluating valid `EvidenceReference` artifacts can transition it to `VERIFIED`.
2. **No Self-Verification:** An agent cannot set its own work to `VERIFIED`.
3. **Zero Partial Truth:** A requirement with 3 acceptance criteria is not `VERIFIED` until all 3 criteria evaluate to `PASSED`.

---

# 14. Requirement Dependency Model

Requirements can declare explicit prerequisite dependencies.

```
       ┌───────────┐
       │  REQ-001  │ (Data Models & Schema)
       └─────┬─────┘
             │
             ├──────────────────────────┐
             ▼                          ▼
       ┌───────────┐              ┌───────────┐
       │  REQ-002  │ (Storage API)│  REQ-003  │ (Auth Engine)
       └─────┬─────┘              └─────┬─────┘
             │                          │
             └───────────┬──────────────┘
                         ▼
                   ┌───────────┐
                   │  REQ-004  │ (REST Endpoints)
                   └───────────┘
```

### Dependency Rules:
1. **Acyclic Enforcement:** The dependency graph must form a strict Directed Acyclic Graph (DAG). Cycles are detected at plan parse time and rejected.
2. **Cascading Blocker:** If `REQ-001` fails or is blocked, all dependent requirements (`REQ-002`, `REQ-003`, `REQ-004`) automatically transition to `BLOCKED`.
3. **Verification Prerequisite:** A dependent requirement cannot be marked `VERIFIED` until all prerequisite requirements are in `VERIFIED` state.

---

# 15. Milestone Model

Milestones represent executable work packages that group requirements for iterative agent execution.

```
TaskTruthGraph
 ├── Requirement: REQ-001 (Schema) ──────────┐
 ├── Requirement: REQ-002 (Storage API) ────┼──► Milestone 1: Core Foundation
 │                                           │    (Target files: models.py, db.py)
 ├── Requirement: REQ-003 (Auth Engine) ────┼──► Milestone 2: Authentication
 └── Requirement: REQ-004 (Endpoints) ──────┴──► Milestone 3: API Integration
```

### Milestone Semantics:
- A `Milestone` maps to a discrete developer invocation turn.
- A `Milestone` is `COMPLETE` when all associated requirements reach `IMPLEMENTED` state and satisfy preflight syntax checks.
- Milestone completion allows the developer loop to advance, but does **not** signify final task completion.

---

# 16. Task Completion Semantics

Task completion is a pure mathematical function of the `TaskTruthGraph`:

$$\text{Task Complete} \iff \begin{cases}
\forall r \in \text{Requirements}_{\text{mandatory}}, & \text{status}(r) = \text{VERIFIED} \\
\forall c \in \text{AcceptanceCriteria}_{\text{mandatory}}, & \text{eval}(c) = \text{PASSED} \\
\forall i \in \text{Invariants}, & \text{violated}(i) = \text{False} \\
\forall e \in \text{RequiredEvidence}, & \text{fresh}(e) = \text{True} \land \text{valid}(e) = \text{True} \\
\text{UnresolvedBlockingDefects} & = \emptyset
\end{cases}$$

```
+-----------------------------------------------------------------------------------+
|                        DETERMINISTIC COMPLETION MATRIX                            |
+------------------------------------+-----------------------+----------------------+
| Condition / Scenario               | Evaluated Task Status | Action / Verdict     |
+------------------------------------+-----------------------+----------------------+
| All mandatory requirements verified| COMPLETE              | Success / Git Commit |
| Tests pass, but REQs unverified    | INCOMPLETE            | Trigger Tester Agent |
| REQs implemented, but tests fail   | FAILED                | Trigger Fix Loop     |
| Step limit reached before verify   | INCOMPLETE_STEP_LIMIT | Resume or Escalate   |
| Token budget exhausted             | INCOMPLETE_RESOURCES  | Halt with Snapshot   |
| Provider quota (429) fails         | BLOCKED_PROVIDER      | Switch or Save State |
| Reviewer rejects architecture      | REVIEW_REJECTED       | Trigger Review Fix   |
+------------------------------------+-----------------------+----------------------+
```

---

# 17. Resource-vs-Work State Separation

To eliminate the conflation identified in P0, ORAGAI explicitly separates **Work Truth State** from **Execution State**:

```
┌────────────────────────────────────────┐     ┌────────────────────────────────────────┐
│            WORK TRUTH STATE            │     │            EXECUTION STATE             │
│        (Domain & Specification)        │     │       (Runtime Resources & Engine)     │
├────────────────────────────────────────┤     ├────────────────────────────────────────┤
│ • Requirement Status: IN_PROGRESS      │     │ • OpenHands Step: 5 of 5 (Exhausted)   │
│ • Acceptance Criteria Met: 2 of 4      │     │ • Turn Tokens Consumed: 12,400 / 15,000│
│ • Target Code Written: Yes             │     │ • Dollar Spend: $0.12 / $0.50          │
│ • Evidence Verified: Partial (50%)     │     │ • Wall-Clock Time: 45s / 300s          │
│ • Work Complete: FALSE                 │     │ • Conversation State: STOPPED          │
└────────────────────────────────────────┘     └────────────────────────────────────────┘
```

### Separation Invariant:
> **An execution termination event (`STEP_LIMIT_REACHED`, `TOKEN_LIMIT_REACHED`, `TIMEOUT`, `INTERRUPTED`) modifies ONLY the Execution State. It is strictly prohibited from mutating any Requirement from `IN_PROGRESS` to `VERIFIED` or declaring the overall Task `COMPLETE`.**

---

# 18. Requirement Mutation Semantics

Requirements may evolve during execution due to user scope changes, discovery of architectural dependencies, or reviewer feedback. All mutations must be formally recorded:

```
┌─────────────────────────────────────────────────────────────┐
│                 REQUIREMENT MUTATION RECORD                 │
├─────────────────────────────────────────────────────────────┤
│ • Mutation ID: MUT-004                                      │
│ • Timestamp: 2026-09-25T05:40:00Z                           │
│ • Author Role: "architect" (or "user")                      │
│ • Target Requirement: REQ-002                               │
│ • Action: REVISED (or ADDED, DEPRECATED, SPLIT, MERGED)     │
│ • Previous State: Description without rate-limiting         │
│ • New State: Description including token bucket rate limits │
│ • Rationale: "Reviewer identified missing DDoS protection"  │
│ • Superseded By: None                                       │
+-------------------------------------------------------------+
```

### Rules:
1. Requirements are **never silently overwritten or deleted**.
2. Modifying an existing requirement creates a new revision and invalidates all previously attached `EvidenceReference` items.
3. Only the `User` or `Architect` (with plan approval) can create or revise requirements.

---

# 19. Agent Responsibility Matrix

Permissions across the Task Truth Model are strictly partitioned using Role-Based Access Control (RBAC):

| Entity / Action | User | Intake | Architect | Developer | Tester | Reviewer | Auditor | Verification Engine |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Create Task** | **Author** | **Author** | Read | Read | Read | Read | Read | Read |
| **Create Requirement** | **Author** | Read | **Author** | Read | Read | Suggest | Suggest | Read |
| **Modify Requirement** | **Author** | Denied | **Author** | Denied | Denied | Denied | Denied | Denied |
| **Create Acceptance Criteria** | Suggest | Read | **Author** | Read | **Author** | Suggest | Suggest | Read |
| **Create Milestone** | Read | Read | **Author** | Read | Read | Read | Read | Read |
| **Write Production Code** | Denied | Denied | Denied | **Author** | Denied | Denied | Denied | Denied |
| **Write Test Code** | Denied | Denied | Denied | Denied | **Author** | Denied | Denied | Denied |
| **Produce Evidence** | Denied | Denied | Denied | Output | **Author** | **Author** | **Author** | **Author** |
| **Mutate Requirement Status** | Override | Denied | Propose | Mark Impl | Denied | Denied | Denied | **Authoritative** |
| **Approve Final Completion** | Override | Denied | Denied | Denied | Denied | Review | Review | **Authoritative** |

---

# 20. Agent Handoff Contract

To eliminate context asymmetry and truncation loss between pipeline stages, ORAGAI defines formal handoff payloads:

```
[ User Request ]
       │
       ▼ (Task Handoff Payload)
[ Architect ]
       │
       ▼ (Architecture Handoff Payload: TaskTruthGraph + PLAN.md + Milestones)
[ Developer ]
       │
       ▼ (Implementation Handoff Payload: TaskTruthGraph + Modified Files + Preflight AST)
[ Tester ]
       │
       ▼ (QA Handoff Payload: TaskTruthGraph + Test Files + Pytest Execution Evidence)
[ Reviewer ]
       │
       ▼ (Review Handoff Payload: TaskTruthGraph + Full Diff + Full Test Suite Report)
[ Verification Gate / Final Completion ]
```

### Invariant:
> **If `PLAN.md` or `TaskTruthGraph` is missing, the system MUST NOT silently fall back to passing the raw user string to downstream agents. It must halt or re-trigger the Architect agent.**

---

# 21. Machine-Readable Schema Proposal

The canonical model is implemented via strict Pydantic v2 schemas:

```python
"""Canonical Task Truth & Requirement Model Schemas for ORAGAI."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    FUNCTIONAL = "FUNCTIONAL"
    BEHAVIORAL = "BEHAVIORAL"
    ARCHITECTURAL = "ARCHITECTURAL"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    COMPATIBILITY = "COMPATIBILITY"
    QUALITY_ASSURANCE = "QUALITY_ASSURANCE"
    DOCUMENTATION = "DOCUMENTATION"


class RequirementProvenance(str, Enum):
    EXPLICIT_USER = "EXPLICIT_USER"
    SYSTEM_INVARIANT = "SYSTEM_INVARIANT"
    ENVIRONMENTAL_CONSTRAINT = "ENVIRONMENTAL_CONSTRAINT"
    DERIVED = "DERIVED"
    AGENT_PROPOSED = "AGENT_PROPOSED"


class RequirementStatus(str, Enum):
    PROPOSED = "PROPOSED"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    WAIVED = "WAIVED"


class VerificationType(str, Enum):
    AUTOMATED_TEST = "AUTOMATED_TEST"
    STATIC_AST = "STATIC_AST"
    FILE_ASSERTION = "FILE_ASSERTION"
    COMMAND_EXEC = "COMMAND_EXEC"
    STATIC_LINT = "STATIC_LINT"
    REVIEWER_RUBRIC = "REVIEWER_RUBRIC"
    AUDIT_VERIFY = "AUDIT_VERIFY"


class EvidenceType(str, Enum):
    PYTEST_RUN = "PYTEST_RUN"
    AST_CHECK = "AST_CHECK"
    LINT_REPORT = "LINT_REPORT"
    REVIEWER_VERDICT = "REVIEWER_VERDICT"
    COMMAND_OUTPUT = "COMMAND_OUTPUT"
    DIFF_STAT = "DIFF_STAT"


class EvidenceReference(BaseModel):
    id: str = Field(..., description="Unique evidence ID, e.g. EVID-001")
    evidence_type: EvidenceType
    producer_role: str = Field(..., description="Agent or tool producing evidence")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    is_passing: bool = False
    artifact_hashes: Dict[str, str] = Field(default_factory=dict)


class AcceptanceCriterion(BaseModel):
    id: str = Field(..., description="Unique criterion ID, e.g. AC-001.1")
    requirement_id: str
    description: str
    verification_type: VerificationType
    given: Optional[str] = None
    when: Optional[str] = None
    then: Optional[str] = None
    target_test: Optional[str] = None
    target_files: List[str] = Field(default_factory=list)
    is_mandatory: bool = True
    is_satisfied: bool = False
    evidence_ids: List[str] = Field(default_factory=list)


class Requirement(BaseModel):
    id: str = Field(..., description="Unique requirement ID, e.g. REQ-001")
    title: str
    description: str
    type: RequirementType = RequirementType.FUNCTIONAL
    provenance: RequirementProvenance = RequirementProvenance.EXPLICIT_USER
    parent_requirement_id: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)  # 1 = Highest
    is_mandatory: bool = True
    status: RequirementStatus = RequirementStatus.PROPOSED
    dependencies: List[str] = Field(default_factory=list)
    milestone_id: Optional[str] = None
    acceptance_criteria: List[AcceptanceCriterion] = Field(default_factory=list)
    target_files: List[str] = Field(default_factory=list)
    version: int = 1


class TaskConstraint(BaseModel):
    id: str = Field(..., description="Unique constraint ID, e.g. CONST-001")
    description: str
    category: str = "ENVIRONMENT"  # ENVIRONMENT, SECURITY, PLATFORM
    enforced_by: str = "PREFLIGHT"


class TaskMilestone(BaseModel):
    id: str = Field(..., description="Unique milestone ID, e.g. MS-01")
    index: int
    title: str
    description: str
    requirement_ids: List[str] = Field(default_factory=list)
    target_files: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    is_completed: bool = False


class TaskTruthGraph(BaseModel):
    task_id: str = Field(..., description="Unique task execution ID")
    original_request: str
    normalized_request: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requirements: List[Requirement] = Field(default_factory=list)
    constraints: List[TaskConstraint] = Field(default_factory=list)
    milestones: List[TaskMilestone] = Field(default_factory=list)
    evidence_store: List[EvidenceReference] = Field(default_factory=list)
    overall_status: str = "IN_PROGRESS"
    version: int = 1

    def is_task_complete(self) -> bool:
        """Evaluate canonical completion function."""
        mandatory_reqs = [r for r in self.requirements if r.is_mandatory]
        if not mandatory_reqs:
            return False
        return all(r.status == RequirementStatus.VERIFIED for r in mandatory_reqs)
```

---

# 22. Compatibility & Migration Strategy

To avoid destabilizing the active codebase, ORAGAI introduces Task Truth via a phased 4-stage adoption strategy:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE A: SHADOW RECOGNITION (P1 -> P2 Transition)                       │
│ • TaskTruthGraph initialized alongside existing strings and PLAN.md.   │
│ • MilestoneParser projected into TaskMilestone entities.                │
│ • Pytest output and Reviewer parsed into EvidenceReference objects.     │
│ • Legacy execution flow remains intact; truth graph runs in shadow.     │
├─────────────────────────────────────────────────────────────────────────┤
│ PHASE B: ADAPTER BRIDGING (P2 Implementation)                           │
│ • ContextManager injects structured TaskTruthGraph into prompts.        │
│ • PipelineCheckpoint persists TaskTruthGraph in `.orchestrator_state`.  │
│ • BasePipeline exposes truth status queries.                            │
├─────────────────────────────────────────────────────────────────────────┤
│ PHASE C: AUTHORITATIVE COMPLETION GATING (P3 Implementation)            │
│ • Pipeline conclusion gated by TaskTruthGraph.is_task_complete().       │
│ • Legacy `pytest == 0` shortcut removed.                                │
│ • Missing PLAN.md triggers replanning rather than raw fallback.        │
├─────────────────────────────────────────────────────────────────────────┤
│ PHASE D: FULL CONVERGENCE (P4+ Hardening)                               │
│ • All agent prompts generated directly from TaskTruthGraph.             │
│ • Telemetry and audit reports render requirement verification matrices. │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 23. Backward Compatibility with Legacy Tasks

For tasks initiated without formal requirement decomposition (e.g., legacy CLI strings or simple one-shot commands):

1. **Synthetic Root Requirement:** The system automatically constructs a synthetic requirement:
   ```yaml
   id: REQ-000
   title: "Execute Legacy Task Specification"
   description: "<raw task description>"
   provenance: EXPLICIT_USER
   type: FUNCTIONAL
   status: IN_PROGRESS
   acceptance_criteria:
     - id: AC-000.1
       verification_type: AUTOMATED_TEST
       description: "Automated test suite execution succeeds with zero failures"
   ```
2. **Graceful Degradation:** Legacy pipelines (`DevTestLoop`, `DocumentationPipeline`) continue functioning without breaking changes while populating the underlying truth graph.

---

# 24. Failure Semantics

Failure states in the Task Truth Model are explicit and non-collapsing:

```
+-----------------------------------------------------------------------------------+
|                            FAILURE STATE TAXONOMY                                 |
+-----------------------------------------------------------------------------------+
|  1. FAILED_VERIFICATION  | Implementation complete, but test/criteria evidence failed.
|  2. BLOCKED_DEPENDENCY   | Prerequisite requirement failed or was blocked.        |
|  3. BLOCKED_ENVIRONMENT  | Missing tools, OS incompatibility, or permissions.     |
|  4. INCOMPLETE_RESOURCE  | Token ceiling or step limit reached before verify.     |
|  5. AMBIGUOUS_REQUEST    | User request lacks verifiable criteria (needs clarify).|
|  6. INVARIANT_VIOLATION  | AST syntax error, placeholder detected, security trip. |
|  7. HUMAN_REJECTED       | Rejected at human approval gate.                       |
+-----------------------------------------------------------------------------------+
```

---

# 25. Security & Governance Invariants

The Task Truth Model preserves and strengthens all P0 Security Invariants:

1. **Zero Stub Invariant:** Requirements for production code cannot be verified if AST inspection detects `# TODO`, `pass` placeholders in public methods, or unhandled `NotImplementedError`.
2. **Workspace Isolation:** Target files in requirements must be validated against `workspace_path.resolve()`. Absolute paths outside workspace are rejected.
3. **RBAC Enforcement:** Developer cannot write to `tests/`; Tester cannot write outside `tests/`; Reviewer has zero write access.
4. **Command Restrictions:** Constraints enforce Windows-safe PowerShell commands and ban chained shell escape characters (`&`, `|`, `;`).
5. **Secret Sanitization:** Evidence payloads must sanitize environment variables and tokens before persisting to disk.

---

# 26. Benchmark Taxonomy Mapping

Validation of the Task Truth Model across the 8 P0 system benchmarks:

```
+-----------------------------------------------------------------------------------+
|                                BENCHMARK MAPPING                                  |
+-----------------------------------------------------------------------------------+
| BM-01: Single-File Bug Fix                                                        |
| • 1 Functional REQ (Bug remediation) + 1 QA REQ (Regression test)                 |
| • AC: Pytest pass for targeted test function; Diff limited to 1 file.            |
+-----------------------------------------------------------------------------------+
| BM-02: Multi-File Feature                                                         |
| • 3-5 Functional REQs + 1 Architectural REQ + 1 QA REQ                            |
| • Decomposed into 2-3 Milestones; ACs require unit + integration tests.           |
+-----------------------------------------------------------------------------------+
| BM-03: Architectural Refactor                                                     |
| • 2 Architectural REQs (Decoupling) + 1 Invariant (Zero regression in existing test)|
| • AC: All existing tests pass + Graft coupling metrics show decreased fan-out.   |
+-----------------------------------------------------------------------------------+
| BM-04: Deep Audit                                                                 |
| • N Architectural/Security REQs mapping to AST & static linter findings.          |
| • AC: Full workspace scan with verified code evidence for all reported findings.  |
+-----------------------------------------------------------------------------------+
| BM-05: Audit-Fix Loop                                                             |
| • 1 REQ per actionable finding in audit backlog.                                  |
| • AC: Target finding remediated, zero syntax errors, regression tests pass.       |
+-----------------------------------------------------------------------------------+
| BM-06: New Subsystem Greenfield                                                   |
| • 5-10 REQs (Models, Services, CLI, Docs, Demo) across 4 Milestones.              |
| • AC: Full test suite pass + Runnable `demo.py` execution succeeds (exit 0).       |
+-----------------------------------------------------------------------------------+
| BM-07: Cross-Platform CLI                                                         |
| • Functional REQs + Compatibility Constraint (Windows PowerShell / UNIX).         |
| • AC: Command execution succeeds without UNIX-specific pipe/grep syntax.         |
+-----------------------------------------------------------------------------------+
| BM-08: Stagnation & Failure Recovery                                              |
| • Fix loop encounters repeated test failure.                                      |
| • Truth state preserves partial progress without tripping premature exit.        |
+-----------------------------------------------------------------------------------+
```

---

# 27. Architectural Anti-Patterns

The following anti-patterns are permanently forbidden:

```
+-----------------------------------------------------------------------------------+
|                              PROHIBITED ANTI-PATTERNS                             |
+-----------------------------------------------------------------------------------+
|  1. "pytest == 0 => Complete"     | Trivial or non-existent tests masquerade as   |
|                                   | requirement completion.                       |
|  2. "Agent Stopped => Complete"   | Step limit exhaustion defaults to success.    |
|  3. "Diff Exists => Complete"     | Producing file edits does not prove intent.   |
|  4. "Reviewer LGTM => Complete"   | Reviewer approves truncated diff without test |
|                                   | suite verification.                           |
|  5. "One Boolean State"           | Flattening multi-dimensional requirements into|
|                                   | `completed: bool`.                            |
|  6. "Agent TODOs = Requirements"  | Ephemeral markdown notes replace formal truth.|
|  7. "Inferred = User Mandate"     | Agent suggestions become blocking constraints.|
|  8. "Budget Kill = Task Failure"  | Token limit wipes out work state.             |
+-----------------------------------------------------------------------------------+
```

---

# 28. Explicit Answers to Architectural Questions

The 25 mandatory architectural questions are answered definitively:

1. **Authoritative source of truth for task completion:** The `TaskTruthGraph` evaluating whether all mandatory `Requirement` and `AcceptanceCriterion` entities are in `VERIFIED` status backed by valid `EvidenceReference` records.
2. **Difference between requirement, acceptance criterion, milestone, and evidence:**
   - *Requirement:* What capability/behavior must exist.
   - *Acceptance Criterion:* How that requirement is objectively evaluated.
   - *Milestone:* When and in what execution order the code is implemented.
   - *Evidence:* Concrete, timestamped data proving the criterion was met.
3. **Which requirements are mandatory:** Requirements with `provenance IN (EXPLICIT_USER, SYSTEM_INVARIANT, ENVIRONMENTAL_CONSTRAINT)` and `is_mandatory = True`.
4. **Can an agent create a new requirement:** Yes, the Architect can create `DERIVED` or `AGENT_PROPOSED` requirements. `AGENT_PROPOSED` requirements are advisory by default.
5. **Can an agent delete a requirement:** No. Requirements can only be `DEPRECATED` or `MUTATED` with a formal `RequirementMutationRecord`.
6. **Can an agent mark a requirement verified:** No. Verification is computed deterministically by the Verification Engine based on valid evidence.
7. **What evidence is sufficient to verify a requirement:** Passing test executions matching target tests, clean PreFlight AST checks, and passing Reviewer rubric evaluations.
8. **Can one piece of evidence verify multiple requirements:** Yes (e.g., a test suite execution verifying multiple functional criteria).
9. **Can one requirement require multiple evidence items:** Yes (e.g., unit test pass + AST symbol verification + documentation check).
10. **What happens when requirements conflict:** The Architect flags an `AMBIGUOUS_REQUIREMENT` incident, halting or prompting via Human Channel.
11. **What happens when a requirement changes during execution:** A `RequirementMutationRecord` is appended, version is incremented, and attached evidence is invalidated.
12. **What happens when tests pass but requirements are incomplete:** Task status remains `INCOMPLETE`; the system prompts Tester/Developer for remaining criteria.
13. **What happens when requirements appear satisfied but tests fail:** Status is `FAILED`; the system routes failure details to Developer Fix Loop.
14. **What happens when the agent reaches its step limit:** Execution status is `STEP_LIMIT_REACHED`; Work Truth remains `IN_PROGRESS`.
15. **What happens when the token budget is exhausted:** Execution status is `BUDGET_EXHAUSTED`; Work Truth is snapshotted to checkpoint for resumption.
16. **What happens when the provider fails (429/500):** Incident recorded; Sentinel attempts provider switch; Work Truth remains safely preserved.
17. **What happens when the user request is ambiguous:** Architect generates requirements with `requires_clarification=True` and queries the user.
18. **What happens when the Architect introduces an inferred requirement:** Tagged as `AGENT_PROPOSED`; cannot block completion unless approved.
19. **How is provenance preserved:** Immutable `RequirementProvenance` enum on every requirement instance.
20. **How is requirement-to-test traceability represented:** `AcceptanceCriterion.target_test` pointing to exact test identifiers.
21. **How is requirement-to-evidence traceability represented:** `AcceptanceCriterion.evidence_ids` linking to `EvidenceReference` records.
22. **How can a later completion gate deterministically determine completion:** By calling `TaskTruthGraph.is_task_complete()`.
23. **What information must every future agent receive:** The normalized `TaskTruthGraph` slice relevant to its role and the active milestone.
24. **What information must never disappear between pipeline stages:** The core user requirements, acceptance criteria, and historical evidence.
25. **What should happen to legacy tasks with no formal requirements:** Synthesized into a default `REQ-000` legacy requirement with smoke test verification.

---

# 29. P1 Exit Criteria

P1 is verified complete against all exit criteria:
- [x] Canonical Task Truth Model defined with 12 normalized entities.
- [x] Requirements have stable, globally unique IDs (`REQ-xxx`).
- [x] Requirement provenance model explicitly defined.
- [x] Acceptance criteria structured with Given/When/Then and machine-readable targets.
- [x] Evidence relationships and freshness contracts formalized.
- [x] Requirement status lifecycle defined with $\text{IMPLEMENTED} \neq \text{VERIFIED}$.
- [x] Resource exhaustion decoupled from work completion.
- [x] Dependency DAG model specified.
- [x] Agent responsibility matrix (RBAC) established.
- [x] Cross-agent handoff contracts defined.
- [x] Pydantic v2 schemas fully specified.
- [x] Backward compatibility and migration strategy detailed.
- [x] Zero production code modified.

---

# 30. P2 Input Contract

The next architectural phase, **P2 — Evidence Model, Collection & Completion Gates**, is authorized to proceed based on the following established contracts:

```
+-----------------------------------------------------------------------------------+
|                                 P2 INPUT CONTRACT                                 |
+-----------------------------------------------------------------------------------+
| P2 MAY ASSUME:                                                                    |
| 1. `TaskTruthGraph`, `Requirement`, `AcceptanceCriterion`, and `EvidenceReference`|
|    have immutable, stable schema definitions as specified in Section 21.          |
| 2. Requirements possess explicit provenance (`EXPLICIT_USER`, `DERIVED`, etc.).   |
| 3. Acceptance criteria define concrete `VerificationType` and `target_test` links.|
| 4. $\text{IMPLEMENTED} \neq \text{VERIFIED}$ is an inviolable system invariant.   |
| 5. Resource limits (`STEP_LIMIT`, `TOKEN_LIMIT`) are execution-state only.        |
+-----------------------------------------------------------------------------------+
| P2 SCOPE OF WORK:                                                                 |
| 1. Design the runtime Evidence Collection Engine (Pytest, AST, Ruff, Reviewer).   |
| 2. Design the Evidence Validation & Freshness Evaluation algorithms.              |
| 3. Implement deterministic Completion Gates that query `TaskTruthGraph`.          |
| 4. Bind Evidence Gates into pipeline transition hooks without FSM redesign.       |
+-----------------------------------------------------------------------------------+
```
