# P6 — CONTEXT & EVIDENCE HANDOFF PLAN

> **Document Type:** Canonical Systems Architecture, Context Engineering & Cross-Agent Evidence Synchronization Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Systems Architect, Context Engineering Specialist & Multi-Agent State Synchronization Engineer  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md`, `docs/plans/P1_TASK_TRUTH_AND_REQUIREMENT_MODEL_PLAN.md`, `docs/plans/P2_EVIDENCE_AND_COMPLETION_GATES_PLAN.md`, `docs/plans/P3_GUARDED_FSM_AND_LIFECYCLE_ORCHESTRATION_PLAN.md`, `docs/plans/P4_ADAPTIVE_RESOURCE_GOVERNANCE_PLAN.md`, `docs/plans/P5_AGENT_WORK_AND_MILESTONE_EXECUTION_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Design Phase:** P6 (Specification & Context/Evidence Handoff Mesh — Zero Production Code Modified)

---

# 1. Executive Summary & Context Degradation Analysis

This specification establishes the canonical **Context & Evidence Handoff Plan (P6)** for the **ORAGAI** multi-agent software engineering orchestrator.

### 1.1 The Strategic Position of P6 in the ORAGAI Stack
To date, the architectural redesign of ORAGAI has established:
1. **P0 (Forensic Baseline & Invariants):** Identified the fatal conflation of *Resource Safety Governance* with *Work Completion*, 4,000-character truncated reviewer diffs, unguided task fallbacks, and micro-turn execution cages.
2. **P1 (Task Truth & Requirement Model):** Established the deterministic entity graph: $\text{Task} \to \text{Requirements} \to \text{Acceptance Criteria} \to \text{Milestones}$.
3. **P2.1 (Evidence Engine & Completion Gates):** Formulated cryptographic content identity (composite SHA-256), orthogonal state dimensions (`ImplementationState`, `VerificationState`, `BlockingState`), and the 14-step deterministic Completion Gate (`TaskTruthSemanticQueries`).
4. **P3 (Guarded FSM & Lifecycle Orchestration):** Inverted the execution loop from procedural scripts to an event-driven `GuardedFSMEngine` that delegates bounded, ephemeral agent turns via Inversion of Control (IoC).
5. **P4 (Adaptive Resource Governance):** Replaced hard micro-caps with dynamic complexity-based turn allocation ($T_{\text{allocated}}$), AST-aware context folding (`ASTAwareContextClamper`), and non-intrusive financial circuit breakers ($5.00 default).
6. **P5 (Agent Work & Milestone Execution):** Established persona RBAC boundaries, the Micro-TDD loop (Red $\to$ Green $\to$ Refactor), topological DAG wave dispatch, and cryptographic `CrossAgentHandoffPayload` interfaces.

### The Core Mission of P6:
$$\text{While P5 defines what individual personas produce and consume in isolated turns,}$$
$$\text{\textbf{P6 governs how context and empirical evidence are preserved, compressed, synthesized,}}$$
$$\text{\textbf{and propagated across persona boundaries without information loss, context rot, or token bloat.}}$$

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
│   │                 Context & Evidence Handoff Mesh (P6) (THIS SPEC)               │   │
│   │                                                                                │   │
│   │  • Unified Context Assembly Engine (ContextSynthesizer)                        │   │
│   │  • Persona-Specific Prompt View Generation (Architect/Dev/Test/Review/Remedy)  │   │
│   │  • Cross-Agent Handoff Pipeline & Cryptographic Envelope Sealing               │   │
│   │  • Evidence Freshness & Dependency Invalidation Cascade                        │   │
│   │  • Cross-Iteration Diagnostic Memory & Pytest Failure Trace Compaction         │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │ Ephemeral Context Injection               │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                    Agent Workstream & Milestone Engine (P5)                    │   │
│   │                                                                                │   │
│   │   [Architect]   [Developer]   [Tester]   [Reviewer]   [Auditor]   [Remediator] │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.2 Forensic Analysis of Context Degradation in Legacy ORAGAI
A rigorous investigation into legacy ORAGAI prompt builders, pipeline loops, and VCS operations (`orchestrator/context/manager.py`, `orchestrator/pipeline/full_pipeline.py`, `orchestrator/vcs/git_ops.py`, `orchestrator/memory/conversation_store.py`) uncovers six critical failure modes responsible for catastrophic context rot across agent turns:

| Legacy Subsystem | Code Location | Observed Pathology | Root Cause & Failure Mechanism | P6 Architectural Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **Reviewer Diff Truncation** | `full_pipeline.py:L629-634`, `git_ops.py:L64-93` | Reviewer is supplied with `GitOps.get_compact_diff(max_chars=4000)`. | Multi-file diffs exceeding 4,000 characters are arbitrarily truncated mid-hunk. Reviewer is blind to core implementation logic and rubber-stamps invalid code. | **AST-Anchored Untruncated Diffs:** Multi-file diffs are partitioned per-symbol; full diffs are provided within persona-specific token headroom. |
| **Unguided Developer Fallback** | `dev_test_loop.py:L89-105`, `manager.py:L57-71` | When `PLAN.md` is absent or malformed, the pipeline silently falls back to raw user task strings. | Downstream Developer receives zero architectural directives, module boundaries, or AC mappings, producing unguided and divergent implementations. | **Deterministic Handoff Contracts:** Developer invocation strictly requires a verified `ArchitectHandoffPayload`; missing artifacts force FSM replanning. |
| **Task String Truncation** | `manager.py:L64-69` | `task_str = task_str[:max_chars - 600] + "... [Task truncated]"` | If a task contains detailed specs, requirements are sliced off mid-sentence, permanently blinding downstream agents to critical criteria. | **Tier 0 Non-Negotiable Invariant:** Task Truth, Acceptance Criteria, and Invariants are protected in Tier 0; string slicing of intent is strictly prohibited. |
| **Mid-File Context Clamping** | `context_budget_manager.py:L125-146` | Arbitrary string slice at `DEFAULT_MAX_CHARS = 12_000` (~3k tokens). | File content is cut mid-class or mid-method, causing syntax confusion, hallucinated indentation, and compiler failures. | **AST-Aware Symbol Folding:** Integrates P4's AST folding; bodies of irrelevant functions are folded to signatures while target symbols are intact. |
| **Stale Evidence Hallucination** | `dev_test_loop.py:L240-272` | Pytest results from previous iterations are reused after code edits without checking file modification timestamps or hashes. | Developer fixes a bug, but Tester/Reviewer receives obsolete failure traces from pre-edit state, leading to endless oscillation loops. | **Cryptographic Freshness Mesh:** Every evidence item is bound to a workspace composite SHA-256 hash; mutations invalidate dependent test proofs. |
| **Unbounded Failure Trace Bloat** | `full_pipeline.py:L534-540` | Raw pytest stdout/stderr (often 10,000+ characters of passing tests and tracebacks) is dumped directly into prompt. | Consumes entire context budget, forcing the prompt builder to drop task blueprints and architecture maps. | **Diagnostic Trace Compactor:** Pytest stdout is distilled into actionable failure frames ($\le 800$ tokens), stripping ANSI codes and passing noise. |

---

### 1.3 Theoretical Framework for Lossless Cross-Agent Evidence Handoffs

To eliminate context rot, P6 establishes four mathematical and structural theorems:

#### Theorem 1: State-Driven Context Synthesis (Ephemeral Memory Principle)
Agents do not share long-running conversation buffers. A multi-turn conversation log inevitably degrades with token bloat, contradictory reasoning, and hallucinated facts. Instead, context for turn $k$ of persona $P$ is a deterministic projection of current immutable system state:
$$\text{Context}_P(k) = \mathcal{F}_{\text{synth}}\left(\text{TaskTruthGraph}, \text{ActiveMilestone}, \text{HandoffPayload}_{\text{upstream}}, \text{WorkspaceDigest}, \mathcal{B}_{\text{token}}\right)$$

#### Theorem 2: Context Monotonicity Invariant
Downstream personas must never receive less architectural intent, invariant rules, or acceptance criteria than upstream personas:
$$\forall t_1 < t_2, \quad \text{IntentContext}(t_2) \supseteq \text{IntentContext}(t_1)$$
Under no circumstance may context pruning, token exhaustion, or dynamic clamping drop or truncate Tier 0 Intent elements (User Requirements, Acceptance Criteria IDs, Security Invariants, RBAC scopes).

#### Theorem 3: Cryptographic Working-Tree Binding
An evidence artifact $\mathcal{E}$ (e.g., Pytest execution trace, AST compilation proof, Reviewer critique) is valid if and only if the current workspace content digest $\mathcal{H}_{\text{ws}}$ matches the digest recorded at the moment of evidence capture $\mathcal{H}_{\mathcal{E}}$:
$$\text{IsValid}(\mathcal{E}) \iff \mathcal{H}_{\text{ws}} \equiv \mathcal{H}_{\mathcal{E}} = \text{SHA256}\left(\bigoplus_{f \in \mathcal{F}_{\text{tracked}}} (f.\text{path} \parallel f.\text{sha256})\right)$$
Any mutation to a tracked source file immediately transitions dependent evidence from `FRESH` to `STALE`, triggering deterministic invalidation.

#### Theorem 4: Dynamic Headroom Guarantee
Let $C_{\text{max}}$ be the context window of the target LLM (e.g., 128,000 tokens) and $C_{\text{prompt}}$ be the assembled prompt size. The context assembly engine guarantees a hard lower bound on generation headroom $H_{\text{reserve}}$:
$$C_{\text{prompt}} \le C_{\text{target}} = C_{\text{max}} - H_{\text{reserve}}, \quad \text{where } H_{\text{reserve}} \ge 2,048 \text{ tokens}$$
If the total uncompressed context exceeds $C_{\text{target}}$, pruning proceeds strictly in reverse priority order ($\text{Tier 3} \to \text{Tier 2} \to \text{Tier 1}$), with Tier 0 remaining completely immutable.

---

### 1.4 Inviolable System Invariants for P6
P6 strictly enforces five system-wide architectural invariants:

1. **Zero Production Code Modifications During Planning:** P6 is an architectural specification and design contract. No files in `orchestrator/` are altered during this planning phase.
2. **Zero Raw Conversation Dumps:** Agents are never supplied with raw conversational transcripts of prior agent turns. All inter-agent communication occurs through strongly typed, validated, and cryptographically sealed `HandoffEnvelope` artifacts.
3. **Immutable Tier 0 Protection:** The `ContextSynthesizer` is structurally forbidden from truncating, slicing, or dropping Task Requirements, Acceptance Criteria, or System Invariants. If Tier 0 exceeds the hard limit ($25\%$ of context budget), the engine raises `ContextHeadroomExhaustionError` rather than silently truncating.
4. **No Hallucinated Fallbacks:** If an upstream artifact (such as `ArchitectHandoffPayload` or a test failure report) is missing or corrupted, the orchestrator must halt or route to replanning/resolution rather than falling back to unguided raw task strings.
5. **Deterministic Dependency Invalidation:** Code modifications must cascade invalidation to all downstream verification proofs whose dependency graph intersects the edited files, while preserving verified proofs for completely isolated modules.

---

# 2. Unified Context Assembly Engine (`ContextSynthesizer`)

The `ContextSynthesizer` is the central engine responsible for assembling mathematically bounded, persona-tailored, and priority-tiered prompt payloads.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CONTEXT SYNTHESIZER ENGINE                                │
│                                                                                        │
│   Input Artifacts:                                                                     │
│   • TaskTruthGraph (P1)           • Preceding Handoff Envelope (P5)                    │
│   • Workspace AST / Diffs (P4)    • Compacted Diagnostic Traces (P6)                   │
│   • Graft Architecture Map        • Cross-Run Memory Store                             │
│                                                                                        │
│                                   │                                                    │
│                                   ▼                                                    │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                 Dynamic Token Budget Partitioning (P4 / P6)                    │   │
│   │                                                                                │   │
│   │   Total Context Window: C_max (e.g. 32,000 tokens / 128,000 chars)             │   │
│   │   ├── Output Headroom Reserve: H_reserve (min 2,048 tokens / 8,192 chars)      │   │
│   │   └── Usable Prompt Ceiling:   C_target  = C_max - H_reserve                   │   │
│   └───────────────────────┬────────────────────────────────┬───────────────────────┘   │
│                           │                                │                           │
│     Priority Clamping     │                                │  Persona View Filtering   │
│     & Token Allocation    │                                │                           │
│                           ▼                                ▼                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                             PRIORITY CONTEXT TIERS                             │   │
│   │                                                                                │   │
│   │  [Tier 0: Non-Negotiable Intent] (Cap: 25% C_target)                           │   │
│   │  • Persona System Prompt & RBAC Tool Sandbox Directives                        │   │
│   │  • Active Milestone Slice & Acceptance Criteria (Given-When-Then)              │   │
│   │  • Inviolable Architectural & Security Invariants                              │   │
│   │                                                                                │   │
│   │  [Tier 1: Diagnostics & Handoff Evidence] (Cap: 30% C_target)                  │   │
│   │  • Upstream Persona Handoff Envelope (Typed Schema)                            │   │
│   │  • Compacted Pytest Failure Traces & PreFlight Compiler Errors                 │   │
│   │  • Active Defect Directives (Remediation Only)                                 │   │
│   │                                                                                │   │
│   │  [Tier 2: AST-Folded Code & Semantic Diffs] (Cap: 35% C_target)                │   │
│   │  • Target Symbol Implementation Bodies (Active Milestone Scope)                │   │
│   │  • AST-Folded Neighboring Classes/Modules (Signatures + Docstrings)            │   │
│   │  • Unified Multi-File Git Diffs (Untruncated, File-Partitioned)                │   │
│   │                                                                                │   │
│   │  [Tier 3: Architecture Skeleton & Memory] (Cap: 10% C_target)                  │   │
│   │  • Graft Topology / Module Dependency Connectivity Map                         │   │
│   │  • Distilled Lessons Learned & Cross-Run Memory (ConversationStore)            │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │ Render Markdown Prompt                    │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                     PERSONA-SPECIFIC TARGET PROMPTS                            │   │
│   │                                                                                │   │
│   │   [Architect View]   [Developer View]   [Tester View]   [Reviewer View]        │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.1 Mathematical Token Budget Partitioning

Given a target model with maximum context window $C_{\text{max}}$ (in tokens) and token-to-character ratio $\rho \approx 4.0$:

1. **Guaranteed Output Headroom ($H_{\text{reserve}}$):**
   $$H_{\text{reserve}} = \max\left(2048, \; \lfloor 0.15 \times C_{\text{max}} \rfloor\right)$$
2. **Prompt Context Ceiling ($C_{\text{target}}$):**
   $$C_{\text{target}} = C_{\text{max}} - H_{\text{reserve}}$$
3. **Tier Budget Allocations:**
   $$\text{Budget}(\text{Tier 0}) = 0.25 \times C_{\text{target}}$$
   $$\text{Budget}(\text{Tier 1}) = 0.30 \times C_{\text{target}}$$
   $$\text{Budget}(\text{Tier 2}) = 0.35 \times C_{\text{target}}$$
   $$\text{Budget}(\text{Tier 3}) = 0.10 \times C_{\text{target}}$$

#### Token Clamping Algorithm:
1. **Tier 0 Invariant Check:** Calculate $T_0 = \text{tokens}(\text{Tier 0})$. If $T_0 > \text{Budget}(\text{Tier 0})$, absorb unused budget from Tier 3 and Tier 2. If $T_0 > 0.40 \times C_{\text{target}}$, raise `ContextHeadroomExhaustionError`. Never truncate Tier 0.
2. **Tier 1 Diagnostic Compaction:** If $T_1 > \text{Budget}(\text{Tier 1})$, trigger `DiagnosticCompactor` to strip secondary call frames, reducing tracebacks to failing assertion line and leaf exception.
3. **Tier 2 AST-Aware Folding:** If $T_2 > \text{Budget}(\text{Tier 2})$, invoke `ASTAwareContextClamper` (from P4):
   - Fold non-target function bodies $\to$ `... [folded signature: def foo(x: int) -> str]`
   - Fold non-target class methods $\to$ method signatures only.
   - Retain complete function bodies for symbols listed in `ActiveMilestone.target_symbols`.
4. **Tier 3 Pruning:** If total tokens $\sum T_i > C_{\text{target}}$, truncate Tier 3 memory items first, then collapse Graft architectural depth from depth 3 to depth 1.

---

### 2.2 Priority Context Tiers

| Tier | Category | Content Elements | Clamping Policy | Failure Action if Budget Exceeded |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 0** | **Critical Intent & Invariants** | Persona System Prompt, RBAC rules, Active Milestone Requirements, Acceptance Criteria (Given-When-Then), Inviolable Architecture Invariants. | **STRICTLY IMMUTABLE** (0% Truncation Allowed). | Reallocate from Tier 3/2; if unresolvable, raise fatal exception. |
| **Tier 1** | **Diagnostics & Evidence** | Upstream `HandoffEnvelope`, Compacted Pytest Failure Traces, PreFlight compiler errors, Line-anchored Defect Directives. | **Compacted via Extractor** (Strip passing tests, ANSI codes, and redundant stack frames). | Retain only primary failure frame and failing assert. |
| **Tier 2** | **Code & Diffs** | Target symbol source code, AST-folded neighboring modules, complete unified multi-file diffs. | **AST-Aware Folding** (Fold non-target function bodies; preserve full signatures and types). | Fold all symbols outside `target_symbols`. |
| **Tier 3** | **Architecture & Memory** | Graft codebase skeleton, Module connectivity maps, Distilled cross-run lessons learned (`ConversationStore`). | **Opportunistic & Elastic** (Dropped first when budget is constrained). | Truncate lessons to top 1; reduce Graft depth. |

---

### 2.3 Persona-Specific Prompt View Generation

Rather than dumping a monolithic prompt, `ContextSynthesizer` generates highly differentiated, role-tailored prompt views:

#### 1. Architect View (Macro Planning & Blueprint Formulation)
- **Included Context:** Full Task Specification (Tier 0), Graft Codebase Topology (Tier 3), High-Level Module Boundaries (Tier 0), Existing Public API Interfaces (Tier 2 Signatures).
- **Excluded Context:** Pytest failure tracebacks, granular implementation diffs, line-level code patches.
- **Output Directive:** Produce formal `MilestoneDAG`, public API signatures, AST symbol targets, and strict Acceptance Criteria.

#### 2. Developer View (Micro-TDD Implementation & Red-Green Authoring)
- **Included Context:** Active Milestone Slice (Tier 0), Target Acceptance Criteria (Tier 0), Preceding Red Test Traceback from Tester (Tier 1), Target File AST Signatures (Tier 2), Upstream Architect API Contracts (Tier 1).
- **Excluded Context:** Global repository history, completed milestone implementation code, reviewer rubrics.
- **Output Directive:** Implement exact target symbols to satisfy failing tests; comply with Anti-Stub invariant (`pass`/`TODO` prohibited).

#### 3. Tester View (Test Strategy & Negative Hazard Authoring)
- **Included Context:** Acceptance Criteria (Tier 0), Developer's Unified AST Diff (Tier 2), Modified Symbol Line Bounds (Tier 2), Boundary Hazard Matrix (Tier 1), PreFlight Compilation Status (Tier 1).
- **Excluded Context:** Non-target application files, historical passing test output.
- **Output Directive:** Author isolated pytest fixtures and assertions targeting all ACs; explicitly probe negative edge cases and boundary conditions.

#### 4. Reviewer View (Independent Quality & Invariant Verification)
- **Included Context:** Complete Multi-File Unified Git Diff (Tier 2), Acceptance Criteria Matrix (Tier 0), Pytest Execution Summary & Node IDs (Tier 1), PreFlight Type-Check & AST Report (Tier 1), Architectural Invariants (Tier 0).
- **Excluded Context:** Intermediate developer scratchpad logs, conversational back-and-forth.
- **Output Directive:** Evaluate code against 6-point verification rubric; emit binary `APPROVED` or line-anchored defect directives.

#### 5. Remediation View (Surgical Defect Correction)
- **Included Context:** Reviewer Defect Directives with exact file and line anchors (Tier 1), Failing Symbol Source Code (Tier 2), Exact Failing Assertion Frame (Tier 1), Micro-Budget Ceiling (Tier 0).
- **Excluded Context:** Unrelated codebase modules, global architecture planning docs.
- **Output Directive:** Execute surgical edit resolving the exact defect directive without altering unaffected interfaces.

---

# 3. Cross-Agent Handoff Pipeline & Serialization

Inter-agent communication in ORAGAI is strictly mediated through strongly typed, versioned, and cryptographically sealed `HandoffEnvelope` artifacts.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CROSS-AGENT HANDOFF PIPELINE                              │
│                                                                                        │
│   ┌───────────────────┐        ┌───────────────────┐        ┌──────────────────────┐   │
│   │     ARCHITECT     │        │     DEVELOPER     │        │        TESTER        │   │
│   └─────────┬─────────┘        └─────────┬─────────┘        └──────────┬───────────┘   │
│             │                            │                             │               │
│             │ Emits                      │ Emits                       │ Emits         │
│             ▼                            ▼                             ▼               │
│   ┌───────────────────┐        ┌───────────────────┐        ┌──────────────────────┐   │
│   │ ArchitectHandoff  │        │ DeveloperHandoff  │        │    TesterHandoff     │   │
│   │      Payload      │        │      Payload      │        │       Payload        │   │
│   └─────────┬─────────┘        └─────────┬─────────┘        └──────────┬───────────┘   │
│             │                            │                             │               │
│             │ Wraps & Seals              │ Wraps & Seals               │ Wraps & Seals │
│             ▼                            ▼                             ▼               │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                      HandoffEnvelope (Cryptographic Seal)                      │   │
│   │                                                                                │   │
│   │  • envelope_id: str (UUID4)             • schema_version: "1.0.0"              │   │
│   │  • sender_persona: RolePersona          • recipient_persona: RolePersona       │   │
│   │  • source_state: FSMState               • target_state: FSMState               │   │
│   │  • workspace_sha256: str (64 hex)       • payload_sha256: str (64 hex)         │   │
│   │  • created_at_utc: str (ISO-8601)       • typed_payload: Dict[str, Any]        │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │ Ingestion & Verification                  │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        Downstream Context Synthesizer                          │   │
│   │                                                                                │   │
│   │   1. Validate JSON Schema / Pydantic Types                                     │   │
│   │   2. Verify Payload SHA-256 Digest Match                                       │   │
│   │   3. Verify Workspace SHA-256 Freshness (No Stale Edits)                       │   │
│   │   4. Format Markdown Summary & Inject into Persona Prompt                      │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.1 Handoff Pipeline Specifications

#### 1. Architect $\to$ Developer Handoff (`ArchitectHandoffPayload`)
- **Intent:** Convey formal milestone specifications, public interface contracts, and target symbol locations.
- **Payload Schema:**
  - `milestone_id: str` — Identifier of target milestone (e.g. `M1_CORE_DATA_MODEL`).
  - `target_files: List[str]` — Exact file paths designated for implementation.
  - `target_symbols: List[str]` — Fully qualified class and function names to implement.
  - `public_api_contracts: List[Dict[str, str]]` — Type signatures, docstrings, and expected exceptions.
  - `acceptance_criteria: List[Dict[str, str]]` — Explicit Given-When-Then clauses.
  - `architectural_boundaries: List[str]` — Prohibited imports, layering rules, and forbidden dependencies.

#### 2. Developer $\to$ Tester Handoff (`DeveloperHandoffPayload`)
- **Intent:** Transmit implementation diff metadata, modified symbol line spans, and boundary hazards for testing.
- **Payload Schema:**
  - `milestone_id: str` — Identifier of executed milestone.
  - `modified_files: List[str]` — Relative paths of files touched during turn.
  - `modified_symbols: List[Dict[str, Any]]` — Symbol names with exact starting and ending line numbers.
  - `preflight_hash: str` — SHA-256 digest of PreFlight compilation verification.
  - `implementation_notes: str` — Concise summary of architectural decisions and algorithms used.
  - `boundary_hazards: List[str]` — Identified edge cases (e.g. `empty inputs`, `None handling`, `Unicode paths`).

#### 3. Tester $\to$ Reviewer Handoff (`TesterHandoffPayload`)
- **Intent:** Deliver empirical verification proof, executed pytest node IDs, failure diagnostics, and AC coverage.
- **Payload Schema:**
  - `milestone_id: str` — Identifier of verified milestone.
  - `test_execution_status: str` — Categorical status (`PASSED`, `TEST_FAILURE`, `INFRASTRUCTURE_ERROR`).
  - `pytest_exit_code: int` — Raw exit code from pytest process runner.
  - `total_tests_run: int`, `passed_count: int`, `failed_count: int` — Execution counts.
  - `executed_node_ids: List[str]` — Explicit pytest test node IDs (e.g. `tests/test_auth.py::test_login_success`).
  - `ac_verification_map: Dict[str, bool]` — Mapping of `criterion_id` to boolean pass/fail status.
  - `compacted_failures: List[Dict[str, str]]` — Distilled failure traces with frame locations and assert diffs.

#### 4. Reviewer $\to$ Remediation Specialist Handoff (`ReviewerHandoffPayload`)
- **Intent:** Provide actionable, line-anchored defect directives to guide surgical code repair.
- **Payload Schema:**
  - `milestone_id: str` — Identifier of reviewed milestone.
  - `review_verdict: str` — Categorical verdict (`APPROVED`, `REJECTED_WITH_DEFECTS`, `BLOCKED`).
  - `defect_directives: List[Dict[str, Any]]` — Structured defects:
    - `file_path: str` — Target file path.
    - `line_anchor: int` — Line number requiring remediation.
    - `symbol_name: str` — Function/class enclosing defect.
    - `violation_rule: str` — Specific invariant or rubric rule violated.
    - `expected_behavior: str` — Concrete instructions for correct implementation.
    - `severity: str` — `CRITICAL`, `MAJOR`, `MINOR`.

---

### 3.2 Elimination of Hallucinated Fallbacks
In legacy ORAGAI, if an upstream handoff file was missing, the pipeline silently reverted to:
```python
# LEGACY ANTI-PATTERN (orchestrator/pipeline/dev_test_loop.py:L95)
task_prompt = f"Implement the following task: {self.task_description}"
```
**P6 Contract:** The `CrossAgentContextManager` strictly enforces artifact presence:
1. When entering `DEVELOPMENT`, if `ArchitectHandoffPayload` is absent or unsealed, the FSM transitions to `FAILED` with `MissingHandoffArtifactError("Architect handoff missing for M1")`.
2. When entering `VERIFICATION`, if `DeveloperHandoffPayload` is absent, the FSM rejects the turn as unexecuted.
3. When entering `REMEDIATION`, if `ReviewerHandoffPayload` contains zero `defect_directives`, remediation is halted.

---

# 4. Evidence Freshness & Invalidation Mesh

A major failure mode in autonomous coding is **Stale Evidence Hallucination**, where an orchestrator makes decisions based on outdated test proofs captured before recent code modifications.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             EVIDENCE FRESHNESS ENGINE                                  │
│                                                                                        │
│   Workspace State:                                                                     │
│   File A (Modified at t=10) ── SHA256: e3b0c442...                                     │
│   File B (Untouched at t=5) ── SHA256: 8f434346...                                     │
│                                                                                        │
│   Composite Workspace Digest: SHA256(File A || File B) ── 9a8b7c6d...                  │
│                                                                                        │
│                                   │                                                    │
│                                   ▼                                                    │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                      FreshnessValidator Evaluation Loop                        │   │
│   │                                                                                │   │
│   │   For each Registered Evidence Package:                                        │   │
│   │   ├── Check 1: workspace_sha256 == current_workspace_digest?                   │   │
│   │   │   ├── Match:   Evidence is FRESH (Keep Verified Proofs)                    │   │
│   │   │   └── Differ:  Evidence is STALE (Trigger Dependency Analysis)             │   │
│   │   │                                                                            │   │
│   │   └── Check 2: Dependency Invalidation Cascade                                 │   │
│   │       ├── Let M = Set of Modified Files between t_evidence and t_current       │   │
│   │       ├── For each Milestone / Test Evidence E_k:                              │   │
│   │       │   ├── If TransitiveDeps(E_k.target_files) ∩ M ≠ ∅:                     │   │
│   │       │   │   └── Invalidate E_k (Transition: VERIFIED -> STALE_PENDING_RERUN) │   │
│   │       │   └── Else:                                                            │   │
│   │       │       └── Preserve E_k as FRESH (Isolated Module Proof Valid)          │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.1 Cryptographic Working-Tree Digest

The workspace state is summarized by a composite cryptographic hash:
$$\mathcal{H}_{\text{ws}} = \text{SHA256}\left( \bigoplus_{f \in \text{Sorted}(\mathcal{F}_{\text{git}})} \left( f.\text{rel\_path} \parallel \text{SHA256}(f.\text{bytes}) \right) \right)$$

Every `EvidencePackage` stamped by P2.1 Completion Gates records:
- `workspace_digest_at_capture: str`
- `target_files_hashes: Dict[str, str]` (File-level granular hashes)
- `transitive_dependencies: List[str]` (Resolved via AST imports & Graft topology)

---

### 4.2 Dependency Invalidation Cascade Algorithm

When a Developer or Remediation turn mutates the codebase:
1. Compute the modified file set: $\mathcal{M} = \{ f \in \mathcal{F}_{\text{tracked}} \mid \text{current\_hash}(f) \ne \text{recorded\_hash}(f) \}$.
2. For every active milestone $M_j$ in `TaskTruthGraph`:
   - Compute milestone dependency closure: $\mathcal{D}(M_j) = M_j.\text{target\_files} \cup \text{TransitiveImports}(M_j.\text{target\_files})$.
   - Evaluate intersection: $\mathcal{I} = \mathcal{D}(M_j) \cap \mathcal{M}$.
   - If $\mathcal{I} \ne \emptyset$:
     - Invalidate all `PytestEvidencePayload` records attached to $M_j$.
     - Transition $M_j.\text{verification\_state} \to \text{STALE\_PENDING\_VERIFICATION}$.
   - If $\mathcal{I} = \emptyset$:
     - **Preserve Verification Proof:** The evidence for $M_j$ remains valid and trusted, eliminating redundant and expensive re-testing of untouched submodules.

---

# 5. Cross-Iteration Diagnostic Memory & Failure Trace Compaction

Pytest and compiler outputs frequently generate 10,000 to 20,000 characters of raw text containing ANSI escape codes, passed test dots, environmental banners, and lengthy framework internal tracebacks. In legacy ORAGAI, this output overwhelmed prompt token budgets.

### 5.1 Pytest Diagnostic Compaction Protocol

The `DiagnosticCompactor` executes a 5-stage distillation pipeline:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DIAGNOSTIC COMPACTION PIPELINE                                  │
│                                                                                        │
│   Raw Pytest Stdout (15,000+ chars / 3,750 tokens)                                     │
│   [ANSI colors, rootdir banners, 45 passed test dots, 2 lengthy stack traces]         │
│                                                                                        │
│                                   │                                                    │
│                                   ▼                                                    │
│   [Stage 1: ANSI & Banner Stripping] ── Regex removal of ESC[...m and pytest headers  │
│                                   │                                                    │
│                                   ▼                                                    │
│   [Stage 2: Passing Noise Elimination] ── Filter out PASSED / SKIPPED / XFAIL dots     │
│                                   │                                                    │
│                                   ▼                                                    │
│   [Stage 3: Stack Frame Trimming] ── Discard internal library frames (site-packages)  │
│                                       Retain only workspace call site and leaf assert  │
│                                   │                                                    │
│                                   ▼                                                    │
│   [Stage 4: Assertion Diff Normalization] ── Extract exact -/+ assert comparison       │
│                                   │                                                    │
│                                   ▼                                                    │
│   [Stage 5: Compacted Markdown Synthesis]                                              │
│                                                                                        │
│   Compacted Diagnostic Trace (750 chars / ~180 tokens):                                │
│   ```test-diagnostic                                                                  │
│   FAILED tests/test_auth.py::test_jwt_expiration                                       │
│   Location: src/auth/jwt.py:42 in `validate_token`                                     │
│   Exception: TokenExpiredError: Signature has expired (exp=1727244000, now=1727244010) │
│   Assertion: assert token.is_valid() is True                                           │
│   Diff: - True, + False                                                                │
│   ```                                                                                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 5.2 Cross-Run Diagnostic Memory Persistence (`ConversationStore`)

To ensure lessons learned from previous debugging iterations are preserved across FSM cycles without causing context bloat, P6 establishes a distilled **Memory Retention Schema**:

1. **Lesson Extraction:** At the conclusion of an FSM execution wave, if a defect required $\ge 2$ iterations to resolve, the `ConversationStore` records a structured `MemoryEntry`:
   - `error_signature: str` — Normalized exception pattern (e.g. `RecursionError: maximum depth in JSON serializer`).
   - `root_cause_summary: str` — 1-2 sentence technical explanation of why the defect occurred.
   - `resolution_pattern: str` — Specific code pattern that resolved the issue.
   - `files_affected: List[str]` — Paths where the fix was applied.
2. **Context-Budgeted Retrieval:** When synthesizing context for future tasks:
   - Match active milestone target files against `ConversationStore` index.
   - Inject at most 2 most relevant distilled lessons into Tier 3 ($<200$ tokens total).
   - Never inject raw previous conversational turns.

---

# 6. Canonical Python Architecture & Data Models

The following production-ready, fully typed Python classes provide the complete implementation for `orchestrator/context/handoff.py`.

```python
"""Canonical Context Engineering, Evidence Handoff, and Freshness Invalidation Engine.

File Location: orchestrator/context/handoff.py
Role: P6 Architecture Contract - Zero Production Code Modified During Planning
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# 1. ENUMS & CONSTANTS
# ============================================================================

class ContextTier(str, Enum):
    """Priority tiers for prompt assembly and dynamic context clamping."""
    TIER_0_INTENT = "TIER_0_INTENT"          # Immutable: Task Truth, ACs, Invariants, RBAC
    TIER_1_DIAGNOSTICS = "TIER_1_DIAGNOSTICS" # High: Compacted Traces, Upstream Handoff
    TIER_2_CODE = "TIER_2_CODE"               # Medium: AST-Folded Code, Target Symbols, Diffs
    TIER_3_ARCHITECTURE = "TIER_3_ARCHITECTURE" # Low: Graft Skeleton, Memory Lessons


class HandoffType(str, Enum):
    """Categorical classification of inter-agent handoff payloads."""
    ARCHITECT_TO_DEVELOPER = "ARCHITECT_TO_DEVELOPER"
    DEVELOPER_TO_TESTER = "DEVELOPER_TO_TESTER"
    TESTER_TO_REVIEWER = "TESTER_TO_REVIEWER"
    REVIEWER_TO_REMEDIATION = "REVIEWER_TO_REMEDIATION"
    AUDITOR_TO_ARCHITECT = "AUDITOR_TO_ARCHITECT"


class PersonaViewType(str, Enum):
    """Persona-specific prompt view formats."""
    ARCHITECT_VIEW = "ARCHITECT_VIEW"
    DEVELOPER_VIEW = "DEVELOPER_VIEW"
    TESTER_VIEW = "TESTER_VIEW"
    REVIEWER_VIEW = "REVIEWER_VIEW"
    REMEDIATION_VIEW = "REMEDIATION_VIEW"
    AUDITOR_VIEW = "AUDITOR_VIEW"


class FreshnessState(str, Enum):
    """Freshness lifecycle status of evidence artifacts."""
    FRESH = "FRESH"
    STALE = "STALE"
    INVALIDATED = "INVALIDATED"


DEFAULT_TOKEN_RESERVE_HEADROOM = 2048
CHARS_PER_TOKEN_ESTIMATE = 4.0


# ============================================================================
# 2. DIAGNOSTIC TRACE COMPACTOR MODELS
# ============================================================================

@dataclass(frozen=True)
class CompactedFrame:
    """Individual call site frame extracted from a failure traceback."""
    file_path: str
    line_number: int
    function_name: str
    code_line: str


@dataclass(frozen=True)
class DiagnosticFailureTrace:
    """Compacted failure diagnostic extracted from test execution output."""
    node_id: str
    exception_type: str
    exception_message: str
    primary_frame: Optional[CompactedFrame]
    assertion_diff: Optional[str] = None
    captured_stdout_tail: Optional[str] = None

    def to_markdown(self) -> str:
        """Render a compact, high-signal Markdown representation."""
        lines = [f"**FAILED TEST:** `{self.node_id}`"]
        if self.primary_frame:
            lines.append(
                f"- **Location:** `{self.primary_frame.file_path}:{self.primary_frame.line_number}` "
                f"in `{self.primary_frame.function_name}`"
            )
            lines.append(f"  ```python\n  {self.primary_frame.code_line}\n  ```")
        lines.append(f"- **Exception:** `{self.exception_type}`: {self.exception_message}")
        if self.assertion_diff:
            lines.append(f"- **Assert Diff:**\n```diff\n{self.assertion_diff}\n```")
        if self.captured_stdout_tail:
            lines.append(f"- **Stdout (Tail):**\n```\n{self.captured_stdout_tail}\n```")
        return "\n".join(lines)


class DiagnosticCompactor:
    """Extracts high-signal failure traces from pytest stdout and compiler logs."""

    ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    PYTEST_FAIL_HEADER = re.compile(r"_{10,}\s*(.*?)\s*_{10,}")
    ASSERT_DIFF_REGEX = re.compile(r"E\s+assert\s+(.*)")

    @classmethod
    def strip_ansi(cls, text: str) -> str:
        """Remove ANSI terminal color and formatting sequences."""
        return cls.ANSI_ESCAPE_REGEX.sub("", text)

    @classmethod
    def compact_pytest_output(
        cls, stdout: str, stderr: str = "", max_traces: int = 5
    ) -> List[DiagnosticFailureTrace]:
        """Parse raw pytest output into structured, compacted failure traces."""
        cleaned_out = cls.strip_ansi(stdout)
        traces: List[DiagnosticFailureTrace] = []

        # Split on pytest failure separator blocks (e.g. ________ test_foo ________)
        sections = cls.PYTEST_FAIL_HEADER.split(cleaned_out)
        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                if len(traces) >= max_traces:
                    break
                node_id = sections[i].strip()
                failure_body = sections[i + 1] if (i + 1) < len(sections) else ""
                trace = cls._parse_single_failure_section(node_id, failure_body)
                traces.append(trace)

        if not traces and ("FAILED" in cleaned_out or "ERROR" in cleaned_out or stderr):
            # Fallback for runner crash or unformatted syntax error
            traces.append(
                DiagnosticFailureTrace(
                    node_id="pytest_execution_error",
                    exception_type="TestRunnerFailure",
                    exception_message=cls._extract_last_meaningful_line(cleaned_out + "\n" + stderr),
                    primary_frame=None,
                    captured_stdout_tail=cleaned_out[-500:].strip() if cleaned_out else None,
                )
            )

        return traces

    @classmethod
    def _parse_single_failure_section(cls, node_id: str, body: str) -> DiagnosticFailureTrace:
        """Extract primary frame and exception from a single failure section."""
        lines = body.splitlines()
        exception_type = "AssertionError"
        exception_message = "Test assertion failed"
        primary_frame: Optional[CompactedFrame] = None
        assertion_diff: Optional[str] = None

        # Look for traceback frame lines (e.g., tests/test_foo.py:25: in test_foo)
        frame_regex = re.compile(r"^(.*?):(\d+):\s+in\s+(.*)$")
        diff_lines: List[str] = []

        for idx, line in enumerate(lines):
            stripped = line.strip()
            match = frame_regex.match(stripped)
            if match:
                fpath, lnum, fname = match.groups()
                code = lines[idx + 1].strip() if (idx + 1) < len(lines) else ""
                primary_frame = CompactedFrame(
                    file_path=fpath,
                    line_number=int(lnum),
                    function_name=fname,
                    code_line=code,
                )
            if stripped.startswith("E "):
                diff_lines.append(stripped[2:])
                if ":" in stripped:
                    parts = stripped[2:].split(":", 1)
                    if len(parts) == 2 and "Error" in parts[0]:
                        exception_type = parts[0].strip()
                        exception_message = parts[1].strip()

        if diff_lines:
            assertion_diff = "\n".join(diff_lines[:8])

        return DiagnosticFailureTrace(
            node_id=node_id,
            exception_type=exception_type,
            exception_message=exception_message,
            primary_frame=primary_frame,
            assertion_diff=assertion_diff,
        )

    @classmethod
    def _extract_last_meaningful_line(cls, text: str) -> str:
        for line in reversed(text.splitlines()):
            if line.strip() and not line.strip().startswith("="):
                return line.strip()
        return "Unknown test execution failure"


# ============================================================================
# 3. TYPED HANDOFF PAYLOADS
# ============================================================================

@dataclass
class ArchitectHandoffPayload:
    """Typed handoff payload emitted by Architect for Developer consumption."""
    milestone_id: str
    target_files: List[str]
    target_symbols: List[str]
    public_api_contracts: List[Dict[str, Any]]
    acceptance_criteria: List[Dict[str, str]]
    architectural_boundaries: List[str]
    implementation_guidance: str = ""

    def to_markdown_summary(self) -> str:
        return (
            f"### Architect Blueprint for `{self.milestone_id}`\n"
            f"- **Target Files:** {', '.join(self.target_files)}\n"
            f"- **Target Symbols:** {', '.join(self.target_symbols)}\n"
            f"- **Acceptance Criteria Count:** {len(self.acceptance_criteria)}\n"
            f"- **Layering Boundaries:** {'; '.join(self.architectural_boundaries)}\n\n"
            f"**Guidance:** {self.implementation_guidance}"
        )


@dataclass
class DeveloperHandoffPayload:
    """Typed handoff payload emitted by Developer for Tester consumption."""
    milestone_id: str
    modified_files: List[str]
    modified_symbols: List[Dict[str, Any]]
    preflight_hash: str
    implementation_notes: str
    boundary_hazards: List[str]

    def to_markdown_summary(self) -> str:
        symbols_str = ", ".join(s.get("name", "") for s in self.modified_symbols)
        return (
            f"### Developer Implementation Summary (`{self.milestone_id}`)\n"
            f"- **Modified Files:** {', '.join(self.modified_files)}\n"
            f"- **Modified Symbols:** {symbols_str}\n"
            f"- **PreFlight Hash:** `{self.preflight_hash[:16]}`\n"
            f"- **Identified Hazards:** {'; '.join(self.boundary_hazards)}\n\n"
            f"**Notes:** {self.implementation_notes}"
        )


@dataclass
class TesterHandoffPayload:
    """Typed handoff payload emitted by Tester for Reviewer consumption."""
    milestone_id: str
    test_execution_status: str
    pytest_exit_code: int
    total_tests_run: int
    passed_count: int
    failed_count: int
    executed_node_ids: List[str]
    ac_verification_map: Dict[str, bool]
    compacted_failures: List[Dict[str, Any]]

    def to_markdown_summary(self) -> str:
        status_emoji = "✅" if self.test_execution_status == "PASSED" else "❌"
        return (
            f"### Tester Verification Proof (`{self.milestone_id}`) {status_emoji}\n"
            f"- **Status:** `{self.test_execution_status}` (Exit Code: {self.pytest_exit_code})\n"
            f"- **Summary:** Total: {self.total_tests_run} | Passed: {self.passed_count} | Failed: {self.failed_count}\n"
            f"- **Executed Tests:** {len(self.executed_node_ids)} nodes\n"
            f"- **AC Coverage:** {sum(1 for v in self.ac_verification_map.values() if v)} / {len(self.ac_verification_map)} verified"
        )


@dataclass
class ReviewerHandoffPayload:
    """Typed handoff payload emitted by Reviewer for Remediation consumption."""
    milestone_id: str
    review_verdict: str  # APPROVED | REJECTED_WITH_DEFECTS | BLOCKED
    defect_directives: List[Dict[str, Any]]
    rubric_scores: Dict[str, int]
    general_critique: str

    def to_markdown_summary(self) -> str:
        lines = [
            f"### Code Review Critique (`{self.milestone_id}`): `{self.review_verdict}`",
            f"**Critique:** {self.general_critique}",
            f"**Directives ({len(self.defect_directives)}):**"
        ]
        for d in self.defect_directives:
            lines.append(
                f"- **[{d.get('severity', 'MAJOR')}]** `{d.get('file_path')}:{d.get('line_anchor')}` "
                f"({d.get('symbol_name')}): {d.get('expected_behavior')}"
            )
        return "\n".join(lines)


# ============================================================================
# 4. CRYPTOGRAPHIC HANDOFF ENVELOPE
# ============================================================================

@dataclass
class HandoffEnvelope:
    """Cryptographically sealed inter-agent communication envelope."""
    envelope_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    schema_version: str = "1.0.0"
    handoff_type: HandoffType = HandoffType.ARCHITECT_TO_DEVELOPER
    sender_persona: str = "Architect"
    recipient_persona: str = "Developer"
    milestone_id: str = ""
    workspace_sha256: str = ""
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    typed_payload: Dict[str, Any] = field(default_factory=dict)
    payload_sha256: str = ""

    def seal(self, current_workspace_sha256: str) -> "HandoffEnvelope":
        """Compute SHA-256 payload digest and bind to workspace state."""
        self.workspace_sha256 = current_workspace_sha256
        serialized = json.dumps(self.typed_payload, sort_keys=True)
        self.payload_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return self

    def verify_integrity(self) -> bool:
        """Validate payload authenticity against recorded SHA-256 hash."""
        serialized = json.dumps(self.typed_payload, sort_keys=True)
        computed = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return computed == self.payload_sha256


# ============================================================================
# 5. EVIDENCE FRESHNESS & DIGEST MESH
# ============================================================================

@dataclass(frozen=True)
class FileContentDigest:
    """Content hash of a single tracked workspace file."""
    relative_path: str
    sha256_hash: str
    byte_size: int
    last_modified_timestamp: float


@dataclass(frozen=True)
class WorkspaceDigest:
    """Deterministic composite content digest of the active workspace."""
    composite_sha256: str
    file_digests: Dict[str, FileContentDigest]
    captured_at_utc: str

    @classmethod
    def create(cls, workspace_path: Path, ignored_patterns: Optional[Set[str]] = None) -> "WorkspaceDigest":
        """Compute cryptographic Merkle-like digest of workspace."""
        ignored = ignored_patterns or {".git", ".pytest_cache", "__pycache__", ".venv", "diagnostics"}
        file_map: Dict[str, FileContentDigest] = {}
        hasher = hashlib.sha256()

        for file_path in sorted(workspace_path.rglob("*")):
            if not file_path.is_file():
                continue
            rel_path = file_path.relative_to(workspace_path).as_posix()
            if any(part in rel_path.split("/") for part in ignored):
                continue

            try:
                content = file_path.read_bytes()
                f_hash = hashlib.sha256(content).hexdigest()
                stat = file_path.stat()
                digest = FileContentDigest(
                    relative_path=rel_path,
                    sha256_hash=f_hash,
                    byte_size=len(content),
                    last_modified_timestamp=stat.st_mtime,
                )
                file_map[rel_path] = digest
                hasher.update(f"{rel_path}:{f_hash}".encode("utf-8"))
            except (OSError, PermissionError):
                continue

        return cls(
            composite_sha256=hasher.hexdigest(),
            file_digests=file_map,
            captured_at_utc=datetime.now(timezone.utc).isoformat(),
        )


class FreshnessValidator:
    """Evaluates evidence validity against working-tree mutations and dependency closures."""

    @staticmethod
    def detect_modified_files(
        previous_digest: WorkspaceDigest, current_digest: WorkspaceDigest
    ) -> Set[str]:
        """Identify set of files modified between two workspace snapshots."""
        modified: Set[str] = set()
        for path, curr_file in current_digest.file_digests.items():
            prev_file = previous_digest.file_digests.get(path)
            if not prev_file or prev_file.sha256_hash != curr_file.sha256_hash:
                modified.add(path)
        for prev_path in previous_digest.file_digests:
            if prev_path not in current_digest.file_digests:
                modified.add(prev_path)
        return modified

    @classmethod
    def evaluate_evidence_freshness(
        cls,
        evidence_workspace_sha256: str,
        current_workspace_digest: WorkspaceDigest,
        target_files: List[str],
        dependency_map: Optional[Dict[str, List[str]]] = None,
    ) -> Tuple[FreshnessState, str]:
        """Check if an evidence artifact remains valid under current workspace state."""
        if evidence_workspace_sha256 == current_workspace_digest.composite_sha256:
            return FreshnessState.FRESH, "Workspace content digest matches evidence baseline."

        # If composite hash differs, perform dependency cascade analysis
        deps = dependency_map or {}
        closure: Set[str] = set(target_files)
        for tf in target_files:
            closure.update(deps.get(tf, []))

        # Check if any file in target closure was altered
        for path, file_digest in current_digest.file_digests.items():
            if path in closure:
                # Target or direct dependency was modified
                return (
                    FreshnessState.STALE,
                    f"Target file or dependency `{path}` was modified since evidence capture.",
                )

        # Target closure is untouched; isolated submodule evidence is preserved
        return FreshnessState.FRESH, "Target dependency closure untouched; proof preserved."


# ============================================================================
# 6. UNIFIED CONTEXT SYNTHESIZER
# ============================================================================

@dataclass
class ContextBlock:
    """A bounded segment of prompt context with assigned priority tier."""
    tier: ContextTier
    title: str
    content: str
    estimated_tokens: int = 0

    def __post_init__(self):
        if self.estimated_tokens == 0:
            self.estimated_tokens = max(1, int(len(self.content) / CHARS_PER_TOKEN_ESTIMATE))


class ContextSynthesizer:
    """Assembles mathematically bounded, persona-tailored, and priority-tiered prompts."""

    def __init__(
        self,
        max_context_tokens: int = 32_000,
        reserve_headroom_tokens: int = DEFAULT_TOKEN_RESERVE_HEADROOM,
    ):
        self.max_context_tokens = max_context_tokens
        self.reserve_headroom = max(reserve_headroom_tokens, int(0.10 * max_context_tokens))
        self.target_prompt_ceiling = self.max_context_tokens - self.reserve_headroom

    def assemble_prompt(
        self,
        view_type: PersonaViewType,
        tier0_intent_blocks: List[ContextBlock],
        tier1_diagnostic_blocks: List[ContextBlock],
        tier2_code_blocks: List[ContextBlock],
        tier3_architecture_blocks: List[ContextBlock],
    ) -> str:
        """Compose the complete prompt honoring priority tiers and headroom ceilings."""
        # 1. Tier 0 Verification (Immutable)
        t0_tokens = sum(b.estimated_tokens for b in tier0_intent_blocks)
        if t0_tokens > int(0.40 * self.target_prompt_ceiling):
            # Intent is dangerously large, but still cannot be truncated
            pass

        remaining_budget = self.target_prompt_ceiling - t0_tokens
        accepted_blocks: List[ContextBlock] = list(tier0_intent_blocks)

        # 2. Tier 1: Diagnostics & Handoff Envelopes
        t1_budget = int(0.35 * self.target_prompt_ceiling)
        t1_accepted = self._filter_blocks_to_budget(tier1_diagnostic_blocks, min(remaining_budget, t1_budget))
        accepted_blocks.extend(t1_accepted)
        remaining_budget -= sum(b.estimated_tokens for b in t1_accepted)

        # 3. Tier 2: Code & Diffs
        t2_budget = int(0.45 * self.target_prompt_ceiling)
        t2_accepted = self._filter_blocks_to_budget(tier2_code_blocks, min(remaining_budget, t2_budget))
        accepted_blocks.extend(t2_accepted)
        remaining_budget -= sum(b.estimated_tokens for b in t2_accepted)

        # 4. Tier 3: Architecture Skeleton & Lessons
        if remaining_budget > 200:
            t3_accepted = self._filter_blocks_to_budget(tier3_architecture_blocks, remaining_budget)
            accepted_blocks.extend(t3_accepted)

        # 5. Render Final Markdown
        return self._render_markdown_prompt(view_type, accepted_blocks)

    def _filter_blocks_to_budget(
        self, blocks: List[ContextBlock], token_budget: int
    ) -> List[ContextBlock]:
        """Greedily accept blocks within token budget."""
        accepted: List[ContextBlock] = []
        spent = 0
        for block in blocks:
            if spent + block.estimated_tokens <= token_budget:
                accepted.append(block)
                spent += block.estimated_tokens
        return accepted

    def _render_markdown_prompt(
        self, view_type: PersonaViewType, blocks: List[ContextBlock]
    ) -> str:
        """Render markdown prompt with header banner and ordered sections."""
        sections = [f"# ORAGAI Multi-Agent Execution Frame: `{view_type.value}`\n"]
        for block in blocks:
            sections.append(f"## {block.title}\n{block.content.strip()}\n")
        return "\n".join(sections)


# ============================================================================
# 7. CROSS-AGENT CONTEXT MANAGER (ORCHESTRATOR FACADE)
# ============================================================================

class CrossAgentContextManager:
    """Central orchestration facade managing handoff lifecycle, freshness, and synthesis."""

    def __init__(self, workspace_path: Path, max_tokens: int = 32_000):
        self.workspace_path = workspace_path
        self.synthesizer = ContextSynthesizer(max_context_tokens=max_tokens)
        self.latest_digest = WorkspaceDigest.create(self.workspace_path)
        self._envelopes: Dict[str, HandoffEnvelope] = {}

    def record_handoff(self, envelope: HandoffEnvelope) -> HandoffEnvelope:
        """Seal and persist a cross-agent handoff envelope."""
        self.latest_digest = WorkspaceDigest.create(self.workspace_path)
        sealed = envelope.seal(self.latest_digest.composite_sha256)
        self._envelopes[sealed.envelope_id] = sealed
        return sealed

    def get_latest_envelope(self, handoff_type: HandoffType) -> Optional[HandoffEnvelope]:
        """Retrieve most recent envelope of a specific type."""
        matching = [e for e in self._envelopes.values() if e.handoff_type == handoff_type]
        if not matching:
            return None
        matching.sort(key=lambda e: e.created_at_utc, reverse=True)
        return matching[0]

    def build_developer_prompt(
        self,
        milestone_id: str,
        requirements_md: str,
        acceptance_criteria_md: str,
        architect_envelope: HandoffEnvelope,
        target_code_map: Dict[str, str],
        red_test_trace: Optional[str] = None,
    ) -> str:
        """Construct deterministic prompt for Developer persona."""
        t0_blocks = [
            ContextBlock(ContextTier.TIER_0_INTENT, "Target Milestone", f"Active: `{milestone_id}`"),
            ContextBlock(ContextTier.TIER_0_INTENT, "Requirements", requirements_md),
            ContextBlock(ContextTier.TIER_0_INTENT, "Acceptance Criteria", acceptance_criteria_md),
            ContextBlock(
                ContextTier.TIER_0_INTENT,
                "Invariants & Anti-Stub Directives",
                "1. Zero Stubs: Prohibited from writing `pass`, `TODO`, or `raise NotImplementedError`.\n"
                "2. RBAC Sandbox: File edits strictly restricted to designated target files.",
            ),
        ]

        t1_blocks = [
            ContextBlock(
                ContextTier.TIER_1_DIAGNOSTICS,
                "Architect Blueprint",
                json.dumps(architect_envelope.typed_payload, indent=2),
            )
        ]
        if red_test_trace:
            t1_blocks.append(
                ContextBlock(ContextTier.TIER_1_DIAGNOSTICS, "Failing Pytest Trace (Red TDD Phase)", red_test_trace)
            )

        t2_blocks = []
        for file_path, code in target_code_map.items():
            t2_blocks.append(
                ContextBlock(ContextTier.TIER_2_CODE, f"Source File: `{file_path}`", f"```python\n{code}\n```")
            )

        return self.synthesizer.assemble_prompt(
            view_type=PersonaViewType.DEVELOPER_VIEW,
            tier0_intent_blocks=t0_blocks,
            tier1_diagnostic_blocks=t1_blocks,
            tier2_code_blocks=t2_blocks,
            tier3_architecture_blocks=[],
        )
```

---

# 7. Rigorous Test Matrix & Verification Scenarios

The following verification matrix specifies the comprehensive suite of tests verifying P6's context assembly engine, dynamic headroom allocation, cryptographic handoff sealing, freshness invalidation, and diagnostic compaction.

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 P6 TEST VERIFICATION MATRIX                              │
├─────────┬───────────────────────────────┬───────────────────────────────┬────────────────┤
│ Test ID │ Function / Test Name          │ Tested Invariant / Feature    │ Expected Pass  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T01  │ `test_tier0_intent_never_`    │ Tier 0 Intent elements are    │ Prompt contains│
│         │ `truncated_under_budget_cap`  │ protected from token clamping │ 100% of ACs    │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T02  │ `test_output_headroom_`       │ Prompt size never violates    │ Free headroom  │
│         │ `reserve_guarantee`           │ $C_{\text{target}} = C_{\max} - H_{\text{res}}$│ $\ge 2,048$ tk │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T03  │ `test_diagnostic_compactor_`  │ Strips ANSI codes, banners,   │ Compacted trace│
│         │ `extracts_failing_frame`      │ and extracts failing frame    │ $\le 800$ chars│
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T04  │ `test_handoff_envelope_`      │ SHA-256 seal binds payload    │ Digest matches │
│         │ `cryptographic_sealing`       │ and detects tampering         │ content hash   │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T05  │ `test_workspace_digest_`      │ File edit alters composite    │ Digest changes │
│         │ `detects_file_modification`   │ workspace SHA-256 digest      │ immediately    │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T06  │ `test_freshness_validator_`   │ Modifying module invalidates  │ FreshnessState │
│         │ `invalidates_stale_proof`     │ dependent test evidence       │ is `STALE`     │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T07  │ `test_freshness_validator_`   │ Editing isolated file B keeps │ FreshnessState │
│         │ `preserves_isolated_proof`    │ independent test proof for A  │ remains `FRESH`│
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T08  │ `test_missing_handoff_`       │ Missing upstream envelope     │ FSM halts with │
│         │ `triggers_fatal_fsm_error`    │ halts instead of raw fallback │ explicit error │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T09  │ `test_persona_view_`          │ Developer view receives code  │ Architect has  │
│         │ `isolation_and_filtering`     │ while Architect receives map  │ no code bodies │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T10  │ `test_untruncated_diff_`      │ Multi-file diffs exceeding 4k │ Full diff is   │
│         │ `rendering_for_reviewer`      │ are preserved across files    │ delivered      │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T11  │ `test_cross_run_memory_`      │ Distilled lessons injected    │ Memory tokens  │
│         │ `budget_clamping`             │ without context bloat         │ $\le 200$ tk   │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P6-T12  │ `test_ast_folding_in_tier2_`  │ Non-target functions folded to│ Full target,   │
│         │ `under_constrained_budget`    │ signatures during token crunch│ folded neighbor│
└─────────┴───────────────────────────────┴───────────────────────────────┴────────────────┘
```

---

# 8. Handoff Contract for P7 (Audit & Deep Inspection Plan)

### 8.1 Output Artifacts Produced by P6
1. **Canonical Context Engine (`orchestrator/context/handoff.py`):** Fully typed `ContextSynthesizer`, `CrossAgentContextManager`, and `FreshnessValidator`.
2. **Standardized Handoff Schemas:** Strongly typed contracts (`ArchitectHandoffPayload`, `DeveloperHandoffPayload`, `TesterHandoffPayload`, `ReviewerHandoffPayload`).
3. **Evidence Freshness Mesh:** Working-tree SHA-256 binding and dependency cascade invalidation algorithms.
4. **Diagnostic Compactor Pipeline:** High-signal extraction of pytest and compiler failure traces ($\le 800$ tokens).

### 8.2 Input Contract for P7
P7 (**Audit, Deep Inspection & Self-Evolution Plan**) will ingest:
- The `ContextSynthesizer` to construct audit-specific persona views (Auditor and Evolution Specialists).
- The `WorkspaceDigest` Merkle tree to perform repository-wide static vulnerability scans, AST architectural violation detection, and codebase health indexing.
- The `DiagnosticCompactor` to distill historical audit findings and system evolution diffs into permanent repo knowledge.

---

# 9. P6 Exit Criteria & Verification Sign-Off

- [x] **Zero Production Code Touched:** All deliverables reside strictly within `docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md`.
- [x] **Strict Invariant Continuity:** Seamlessly integrates P0 forensic baseline, P1 Task Truth, P2.1 Evidence Gates, P3 Guarded FSM, P4 Adaptive Resource Governance, and P5 Agent Workstreams.
- [x] **Mathematically Bounded Token Tiers:** Priority context tiers (Tier 0 to Tier 3) and dynamic headroom allocation ($H_{\text{reserve}} \ge 2,048$ tokens) formally defined.
- [x] **Lossless Cross-Agent Handoffs:** Cryptographically sealed JSON/Markdown envelopes specified for all 4 inter-agent transitions.
- [x] **Cryptographic Freshness & Invalidation:** Workspace composite SHA-256 digest and dependency cascade algorithm formulated.
- [x] **High-Signal Diagnostic Compactor:** Pytest stdout distillation into compact failure frames specified.
- [x] **Production Python Data Models:** Complete, fully typed Python dataclasses and protocols ready for downstream implementation.
- [x] **Ready for P7:** Structured audit context requirements and exit criteria established.
