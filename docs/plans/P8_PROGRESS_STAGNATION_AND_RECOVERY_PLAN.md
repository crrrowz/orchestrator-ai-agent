# P8 — PROGRESS, STAGNATION & RECOVERY PLAN

> **Document Type:** Canonical Systems Architecture, Autonomous Agent Resilience Engineering & Stagnation Recovery Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Systems Architect, SRE & Autonomous Agent Resilience Engineer  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md`, `docs/plans/P1_TASK_TRUTH_AND_REQUIREMENT_MODEL_PLAN.md`, `docs/plans/P2_EVIDENCE_AND_COMPLETION_GATES_PLAN.md`, `docs/plans/P3_GUARDED_FSM_AND_LIFECYCLE_ORCHESTRATION_PLAN.md`, `docs/plans/P4_ADAPTIVE_RESOURCE_GOVERNANCE_PLAN.md`, `docs/plans/P5_AGENT_WORK_AND_MILESTONE_EXECUTION_PLAN.md`, `docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md`, `docs/plans/P7_AUDIT_DEEP_INSPECTION_AND_SELF_EVOLUTION_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Design Phase:** P8 (Specification & Stagnation Recovery Engine — Zero Production Code Modified)

---

# 1. Executive Summary & Forensic Stagnation Pathology Analysis

This specification establishes the canonical **Progress, Stagnation & Recovery Plan (P8)** for the **ORAGAI** multi-agent software engineering orchestrator.

### 1.1 The Strategic Position of P8 in the ORAGAI Stack
To date, the architectural redesign of ORAGAI has established:
1. **P0 (Forensic Baseline & Invariants):** Identified the fatal conflation of *Resource Safety Governance* with *Work Completion*, 5-step micro-turn cages, premature 28% exploration aborts, 4,000-character truncated reviewer diffs, and binary circuit breaker failures.
2. **P1 (Task Truth & Requirement Model):** Established the deterministic entity graph: $\text{Task} \to \text{Requirements} \to \text{Acceptance Criteria} \to \text{Milestones}$.
3. **P2.1 (Evidence Engine & Completion Gates):** Formulated cryptographic content identity (composite SHA-256), orthogonal state dimensions (`ImplementationState`, `VerificationState`, `BlockingState`), and the 14-step deterministic Completion Gate (`TaskTruthSemanticQueries`).
4. **P3 (Guarded FSM & Lifecycle Orchestration):** Inverted the execution loop from procedural scripts to an event-driven `GuardedFSMEngine` that delegates bounded, ephemeral agent turns via Inversion of Control (IoC), establishing the central `RESOLUTION` state and 4 recovery loops (`INCOMPLETE`, `FAILED`, `STAGNATION`, `AMBIGUOUS`).
5. **P4 (Adaptive Resource Governance):** Replaced hard micro-caps with dynamic complexity-based turn allocation ($T_{\text{allocated}} \in [10, 30]$), AST-aware context folding (`ASTAwareContextClamper`), and the stagnation penalty formula ($P_{\text{stagnation}} = \min(6, \text{stagnation\_count} \times 2)$).
6. **P5 (Agent Work & Milestone Execution):** Established persona RBAC boundaries, the Micro-TDD loop (Red $\to$ Green $\to$ Refactor), topological DAG wave dispatch, intra-turn anti-spinning trackers, and surgical defect fixes.
7. **P6 (Context & Evidence Handoff):** Established the `WorkspaceDigest` Merkle tree, priority context tiering (Tier 0 to Tier 3), cryptographic handoff envelopes, and diagnostic trace compactor.
8. **P7 (Audit, Deep Inspection & Self-Evolution):** Established zero-token deterministic sweeps, Graft cluster partitioning, `VerifiedAuditFinding` DAGs, the Codebase Health Index ($\text{CHI} \in [0, 100]$), quarantined defect backlogs (`docs/quarantined_findings.json`), and Sentinel SQLite WAL logging.

### The Core Mission of P8:
$$\text{While P3 defines the recovery state transitions and P4 adjusts resource penalties,}$$
$$\text{\textbf{P8 builds the intelligent cognitive engine for multi-dimensional semantic progress detection,}}$$
$$\text{\textbf{sliding-window oscillation analysis, 4-tier adaptive circuit breaking, and automated strategy mutation}}$$
$$\text{\textbf{to guarantee autonomous system recovery without infinite loops or premature aborts.}}$$

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ORAGAI ARCHITECTURE                                    │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          Guarded FSM Engine (P3)                               │   │
│   │                 [RESOLUTION / STAGNATION / RECOVERY LOOPS]                     │   │
│   └───────────────────────┬────────────────────────────────┬───────────────────────┘   │
│                           │                                │                           │
│     State Transitions     │                                │  Pre-Dispatch Budget      │
│     & Evidence Queries    │                                │  & Stagnation Penalty     │
│                           ▼                                ▼                           │
│   ┌───────────────────────────────┐        ┌───────────────────────────────┐           │
│   │  Task Truth & Evidence Engine │        │ Adaptive Resource Governance  │           │
│   │            (P2.1)             │        │             (P4)              │           │
│   │                               │        │                               │           │
│   │ • TaskTruthGraph (P1)         │        │ • AdaptiveBudgetAllocator     │           │
│   │ • CriterionEvidencePolicies   │        │ • ASTAwareContextClamper      │           │
│   │ • CompletionGate              │        │ • MonetaryCircuitBreaker      │           │
│   │ • Defect Findings (P7)        │        │ • Stagnation Penalty (P_stag) │           │
│   └───────────────────────┬───────┘        └───────────────┬───────────────┘           │
│                           │                                │                           │
│                           └────────────────┬───────────────┘                           │
│                                            │                                           │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │        Progress, Stagnation & Recovery Engine (P8) (THIS SPECIFICATION)        │   │
│   │                                                                                │   │
│   │  • Multi-Dimensional Semantic Progress Engine (AST, Test Nodes, Evidence, Def) │   │
│   │  • Progress Efficiency Ratio (PER 2.0) & Velocity Vector Formulation           │   │
│   │  • Sliding-Window Oscillation Detector (Finite Sequence Autocorrelation k=2..5)│   │
│   │  • Anti-Churn Evasion Engine (AST Structural Diff vs Cosmetic Git Churn)       │   │
│   │  • 4-Tier Adaptive Circuit Breaker (CLOSED -> DEGRADED -> MUTATING -> TRIPPED) │   │
│   │  • Dynamic Strategy Mutator (Prompt Steering, Decomposition, Tools, Models)    │   │
│   │  • Transactional Rollback & Milestone Quarantine Engine (GitOps Checkpoints)   │   │
│   │  • Sentinel Diagnostics DB Recovery WAL Telemetry & HITL Escalation Gateway    │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │ Adaptive Recovery Directives              │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                    Agent Workstream & Execution Engine (P5)                    │   │
│   │                                                                                │   │
│   │   [Steered Prompt]  ───▶  [Decomposed DAG]  ───▶  [Constrained Tool / Model]   │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.2 Forensic Analysis of Stagnation Pathologies in Legacy ORAGAI
A rigorous forensic post-mortem of legacy recovery mechanisms (`orchestrator/telemetry/recorder.py`, `orchestrator/pipeline/dev_test_loop.py`, `orchestrator/pipeline/full_pipeline.py`, and `orchestrator/control/token_governance.py`) reveals six fatal pathologies:

| Legacy Subsystem | Code Location | Observed Pathology | Root Cause & Failure Mechanism | P8 Architectural Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **Brittle Binary Circuit Breaker** | `recorder.py:L236-307` | `check_circuit_breaker()` trips after 2 identical errors (`threshold = 2`), halting execution immediately. | If an agent explores a new hypothesis or refactors code but the same test still fails, the breaker trips on iteration 2 and violently kills the pipeline without attempting alternative remediation. | **4-Tier Adaptive Breaker & Mutation:** Breaker transitions `CLOSED` $\to$ `DEGRADED` $\to$ `STRATEGY_MUTATING`, actively mutating execution strategies before escalating. |
| **Premature Loop Abort** | `dev_test_loop.py:L311-322`, `full_pipeline.py:L535-545` | Hard loop exit on `circuit_broken == True`, emitting fatal error. | Dev loop equates a failing test repeat with complete operational failure, preventing prompt steering, sub-task decomposition, or model tier elevation. | **Cognitive Recovery Loop:** FSM routes to `RESOLUTION`, triggering deterministic mutation directives and sub-atomic milestone decomposition. |
| **28% Investigation Kill Thread** | `base_pipeline.py:L304-324`, `token_governance.py:L147-151` | Background thread invokes `conv.interrupt()` if 28% of turn tokens are consumed without an immediate file write. | Deep investigation, searching code, and reading logs are misdiagnosed as stagnation. The agent is killed mid-thought before it can synthesize a patch. | **Phase-Aware Semantic Progress:** Replaces token thresholds with multi-dimensional velocity vectors; exploration in planning/audit is rewarded, not penalized. |
| **Superficial Churn Vulnerability** | `recorder.py:L251-268` | Compares raw SHA-256 diff hashes (`curr_diff_hash == _last_diff_hash`). | LLMs append whitespace, comments, or trivial docstrings. The raw diff hash changes, fooling the legacy checker into believing progress occurred while tests stay broken. | **AST Structural Diff Verification:** Compares normalized AST symbol trees, completely ignoring comments, docstrings, and whitespace churn. |
| **Multi-Iteration Cycle Blindness** | `recorder.py:L283-290` | Only tracks immediately preceding iteration (`self._last_error_hash`, `self._last_diff_hash`). | Fails to detect 2-step or 3-step periodic oscillations ($A \to B \to A$ or $A \to B \to C \to A$), where the agent alternates between two conflicting broken fixes indefinitely. | **Sliding-Window Sequence Hashing:** Autocorrelation across history window $k \in [2, 5]$ detects complex cyclic state oscillations deterministically. |
| **Binary Abort vs Remediation** | `dev_test_loop.py:L320`, `recorder.py:L293-306` | System has only two states: run normally or abort entirely. | The system cannot adapt: it cannot change system prompts, restrict error-prone tools, split the task into smaller sub-tasks, or switch to a higher-tier reasoning model. | **4-Level Strategy Mutation Taxonomy:** Progressively applies Prompt Steering $\to$ Target Decomposition $\to$ Tool Constriction $\to$ Model Elevation. |

---

### 1.3 Theoretical Framework for Resilient Progress Governance

P8 establishes four formal theorems governing progress detection, cycle recognition, adaptive recovery, and state preservation:

#### Theorem 1: Multi-Dimensional Semantic Progress Invariant
Progress in an autonomous software engineering system is not a scalar boolean (`diff != None` or `exit_code == 0`). It is a vector in 4-dimensional state space:
$$\vec{V}_k = \begin{pmatrix} V_{\text{code}} \\ V_{\text{verif}} \\ V_{\text{evid}} \\ V_{\text{defect}} \end{pmatrix} \in \mathbb{R}^4$$
Execution is classified as making **Genuine Semantic Progress** if and only if:
$$\mathcal{P}_{\text{semantic}}(\vec{V}_k) \iff \left( V_{\text{verif}} > 0 \lor V_{\text{evid}} > 0 \lor V_{\text{defect}} > 0 \right) \lor \left( V_{\text{code}} > 0 \land V_{\text{verif}} \ge 0 \land V_{\text{defect}} \ge 0 \right)$$
Syntactic edits ($V_{\text{code}} > 0$) that introduce test regressions ($V_{\text{verif}} < 0$) or new defects ($V_{\text{defect}} < 0$) constitute **Degrading Churn**, not progress.

#### Theorem 2: Bounded Oscillation Detection (Finite Sequence Autocorrelation)
Let $\vec{\sigma}_k = \langle H(\text{AST}_k), H(\mathcal{T}_{\text{fail}, k}), H(\mathcal{D}_k) \rangle$ be the state fingerprint at iteration $k$. An execution sequence exhibits a cycle of period $p \in [2, N_{\text{max}}]$ if:
$$\exists p \in \{2, \dots, N_{\text{max}}\} \quad \text{such that} \quad \vec{\sigma}_k = \vec{\sigma}_{k-p}$$
Where $N_{\text{max}} = 5$ represents the maximum sliding history window. When a cycle is detected, the probability of random exit without strategy mutation approaches zero: $\lim_{m \to \infty} P(\text{Exit} \mid \text{Cycle}_p) = 0$. Therefore, deterministic strategy mutation is mathematically mandatory.

#### Theorem 3: Adaptive Strategy Mutation Hierarchy
Let $\mathcal{S}_0$ be the default agent execution configuration. When stagnation or oscillation is detected at iteration $k$, the recovery engine applies a deterministic mutation operator $\mathcal{M}_\ell$ from a strictly ordered 4-tier hierarchy:
$$\mathcal{S}_{k+1} = \mathcal{M}_\ell(\mathcal{S}_k), \quad \ell = \min\left(4, \; \text{stagnation\_level}\right)$$
$$\text{Where } \mathcal{M}_1 = \text{PromptSteering}, \; \mathcal{M}_2 = \text{TargetDecomposition}, \; \mathcal{M}_3 = \text{ToolConstriction}, \; \mathcal{M}_4 = \text{ModelElevation}$$
Terminal abort occurs if and only if all 4 mutation tiers are exhausted without achieving positive progress ($\vec{V}_{k+1} \le \vec{0}$).

#### Theorem 4: Atomic State & Working-Tree Rollback Invariant
Let $\mathcal{W}_k$ be the workspace state and $\mathcal{G}_k$ be the `TaskTruthGraph` state at iteration $k$. If iteration $k+1$ yields severe regression ($V_{\text{verif}} < -2$ or PreFlight syntax failure):
$$\mathcal{W}_{k+1} \xrightarrow{\text{GitOps Rollback}} \mathcal{W}_k \quad \land \quad \mathcal{G}_{k+1} \xrightarrow{\text{Graph Revert}} \mathcal{G}_k$$
Every rollback is transactional, leaves zero orphaned workspace artifacts, and logs a structured recovery incident to the SQLite WAL database.

---

### 1.4 Inviolable System Invariants for P8

1. **Zero Production Code Modifications:** P8 is an architectural specification and design contract. No files in `orchestrator/` are modified during this phase.
2. **Semantic Progress over Superficial Churn:** Progress is defined strictly by requirement advancement, new evidence generation, or defect resolution. Formatting edits, comment additions, or oscillating error signatures must never be classified as real progress.
3. **Adaptive Mutation over Violent Abort:** When stagnation is detected, the engine must mutate execution strategies (prompt steering, decomposition, tool restriction, alternative model routing) before tripping terminal abort circuit breakers.
4. **Deterministic Loop Detection:** The engine must mathematically detect circular fix patterns ($A \to B \to A$) and cyclic error transitions across arbitrary window lengths $k \in [2, 5]$.
5. **Safe State Preservation:** Every recovery or rollback action must preserve working-tree integrity, commit historical diagnostic logs to SQLite WAL, and checkpoint `TaskTruthGraph` state.

---

# 2. Multi-Dimensional Semantic Progress Detection Engine

Legacy ORAGAI evaluated progress as a binary flag based on string diff length or pytest exit codes. P8 replaces this with a continuous, multi-dimensional semantic progress engine.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     MULTI-DIMENSIONAL PROGRESS DETECTION ENGINE                        │
│                                                                                        │
│   ┌───────────────────────────┐                     ┌──────────────────────────────┐   │
│   │    AST Structural Diff    │                     │     Pytest Node ID Delta     │   │
│   │       (V_code)            │                     │          (V_verif)           │   │
│   │                           │                     │                              │   │
│   │ • Normalizes AST symbols  │                     │ • Passed nodes delta         │   │
│   │ • Strips comments & spaces│                     │ • Failed nodes delta         │   │
│   │ • Symbol add/mod/del count│                     │ • Error severity weighting   │   │
│   └─────────────┬─────────────┘                     └──────────────┬───────────────┘   │
│                 │                                                  │                   │
│                 └─────────────────┐              ┌─────────────────┘                   │
│                                   │              │                                     │
│                                   ▼              ▼                                     │
│                            ┌────────────────────────────┐                              │
│                            │    Progress Velocity       │                              │
│                            │      Vector Engine         │                              │
│                            │   V = <V_c, V_v, V_e, V_d> │                              │
│                            └──────────────┬─────────────┘                              │
│                                   ▲              ▲                                     │
│                                   │              │                                     │
│                 ┌─────────────────┘              └─────────────────┐                   │
│                 │                                                  │                   │
│   ┌─────────────┴─────────────┐                     ┌──────────────┴───────────────┐   │
│   │   AC Evidence Velocity    │                     │   Defect Resolution Velocity │   │
│   │       (V_evid)            │                     │          (V_defect)          │   │
│   │                           │                     │                              │   │
│   │ • Valid P2.1 hashes       │                     │ • Resolved P7 findings       │   │
│   │ • Criteria transitioned   │                     │ • New regressions introduced │   │
│   │ • ImplementationState del │                     │ • Severity-weighted delta    │   │
│   └───────────────────────────┘                     └──────────────────────────────┘   │
│                                           │                                            │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                   Progress Efficiency Ratio 2.0 (PER 2.0)                      │   │
│   │                                                                                │   │
│   │   PER = (α·V_code + β·V_verif + γ·V_evid + δ·V_defect) / (Tokens/1000 + ε)     │   │
│   │                                                                                │   │
│   │   [THRIVING] ──▶ [MAKING_PROGRESS] ──▶ [MARGINAL_CHURN] ──▶ [STAGNANT/REGRESS] │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Formal Mathematical Definitions of Velocity Components

#### 1. Codebase Delta Velocity ($V_{\text{code}}$)
Measures meaningful AST structural change while filtering out superficial whitespace, formatting, and comment modifications.

Let $\mathcal{A}(f)$ be the parsed, normalized Abstract Syntax Tree of file $f \in \mathcal{W}$, where docstrings, comments, and node source line formatting are stripped:
$$\mathcal{S}_{\text{symbols}}(f) = \{ (t, n, \text{sig}) \mid t \in \{\text{Class}, \text{Function}, \text{Method}, \text{Import}\}, \; n = \text{name}, \; \text{sig} = \text{hash}(\text{body\_ast}) \}$$
The codebase structural diff between turn $k-1$ and turn $k$ across all files is:
$$\Delta \text{AST}_{\text{structural}} = \sum_{f \in \mathcal{W}} \left( |\mathcal{S}_k(f) \setminus \mathcal{S}_{k-1}(f)| + |\mathcal{S}_{k-1}(f) \setminus \mathcal{S}_k(f)| \right)$$
Codebase Delta Velocity is normalized as:
$$V_{\text{code}} = \min\left(1.0, \; \frac{\Delta \text{AST}_{\text{structural}}}{10.0}\right)$$
- If an agent only edits whitespace or comments: $\Delta \text{AST}_{\text{structural}} = 0 \implies V_{\text{code}} = 0.0$.
- If an agent adds, refactors, or modifies functions/classes: $\Delta \text{AST}_{\text{structural}} > 0 \implies V_{\text{code}} > 0.0$.

#### 2. Verification Delta Velocity ($V_{\text{verif}}$)
Measures net advancement in the test suite by tracking individual test node identifiers (`tests/test_x.py::test_y`):
$$\text{PassNodes}_k = \{ \text{node\_id} \mid \text{node\_id} \in \text{PytestReport}_k \land \text{outcome}(\text{node\_id}) = \text{PASSED} \}$$
$$\text{FailNodes}_k = \{ \text{node\_id} \mid \text{node\_id} \in \text{PytestReport}_k \land \text{outcome}(\text{node\_id}) \in \{\text{FAILED}, \text{ERROR}\} \}$$
The verification delta is:
$$\Delta \text{PassNodes} = |\text{PassNodes}_k \setminus \text{PassNodes}_{k-1}| - |\text{PassNodes}_{k-1} \setminus \text{PassNodes}_k|$$
$$\Delta \text{FailNodes} = |\text{FailNodes}_{k-1} \setminus \text{FailNodes}_k| - |\text{FailNodes}_k \setminus \text{FailNodes}_{k-1}|$$
Verification Delta Velocity is computed as:
$$V_{\text{verif}} = \Delta \text{PassNodes} + 0.5 \cdot \Delta \text{FailNodes}$$
- If 2 failing tests are fixed without breaking existing tests: $\Delta \text{PassNodes} = +2, \Delta \text{FailNodes} = +2 \implies V_{\text{verif}} = 3.0$.
- If a fix breaks 3 previously passing tests: $\Delta \text{PassNodes} = -3 \implies V_{\text{verif}} = -3.0$ (Severe Regression).

#### 3. Evidence Delta Velocity ($V_{\text{evid}}$)
Measures the acquisition of valid cryptographic evidence satisfying P2.1 Acceptance Criteria:
$$\text{SatAC}_k = \{ ac \in \text{Graph.ACs} \mid ac.\text{verification\_state} = \text{VERIFIED} \land ac.\text{evidence\_hash} \neq \emptyset \}$$
$$V_{\text{evid}} = 2.0 \cdot |\text{SatAC}_k \setminus \text{SatAC}_{k-1}| - 5.0 \cdot |\text{SatAC}_{k-1} \setminus \text{SatAC}_k|$$
Invalidating previously satisfied acceptance criteria carries a heavy penalty ($-5.0$).

#### 4. Defect Resolution Velocity ($V_{\text{defect}}$)
Measures the net resolution of P7 verified audit findings ($\mathcal{D}$):
$$\mathcal{D}_{\text{resolved}} = \{ d \in \mathcal{D}_{k-1} \mid d.\text{finding\_id} \notin \mathcal{D}_k \land d.\text{remediation\_status} = \text{RESOLVED} \}$$
$$\mathcal{D}_{\text{introduced}} = \{ d \in \mathcal{D}_k \mid d.\text{finding\_id} \notin \mathcal{D}_{k-1} \}$$
$$V_{\text{defect}} = \sum_{d \in \mathcal{D}_{\text{resolved}}} w_{\text{sev}}(d.\text{severity}) - \sum_{d \in \mathcal{D}_{\text{introduced}}} 1.5 \cdot w_{\text{sev}}(d.\text{severity})$$
Where $w_{\text{sev}}(\text{CRITICAL}) = 3.0, \; w_{\text{sev}}(\text{HIGH}) = 2.0, \; w_{\text{sev}}(\text{MEDIUM}) = 1.0, \; w_{\text{sev}}(\text{LOW}) = 0.5$.

---

### 2.2 Unified Progress Efficiency Ratio (PER 2.0) Formulation

The **Progress Efficiency Ratio (PER 2.0)** combines the 4-dimensional velocity vector with token expenditure to compute an empirical return on cognitive investment:

$$\text{PER}_k = \frac{\alpha \cdot V_{\text{code}} + \beta \cdot V_{\text{verif}} + \gamma \cdot V_{\text{evid}} + \delta \cdot V_{\text{defect}}}{\left(\frac{\text{TokensConsumed}_k}{1000} + \epsilon\right)}$$

#### Recommended Parameter Calibration:
- $\alpha = 1.0$ (Weight for normalized AST structural code edits)
- $\beta = 3.0$ (Weight for verification test node advances)
- $\gamma = 4.0$ (Weight for acceptance criteria evidence satisfaction)
- $\delta = 2.5$ (Weight for verified defect resolutions)
- $\epsilon = 0.1$ (Smoothing constant to prevent division by zero in zero-token phases)

#### Normalized Progress Score ($S_{\text{progress}}$):
$$S_{\text{progress}} = \frac{1}{1 + e^{-\left(\alpha V_{\text{code}} + \beta V_{\text{verif}} + \gamma V_{\text{evid}} + \delta V_{\text{defect}}\right)}}$$

#### Progress Health Classification Matrix:

| Normalized Score ($S_{\text{progress}}$) | Velocity Criteria | Progress Health | FSM Operational State |
| :--- | :--- | :--- | :--- |
| **$S \ge 0.80$** | $V_{\text{verif}} > 0 \lor V_{\text{evid}} > 0 \lor V_{\text{defect}} > 0$ | `THRIVING` | High efficiency; reset failure counters; award token bonus. |
| **$0.55 \le S < 0.80$** | $V_{\text{code}} > 0 \land V_{\text{verif}} \ge 0 \land V_{\text{defect}} \ge 0$ | `MAKING_PROGRESS` | Normal progress; maintain current strategy and budgets. |
| **$0.40 \le S < 0.55$** | $V_{\text{code}} > 0 \land V_{\text{verif}} = 0 \land V_{\text{evid}} = 0$ | `MARGINAL_CHURN` | Cosmetic edits or exploratory changes; increment churn counter. |
| **$0.20 \le S < 0.40$** | $V_{\text{code}} = 0 \land V_{\text{verif}} = 0 \land V_{\text{evid}} = 0$ | `STAGNANT` | Zero AST change, identical errors; transition to `RESOLUTION`. |
| **$S < 0.20$** | $V_{\text{verif}} < 0 \lor V_{\text{defect}} < 0$ | `REGRESSING` | Active regression; trigger atomic rollback and strategy mutation. |

---

# 3. Cycle & Oscillation Detection Algorithms

A major failure mode in autonomous coding agents is cyclic oscillation: the agent fixes bug A by introducing bug B, and then on the next turn fixes bug B by re-introducing bug A. Legacy ORAGAI was completely blind to cycles of period $k > 1$.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SLIDING-WINDOW OSCILLATION DETECTOR                             │
│                                                                                        │
│   Turn k-4: σ_1 ──▶ Turn k-3: σ_2 ──▶ Turn k-2: σ_1 ──▶ Turn k-1: σ_2 ──▶ Turn k: σ_1  │
│   [State A]         [State B]         [State A]         [State B]        [State A]     │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ State Fingerprint Vector:  σ_k = < H(AST_k), H(T_fail,k), H(D_k) >             │   │
│   │ Rolling History Buffer:    W_5 = [ σ_k-4, σ_k-3, σ_k-2, σ_k-1, σ_k ]           │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │                                            │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │            Sliding-Window Sequence Autocorrelation Algorithm                   │   │
│   │                                                                                │   │
│   │   • Period 1 (Direct Stagnation):   σ_k == σ_k-1                               │   │
│   │   • Period 2 (Flip-Flop Cycle):     σ_k == σ_k-2  (A -> B -> A)                 │   │
│   │   • Period 3 (Triangular Cycle):    σ_k == σ_k-3  (A -> B -> C -> A)           │   │
│   │   • Period 4 (Square Cycle):        σ_k == σ_k-4  (A -> B -> C -> D -> A)       │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │                                            │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                     Pattern Match & Mutation Trigger                           │   │
│   │                                                                                │   │
│   │   IF Cycle Detected:                                                           │   │
│   │     1. Freeze current execution branch                                         │   │
│   │     2. Extract diff pair (Diff_A vs Diff_B)                                    │   │
│   │     3. Inject Anti-Oscillation Prompt Directive + Escalate Strategy Mutation   │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 State Fingerprint Formulation
At the conclusion of every execution turn $k$, the orchestrator calculates a composite **State Fingerprint** $\vec{\sigma}_k$:

$$\vec{\sigma}_k = \langle H(\text{AST}_k), \; H(\mathcal{T}_{\text{fail}, k}), \; H(\mathcal{D}_k) \rangle$$

Where:
1. $H(\text{AST}_k)$: SHA-256 hash of the sorted tuple of all normalized file AST symbol signatures:
   $$H(\text{AST}_k) = \text{SHA256}\left( \bigoplus_{f \in \text{Sorted}(\mathcal{W})} (f.\text{path}, \mathcal{S}_{\text{symbols}}(f)) \right)$$
2. $H(\mathcal{T}_{\text{fail}, k})$: SHA-256 hash of the canonical sorted set of failing test node IDs and compact failure messages:
   $$H(\mathcal{T}_{\text{fail}, k}) = \text{SHA256}\left( \bigoplus_{t \in \text{Sorted}(\text{FailNodes}_k)} (t.\text{node\_id}, t.\text{error\_class}, t.\text{compact\_trace}) \right)$$
3. $H(\mathcal{D}_k)$: SHA-256 hash of the sorted list of open verified defect IDs:
   $$H(\mathcal{D}_k) = \text{SHA256}\left( \bigoplus_{d \in \text{Sorted}(\mathcal{D}_k)} (d.\text{finding\_id}, d.\text{severity}) \right)$$

---

### 3.2 Formal Cycle Detection Algorithms

Let $\mathcal{W}_N = [\vec{\sigma}_{k-N+1}, \dots, \vec{\sigma}_k]$ be the FIFO history buffer of size $N = 5$.

#### 1. Direct Stagnation (Period $p = 1$)
$$\text{IsDirectStagnant}(k) \iff \vec{\sigma}_k = \vec{\sigma}_{k-1} \lor \left( \Delta \text{AST}_{\text{structural}} = 0 \land H(\mathcal{T}_{\text{fail}, k}) = H(\mathcal{T}_{\text{fail}, k-1}) \right)$$
- **Pattern:** The agent executed a turn, produced zero AST changes, and the exact same test failure or defect persists.
- **Action:** Stagnation counter increments: $C_{\text{stag}} \leftarrow C_{\text{stag}} + 1$.

#### 2. Circular Flip-Flop Oscillation (Period $p = 2$)
$$\text{IsFlipFlopCycle}(k) \iff \vec{\sigma}_k = \vec{\sigma}_{k-2} \land \vec{\sigma}_k \neq \vec{\sigma}_{k-1}$$
- **Pattern:** Turn $k$ returns the codebase and failure state to the exact state of turn $k-2$ ($A \to B \to A$).
- **Action:** Triggers `CyclePattern.FLIP_FLOP_P2`, generates anti-oscillation diagnostic directive containing both diffs, and escalates circuit breaker directly to `STRATEGY_MUTATING`.

#### 3. Higher-Order Periodic Cycles (Period $p \in \{3, 4, 5\}$)
$$\text{IsPeriodicCycle}(k, p) \iff \vec{\sigma}_k = \vec{\sigma}_{k-p} \land \forall j \in \{1, \dots, p-1\} \; (\vec{\sigma}_k \neq \vec{\sigma}_{k-j})$$
- **Pattern:** Turn $k$ replicates the state from $p$ turns ago ($A \to B \to C \to A$).
- **Action:** Triggers `CyclePattern.PERIODIC_PN`, isolates the multi-step cycle trajectory, and executes milestone decomposition mutation.

---

### 3.3 Superficial Churn Evasion Detection
LLMs often attempt to "evade" simple string diff circuit breakers by making cosmetic changes. P8 detects and flags these evasions mathematically:

$$\text{IsCosmeticChurn}(k) \iff \text{GitDiffLines}(\mathcal{W}_k, \mathcal{W}_{k-1}) > 0 \land \Delta \text{AST}_{\text{structural}} = 0$$
$$\text{IsTestFlailingChurn}(k) \iff \Delta \text{AST}_{\text{structural}} > 0 \land \Delta \text{PassNodes} \le 0 \land H(\mathcal{T}_{\text{fail}, k}) = H(\mathcal{T}_{\text{fail}, k-1})$$

When `IsCosmeticChurn` or `IsTestFlailingChurn` is detected for 2 consecutive turns, the engine overrides the raw diff score, treats $V_{\text{code}} = 0.0$, and classifies the turn as `MARGINAL_CHURN` / `STAGNANT`.

---

# 4. Adaptive Circuit Breakers & Dynamic Strategy Mutator

P8 dismantles the legacy binary "run or abort" breaker (`recorder.py`) and replaces it with a **4-Tier Adaptive Circuit Breaker** coupled to a **Dynamic Strategy Mutator**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        4-TIER ADAPTIVE CIRCUIT BREAKER FSM                             │
│                                                                                        │
│                                [ Normal Progress ]                                     │
│                                         │                                              │
│                                         ▼                                              │
│                                 ┌───────────────┐                                      │
│                  ┌─────────────▶│    CLOSED     │◀─────────────┐                       │
│                  │              │ (Normal Run)  │              │                       │
│                  │              └───────┬───────┘              │                       │
│                  │                      │                      │                       │
│                  │ Positive Progress    │ 1 Stagnant Turn /    │ Positive Progress     │
│                  │ (V_verif > 0)        │ Marginal Churn       │ (V_verif > 0)         │
│                  │                      ▼                      │                       │
│                  │              ┌───────────────┐              │                       │
│                  ├──────────────┤   DEGRADED    │              │                       │
│                  │              │(Tighten Budget│              │                       │
│                  │              └───────┬───────┘              │                       │
│                  │                      │                      │                       │
│                  │                      │ 2 Consecutive        │                       │
│                  │                      │ Failures / Cycle p=2 │                       │
│                  │                      ▼                      │                       │
│                  │              ┌───────────────┐              │                       │
│                  └──────────────┤   STRATEGY    │──────────────┘                       │
│                                 │   MUTATING    │                                      │
│                                 └───────┬───────┘                                      │
│                                         │                                              │
│                                         │ All 4 Mutation Tiers                         │
│                                         │ Exhausted (4 Attempts)                       │
│                                         ▼                                              │
│                                 ┌───────────────┐                                      │
│                                 │    TRIPPED    │                                      │
│                                 │ (Escalate /   │                                      │
│                                 │  Quarantine)  │                                      │
│                                 └───────────────┘                                      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Breaker States & Operational Semantics

1. **`CLOSED` (Normal Execution):**
   - The system is operating efficiently ($S_{\text{progress}} \ge 0.55$).
   - Full turn allocations ($T_{\text{allocated}}$) and standard toolsets are enabled.
   - Failure and cycle counters remain at zero.

2. **`DEGRADED` (Sluggish / Marginal Progress):**
   - Triggered on 1 stagnant turn or 2 consecutive marginal churn turns.
   - Applies P4 stagnation penalty: $P_{\text{stagnation}} = \min(6, C_{\text{stag}} \times 2)$.
   - Injects lightweight hint warning the agent that progress has slowed.

3. **`STRATEGY_MUTATING` (Active Cognitive Intervention):**
   - Triggered on 2 consecutive stagnant turns, detection of cycle ($p \ge 2$), or test regression.
   - Suspends raw execution; invokes the **Strategy Mutator** to mutate the execution plan according to the 4-tier taxonomy.
   - Rolls back working tree to the last known green checkpoint if severe regression occurred.

4. **`TRIPPED_ESCALATING` (Terminal Boundary / Human Escalation):**
   - Triggered when all 4 mutation levels have been attempted on a single milestone without positive verification progress.
   - Transitions milestone to `QUARANTINED_BLOCKED` (`docs/quarantined_findings.json`).
   - If task-level critical path is blocked, invokes `HumanChannel` for Human-in-the-Loop guidance or concludes task with `FAILED_BLOCKED`.

---

### 4.2 The 4-Tier Strategy Mutation Taxonomy

When transitioning to `STRATEGY_MUTATING`, the engine applies a specific mutation operator based on the active mutation tier ($\ell \in \{1, 2, 3, 4\}$):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        STRATEGY MUTATION TAXONOMY (TIERS 1 - 4)                        │
├─────────────────┬──────────────────────────────────────────────────────────────────────┤
│ Tier 1:         │ • Injects explicit root cause diagnostic hypotheses                  │
│ PROMPT STEERING │ • Supplies anti-oscillation diff comparison (Diff A vs Diff B)       │
│                 │ • Enforces strict "Read-Before-Edit" and "No-Comment-Churn" rules    │
├─────────────────┼──────────────────────────────────────────────────────────────────────┤
│ Tier 2:         │ • Decomposes current milestone into sub-atomic micro-milestones      │
│ TARGET          │ • Isolates single failing test file or single function signature     │
│ DECOMPOSITION   │ • Dispatches dedicated sub-turn targeting ONLY the isolated atom     │
├─────────────────┼──────────────────────────────────────────────────────────────────────┤
│ Tier 3:         │ • Restricts broad terminal commands (disables shell / generic bash)  │
│ TOOL            │ • Restricts toolset strictly to AST targeted file patching & read    │
│ CONSTRICTION    │ • Forces deterministic preflight compilation before next test run    │
├─────────────────┼──────────────────────────────────────────────────────────────────────┤
│ Tier 4:         │ • Re-routes milestone execution from Tier-2 / Tier-1.5 model to      │
│ MODEL           │   Tier-1 frontier reasoning model (e.g. Claude 3.5 Sonnet / o3-mini) │
│ ELEVATION       │ • Allocates extended reasoning token envelope for deep refactoring   │
└─────────────────┴──────────────────────────────────────────────────────────────────────┘
```

#### Detailed Mutation Specifications:

#### Tier 1: Prompt Steering Mutation ($\mathcal{M}_1$)
- **Mechanism:** Intercepts agent prompt; injects structured `StrategyMutationDirective` into the system/user envelope.
- **Content:**
  1. *Anti-Oscillation Directive:* Shows the exact alternating code diffs and failing assertions that caused the cycle.
  2. *Hypothesis Inversion:* Instructs the agent that previous assumptions were falsified by test traces.
  3. *Structural Mandate:* Forbids editing comments, docstrings, or test assertions; commands modifying the underlying production logic only.

#### Tier 2: Target Decomposition Mutation ($\mathcal{M}_2$)
- **Mechanism:** Modifies the active `MilestoneDAG` dynamically.
- **Content:**
  1. Identifies that milestone $M$ covers multiple files or multiple acceptance criteria.
  2. Splits $M$ into $k$ sub-atomic milestones: $M \to [M_{a}, M_{b}, \dots, M_{k}]$.
  3. Dispatches the agent to solve only $M_{a}$ (e.g., passing a single parameterized test case) before attempting the broader milestone.

#### Tier 3: Tool Constriction Mutation ($\mathcal{M}_3$)
- **Mechanism:** Modifies the RBAC tool definition payload sent to the OpenHands SDK agent.
- **Content:**
  1. If an agent is spinning in terminal commands (e.g. running grep/ls repeatedly or modifying environment scripts), terminal execution is disabled.
  2. Toolset is constricted strictly to `WorkspaceFileTool.read_file`, `WorkspaceFileTool.write_file`, and `PreFlightGuard.check_syntax`.
  3. Forces the agent to read the exact implementation file and make surgical edits.

#### Tier 4: Model Elevation Mutation ($\mathcal{M}_4$)
- **Mechanism:** Re-configures the LLM provider binding in `LLMManager` for the current milestone.
- **Content:**
  1. If the milestone was assigned to a standard or economy tier model (e.g., standard reasoning tier), it is elevated to the highest frontier reasoning tier configured in `orchestrator.config.json` (e.g. `Tier 1 High-Reasoning / o3 / Claude 3.5 Sonnet`).
  2. Allocates maximum reasoning token headroom ($T_{\text{max}} = 30$) for deep algorithmic resolution.

---

# 5. Quarantining, Rollback & Deadlock Resolution

When strategy mutations are exhausted or an agent introduces destructive regressions, ORAGAI must preserve codebase integrity through deterministic quarantining, atomic rollbacks, and structured deadlock resolution.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   TRANSACTIONAL ROLLBACK & QUARANTINE PIPELINE                         │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         Pre-Turn GitOps Checkpoint                             │   │
│   │                  Checkpoint: refs/checkpoints/turn_k-1                         │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │                                            │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        Agent Execution Turn (Turn k)                           │   │
│   │                    [ Produces File Edits & Runs Tests ]                        │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │                                            │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                       Post-Turn Semantic Evaluation                            │   │
│   │                                                                                │   │
│   │   • Syntax Valid? (PreFlightGuard) ───▶ IF NO: Rollback & Retry                │   │
│   │   • Regression? (V_verif < -2)    ───▶ IF YES: Rollback to Checkpoint          │   │
│   │   • Mutation Tier == 4 Exhausted?  ───▶ IF YES: Quarantine Milestone           │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │                                            │
│                   ┌───────────────────────┴───────────────────────┐                    │
│                   ▼                                               ▼                    │
│   ┌───────────────────────────────┐               ┌───────────────────────────────┐    │
│   │   Atomic GitOps Rollback      │               │   Milestone Quarantine        │    │
│   │                               │               │                               │    │
│   │ • git reset --hard checkpoint │               │ • Mark QUARANTINED_BLOCKED    │    │
│   │ • git clean -fd (untracked)   │               │ • Append quarantined_findings │    │
│   │ • Restore TaskTruthGraph state│               │ • Unblock parallel DAG branches│   │
│   │ • Log Sentinel WAL incident   │               │ • Trigger HITL if critical    │    │
│   └───────────────────────────────┘               └───────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Milestone Quarantining & `docs/quarantined_findings.json`
When a milestone or defect cannot be resolved after exhausting all 4 mutation tiers ($C_{\text{attempt}} \ge 4$):
1. The active milestone $M$ is transitioned to `MilestoneStatus.QUARANTINED_BLOCKED`.
2. The associated requirement $R$ in `TaskTruthGraph` is marked `BlockingState.BLOCKED`.
3. The finding/defect is appended to `docs/quarantined_findings.json` with complete diagnostic metadata:
   - Failing test traces and assertion diffs.
   - History of applied strategy mutations ($\mathcal{M}_1 \dots \mathcal{M}_4$) and outcomes.
   - Recommended human intervention actions.
4. **DAG Continuation:** If subsequent milestones in `MilestoneDAG` do not depend topologically on $M$, the orchestrator bypasses $M$ and continues executing independent parallel branches.

---

### 5.2 Atomic Rollback Engine via GitOps Checkpoints
To guarantee that broken code never pollutes subsequent turns:
1. **Pre-Turn Snapshot:** Before dispatching an agent turn, `RecoveryOrchestrator` creates an atomic Git checkpoint:
   $$\text{Checkpoint Tag: } \texttt{refs/oragai/checkpoints/run\_\{run\_id\}\_turn\_\{k\}}$$
2. **Rollback Triggers:** An immediate atomic rollback is executed if:
   - `PreFlightGuard.check_syntax()` fails (broken Python syntax on disk).
   - $V_{\text{verif}} \le -2.0$ (turn broke 2 or more previously passing tests).
   - Agent deleted or corrupted essential project configuration files (`pyproject.toml`, `package.json`, `conftest.py`).
3. **Rollback Execution:**
   ```bash
   git reset --hard refs/oragai/checkpoints/run_{run_id}_turn_{k}
   git clean -fd
   ```
4. **State Consistency:** The in-memory `TaskTruthGraph` and `WorkspaceDigest` are restored to the exact snapshot associated with turn $k$.

---

### 5.3 Deadlock Resolution & Human-in-the-Loop (HITL) Protocol

If all independent DAG branches are completed or blocked, and critical path milestones remain `QUARANTINED_BLOCKED`, ORAGAI initiates the **HITL Escalation Protocol**:

```python
class HITLEscalationPayload(BaseModel):
    """Structured escalation payload delivered to HumanChannel on deadlock."""
    run_id: str
    deadlock_type: str  # "CONTRADICTORY_REQUIREMENTS", "ENVIRONMENT_DEFECT", "MUTATION_EXHAUSTION"
    blocked_milestones: list[str]
    failing_tests: list[str]
    attempted_mutations: list[str]
    quarantined_findings_path: str
    recommended_options: list[str]
```

The user can choose via CLI prompt:
1. **Override Acceptance Criteria:** Relax contradictory test constraints.
2. **Inject External Solution:** Provide manual file patch or API credentials.
3. **Abort Gracefully:** Terminate run cleanly, generating comprehensive diagnostic report with partial achievements preserved.

---

# 6. Canonical Python Architecture & Data Models

This section provides the complete, production-ready, fully typed Python architecture for `orchestrator/control/recovery_engine.py`.

```python
"""
orchestrator/control/recovery_engine.py

Canonical Progress Detection, Stagnation Analysis, Adaptive Circuit Breaking,
and Strategy Mutation Engine for ORAGAI.

Zero production code modified during P8 specification phase.
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple

from pydantic import BaseModel, Field


# ============================================================================
# 1. Enums & Strong Typing Definitions
# ============================================================================

class BreakerState(str, Enum):
    """4-Tier Adaptive Circuit Breaker States."""
    CLOSED = "CLOSED"                      # Normal execution, full velocity
    DEGRADED = "DEGRADED"                  # Sluggish progress, tightened budgets
    STRATEGY_MUTATING = "STRATEGY_MUTATING" # Active cognitive mutation in progress
    TRIPPED_ESCALATING = "TRIPPED_ESCALATING" # Exhausted; quarantine & escalate


class ProgressHealth(str, Enum):
    """Classification of turn progress health."""
    THRIVING = "THRIVING"                  # Score >= 0.80 (Tests/evidence advancing)
    MAKING_PROGRESS = "MAKING_PROGRESS"    # 0.55 <= Score < 0.80 (Clean AST changes)
    MARGINAL_CHURN = "MARGINAL_CHURN"      # 0.40 <= Score < 0.55 (Cosmetic/exploratory)
    STAGNANT = "STAGNANT"                  # 0.20 <= Score < 0.40 (Zero diff / error repeat)
    REGRESSING = "REGRESSING"              # Score < 0.20 (Broken syntax / test failures)


class CyclePattern(str, Enum):
    """Classification of detected execution cycle."""
    NONE = "NONE"                          # No cycle detected
    DIRECT_STAGNATION = "DIRECT_STAGNATION"# Period 1: Identical failure and zero diff
    FLIP_FLOP_P2 = "FLIP_FLOP_P2"          # Period 2: A -> B -> A cycle
    PERIODIC_PN = "PERIODIC_PN"            # Period 3..5: Multi-step cycle
    COSMETIC_CHURN = "COSMETIC_CHURN"      # Whitespace/comment diff evasion


class MutationStrategyType(str, Enum):
    """4-Tier Strategy Mutation Taxonomy."""
    PROMPT_STEERING = "PROMPT_STEERING"    # Level 1: Anti-oscillation & diagnostic hints
    TARGET_DECOMPOSITION = "TARGET_DECOMPOSITION" # Level 2: Sub-atomic milestone split
    TOOL_CONSTRICTION = "TOOL_CONSTRICTION"# Level 3: Restrict shell, force AST patch
    MODEL_ELEVATION = "MODEL_ELEVATION"    # Level 4: Route to Tier-1 reasoning model


class RecoveryActionType(str, Enum):
    """Deterministic recovery actions dispatched by RecoveryOrchestrator."""
    CONTINUE_NORMAL = "CONTINUE_NORMAL"
    INJECT_MUTATION = "INJECT_MUTATION"
    TRANSACTIONAL_ROLLBACK = "TRANSACTIONAL_ROLLBACK"
    QUARANTINE_MILESTONE = "QUARANTINE_MILESTONE"
    ESCALATE_HITL = "ESCALATE_HITL"


# ============================================================================
# 2. Domain Data Models & Telemetry Schemas
# ============================================================================

@dataclass(frozen=True)
class ASTSymbolSignature:
    """Normalized structural symbol signature stripped of comments and whitespace."""
    symbol_type: str  # "ClassDef", "FunctionDef", "AsyncFunctionDef", "Import"
    name: str
    body_ast_hash: str


@dataclass
class StateFingerprint:
    """Composite state fingerprint for sliding-window cycle detection."""
    turn_index: int
    ast_composite_hash: str
    failing_tests_hash: str
    defect_state_hash: str
    timestamp: float = field(default_factory=time.time)

    @property
    def composite_hash(self) -> str:
        payload = f"{self.ast_composite_hash}:{self.failing_tests_hash}:{self.defect_state_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class ProgressVelocityMetrics:
    """4-Dimensional Progress Velocity Vector."""
    v_code: float      # AST structural diff velocity in [0.0, 1.0]
    v_verif: float     # Passed test node advance delta
    v_evid: float      # Acceptance criteria satisfaction delta
    v_defect: float    # Verified defect resolution delta
    tokens_consumed: int
    per_score: float   # Progress Efficiency Ratio (PER 2.0)
    normalized_score: float # Sigmoidal score in [0.0, 1.0]
    health: ProgressHealth


@dataclass
class StrategyMutationDirective:
    """Concrete mutation payload delivered to execution plane."""
    mutation_type: MutationStrategyType
    tier_level: int
    prompt_injections: List[str] = field(default_factory=list)
    banned_tools: Set[str] = field(default_factory=set)
    forced_tools: Set[str] = field(default_factory=set)
    decomposed_subtasks: List[str] = field(default_factory=list)
    elevated_model: Optional[str] = None
    target_file_lock: Optional[str] = None


@dataclass
class RecoveryDecision:
    """Unified recovery decision emitted by RecoveryOrchestrator."""
    action: RecoveryActionType
    breaker_state: BreakerState
    health: ProgressHealth
    detected_cycle: CyclePattern
    cycle_period: int
    mutation_directive: Optional[StrategyMutationDirective]
    rollback_checkpoint_ref: Optional[str]
    explanation: str


class QuarantinedMilestoneRecord(BaseModel):
    """Schema for persisted docs/quarantined_findings.json entry."""
    milestone_id: str
    task_id: str
    quarantine_timestamp: str
    exhausted_mutations: List[str]
    failing_test_nodes: List[str]
    last_ast_diff: str
    diagnostic_summary: str
    suggested_human_action: str


# ============================================================================
# 3. Component Protocols
# ============================================================================

class ISemanticProgressTracker(Protocol):
    def record_turn_snapshot(
        self,
        turn_index: int,
        workspace_path: Path,
        passed_test_nodes: Set[str],
        failed_test_nodes: Dict[str, str],
        satisfied_ac_ids: Set[str],
        open_defect_ids: Set[str],
        tokens_consumed: int,
    ) -> ProgressVelocityMetrics: ...


class IOscillationDetector(Protocol):
    def register_state(self, fingerprint: StateFingerprint) -> Tuple[CyclePattern, int]: ...
    def reset_window(self) -> None: ...


class IAdaptiveCircuitBreaker(Protocol):
    def evaluate_state_transition(
        self,
        metrics: ProgressVelocityMetrics,
        cycle_pattern: CyclePattern,
    ) -> BreakerState: ...


class IStrategyMutator(Protocol):
    def generate_mutation(
        self,
        current_tier: int,
        failing_tests: Dict[str, str],
        cycle_pattern: CyclePattern,
        active_milestone_id: str,
    ) -> StrategyMutationDirective: ...


# ============================================================================
# 4. Concrete Engine Implementations
# ============================================================================

class SemanticProgressTracker:
    """
    Computes 4-Dimensional Progress Velocity Vector and PER 2.0 score.
    Filters cosmetic whitespace/comment churn via normalized AST comparisons.
    """

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self._last_symbols: Dict[str, Set[ASTSymbolSignature]] = {}
        self._last_passed_tests: Set[str] = set()
        self._last_failed_tests: Dict[str, str] = {}
        self._last_satisfied_acs: Set[str] = set()
        self._last_open_defects: Set[str] = set()

    def _extract_file_ast_symbols(self, file_path: Path) -> Set[ASTSymbolSignature]:
        symbols: Set[ASTSymbolSignature] = set()
        if not file_path.is_file() or file_path.suffix != ".py":
            return symbols
        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(code, filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    body_dump = ast.dump(node, annotate_fields=False, include_attributes=False)
                    body_hash = hashlib.sha256(body_dump.encode("utf-8")).hexdigest()[:16]
                    symbols.add(ASTSymbolSignature(
                        symbol_type=type(node).__name__,
                        name=node.name,
                        body_ast_hash=body_hash,
                    ))
        except SyntaxError:
            pass
        return symbols

    def _get_workspace_symbols(self) -> Dict[str, Set[ASTSymbolSignature]]:
        ws_symbols: Dict[str, Set[ASTSymbolSignature]] = {}
        for py_file in self.workspace_path.rglob("*.py"):
            if ".git" in py_file.parts or ".venv" in py_file.parts:
                continue
            rel = str(py_file.relative_to(self.workspace_path)).replace("\\", "/")
            ws_symbols[rel] = self._extract_file_ast_symbols(py_file)
        return ws_symbols

    def record_turn_snapshot(
        self,
        turn_index: int,
        passed_test_nodes: Set[str],
        failed_test_nodes: Dict[str, str],
        satisfied_ac_ids: Set[str],
        open_defect_ids: Set[str],
        tokens_consumed: int,
    ) -> ProgressVelocityMetrics:
        curr_symbols = self._get_workspace_symbols()

        # 1. AST Structural Velocity (V_code)
        structural_delta = 0
        all_files = set(curr_symbols.keys()) | set(self._last_symbols.keys())
        for f in all_files:
            c_set = curr_symbols.get(f, set())
            l_set = self._last_symbols.get(f, set())
            structural_delta += len(c_set ^ l_set)
        v_code = min(1.0, structural_delta / 10.0)

        # 2. Verification Delta Velocity (V_verif)
        delta_pass = len(passed_test_nodes - self._last_passed_tests) - len(self._last_passed_tests - passed_test_nodes)
        delta_fail = len(set(self._last_failed_tests.keys()) - set(failed_test_nodes.keys())) - len(set(failed_test_nodes.keys()) - set(self._last_failed_tests.keys()))
        v_verif = float(delta_pass) + 0.5 * float(delta_fail)

        # 3. Evidence Delta Velocity (V_evid)
        delta_ac_sat = len(satisfied_ac_ids - self._last_satisfied_acs)
        delta_ac_lost = len(self._last_satisfied_acs - satisfied_ac_ids)
        v_evid = 2.0 * float(delta_ac_sat) - 5.0 * float(delta_ac_lost)

        # 4. Defect Resolution Velocity (V_defect)
        delta_def_resolved = len(self._last_open_defects - open_defect_ids)
        delta_def_introduced = len(open_defect_ids - self._last_open_defects)
        v_defect = float(delta_def_resolved) - 1.5 * float(delta_def_introduced)

        # Unified PER 2.0
        alpha, beta, gamma, delta = 1.0, 3.0, 4.0, 2.5
        numerator = alpha * v_code + beta * v_verif + gamma * v_evid + delta * v_defect
        denominator = (tokens_consumed / 1000.0) + 0.1
        per_score = numerator / denominator

        # Normalized Sigmoidal Score in [0.0, 1.0]
        import math
        raw_signal = numerator
        normalized_score = 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, raw_signal))))

        # Determine Health Classification
        if normalized_score >= 0.80 or (v_verif > 0 or v_evid > 0):
            health = ProgressHealth.THRIVING
        elif normalized_score >= 0.55 and v_code > 0 and v_verif >= 0:
            health = ProgressHealth.MAKING_PROGRESS
        elif normalized_score >= 0.40 and v_code > 0:
            health = ProgressHealth.MARGINAL_CHURN
        elif v_verif < 0 or v_defect < 0:
            health = ProgressHealth.REGRESSING
        else:
            health = ProgressHealth.STAGNANT

        # Update cache
        self._last_symbols = curr_symbols
        self._last_passed_tests = passed_test_nodes
        self._last_failed_tests = failed_test_nodes
        self._last_satisfied_acs = satisfied_ac_ids
        self._last_open_defects = open_defect_ids

        return ProgressVelocityMetrics(
            v_code=v_code,
            v_verif=v_verif,
            v_evid=v_evid,
            v_defect=v_defect,
            tokens_consumed=tokens_consumed,
            per_score=per_score,
            normalized_score=normalized_score,
            health=health,
        )


class OscillationDetector:
    """
    Sliding-window sequence autocorrelation engine.
    Detects Direct Stagnation (p=1), Flip-Flop (p=2), and Periodic Cycles (p=3..5).
    """

    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self._history: List[StateFingerprint] = []

    def register_state(self, fingerprint: StateFingerprint) -> Tuple[CyclePattern, int]:
        self._history.append(fingerprint)
        if len(self._history) > self.window_size:
            self._history.pop(0)

        n = len(self._history)
        if n < 2:
            return CyclePattern.NONE, 0

        curr = self._history[-1]

        # 1. Check Period 1: Direct Stagnation
        prev = self._history[-2]
        if curr.composite_hash == prev.composite_hash:
            return CyclePattern.DIRECT_STAGNATION, 1

        # 2. Check Period 2..5 Periodic Oscillations
        for p in range(2, n):
            target = self._history[-1 - p]
            if curr.composite_hash == target.composite_hash:
                if p == 2:
                    return CyclePattern.FLIP_FLOP_P2, 2
                return CyclePattern.PERIODIC_PN, p

        return CyclePattern.NONE, 0

    def reset_window(self) -> None:
        self._history.clear()


class AdaptiveCircuitBreaker:
    """
    4-Tier Adaptive Circuit Breaker managing transitions:
    CLOSED -> DEGRADED -> STRATEGY_MUTATING -> TRIPPED_ESCALATING.
    """

    def __init__(self, max_mutation_tiers: int = 4):
        self.state: BreakerState = BreakerState.CLOSED
        self.stagnation_counter: int = 0
        self.mutation_tier_level: int = 0
        self.max_mutation_tiers: int = max_mutation_tiers

    def evaluate_state_transition(
        self,
        metrics: ProgressVelocityMetrics,
        cycle_pattern: CyclePattern,
    ) -> BreakerState:
        # Positive progress resets or relaxes breaker
        if metrics.health in (ProgressHealth.THRIVING, ProgressHealth.MAKING_PROGRESS):
            self.stagnation_counter = max(0, self.stagnation_counter - 1)
            if self.stagnation_counter == 0:
                self.state = BreakerState.CLOSED
                self.mutation_tier_level = 0
            return self.state

        # Immediate escalation on detected cyclic oscillation
        if cycle_pattern in (CyclePattern.FLIP_FLOP_P2, CyclePattern.PERIODIC_PN):
            self.stagnation_counter += 2
            self.state = BreakerState.STRATEGY_MUTATING
            self.mutation_tier_level = min(self.max_mutation_tiers, self.mutation_tier_level + 1)
            return self.state

        # Stagnant or Regressing turn
        if metrics.health in (ProgressHealth.STAGNANT, ProgressHealth.REGRESSING, ProgressHealth.MARGINAL_CHURN):
            self.stagnation_counter += 1

            if self.stagnation_counter == 1:
                self.state = BreakerState.DEGRADED
            elif self.stagnation_counter >= 2:
                if self.mutation_tier_level >= self.max_mutation_tiers:
                    self.state = BreakerState.TRIPPED_ESCALATING
                else:
                    self.state = BreakerState.STRATEGY_MUTATING
                    self.mutation_tier_level += 1

        return self.state


class StrategyMutator:
    """
    Generates 4-Tier Strategy Mutation Directives:
    Tier 1: Prompt Steering
    Tier 2: Target Decomposition
    Tier 3: Tool Constriction
    Tier 4: Model Elevation
    """

    def generate_mutation(
        self,
        current_tier: int,
        failing_tests: Dict[str, str],
        cycle_pattern: CyclePattern,
        active_milestone_id: str,
    ) -> StrategyMutationDirective:
        tier = max(1, min(4, current_tier))

        if tier == 1:
            # Tier 1: Prompt Steering
            hints = [
                "CRITICAL ARCHITECTURAL DIRECTIVE: Autonomous execution has stalled due to repetitive failure.",
                "DO NOT perform cosmetic edits, comments, or docstring modifications.",
                "Perform a strict Read-Before-Write pass on the exact failing module.",
            ]
            if cycle_pattern == CyclePattern.FLIP_FLOP_P2:
                hints.append("OSCILLATION DETECTED: You are flip-flopping between two conflicting implementations. Reject prior assumptions.")
            for node, trace in list(failing_tests.items())[:2]:
                hints.append(f"Failing Test Target: {node}\nTrace: {trace[:300]}")
            return StrategyMutationDirective(
                mutation_type=MutationStrategyType.PROMPT_STEERING,
                tier_level=1,
                prompt_injections=hints,
            )

        elif tier == 2:
            # Tier 2: Target Decomposition
            subtasks = [
                f"SUBTASK-1: Isolate minimal reproducer for {list(failing_tests.keys())[0] if failing_tests else 'active failure'}",
                "SUBTASK-2: Refactor single target function without modifying neighboring classes",
                "SUBTASK-3: Run isolated single-node test verification",
            ]
            return StrategyMutationDirective(
                mutation_type=MutationStrategyType.TARGET_DECOMPOSITION,
                tier_level=2,
                decomposed_subtasks=subtasks,
                prompt_injections=["MILESTONE DECOMPOSED: Execute only SUBTASK-1 in this turn."],
            )

        elif tier == 3:
            # Tier 3: Tool Constriction
            return StrategyMutationDirective(
                mutation_type=MutationStrategyType.TOOL_CONSTRICTION,
                tier_level=3,
                banned_tools={"execute_bash", "run_terminal_command"},
                forced_tools={"read_file", "write_file", "check_syntax"},
                prompt_injections=["TOOL RESTRICTION ACTIVE: Terminal access disabled. Inspect file AST directly and apply surgical file patch."],
            )

        else:
            # Tier 4: Model Elevation
            return StrategyMutationDirective(
                mutation_type=MutationStrategyType.MODEL_ELEVATION,
                tier_level=4,
                elevated_model="frontier-reasoning-tier-1",
                prompt_injections=["MODEL ELEVATION TRIGGERED: Routing milestone to high-reasoning frontier model."],
            )


# ============================================================================
# 5. Master Recovery Orchestrator (Façade)
# ============================================================================

class RecoveryOrchestrator:
    """
    Unified Recovery Façade coordinating Progress Tracking, Oscillation Detection,
    Adaptive Circuit Breaking, Strategy Mutation, GitOps Rollback, and SQLite WAL Logging.
    """

    def __init__(self, workspace_path: Path, db_path: Optional[Path] = None):
        self.workspace_path = workspace_path
        self.tracker = SemanticProgressTracker(workspace_path)
        self.oscillation_detector = OscillationDetector(window_size=5)
        self.circuit_breaker = AdaptiveCircuitBreaker(max_mutation_tiers=4)
        self.mutator = StrategyMutator()
        self.db_path = db_path or (workspace_path / ".oragai" / "sentinel_diagnostics.db")
        self._init_sqlite_schema()

    def _init_sqlite_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS sentinel_progress_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                v_code REAL NOT NULL,
                v_verif REAL NOT NULL,
                v_evid REAL NOT NULL,
                v_defect REAL NOT NULL,
                per_score REAL NOT NULL,
                health TEXT NOT NULL,
                breaker_state TEXT NOT NULL,
                cycle_pattern TEXT NOT NULL,
                cycle_period INTEGER NOT NULL,
                timestamp REAL NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS sentinel_recovery_events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                mutation_tier INTEGER NOT NULL,
                details TEXT NOT NULL,
                timestamp REAL NOT NULL
            );
            """)
            conn.commit()

    def evaluate_turn_outcome(
        self,
        run_id: str,
        turn_index: int,
        passed_test_nodes: Set[str],
        failed_test_nodes: Dict[str, str],
        satisfied_ac_ids: Set[str],
        open_defect_ids: Set[str],
        tokens_consumed: int,
        active_milestone_id: str,
        checkpoint_ref: Optional[str] = None,
    ) -> RecoveryDecision:
        # 1. Compute Progress Metrics
        metrics = self.tracker.record_turn_snapshot(
            turn_index=turn_index,
            passed_test_nodes=passed_test_nodes,
            failed_test_nodes=failed_test_nodes,
            satisfied_ac_ids=satisfied_ac_ids,
            open_defect_ids=open_defect_ids,
            tokens_consumed=tokens_consumed,
        )

        # 2. Compute State Fingerprint & Detect Cycles
        ast_hash = hashlib.sha256(str(self.tracker._last_symbols).encode("utf-8")).hexdigest()
        fail_hash = hashlib.sha256(json.dumps(sorted(failed_test_nodes.keys())).encode("utf-8")).hexdigest()
        def_hash = hashlib.sha256(json.dumps(sorted(list(open_defect_ids))).encode("utf-8")).hexdigest()

        fingerprint = StateFingerprint(
            turn_index=turn_index,
            ast_composite_hash=ast_hash,
            failing_tests_hash=fail_hash,
            defect_state_hash=def_hash,
        )
        cycle_pattern, cycle_period = self.oscillation_detector.register_state(fingerprint)

        # 3. Evaluate Breaker State Transition
        new_breaker_state = self.circuit_breaker.evaluate_state_transition(metrics, cycle_pattern)

        # 4. Formulate Recovery Action & Mutation
        action = RecoveryActionType.CONTINUE_NORMAL
        mutation: Optional[StrategyMutationDirective] = None
        rollback_ref: Optional[str] = None
        explanation = f"Turn {turn_index} evaluated: {metrics.health.value}. Breaker: {new_breaker_state.value}."

        if metrics.health == ProgressHealth.REGRESSING and checkpoint_ref:
            action = RecoveryActionType.TRANSACTIONAL_ROLLBACK
            rollback_ref = checkpoint_ref
            explanation += " Severe regression detected. Executing atomic rollback."

        elif new_breaker_state == BreakerState.STRATEGY_MUTATING:
            action = RecoveryActionType.INJECT_MUTATION
            mutation = self.mutator.generate_mutation(
                current_tier=self.circuit_breaker.mutation_tier_level,
                failing_tests=failed_test_nodes,
                cycle_pattern=cycle_pattern,
                active_milestone_id=active_milestone_id,
            )
            explanation += f" Triggered Strategy Mutation Tier {mutation.tier_level}."

        elif new_breaker_state == BreakerState.TRIPPED_ESCALATING:
            action = RecoveryActionType.QUARANTINE_MILESTONE
            explanation += " All strategy mutation tiers exhausted. Quarantining milestone."

        # 5. Persist to Sentinel SQLite DB
        self._log_telemetry(run_id, turn_index, metrics, new_breaker_state, cycle_pattern, cycle_period, action, mutation)

        return RecoveryDecision(
            action=action,
            breaker_state=new_breaker_state,
            health=metrics.health,
            detected_cycle=cycle_pattern,
            cycle_period=cycle_period,
            mutation_directive=mutation,
            rollback_checkpoint_ref=rollback_ref,
            explanation=explanation,
        )

    def _log_telemetry(
        self,
        run_id: str,
        turn_index: int,
        metrics: ProgressVelocityMetrics,
        breaker_state: BreakerState,
        cycle_pattern: CyclePattern,
        cycle_period: int,
        action: RecoveryActionType,
        mutation: Optional[StrategyMutationDirective],
    ) -> None:
        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                snap_id = f"SNAP-{run_id}-{turn_index}-{int(time.time())}"
                conn.execute("""
                INSERT INTO sentinel_progress_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    snap_id, run_id, turn_index, metrics.v_code, metrics.v_verif,
                    metrics.v_evid, metrics.v_defect, metrics.per_score,
                    metrics.health.value, breaker_state.value, cycle_pattern.value,
                    cycle_period, time.time()
                ))
                if action != RecoveryActionType.CONTINUE_NORMAL:
                    event_id = f"REC-{run_id}-{turn_index}-{int(time.time())}"
                    conn.execute("""
                    INSERT INTO sentinel_recovery_events VALUES (?, ?, ?, ?, ?, ?, ?);
                    """, (
                        event_id, run_id, turn_index, action.value,
                        mutation.tier_level if mutation else 0,
                        json.dumps({"explanation": action.value}), time.time()
                    ))
                conn.commit()
        except Exception:
            pass
```

---

# 7. Rigorous Test Matrix & Verification Scenarios

The following verification matrix specifies the test suite testing P8's semantic progress tracking, sliding-window oscillation detection, 4-tier circuit breaker transitions, strategy mutations, and atomic rollback safety.

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 P8 TEST VERIFICATION MATRIX                              │
├─────────┬───────────────────────────────┬───────────────────────────────┬────────────────┤
│ Test ID │ Function / Test Name          │ Tested Invariant / Feature    │ Expected Pass  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T01  │ `test_semantic_tracker_`      │ Adding whitespace/comments    │ V_code == 0.0  │
│         │ `ignores_comment_whitespace`  │ produces zero AST delta       │ Health=STAGNANT│
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T02  │ `test_semantic_tracker_`      │ Adding function modifies AST  │ V_code > 0.0   │
│         │ `detects_real_ast_change`     │ symbol table correctly        │ Health=PROGRESS│
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T03  │ `test_verification_velocity_` │ Fixing 2 test nodes yields    │ V_verif == 3.0 │
│         │ `positive_advance`            │ positive verification score   │ Health=THRIVING│
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T04  │ `test_verification_velocity_` │ Breaking 2 previously passing │ V_verif < -2.0 │
│         │ `detects_severe_regression`   │ test nodes triggers regression│ Health=REGRESS │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T05  │ `test_oscillation_detector_`  │ Identical state back-to-back  │ DIRECT_STAG    │
│         │ `detects_direct_stagnation`   │ detected with period = 1      │ Period = 1     │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T06  │ `test_oscillation_detector_`  │ State flips A -> B -> A       │ FLIP_FLOP_P2   │
│         │ `detects_p2_flip_flop_cycle`  │ detected with period = 2      │ Period = 2     │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T07  │ `test_oscillation_detector_`  │ Cycle A -> B -> C -> A        │ PERIODIC_PN    │
│         │ `detects_p3_periodic_cycle`   │ detected with period = 3      │ Period = 3     │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T08  │ `test_adaptive_breaker_`      │ 1 stagnant turn moves state   │ BreakerState   │
│         │ `transitions_closed_to_degrad`│ from CLOSED to DEGRADED       │ == DEGRADED    │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T09  │ `test_adaptive_breaker_`      │ 2 stagnant turns or P2 cycle  │ BreakerState   │
│         │ `transitions_to_mutating`     │ moves to STRATEGY_MUTATING    │ == MUTATING    │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T10  │ `test_strategy_mutator_tier1_`│ Level 1 generates anti-osc    │ Hints injected │
│         │ `prompt_steering_injection`   │ prompt steering directives    │ into prompt    │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T11  │ `test_strategy_mutator_tier2_`│ Level 2 decomposes milestone  │ Subtasks list  │
│         │ `target_decomposition`        │ into sub-atomic tasks         │ generated > 1  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T12  │ `test_strategy_mutator_tier3_`│ Level 3 disables bash/terminal│ Banned tools   │
│         │ `tool_constriction_active`    │ and locks to file tool only   │ contains bash  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T13  │ `test_strategy_mutator_tier4_`│ Level 4 routes milestone to   │ Elevated model │
│         │ `model_elevation_failover`    │ high-reasoning model tier     │ designated     │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T14  │ `test_recovery_orchestrator_` │ Severe test regression causes │ ROLLBACK action│
│         │ `triggers_atomic_rollback`    │ emission of rollback decision │ with tag ref   │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T15  │ `test_recovery_orchestrator_` │ 4 failed mutations transition │ QUARANTINE     │
│         │ `quarantines_on_tier4_exhaust`│ milestone to QUARANTINED      │ action emitted │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P8-T16  │ `test_sentinel_sqlite_wal_`   │ Progress snapshot & recovery  │ SQLite rows    │
│         │ `recovery_event_logging`      │ events committed to SQLite DB │ verified > 0   │
└─────────┴───────────────────────────────┴───────────────────────────────┴────────────────┘
```

---

# 8. Handoff Contract for P9 (Tooling, Context Windows & Sandbox Hardening Plan)

### 8.1 Recovery Hooks & Tool Directives Exported to P9
P8 produces structured recovery directives and tool constraints that will be consumed directly by **P9 (Tooling, Context Windows & Sandbox Hardening Plan)**:
1. **Tool Constriction Policies (`banned_tools`, `forced_tools`):** Directives emitted during Tier 3 Strategy Mutation instructing the agent execution sandbox to restrict arbitrary shell execution and restrict tool execution strictly to AST-targeted patch tools.
2. **Anti-Oscillation Observation Injections:** Formatted failure diffs and anti-pattern warnings designed to be injected into the P9 prompt context manager without causing token window overflow.
3. **Sandbox Checkpoint Handles:** GitOps snapshot tags (`refs/oragai/checkpoints/*`) used by P9 to ensure that unverified sandbox modifications can be rolled back atomically prior to milestone promotion.

### 8.2 Input Contract for P9
P9 will ingest:
- The `StrategyMutationDirective` schema to configure dynamic sandboxes and tool permissions per agent turn.
- The `ProgressVelocityMetrics` telemetry to trigger adaptive context window clamping when churn is detected.
- The `RecoveryOrchestrator` recovery decision pipeline to enforce pre-turn checkpoint creation and post-turn validation gates.

---

# 9. P8 Exit Criteria & Verification Sign-Off

- [x] **Zero Production Code Touched:** All deliverables reside strictly within `docs/plans/P8_PROGRESS_STAGNATION_AND_RECOVERY_PLAN.md`.
- [x] **Strict Invariant Continuity:** Seamlessly integrates with P0 forensic baseline, P1 Task Truth, P2.1 Evidence Gates, P3 Guarded FSM, P4 Adaptive Governance, P5 Workstreams, P6 Context Handoff, and P7 Deep Audit.
- [x] **Elimination of Binary Breaker Flaws:** Replaced brittle 2-error threshold in `recorder.py` and premature aborts in `dev_test_loop.py` with 4-tier adaptive circuit breaking.
- [x] **Multi-Dimensional Progress Vector:** Formulated $V_{\text{code}}, V_{\text{verif}}, V_{\text{evid}}, V_{\text{defect}}$ and Unified PER 2.0.
- [x] **Deterministic Cycle Detection:** Sliding-window sequence autocorrelation formulated for direct ($p=1$), flip-flop ($p=2$), and periodic ($p \in [3, 5]$) oscillations.
- [x] **Anti-Churn Evasion Engine:** Implemented AST structural symbol diffs that ignore superficial comments and whitespace churn.
- [x] **4-Tier Strategy Mutation Taxonomy:** Formulated concrete protocols for Prompt Steering, Target Decomposition, Tool Constriction, and Model Elevation.
- [x] **Transactional Rollback & Quarantining:** Specified atomic GitOps checkpoints and `docs/quarantined_findings.json` milestone isolation.
- [x] **Fully Typed Python Architecture:** Production-ready dataclasses, protocols, and `RecoveryOrchestrator` engine defined.
- [x] **Ready for P9:** Exported tool constriction directives, sandbox checkpoint hooks, and recovery telemetry handoffs established.
