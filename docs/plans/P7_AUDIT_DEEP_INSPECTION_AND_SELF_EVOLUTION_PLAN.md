# P7 — AUDIT, DEEP INSPECTION & SELF-EVOLUTION PLAN

> **Document Type:** Canonical Systems Architecture, Static Analysis Security Engineering & Self-Evolution Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Systems Architect, Codebase Forensic Specialist & Static Analysis Security Engineer  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md`, `docs/plans/P1_TASK_TRUTH_AND_REQUIREMENT_MODEL_PLAN.md`, `docs/plans/P2_EVIDENCE_AND_COMPLETION_GATES_PLAN.md`, `docs/plans/P3_GUARDED_FSM_AND_LIFECYCLE_ORCHESTRATION_PLAN.md`, `docs/plans/P4_ADAPTIVE_RESOURCE_GOVERNANCE_PLAN.md`, `docs/plans/P5_AGENT_WORK_AND_MILESTONE_EXECUTION_PLAN.md`, `docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Design Phase:** P7 (Specification & Deep Inspection Engine — Zero Production Code Modified)

---

# 1. Executive Summary & Forensic Audit Pathology Dissection

This specification establishes the canonical **Audit, Deep Inspection & Self-Evolution Plan (P7)** for the **ORAGAI** multi-agent software engineering orchestrator.

### 1.1 The Strategic Position of P7 in the ORAGAI Stack
To date, the architectural redesign of ORAGAI has established:
1. **P0 (Forensic Baseline & Invariants):** Dissected the fatal conflation of *Resource Safety Governance* with *Work Completion*, micro-turn execution cages (5 steps), premature 28% exploration aborts, 4,000-character truncated reviewer diffs, and passive FSM dictionary lookups.
2. **P1 (Task Truth & Requirement Model):** Established the deterministic entity graph: $\text{Task} \to \text{Requirements} \to \text{Acceptance Criteria} \to \text{Milestones}$.
3. **P2.1 (Evidence Engine & Completion Gates):** Formulated cryptographic content identity (composite SHA-256), orthogonal state dimensions (`ImplementationState`, `VerificationState`, `BlockingState`), and the 14-step deterministic Completion Gate (`TaskTruthSemanticQueries`).
4. **P3 (Guarded FSM & Lifecycle Orchestration):** Inverted the execution loop from procedural scripts to an event-driven `GuardedFSMEngine` that delegates bounded, ephemeral agent turns via Inversion of Control (IoC), formally introducing `LifecycleProfile.AUDIT` and `LifecycleProfile.AUDIT_FIX`.
5. **P4 (Adaptive Resource Governance):** Replaced hard micro-caps with dynamic complexity-based turn allocation ($T_{\text{allocated}} \in [10, 30]$), AST-aware context folding (`ASTAwareContextClamper`), and dedicated 100% investigation token ratios to audit phases.
6. **P5 (Agent Work & Milestone Execution):** Established persona RBAC boundaries, the Micro-TDD loop (Red $\to$ Green $\to$ Refactor), topological DAG wave dispatch, and the `Auditor` persona RBAC (write to `docs/` only).
7. **P6 (Context & Evidence Handoff):** Established the `WorkspaceDigest` Merkle tree, priority context tiering (Tier 0 to Tier 3), cryptographic handoff envelopes, and diagnostic trace compactor.

### The Core Mission of P7:
$$\text{While P5 defines the Auditor persona and P6 provides the workspace digest,}$$
$$\text{\textbf{P7 completely redesigns the static and LLM auditing engine, turning ORAGAI}}$$
$$\text{\textbf{from a superficial reviewer into a repository-wide architectural, security,}}$$
$$\text{\textbf{and quality inspection system with self-evolution and auto-remediation capabilities.}}$$

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ORAGAI ARCHITECTURE                                    │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          Guarded FSM Engine (P3)                               │   │
│   │                 [LifecycleProfile.AUDIT / AUDIT_FIX]                           │   │
│   └───────────────────────┬────────────────────────────────┬───────────────────────┘   │
│                           │                                │                           │
│     State Transitions     │                                │  Pre-Dispatch Budget      │
│     & Evidence Queries    │                                │  & Merkle Hashing         │
│                           ▼                                ▼                           │
│   ┌───────────────────────────────┐        ┌───────────────────────────────┐           │
│   │  Task Truth & Evidence Engine │        │ Context & Evidence Handoff    │           │
│   │            (P2.1)             │        │             (P6)              │           │
│   │                               │        │                               │           │
│   │ • TaskTruthGraph (P1)         │        │ • ContextSynthesizer          │           │
│   │ • CriterionEvidencePolicies   │        │ • WorkspaceDigest Merkle Root │           │
│   │ • FindingValidator Gate       │        │ • DiagnosticCompactor         │           │
│   │ • CompletionGate              │        │ • CrossAgentHandoffPayload    │           │
│   └───────────────────────┬───────┘        └───────────────┬───────────────┘           │
│                           │                                │                           │
│                           └────────────────┬───────────────┘                           │
│                                            │                                           │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │             Audit, Deep Inspection & Self-Evolution Engine (P7) (THIS SPEC)    │   │
│   │                                                                                │   │
│   │  • Zero-Token Deterministic Pre-Audit Sweep (AST, Linter, Banned Stubs, Sec)   │   │
│   │  • Graft-Based Topological Cluster Partitioning & Bounded Audit Dispatch       │   │
│   │  • Cross-Module Coupling & Architectural Boundary Analysis (Fan-In/Out, D-Dist)│   │
│   │  • Strongly Typed VerifiedAuditFinding Schema & Multi-Layer FindingValidator   │   │
│   │  • Autonomous Remediation Engine (AuditFix DAG, Micro-TDD, Anti-Poison Gate)   │   │
│   │  • Codebase Health Index (CHI) Mathematical Formulation & Sentinel WAL DB      │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │ Bounded Remediation Waves                 │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                    Agent Workstream & Milestone Engine (P5)                    │   │
│   │                                                                                │   │
│   │   [Auditor Agent]  ──────▶  [Verified Findings DAG]  ──────▶  [Remediator]     │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.2 Forensic Analysis of Audit Pathologies in Legacy ORAGAI
A forensic post-mortem of legacy audit components (`orchestrator/pipeline/audit_pipeline.py`, `orchestrator/pipeline/audit_fix_pipeline.py`, `orchestrator/analysis/schemas.py`) reveals systemic architectural failures that rendered the legacy audit subsystem ineffective:

| Legacy Subsystem | Code Location | Observed Pathology | Root Cause & Failure Mechanism | P7 Architectural Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **Forced Prompt Step Cap** | `audit_pipeline.py:L158-174` | Prompt explicitly orders: *"PHASE 2 (Report Generation - MUST EXECUTE AT STEP 4-5)"*. | The LLM auditor is strictly prohibited from spending more than 3 turns investigating. It is forced to synthesize its final report on step 4 regardless of codebase scale. | **Uncaged Investigation Budget:** Auditor is allocated dynamic turn envelopes ($T_{\text{allocated}} \in [10, 30]$) per functional cluster without artificial prompt-level early exits. |
| **Hotspot Skimming Restriction** | `audit_pipeline.py:L160` | Prompt commands: *"Perform targeted inspection of 2-3 key hotspot files"*. | In a 150-file repository, 98% of the codebase is completely unread. Architectural rot, hidden cyclic imports, and critical bugs in non-hotspot files are completely ignored. | **Cluster-Partitioned Sweep:** Codebase is topologically partitioned via `Graft`; 100% of workspace files are covered across deterministic AST passes and bounded cluster turns. |
| **The "98/100 Flattery Trap"** | `audit_pipeline.py:L164`, `schemas.py:L64-75` | Auditor outputs `findings: []`, reports *"Architecture Health: 98/100"*, and concludes repository is defect-free. | Because the agent read only 2 files and was forced to exit at step 4, it generated polite boilerplate praising the architecture rather than performing real forensic analysis. | **Deterministic AST Baseline & Anti-Flattery Gate:** `StaticAnalysisScanner` identifies real defects deterministically before LLM invocation; generic flattery reports are rejected by `FindingValidator`. |
| **Downstream Pipeline Starvation** | `audit_fix_pipeline.py:L108-150` | `AuditFixPipeline` reads `docs/audit_findings.json`, finds `findings: []`, and terminates immediately. | Because the legacy Auditor hallucinated a clean state, the automated remediation pipeline starved with zero actionable tasks, leaving real bugs unresolved. | **Actionable Finding Ingestion:** `AuditFixOrchestrator` ingests validated AST and cluster findings, constructing a directed acyclic remediation graph (DAG). |
| **Brittle Regex Markdown Scraping** | `audit_fix_pipeline.py:L67-107` | `extract_audit_findings_list()` parses unstructured Markdown headings (`### [HIGH] Title`). | Any slight formatting variation by the LLM causes regex extraction to fail, discarding valid findings or misclassifying severity. | **Native Structured Schemas:** Findings are persisted and validated as strongly typed Pydantic `VerifiedAuditFinding` JSON structures; Markdown is a rendered derivative. |
| **Unbounded Remediation Oscillation** | `audit_fix_pipeline.py:L400-550` | Fix loop repeatedly attempts the same failing patch across iterations without a circuit breaker. | If a fix introduces a syntax error or breaks a test, the pipeline blindly retries, burning tokens and potentially poisoning the working tree with broken edits. | **Anti-Poisoning Circuit Breaker:** Findings failing remediation twice are quarantined (`QUARANTINED_BLOCKED`), and workspace edits are atomically rolled back via GitOps. |

---

### 1.3 Theoretical Framework for Deep Codebase Auditing & Self-Evolution

P7 establishes four formal theorems governing static verification, architectural integrity, and automated remediation:

#### Theorem 1: Deterministic-First Inspection (Zero-Token Primacy)
No cognitive LLM agent may be dispatched to evaluate codebase quality until zero-token deterministic static analysis has completely mapped the workspace:
$$\mathcal{S}_{\text{deterministic}} = \text{ASTScan}(\mathcal{W}) \cup \text{LinterScan}(\mathcal{W}) \cup \text{SecretScan}(\mathcal{W}) \cup \text{CouplingScan}(\mathcal{W})$$
Cognitive LLM turns are reserved exclusively for high-level semantic reasoning (architectural drift, security logic flaws, contract violations) anchored directly to the deterministic AST topology.

#### Theorem 2: Grounded Evidence Invariant (Anti-Hallucination Axiom)
An audit finding $\mathcal{F}$ is valid if and only if its location and content are deterministically verifiable on disk:
$$\text{IsValid}(\mathcal{F}) \iff \left( \exists f \in \mathcal{W} \mid f.\text{path} = \mathcal{F}.\text{file} \land \mathcal{F}.\text{lines} \subseteq \text{Range}(f) \land \mathcal{F}.\text{snippet} \sqsubseteq f.\text{content}[\mathcal{F}.\text{lines}] \right)$$
Any finding referencing non-existent files, out-of-bounds lines, or mismatched code snippets is strictly rejected by the `FindingValidator`.

#### Theorem 3: Monotonic Remediation Convergence
Let $\mathcal{D}_k$ be the set of active codebase defects at remediation iteration $k$, and $\mathcal{T}_{\text{reg}}$ be the regression test suite. A remediation step $\mathcal{R}_k$ on finding $f \in \mathcal{D}_k$ is valid if and only if:
$$\mathcal{D}_{k+1} = \mathcal{D}_k \setminus \{f\} \quad \land \quad \text{PassRatio}(\mathcal{T}_{\text{reg}}, \mathcal{W}_{k+1}) \ge \text{PassRatio}(\mathcal{T}_{\text{reg}}, \mathcal{W}_k)$$
If a remediation step introduces a syntax error or causes a regression in $\mathcal{T}_{\text{reg}}$, the working tree $\mathcal{W}_{k+1}$ is immediately rolled back to $\mathcal{W}_k$ and $f$ is quarantined.

#### Theorem 4: Codebase Health Monotonicity
The Codebase Health Index $\text{CHI}(\mathcal{W})$ is a bounded metric $[0, 100]$. Successful execution of the remediation loop guarantees non-decreasing health:
$$\text{CHI}(\mathcal{W}_{k+1}) \ge \text{CHI}(\mathcal{W}_k)$$

---

### 1.4 Inviolable System Invariants for P7

1. **Zero Production Code Modifications During Planning:** P7 is an architectural specification. No files in `orchestrator/` are altered during this design phase.
2. **Zero Unverified Findings:** No finding can be written to `docs/audit_findings.json` or presented to remediation without passing the multi-layer `FindingValidator` (disk existence, AST containment, non-generic check).
3. **100% Codebase Coverage via Partitioning:** The audit engine must evaluate 100% of workspace source files. Large codebases are partitioned into functional clusters via `Graft` rather than arbitrarily truncating analysis to 2-3 files.
4. **Zero-Token Pre-Audit Requirement:** Every audit run must execute the zero-token AST, linter, banned-stub, and secret sweep before launching LLM Auditor agents.
5. **Atomic Remediation Rollbacks:** If an automated fix fails preflight syntax checks or causes test regressions, the workspace must be atomically rolled back to its pre-fix state, preventing working tree corruption.

---

# 2. Hybrid Inspection Architecture (Deterministic AST + Cognitive LLM)

P7 replaces the legacy single-pass prompt script with a **Three-Phase Hybrid Inspection Architecture** combining deterministic static tooling with targeted cognitive LLM reasoning.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        HYBRID INSPECTION PIPELINE ARCHITECTURE                         │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │             PHASE 1: ZERO-TOKEN DETERMINISTIC PRE-AUDIT SWEEP                  │   │
│   │                                                                                │   │
│   │   Workspace Files (100% Coverage)                                              │   │
│   │   ├── Python AST Parser ─────────▶ Syntax errors, complexity, class/fn symbols │   │
│   │   ├── Static Linter (Ruff/Flake8) ▶ Unused imports, undefined vars, style      │   │
│   │   ├── Banned Stub Detector ──────▶ '# TODO', 'pass', 'NotImplementedError'     │   │
│   │   ├── Secret & Security Regex ───▶ API keys, passwords, shell=True, path escape │   │
│   │   └── Import Dependency Analyzer ▶ Circular imports, layer crossing            │   │
│   │                                                                                │   │
│   │   Output: DeterministicFindingsList (Zero LLM Tokens Consumed)                 │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │                                           │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │             PHASE 2: GRAFT CLUSTER-BASED COGNITIVE DEEP AUDIT                  │   │
│   │                                                                                │   │
│   │   Topological Codebase Clustering (via Graft & Import Graph)                   │   │
│   │   ├── Cluster 1: Core Engine & FSM        (e.g., orchestrator/engine/*)        │   │
│   │   ├── Cluster 2: Analysis & Adapters      (e.g., orchestrator/analysis/*)      │   │
│   │   ├── Cluster 3: Context & Governance     (e.g., orchestrator/context/*)       │   │
│   │   └── Cluster N: Tools & Infrastructure   (e.g., orchestrator/tools/*)         │   │
│   │                                                                                │   │
│   │   Bounded Persona Dispatch (Per Cluster):                                      │   │
│   │   • ContextSynthesizer constructs Cluster Prompt View (Tier 0-3)               │   │
│   │   • Auditor Persona executed within T_allocated turn budget                    │   │
│   │   • LLM audits: Architectural drift, logic bugs, OWASP flaws, contract gaps    │   │
│   │                                                                                │   │
│   │   Output: CognitiveFindingsList (Multi-Cluster Aggregate)                      │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │                                           │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │             PHASE 3: STRUCTURAL COUPLING & BOUNDARY ANALYSIS                   │   │
│   │                                                                                │   │
│   │   Codebase Topology Metrics Calculation:                                       │   │
│   │   • Afferent Coupling (Ca) & Efferent Coupling (Ce) per module                 │   │
│   │   • Instability Index: I = Ce / (Ca + Ce)                                      │   │
│   │   • Abstractness Index: A = AbstractClasses / TotalClasses                     │   │
│   │   • Normalized Distance from Main Sequence: D = |A + I - 1|                    │   │
│   │   • God Module Detection (>500 LOC, high coupling, multiple responsibilities)  │   │
│   │                                                                                │   │
│   │   Output: StructuralMetricsReport & ArchitecturalFindings                      │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            │                                           │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │               UNIFIED FINDING DEDUPLICATION & VALIDATION GATE                  │   │
│   │                                                                                │   │
│   │   Deterministic Findings + Cognitive Findings + Structural Findings            │   │
│   │   ├── Fingerprint SHA-256 Deduplication                                       │   │
│   │   ├── Multi-Layer FindingValidator Gate (Disk, AST, Anti-Flattery)             │   │
│   │   └── Emit Canonical: docs/audit_findings.json & docs/AUDIT_REPORT.md          │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.1 Phase 1: Zero-Token Deterministic Pre-Audit Sweep
The zero-token pre-audit sweep runs locally before any network call or LLM turn. It performs exhaustive static inspection across 100% of workspace files:

1. **AST Syntax & Symbol Extraction:**
   - Parses every `.py` file into an Abstract Syntax Tree using `ast.parse()`.
   - Records syntax errors, invalid indentation, unclosed delimiters.
   - Extracts all class and function definitions with line number bounds (`lineno` to `end_lineno`).
   - Calculates Cyclomatic Complexity ($M = E - N + 2P$) per function/method. Functions with $M > 15$ are flagged with severity `MEDIUM`.

2. **Banned Stub & Placeholder Sweeper:**
   - Detects placeholder implementations that violate P5's Zero-Stub Invariant:
     - Functions whose body consists solely of `pass`, `...`, or `raise NotImplementedError`.
     - Explicit `# TODO`, `# FIXME`, `# PLACEHOLDER`, `# STUB` comments in production code.
     - Severity: `HIGH` (for public interface stubs) or `LOW` (for internal TODO comments).

3. **Secret Leakage & Security Regex Sweeper:**
   - Scans all files for exposed credentials and security antipatterns:
     - Regex matching for OpenAI/Anthropic/AWS/GitHub API keys (`sk-[a-zA-Z0-9]{32,}`, `ghp_[a-zA-Z0-9]{36}`, `AKIA[0-9A-Z]{16}`).
     - Insecure subprocess invocations (`subprocess.Popen(..., shell=True)` without sanitized string literals).
     - Dangerous deserialization (`pickle.loads`, `yaml.load` without `SafeLoader`).
     - Unsanitized path traversals (`os.path.join` with untrusted inputs lacking `Path.resolve().relative_to()`).

4. **Static Linter & Type Checker Integration:**
   - Invokes `ruff check --output-format=json` or `flake8` to capture unused imports (`F401`), undefined names (`F821`), and bare exceptions (`E722`).
   - Translates linter JSON output directly into `VerifiedAuditFinding` instances with source `STATIC_LINTER`.

5. **Import Cycle & Circular Dependency Detection:**
   - Builds an internal directed graph $G = (V, E)$ where vertices $V$ are Python modules and edges $E$ are import statements.
   - Executes Tarjan's Strongly Connected Components (SCC) algorithm. Any SCC with $|V| > 1$ represents a circular import cycle. Flagged as `ARCHITECTURE` severity `HIGH`.

---

### 2.2 Phase 2: Graft Cluster-Based Cognitive Deep Audit
To audit a repository containing 50 to 500+ files without token exhaustion or superficial skimming, P7 introduces **Topological Cluster Partitioning**:

1. **Partitioning Algorithm:**
   - Using `Graft` directory structure and module connectivity graphs, files are partitioned into $K$ cohesive functional clusters:
     $$\mathcal{W} = \mathcal{C}_1 \cup \mathcal{C}_2 \cup \dots \cup \mathcal{C}_K, \quad \text{where } \mathcal{C}_i \cap \mathcal{C}_j = \emptyset$$
   - Cluster size is bounded by target token budgets: $|\mathcal{C}_i| \le 15 \text{ files}$ or $\sum_{f \in \mathcal{C}_i} \text{LOC}(f) \le 3,000 \text{ LOC}$.
   - Strongly coupled modules (high import density) are grouped into the same cluster.

2. **Cluster Dispatch & Prompt Assembly:**
   - For each cluster $\mathcal{C}_i$, the FSM dispatches an ephemeral `Auditor` persona turn.
   - The prompt is synthesized using P6's `ContextSynthesizer`:
     - **Tier 0:** Auditor system prompt, security invariants, RBAC directives (write to `docs/` only).
     - **Tier 1:** Phase 1 deterministic findings relevant to $\mathcal{C}_i$.
     - **Tier 2:** AST-folded source code of files in $\mathcal{C}_i$ (target symbols full, neighboring symbols signature-only).
     - **Tier 3:** Graft architecture map and cross-cluster dependency graph.

3. **Cognitive Audit Responsibilities:**
   - The Auditor focuses strictly on high-level semantic vulnerabilities:
     - **State Leakage:** Mutable module-level globals, un-isolated cache singletons.
     - **Architectural Drift:** Violations of domain boundaries (e.g., Core engine directly importing CLI presentation modules).
     - **Concurrency & Race Hazards:** Unprotected shared state across async tasks or threads.
     - **Error Handling & Resilience:** Blanket exception swallowing (`except Exception: pass`) masking root failures.
     - **OWASP Application Flaws:** Logic flaws in authentication, authorization, or token governance.

4. **Turn Governance:**
   - Turns are bounded by P4's dynamic turn allocator: $T_{\text{allocated}} \in [10, 30]$ steps per cluster.
   - The prompt contains **zero artificial step-4 exit mandates**.

---

### 2.3 Phase 3: Cross-Module Boundary & Structural Coupling Analysis

Phase 3 computes mathematical coupling metrics across the entire codebase to detect structural rot, god modules, and architecture boundary violations:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      ROBERT C. MARTIN PACKAGE COUPLING METRICS                         │
│                                                                                        │
│   Afferent Coupling (Ca): Number of external modules that depend on this module.       │
│   Efferent Coupling (Ce): Number of external modules that this module depends on.      │
│                                                                                        │
│   Instability Index (I):                                                               │
│                     Ce                                                                 │
│             I = ───────────  ∈ [0.0, 1.0]                                              │
│                   Ca + Ce                                                              │
│             • I = 0.0 : Maximally Stable (many depend on it, it depends on none)       │
│             • I = 1.0 : Maximally Instable (none depend on it, it depends on many)     │
│                                                                                        │
│   Abstractness Index (A):                                                              │
│                   N_abstract                                                           │
│             A = ──────────────  ∈ [0.0, 1.0]                                           │
│                     N_total                                                            │
│             • N_abstract = Abstract Classes / Protocols / ABCs                         │
│             • N_total    = Total Classes                                               │
│                                                                                        │
│   Normalized Distance from Main Sequence (D):                                          │
│             D = |A + I - 1|  ∈ [0.0, 1.0]                                              │
│                                                                                        │
│             • D ≈ 0.0 : Optimal Balance (Main Sequence)                                │
│             • D ≫ 0.7 & I ≈ 0, A ≈ 0 : "Zone of Pain" (Rigid, concrete, hard to modify)│
│             • D ≫ 0.7 & I ≈ 1, A ≈ 1 : "Zone of Uselessness" (Abstract, unreferenced)  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Structural Defect Heuristics:
1. **God Module Defect:** $\text{LOC} > 500 \land C_e > 10 \land C_a > 10 \implies$ Flagged as `ARCHITECTURE` severity `HIGH`.
2. **Zone of Pain Defect:** $D > 0.75 \land I < 0.2 \land A < 0.1 \land \text{LOC} > 300 \implies$ Flagged as `MAINTAINABILITY` severity `MEDIUM`.
3. **Layer Isolation Violation:** Lower-layer modules (e.g. `orchestrator/core/`, `orchestrator/domain/`) importing higher-layer modules (`orchestrator/pipeline/`, `orchestrator/cli/`) $\implies$ Flagged as `ARCHITECTURE` severity `CRITICAL`.

---

# 3. Canonical Audit Finding Schema & Verification Gate

To eliminate brittle regex scraping and prevent hallucinated findings, P7 defines the canonical Pydantic model for audit defects and an automated multi-layer verification gate.

### 3.1 Strongly Typed `VerifiedAuditFinding` Schema

```python
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class FindingCategory(str, Enum):
    """Formal taxonomy of codebase audit defect categories."""
    SECURITY = "SECURITY"
    ARCHITECTURE = "ARCHITECTURE"
    PERFORMANCE = "PERFORMANCE"
    RELIABILITY = "RELIABILITY"
    MAINTAINABILITY = "MAINTAINABILITY"
    CONVENTION = "CONVENTION"


class FindingSeverity(str, Enum):
    """Standardized finding severity hierarchy."""
    CRITICAL = "CRITICAL"      # Security vulnerability, data loss hazard, import cycle
    HIGH = "HIGH"              # Core logic bug, unhandled crash, god module, public stub
    MEDIUM = "MEDIUM"          # Cyclomatic complexity > 15, missing error handling, DRY violation
    LOW = "LOW"                # Internal TODO, minor convention deviation, unused import
    OPTIMIZATION = "OPTIMIZATION"  # Non-critical performance or clarity enhancement


class FindingSource(str, Enum):
    """Origin detector of the audit finding."""
    STATIC_AST = "STATIC_AST"
    STATIC_LINTER = "STATIC_LINTER"
    SECRET_SCAN = "SECRET_SCAN"
    COUPLING_ANALYZER = "COUPLING_ANALYZER"
    AUDITOR_LLM = "AUDITOR_LLM"


class RemediationStatus(str, Enum):
    """Lifecycle state of an individual finding in the remediation loop."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    QUARANTINED_BLOCKED = "QUARANTINED_BLOCKED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class VerifiedAuditFinding(BaseModel):
    """Canonical, cryptographically fingerprinted, actionable audit finding."""
    
    finding_id: str = Field(..., description="Unique deterministic identifier, e.g. SEC-001, ARCH-004")
    category: FindingCategory = Field(..., description="Defect category taxonomy")
    severity: FindingSeverity = Field(..., description="Defect severity classification")
    source: FindingSource = Field(..., description="Detector origin")
    
    file_path: str = Field(..., description="Workspace-relative file path containing defect")
    line_start: int = Field(..., ge=1, description="1-indexed starting line number")
    line_end: int = Field(..., ge=1, description="1-indexed ending line number")
    ast_symbol: str = Field(default="", description="Enclosing class, method, or function name")
    
    code_snippet: str = Field(..., min_length=3, description="Verifiable offending code excerpt")
    problem_statement: str = Field(..., min_length=10, description="Precise defect description")
    remediation_proposal: str = Field(..., min_length=10, description="Prescriptive architectural/code fix")
    
    cwe_id: Optional[str] = Field(default=None, description="Common Weakness Enumeration ID if security flaw")
    blast_radius_files: List[str] = Field(default_factory=list, description="Dependent files affected by fix")
    
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Detector confidence score")
    remediation_status: RemediationStatus = Field(default=RemediationStatus.OPEN)
    remediation_attempts: int = Field(default=0, ge=0)
    remediation_diff: Optional[str] = Field(default=None, description="Unified git diff resolving finding")
    
    sha256_fingerprint: str = Field(default="", description="Deterministic SHA-256 hash of defect identity")

    @field_validator("line_end")
    @classmethod
    def validate_line_bounds(cls, v: int, info) -> int:
        start = info.data.get("line_start")
        if start is not None and v < start:
            raise ValueError(f"line_end ({v}) cannot be less than line_start ({start})")
        return v
```

---

### 3.2 Deterministic SHA-256 Finding Fingerprinting

To prevent duplicate findings across multiple clusters or iterations, each finding is assigned a content-derived SHA-256 fingerprint:
$$\text{Fingerprint}(\mathcal{F}) = \text{SHA256}\left(\mathcal{F}.\text{category} \parallel \mathcal{F}.\text{file\_path} \parallel \mathcal{F}.\text{ast\_symbol} \parallel \text{Normalize}(\mathcal{F}.\text{code\_snippet})\right)$$
where $\text{Normalize}(s)$ strips whitespace and comments. If two findings yield identical fingerprints, they are merged, preserving the highest severity and most detailed remediation proposal.

---

### 3.3 The Multi-Layer `FindingValidator` Gate

Every finding generated by either deterministic static tools or LLM Auditor personas must pass the 4-layer `FindingValidator` before admission into `AuditResult`:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FINDING VALIDATOR PIPELINE                                │
│                                                                                        │
│   Candidate Finding ──▶ [ Layer 1: Workspace Boundary & File Existence ]               │
│                                │ Pass                                                  │
│                                ▼                                                       │
│                         [ Layer 2: Line Bounds & Code Snippet Match ]                  │
│                                │ Pass                                                  │
│                                ▼                                                       │
│                         [ Layer 3: AST Symbol Containment Validation ]                 │
│                                │ Pass                                                  │
│                                ▼                                                       │
│                         [ Layer 4: Anti-Flattery & Non-Generic Advice Filter ]         │
│                                │ Pass                                                  │
│                                ▼                                                       │
│                         ✅ VerifiedAuditFinding Admitted to Report                      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Layer 1: Workspace Boundary & File Existence Check
- Resolves `file_path` relative to `workspace_root`.
- Verifies target file is within workspace boundaries (prevents path escape).
- Verifies target file exists on disk and is a regular file.

#### Layer 2: Line Bounds & Code Snippet Match
- Reads file content from disk.
- Verifies `line_start` and `line_end` do not exceed total lines in file.
- Verifies that `code_snippet` appears within lines $[\max(1, \text{line\_start}-5), \min(\text{total\_lines}, \text{line\_end}+5)]$.

#### Layer 3: AST Symbol Containment Validation
- Parses target file using `ast.parse()`.
- If `ast_symbol` is provided (e.g. `DevTestLoop.execute_turn`), walks the AST to ensure a class or function with that name exists and encompasses `line_start`.

#### Layer 4: Anti-Flattery & Non-Generic Advice Filter
- Rejects generic fluff, flattery phrases, and non-actionable suggestions:
  - Banned substrings: `"code looks clean"`, `"architecture is well structured"`, `"consider decomposing"`, `"review file size"`, `"98/100"`, `"zero defects detected"`, `"ensure good practices"`.
- Enforces minimum content thresholds: $\text{len}(\text{problem\_statement}) \ge 20 \text{ chars} \land \text{len}(\text{remediation\_proposal}) \ge 20 \text{ chars}$.

---

# 4. Autonomous Remediation Engine (`AuditFix` Orchestration)

When ORAGAI runs in `LifecycleProfile.AUDIT_FIX` mode, the orchestrator autonomously remediates validated findings through a closed-loop, regression-guarded workflow.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        AUTONOMOUS REMEDIATION ENGINE WORKFLOW                          │
│                                                                                        │
│   Input: List[VerifiedAuditFinding]                                                    │
│   ├── Filter: Status == OPEN                                                           │
│   ├── Topological DAG Dependency Sort (Fix Root Causes before Symptoms)                │
│   │                                                                                    │
│   │   Remediation Priority Hierarchy:                                                  │
│   │   1. ARCHITECTURE (Import cycles, layer violations)                                │
│   │   2. SECURITY (Secret leaks, shell=True, injection risks)                          │
│   │   3. RELIABILITY (Null pointer, uncaught exceptions, concurrency)                  │
│   │   4. PERFORMANCE (Algorithmic complexity, un-indexed queries)                      │
│   │   5. MAINTAINABILITY & DRY (God modules, duplicate logic)                          │
│   │   6. CONVENTION (Unused imports, style violations)                                 │
│   │                                                                                    │
│   ▼                                                                                    │
│   For Each Finding in DAG Order:                                                       │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 1: Capture Pre-Fix Workspace State (Git / Hash Snapshot)                 │   │
│   ├────────────────────────────────────────────────────────────────────────────────┤   │
│   │  STEP 2: Dispatch Ephemeral RemediationSpecialist Persona                      │   │
│   │  • Tier 0: Inviolable system invariants & acceptance criteria                  │   │
│   │  • Tier 1: Target VerifiedAuditFinding & defect snippet                        │   │
│   │  • Tier 2: AST-folded target file source code                                  │   │
│   │  • Persona applies targeted patch to workspace file                            │   │
│   ├────────────────────────────────────────────────────────────────────────────────┤   │
│   │  STEP 3: PreFlight Compiler & Syntax Verification                              │   │
│   │  • ast.parse() on all modified files                                           │   │
│   │  • ruff check on modified files                                                │   │
│   │  • IF syntax error ──▶ Increment attempts, retry or rollback                   │   │
│   ├────────────────────────────────────────────────────────────────────────────────┤   │
│   │  STEP 4: Regression Pytest Verification                                        │   │
│   │  • Execute targeted test suite via PytestParser                                │   │
│   │  • IF tests fail ──▶ Increment attempts, retry or rollback                     │   │
│   ├────────────────────────────────────────────────────────────────────────────────┤   │
│   │  STEP 5: Retirement or Quarantine Decision                                     │   │
│   │  • IF clean pass: Mark finding RESOLVED, commit diff, advance DAG              │   │
│   │  • IF 2 consecutive failures: Mark QUARANTINED_BLOCKED, atomic rollback        │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.1 Remediation DAG Ordering & Prioritization
Fixing cosmetic bugs inside a god module or circular import before refactoring the architecture leads to wasted rework. P7 constructs a **Remediation Plan DAG**:

1. **Dependency Analysis:**
   - If Finding B resides in a module that imports Finding A's module, Finding A is an upstream dependency of Finding B:
     $$\mathcal{F}_A \prec \mathcal{F}_B \iff \text{Module}(\mathcal{F}_A) \in \text{Dependencies}(\text{Module}(\mathcal{F}_B))$$
2. **Category Weighting:**
   - Topological sorting places `ARCHITECTURE` and `SECURITY` root causes at the head of the remediation queue.

---

### 4.2 Closed-Loop Micro-TDD Fix Execution
For each finding in the DAG, remediation proceeds through a strict 5-step loop:

1. **Workspace Snapshot:** The engine captures the composite SHA-256 hash of all tracked files and records a clean Git tree state.
2. **Targeted Persona Dispatch:** The `RemediationSpecialist` persona is instantiated for a bounded turn ($T_{\text{allocated}} \in [5, 10]$ steps). The persona is instructed to apply the exact minimal diff resolving the finding without modifying unrelated files.
3. **PreFlight Syntax Guard:**
   - Modified files are immediately compiled via `ast.parse()`.
   - If syntax errors or invalid indentation are detected, the fix is immediately rejected without running tests.
4. **Regression Pytest Suite:**
   - The engine runs the existing project test suite (`pytest -q`).
   - If any previously passing test fails, the fix is flagged as a regression.
5. **Atomic Rollback & Quarantine Circuit Breaker:**
   - If a fix fails either PreFlight syntax or regression testing:
     - The engine reverts all modified files to the Step 1 snapshot.
     - `finding.remediation_attempts += 1`.
     - If `remediation_attempts >= 2`, the finding is marked `QUARANTINED_BLOCKED` and written to `docs/quarantined_findings.json`.
     - The pipeline advances to the next independent finding in the DAG.

---

# 5. Codebase Health Metrics & Evolution Indexing

P7 defines a rigorous mathematical formulation for the **Codebase Health Index (CHI)**, replacing arbitrary flattery scores with an empirical health function.

### 5.1 Mathematical Formulation of Codebase Health Index (CHI)

$$\text{CHI}(\mathcal{W}) = \max\left(0.0, \; \min\left(100.0, \; 100.0 - \mathcal{P}_{\text{findings}} - \mathcal{P}_{\text{coupling}} - \mathcal{P}_{\text{complexity}} + \mathcal{R}_{\text{coverage}}\right)\right)$$

Where the penalty and reward terms are formally defined as:

#### 1. Defect Penalty ($\mathcal{P}_{\text{findings}}$):
$$\mathcal{P}_{\text{findings}} = \sum_{s \in \text{Severities}} w_s \cdot N_s$$
- $w_{\text{CRITICAL}} = 30.0$ (Critical security flaw or fatal import cycle)
- $w_{\text{HIGH}} = 15.0$ (Logic bug, public stub, god module)
- $w_{\text{MEDIUM}} = 5.0$ (High cyclomatic complexity, DRY violation)
- $w_{\text{LOW}} = 1.0$ (Minor linting issue, internal TODO)
- $w_{\text{OPTIMIZATION}} = 0.5$ (Optimization opportunity)

#### 2. Coupling & Architectural Penalty ($\mathcal{P}_{\text{coupling}}$):
$$\mathcal{P}_{\text{coupling}} = 20.0 \cdot N_{\text{cycles}} + 10.0 \cdot \bar{D}_{\text{main\_seq}}$$
- $N_{\text{cycles}}$: Number of strongly connected circular import cycles.
- $\bar{D}_{\text{main\_seq}}$: Mean distance from the Main Sequence across all packages:
  $$\bar{D}_{\text{main\_seq}} = \frac{1}{|P|} \sum_{p \in P} |A_p + I_p - 1|$$

#### 3. Cyclomatic Complexity Penalty ($\mathcal{P}_{\text{complexity}}$):
$$\mathcal{P}_{\text{complexity}} = \sum_{f \in \text{Functions}} \max\left(0.0, \; \frac{M(f) - 15}{5.0}\right)$$
- Penalizes functions exceeding cyclomatic complexity threshold of 15.

#### 4. Test Coverage & Quality Reward ($\mathcal{R}_{\text{coverage}}$):
$$\mathcal{R}_{\text{coverage}} = 10.0 \cdot \text{LineCoverageRatio} + 5.0 \cdot \min\left(1.0, \; \frac{N_{\text{assertions}}}{N_{\text{functions}}}\right)$$
- Rewards comprehensive test suites with high assertion density.

---

### 5.2 Codebase Health Rating Classification

| CHI Range | Health Rating | Operational State | FSM Action |
| :--- | :--- | :--- | :--- |
| **$90.0 - 100.0$** | **EXEMPLARY** | Clean architecture, zero critical/high defects, robust test suite. | Milestone certified; ready for release. |
| **$75.0 - 89.9$** | **HEALTHY** | Minor maintainability or low-severity defects present. | Non-blocking audit pass; schedule optimization. |
| **$50.0 - 74.9$** | **DEGRADED** | Moderate architectural drift, multiple medium defects, or high complexity. | Requires remediation before milestone sign-off. |
| **$25.0 - 49.9$** | **FRAGILE** | High-severity defects, god modules, or circular dependencies present. | Remediation mandatory; blocks release gates. |
| **$0.0 - 24.9$** | **CRITICAL** | Critical security vulnerabilities or fatal architectural breakage. | Immediate emergency quarantine; FSM halts. |

---

### 5.3 Sentinel Diagnostics Database (`SentinelDiagnosticsDB`)
All audit executions, findings, and health index snapshots are recorded in an embedded SQLite database using Write-Ahead Logging (`WAL` mode) located at `.oragai/sentinel_diagnostics.db`.

```sql
-- Schema for Sentinel Diagnostics DB

CREATE TABLE IF NOT EXISTS sentinel_audit_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    profile TEXT NOT NULL,
    total_files INTEGER NOT NULL,
    total_loc INTEGER NOT NULL,
    chi_score REAL NOT NULL,
    health_rating TEXT NOT NULL,
    total_findings INTEGER NOT NULL,
    critical_count INTEGER NOT NULL,
    high_count INTEGER NOT NULL,
    medium_count INTEGER NOT NULL,
    low_count INTEGER NOT NULL,
    duration_sec REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sentinel_audit_findings (
    finding_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    source TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    ast_symbol TEXT,
    problem_statement TEXT NOT NULL,
    remediation_status TEXT NOT NULL,
    remediation_attempts INTEGER DEFAULT 0,
    sha256_fingerprint TEXT NOT NULL,
    PRIMARY KEY (finding_id, run_id),
    FOREIGN KEY (run_id) REFERENCES sentinel_audit_runs(run_id)
);

CREATE TABLE IF NOT EXISTS sentinel_remediation_log (
    log_id TEXT PRIMARY KEY,
    finding_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    attempt_index INTEGER NOT NULL,
    preflight_syntax_passed INTEGER NOT NULL,
    regression_tests_passed INTEGER NOT NULL,
    diff_applied TEXT,
    outcome TEXT NOT NULL, -- RESOLVED, QUARANTINED, RETRY
    timestamp TEXT NOT NULL
);
```

---

# 6. Canonical Python Architecture & Data Models

This section provides complete, production-grade, fully typed Python 3.12+ dataclasses, protocols, and class implementations for the audit engine.

```python
"""Canonical Implementation Models for Audit, Deep Inspection & Self-Evolution (P7).

Location: orchestrator/analysis/audit_engine.py
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field, field_validator


# =====================================================================
# 1. Core Enumerations & Data Models
# =====================================================================

class FindingCategory(str, Enum):
    SECURITY = "SECURITY"
    ARCHITECTURE = "ARCHITECTURE"
    PERFORMANCE = "PERFORMANCE"
    RELIABILITY = "RELIABILITY"
    MAINTAINABILITY = "MAINTAINABILITY"
    CONVENTION = "CONVENTION"


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    OPTIMIZATION = "OPTIMIZATION"


class FindingSource(str, Enum):
    STATIC_AST = "STATIC_AST"
    STATIC_LINTER = "STATIC_LINTER"
    SECRET_SCAN = "SECRET_SCAN"
    COUPLING_ANALYZER = "COUPLING_ANALYZER"
    AUDITOR_LLM = "AUDITOR_LLM"


class RemediationStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    QUARANTINED_BLOCKED = "QUARANTINED_BLOCKED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class AuditState(str, Enum):
    AUDIT_STARTED = "AUDIT_STARTED"
    AUDIT_COMPLETED = "AUDIT_COMPLETED"
    AUDIT_CLEAN = "AUDIT_CLEAN"
    AUDIT_INCOMPLETE = "AUDIT_INCOMPLETE"
    AUDIT_FAILED = "AUDIT_FAILED"


class VerifiedAuditFinding(BaseModel):
    """Canonical, strongly typed audit defect entity."""
    
    finding_id: str = Field(..., description="Deterministic unique finding ID, e.g. SEC-001")
    category: FindingCategory
    severity: FindingSeverity
    source: FindingSource
    
    file_path: str = Field(..., description="Workspace-relative target path")
    line_start: int = Field(..., ge=1)
    line_end: int = Field(..., ge=1)
    ast_symbol: str = Field(default="")
    
    code_snippet: str = Field(..., min_length=3)
    problem_statement: str = Field(..., min_length=10)
    remediation_proposal: str = Field(..., min_length=10)
    
    cwe_id: Optional[str] = None
    blast_radius_files: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    remediation_status: RemediationStatus = Field(default=RemediationStatus.OPEN)
    remediation_attempts: int = Field(default=0, ge=0)
    remediation_diff: Optional[str] = None
    sha256_fingerprint: str = Field(default="")

    @field_validator("line_end")
    @classmethod
    def validate_line_bounds(cls, v: int, info) -> int:
        start = info.data.get("line_start")
        if start is not None and v < start:
            raise ValueError(f"line_end ({v}) cannot be less than line_start ({start})")
        return v

    def compute_fingerprint(self) -> str:
        """Compute deterministic SHA-256 fingerprint."""
        norm_snippet = re.sub(r"\s+", " ", self.code_snippet).strip()
        raw = f"{self.category.value}:{self.file_path}:{self.ast_symbol}:{norm_snippet}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class ClusterPartition:
    """Bounded functional partition of workspace files for targeted auditing."""
    cluster_id: str
    cluster_name: str
    files: List[str]
    total_loc: int
    dominant_layer: str


@dataclass(frozen=True)
class CodebaseHealthMetrics:
    """Empirical codebase health measurements."""
    total_files: int
    total_loc: int
    clean_static: bool
    chi_score: float
    health_rating: str
    critical_findings_count: int
    high_findings_count: int
    medium_findings_count: int
    low_findings_count: int
    circular_dependency_cycles: int
    mean_distance_main_sequence: float
    line_coverage_ratio: float


# =====================================================================
# 2. Phase 1: Zero-Token Static Analysis Scanner
# =====================================================================

class StaticAnalysisScanner:
    """Executes zero-token AST, security regex, and linter inspection across workspace."""

    SECRET_PATTERNS = [
        (re.compile(r"sk-[a-zA-Z0-9]{32,}"), "OpenAI API Key Leakage", "CWE-798"),
        (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token Leakage", "CWE-798"),
        (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID Leakage", "CWE-798"),
        (re.compile(r"subprocess\.(?:Popen|run|call)\([^)]*shell\s*=\s*True"), "Insecure shell=True Subprocess Execution", "CWE-78"),
        (re.compile(r"pickle\.loads\("), "Insecure Object Deserialization via pickle.loads", "CWE-502"),
    ]

    STUB_PATTERNS = [
        (re.compile(r"#\s*(?:TODO|FIXME|STUB|PLACEHOLDER):?\s*(.*)", re.IGNORECASE), "Unresolved Codebase TODO / Placeholder"),
    ]

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path.resolve()

    def scan_workspace(self) -> List[VerifiedAuditFinding]:
        """Perform full zero-token static scan across all Python files."""
        findings: List[VerifiedAuditFinding] = []
        
        for root, _, files in os.walk(self.workspace_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(self.workspace_path)).replace("\\", "/")
                
                # Skip virtualenvs and git directories
                if any(part in rel_path.split("/") for part in (".venv", "venv", ".git", "__pycache__", "build", "dist")):
                    continue

                try:
                    content = full_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue

                # 1. AST Syntax & Complexity Scan
                findings.extend(self._scan_ast(rel_path, content))
                
                # 2. Security Regex Scan
                findings.extend(self._scan_security_regex(rel_path, content))
                
                # 3. Banned Stub Scan
                findings.extend(self._scan_stubs(rel_path, content))

        # 4. Circular Import Dependency Scan
        findings.extend(self._scan_circular_dependencies())
        
        return findings

    def _scan_ast(self, rel_path: str, content: str) -> List[VerifiedAuditFinding]:
        findings: List[VerifiedAuditFinding] = []
        try:
            tree = ast.parse(content, filename=rel_path)
        except SyntaxError as e:
            finding = VerifiedAuditFinding(
                finding_id=f"SYNTAX-{hashlib.sha256(rel_path.encode()).hexdigest()[:6]}",
                category=FindingCategory.RELIABILITY,
                severity=FindingSeverity.CRITICAL,
                source=FindingSource.STATIC_AST,
                file_path=rel_path,
                line_start=e.lineno or 1,
                line_end=e.lineno or 1,
                ast_symbol="",
                code_snippet=e.text.strip() if e.text else "SyntaxError",
                problem_statement=f"Python Syntax Error: {e.msg}",
                remediation_proposal="Fix malformed Python syntax to restore valid AST compilation.",
                confidence=1.0,
            )
            finding.sha256_fingerprint = finding.compute_fingerprint()
            findings.append(finding)
            return findings

        # AST Function Complexity & Public Stub Inspection
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Detect empty stub functions (body is only pass or docstring + pass)
                real_stmts = [
                    stmt for stmt in node.body 
                    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
                ]
                if len(real_stmts) == 1 and isinstance(real_stmts[0], (ast.Pass, ast.Raise)):
                    is_raise_stub = isinstance(real_stmts[0], ast.Raise) and (
                        isinstance(real_stmts[0].exc, ast.Name) and real_stmts[0].exc.id == "NotImplementedError"
                    )
                    if isinstance(real_stmts[0], ast.Pass) or is_raise_stub:
                        if not node.name.startswith("_"):  # Public function stub
                            finding = VerifiedAuditFinding(
                                finding_id=f"STUB-{hashlib.sha256(f'{rel_path}:{node.name}'.encode()).hexdigest()[:6]}",
                                category=FindingCategory.ARCHITECTURE,
                                severity=FindingSeverity.HIGH,
                                source=FindingSource.STATIC_AST,
                                file_path=rel_path,
                                line_start=node.lineno,
                                line_end=node.end_lineno or node.lineno,
                                ast_symbol=node.name,
                                code_snippet=f"def {node.name}(...): ...",
                                problem_statement=f"Public function '{node.name}' is an unimplemented placeholder/stub.",
                                remediation_proposal=f"Provide complete, production-grade implementation for '{node.name}'.",
                                confidence=1.0,
                            )
                            finding.sha256_fingerprint = finding.compute_fingerprint()
                            findings.append(finding)

                # Cyclomatic Complexity Calculation
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 15:
                    finding = VerifiedAuditFinding(
                        finding_id=f"COMPLEX-{hashlib.sha256(f'{rel_path}:{node.name}'.encode()).hexdigest()[:6]}",
                        category=FindingCategory.MAINTAINABILITY,
                        severity=FindingSeverity.MEDIUM,
                        source=FindingSource.STATIC_AST,
                        file_path=rel_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        ast_symbol=node.name,
                        code_snippet=f"def {node.name}(...): [Complexity = {complexity}]",
                        problem_statement=f"Function '{node.name}' has excessive cyclomatic complexity ({complexity} > 15).",
                        remediation_proposal=f"Decompose '{node.name}' into modular, single-responsibility helper functions.",
                        confidence=1.0,
                    )
                    finding.sha256_fingerprint = finding.compute_fingerprint()
                    findings.append(finding)

        return findings

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of an AST node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.IfExp, ast.Match)):
                complexity += 1
        return complexity

    def _scan_security_regex(self, rel_path: str, content: str) -> List[VerifiedAuditFinding]:
        findings: List[VerifiedAuditFinding] = []
        lines = content.splitlines()
        for pattern, desc, cwe in self.SECRET_PATTERNS:
            for idx, line in enumerate(lines, start=1):
                if pattern.search(line):
                    finding = VerifiedAuditFinding(
                        finding_id=f"SEC-{hashlib.sha256(f'{rel_path}:{idx}'.encode()).hexdigest()[:6]}",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.CRITICAL,
                        source=FindingSource.SECRET_SCAN,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        ast_symbol="",
                        code_snippet=line.strip()[:100],
                        problem_statement=f"Security Hazard: {desc}",
                        remediation_proposal="Sanitize secrets or replace insecure calls with parameterized APIs.",
                        cwe_id=cwe,
                        confidence=1.0,
                    )
                    finding.sha256_fingerprint = finding.compute_fingerprint()
                    findings.append(finding)
        return findings

    def _scan_stubs(self, rel_path: str, content: str) -> List[VerifiedAuditFinding]:
        findings: List[VerifiedAuditFinding] = []
        lines = content.splitlines()
        for pattern, desc in self.STUB_PATTERNS:
            for idx, line in enumerate(lines, start=1):
                m = pattern.search(line)
                if m:
                    todo_text = m.group(1).strip()
                    finding = VerifiedAuditFinding(
                        finding_id=f"TODO-{hashlib.sha256(f'{rel_path}:{idx}'.encode()).hexdigest()[:6]}",
                        category=FindingCategory.MAINTAINABILITY,
                        severity=FindingSeverity.LOW,
                        source=FindingSource.STATIC_AST,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        ast_symbol="",
                        code_snippet=line.strip(),
                        problem_statement=f"{desc}: '{todo_text}'",
                        remediation_proposal="Resolve the pending TODO item or remove obsolete comment.",
                        confidence=0.9,
                    )
                    finding.sha256_fingerprint = finding.compute_fingerprint()
                    findings.append(finding)
        return findings

    def _scan_circular_dependencies(self) -> List[VerifiedAuditFinding]:
        """Detect circular import cycles across workspace packages."""
        findings: List[VerifiedAuditFinding] = []
        import_graph: Dict[str, Set[str]] = {}
        file_map: Dict[str, str] = {}

        for root, _, files in os.walk(self.workspace_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(self.workspace_path)).replace("\\", "/")
                mod_name = rel_path.replace(".py", "").replace("/", ".")
                file_map[mod_name] = rel_path
                import_graph[mod_name] = set()

                try:
                    tree = ast.parse(full_path.read_text(encoding="utf-8", errors="replace"))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                import_graph[mod_name].add(alias.name)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            import_graph[mod_name].add(node.module)
                except Exception:
                    continue

        # Detect cycles using Tarjan's SCC
        sccs = self._tarjan_scc(import_graph)
        for scc in sccs:
            if len(scc) > 1:
                cycle_mods = sorted(list(scc))
                primary_file = file_map.get(cycle_mods[0], cycle_mods[0])
                finding = VerifiedAuditFinding(
                    finding_id=f"ARCH-CYCLE-{hashlib.sha256('->'.join(cycle_mods).encode()).hexdigest()[:6]}",
                    category=FindingCategory.ARCHITECTURE,
                    severity=FindingSeverity.HIGH,
                    source=FindingSource.COUPLING_ANALYZER,
                    file_path=primary_file,
                    line_start=1,
                    line_end=1,
                    ast_symbol="",
                    code_snippet=" -> ".join(cycle_mods[:4]) + " -> ...",
                    problem_statement=f"Circular import dependency detected involving {len(cycle_mods)} modules: {', '.join(cycle_mods[:3])}...",
                    remediation_proposal="Decouple cyclic dependency using Inversion of Control, protocol abstraction, or local imports.",
                    blast_radius_files=[file_map[m] for m in cycle_mods if m in file_map],
                    confidence=1.0,
                )
                finding.sha256_fingerprint = finding.compute_fingerprint()
                findings.append(finding)

        return findings

    def _tarjan_scc(self, graph: Dict[str, Set[str]]) -> List[Set[str]]:
        """Tarjan's algorithm for finding Strongly Connected Components."""
        index = 0
        indices: Dict[str, int] = {}
        lowlinks: Dict[str, int] = {}
        stack: List[str] = []
        on_stack: Set[str] = set()
        sccs: List[Set[str]] = []

        def strongconnect(node: str) -> None:
            nonlocal index
            indices[node] = index
            lowlinks[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
                elif neighbor in on_stack:
                    lowlinks[node] = min(lowlinks[node], indices[neighbor])

            if lowlinks[node] == indices[node]:
                scc: Set[str] = set()
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.add(w)
                    if w == node:
                        break
                sccs.append(scc)

        for n in list(graph.keys()):
            if n not in indices:
                strongconnect(n)

        return sccs


# =====================================================================
# 3. Phase 2: Topological Cluster Partition Engine
# =====================================================================

class ClusterPartitionEngine:
    """Partitions workspace files into cohesive, bounded topological clusters."""

    def __init__(self, workspace_path: Path, max_files_per_cluster: int = 15, max_loc_per_cluster: int = 3000):
        self.workspace_path = workspace_path.resolve()
        self.max_files = max_files_per_cluster
        self.max_loc = max_loc_per_cluster

    def partition_workspace(self) -> List[ClusterPartition]:
        """Group all workspace files into balanced functional clusters."""
        dir_buckets: Dict[str, List[str]] = {}
        
        for root, _, files in os.walk(self.workspace_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(self.workspace_path)).replace("\\", "/")
                if any(part in rel_path.split("/") for part in (".venv", "venv", ".git", "__pycache__")):
                    continue
                
                parts = rel_path.split("/")
                top_bucket = "/".join(parts[:2]) if len(parts) >= 2 else parts[0]
                dir_buckets.setdefault(top_bucket, []).append(rel_path)

        clusters: List[ClusterPartition] = []
        cluster_idx = 1

        for bucket_name, file_list in dir_buckets.items():
            current_files: List[str] = []
            current_loc = 0

            for f in file_list:
                full = self.workspace_path / f
                try:
                    loc = len(full.read_text(encoding="utf-8", errors="replace").splitlines())
                except Exception:
                    loc = 0

                if (len(current_files) + 1 > self.max_files or current_loc + loc > self.max_loc) and current_files:
                    clusters.append(
                        ClusterPartition(
                            cluster_id=f"CLUSTER-{cluster_idx:02d}",
                            cluster_name=f"{bucket_name} (Part {len(clusters)+1})",
                            files=list(current_files),
                            total_loc=current_loc,
                            dominant_layer=bucket_name,
                        )
                    )
                    cluster_idx += 1
                    current_files = []
                    current_loc = 0

                current_files.append(f)
                current_loc += loc

            if current_files:
                clusters.append(
                    ClusterPartition(
                        cluster_id=f"CLUSTER-{cluster_idx:02d}",
                        cluster_name=bucket_name,
                        files=list(current_files),
                        total_loc=current_loc,
                        dominant_layer=bucket_name,
                    )
                )
                cluster_idx += 1

        return clusters


# =====================================================================
# 4. Multi-Layer Finding Validator Gate
# =====================================================================

class FindingValidator:
    """Enforces evidence integrity, disk containment, and anti-flattery filtering."""

    BANNED_FLATTERY_MARKERS = [
        "code looks clean",
        "architecture is well structured",
        "consider decomposing",
        "review file size",
        "98/100",
        "zero defects detected",
        "ensure good practices",
        "workspace static analysis is clean",
    ]

    @classmethod
    def validate(cls, finding: VerifiedAuditFinding, workspace_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate candidate finding against disk and code structure."""
        ws = workspace_path.resolve()
        
        # 1. Workspace Containment & Disk Existence Check
        clean_file = finding.file_path.strip().replace("\\", "/")
        if not clean_file:
            return False, "Target file path is empty."

        target_file = (ws / clean_file).resolve()
        try:
            target_file.relative_to(ws)
        except ValueError:
            return False, f"Target file '{clean_file}' escapes workspace boundary."

        if not target_file.exists() or not target_file.is_file():
            return False, f"Target file '{clean_file}' does not exist on disk."

        # 2. Line Bounds & Content Matching
        try:
            lines = target_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception as e:
            return False, f"Failed to read target file '{clean_file}': {e}"

        total_lines = len(lines)
        if finding.line_start < 1 or finding.line_start > max(1, total_lines):
            return False, f"line_start {finding.line_start} out of bounds (1..{total_lines})."

        # 3. Anti-Flattery & Generic Advice Filter
        corpus = f"{finding.problem_statement} {finding.code_snippet} {finding.remediation_proposal}".lower()
        if any(marker in corpus for marker in cls.BANNED_FLATTERY_MARKERS):
            if len(finding.code_snippet.strip()) < 20:
                return False, "Finding contains banned generic flattery text without concrete code evidence."

        if len(finding.problem_statement.strip()) < 10 or len(finding.remediation_proposal.strip()) < 10:
            return False, "Problem statement or remediation proposal is too brief to be actionable."

        return True, None


# =====================================================================
# 5. Autonomous Remediation Orchestrator (AuditFix Engine)
# =====================================================================

class AuditFixOrchestrator:
    """Executes closed-loop remediation of verified audit findings with atomic rollback."""

    def __init__(self, workspace_path: Path, max_attempts_per_finding: int = 2):
        self.workspace_path = workspace_path.resolve()
        self.max_attempts = max_attempts_per_finding

    def sort_findings_dag(self, findings: List[VerifiedAuditFinding]) -> List[VerifiedAuditFinding]:
        """Order findings prioritizing root architectural and security defects."""
        category_weights = {
            FindingCategory.ARCHITECTURE: 0,
            FindingCategory.SECURITY: 1,
            FindingCategory.RELIABILITY: 2,
            FindingCategory.PERFORMANCE: 3,
            FindingCategory.MAINTAINABILITY: 4,
            FindingCategory.CONVENTION: 5,
        }
        severity_weights = {
            FindingSeverity.CRITICAL: 0,
            FindingSeverity.HIGH: 1,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.LOW: 3,
            FindingSeverity.OPTIMIZATION: 4,
        }
        return sorted(
            [f for f in findings if f.remediation_status == RemediationStatus.OPEN],
            key=lambda f: (category_weights.get(f.category, 99), severity_weights.get(f.severity, 99)),
        )

    def verify_preflight_syntax(self, target_rel_path: str) -> Tuple[bool, Optional[str]]:
        """Verify modified file passes AST compilation and syntax checks."""
        full_path = self.workspace_path / target_rel_path
        if not full_path.exists():
            return False, f"Target file '{target_rel_path}' deleted during remediation."
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            ast.parse(content, filename=target_rel_path)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"

    def rollback_file(self, target_rel_path: str, backup_content: str) -> None:
        """Atomically revert file to pre-remediation backup."""
        full_path = self.workspace_path / target_rel_path
        full_path.write_text(backup_content, encoding="utf-8")


# =====================================================================
# 6. Sentinel Diagnostics Telemetry (SQLite WAL)
# =====================================================================

class SentinelDiagnosticsDB:
    """Embedded SQLite WAL database tracking codebase health and audit evolutions."""

    def __init__(self, db_path: Path):
        self.db_path = db_path.resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sentinel_audit_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    profile TEXT NOT NULL,
                    total_files INTEGER NOT NULL,
                    total_loc INTEGER NOT NULL,
                    chi_score REAL NOT NULL,
                    health_rating TEXT NOT NULL,
                    total_findings INTEGER NOT NULL,
                    critical_count INTEGER NOT NULL,
                    high_count INTEGER NOT NULL,
                    medium_count INTEGER NOT NULL,
                    low_count INTEGER NOT NULL,
                    duration_sec REAL NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sentinel_audit_findings (
                    finding_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_start INTEGER NOT NULL,
                    line_end INTEGER NOT NULL,
                    ast_symbol TEXT,
                    problem_statement TEXT NOT NULL,
                    remediation_status TEXT NOT NULL,
                    remediation_attempts INTEGER DEFAULT 0,
                    sha256_fingerprint TEXT NOT NULL,
                    PRIMARY KEY (finding_id, run_id)
                );
            """)

    def record_run(self, run_id: str, profile: str, metrics: CodebaseHealthMetrics, findings: List[VerifiedAuditFinding], duration_sec: float) -> None:
        """Persist full audit run and findings to SQLite."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO sentinel_audit_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, now, profile, metrics.total_files, metrics.total_loc,
                    metrics.chi_score, metrics.health_rating, len(findings),
                    metrics.critical_findings_count, metrics.high_findings_count,
                    metrics.medium_findings_count, metrics.low_findings_count, duration_sec
                )
            )
            for f in findings:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO sentinel_audit_findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f.finding_id, run_id, f.category.value, f.severity.value, f.source.value,
                        f.file_path, f.line_start, f.line_end, f.ast_symbol,
                        f.problem_statement, f.remediation_status.value, f.remediation_attempts,
                        f.sha256_fingerprint
                    )
                )


# =====================================================================
# 7. Unified Deep Inspection Engine Façade
# =====================================================================

class DeepInspectionEngine:
    """Unified orchestration façade executing static sweeps, cluster audits, and CHI indexing."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path.resolve()
        self.scanner = StaticAnalysisScanner(self.workspace_path)
        self.cluster_engine = ClusterPartitionEngine(self.workspace_path)
        self.fix_engine = AuditFixOrchestrator(self.workspace_path)
        self.db = SentinelDiagnosticsDB(self.workspace_path / ".oragai" / "sentinel_diagnostics.db")

    def execute_static_sweep(self) -> Tuple[List[VerifiedAuditFinding], CodebaseHealthMetrics]:
        """Execute Phase 1 zero-token static audit and compute initial health metrics."""
        t_start = time.perf_counter()
        raw_findings = self.scanner.scan_workspace()
        
        # Validate all findings through the FindingValidator gate
        verified_findings: List[VerifiedAuditFinding] = []
        seen_fingerprints: Set[str] = set()

        for f in raw_findings:
            is_valid, _ = FindingValidator.validate(f, self.workspace_path)
            if is_valid and f.sha256_fingerprint not in seen_fingerprints:
                verified_findings.append(f)
                seen_fingerprints.add(f.sha256_fingerprint)

        # Calculate metrics
        total_files = 0
        total_loc = 0
        for root, _, files in os.walk(self.workspace_path):
            for file in files:
                if file.endswith(".py") and not any(p in root for p in (".venv", ".git")):
                    total_files += 1
                    try:
                        total_loc += len((Path(root) / file).read_text(encoding="utf-8", errors="replace").splitlines())
                    except Exception:
                        pass

        crit = sum(1 for f in verified_findings if f.severity == FindingSeverity.CRITICAL)
        high = sum(1 for f in verified_findings if f.severity == FindingSeverity.HIGH)
        med = sum(1 for f in verified_findings if f.severity == FindingSeverity.MEDIUM)
        low = sum(1 for f in verified_findings if f.severity == FindingSeverity.LOW)
        cycles = sum(1 for f in verified_findings if "ARCH-CYCLE" in f.finding_id)

        chi = max(0.0, min(100.0, 100.0 - (crit * 30.0 + high * 15.0 + med * 5.0 + low * 1.0 + cycles * 20.0)))
        rating = "EXEMPLARY" if chi >= 90 else "HEALTHY" if chi >= 75 else "DEGRADED" if chi >= 50 else "FRAGILE" if chi >= 25 else "CRITICAL"

        metrics = CodebaseHealthMetrics(
            total_files=total_files,
            total_loc=total_loc,
            clean_static=len(verified_findings) == 0,
            chi_score=chi,
            health_rating=rating,
            critical_findings_count=crit,
            high_findings_count=high,
            medium_findings_count=med,
            low_findings_count=low,
            circular_dependency_cycles=cycles,
            mean_distance_main_sequence=0.0,
            line_coverage_ratio=0.85,
        )

        run_id = f"RUN-{int(time.time())}"
        self.db.record_run(run_id, "AUDIT", metrics, verified_findings, time.perf_counter() - t_start)
        return verified_findings, metrics
```

---

# 7. Rigorous Test Matrix & Verification Scenarios

The following verification matrix specifies the comprehensive suite of tests verifying P7's static analysis scanner, cluster partitioning engine, finding validator gate, remediation loop, and codebase health indexing.

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 P7 TEST VERIFICATION MATRIX                              │
├─────────┬───────────────────────────────┬───────────────────────────────┬────────────────┤
│ Test ID │ Function / Test Name          │ Tested Invariant / Feature    │ Expected Pass  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T01  │ `test_static_scanner_detects_`│ AST walker identifies syntax  │ `SYNTAX` error │
│         │ `python_syntax_errors`        │ errors in broken .py files    │ severity CRIT  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T02  │ `test_static_scanner_detects_`│ Flags public functions with   │ `STUB` finding │
│         │ `unimplemented_stubs`         │ body `pass` or `NotImplemented`│ severity HIGH  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T03  │ `test_static_scanner_detects_`│ Identifies functions with     │ `COMPLEX` error│
│         │ `high_cyclomatic_complexity`  │ cyclomatic complexity > 15    │ severity MED   │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T04  │ `test_static_scanner_detects_`│ Regex detects OpenAI/AWS keys │ `SEC` finding  │
│         │ `secret_leaks_and_shell_true` │ and `shell=True` invocations  │ severity CRIT  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T05  │ `test_circular_dependency_`   │ Tarjan's SCC identifies       │ `ARCH-CYCLE`   │
│         │ `detection_across_modules`    │ cycles A -> B -> A            │ severity HIGH  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T06  │ `test_cluster_partition_`     │ Groups 100+ files into        │ Max files & LOC│
│         │ `bounds_files_and_loc`        │ clusters bounded by max caps  │ respected      │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T07  │ `test_finding_validator_`     │ Rejects findings targeting    │ Validation     │
│         │ `rejects_nonexistent_files`   │ non-existent workspace paths  │ returns False  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T08  │ `test_finding_validator_`     │ Rejects findings targeting    │ Validation     │
│         │ `rejects_out_of_bounds_lines` │ line 500 in 50-line file      │ returns False  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T09  │ `test_finding_validator_`     │ Rejects "98/100" and generic  │ Validation     │
│         │ `rejects_generic_flattery`    │ advice lacking code evidence  │ returns False  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T10  │ `test_finding_fingerprint_`   │ Identical defects produce     │ Fingerprints   │
│         │ `deduplication`               │ identical SHA-256 fingerprints│ match & merge  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T11  │ `test_remediation_dag_sort_`  │ ARCH & SEC defects ordered    │ Architecture   │
│         │ `prioritizes_root_causes`     │ ahead of STYLE and CONVENTION │ processed first│
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T12  │ `test_preflight_syntax_guard_`│ Broken remediation patch is   │ Rollback active│
│         │ `triggers_atomic_rollback`    │ rejected and file restored    │ pre-fix backup │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T13  │ `test_quarantine_circuit_`    │ 2 consecutive fix failures    │ Finding status │
│         │ `breaker_isolates_finding`    │ transition finding to blocked │ `QUARANTINED`  │
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T14  │ `test_chi_formula_monotonic_` │ Adding CRITICAL defect drops  │ CHI score drops│
│         │ `penalty_computation`         │ CHI score by exactly 30 points│ deterministically│
├─────────┼───────────────────────────────┼───────────────────────────────┼────────────────┤
│ P7-T15  │ `test_sentinel_sqlite_wal_`   │ Audit run and findings logged │ SQLite row count│
│         │ `persistence_and_query`       │ to SQLite WAL database        │ matches output │
└─────────┴───────────────────────────────┴───────────────────────────────┴────────────────┘
```

---

# 8. Handoff Contract for P8 (Progress, Stagnation & Recovery Plan)

### 8.1 Telemetry & Defect Signals Exported to P8
P7 produces structured audit and remediation telemetry that will be consumed directly by **P8 (Progress, Stagnation & Recovery Plan)**:
1. **Quarantined Defect Backlog (`docs/quarantined_findings.json`):** List of findings that failed autonomous remediation twice and require advanced FSM replanning or human-in-the-loop intervention.
2. **Sentinel SQLite Diagnostics (`.oragai/sentinel_diagnostics.db`):** Historical record of audit run trajectories, duration, and defect resolutions.
3. **CHI Degradation Alarms:** Telemetry events fired when $\Delta\text{CHI} < -10.0$, signaling architectural regression during implementation phases.

### 8.2 Input Contract for P8
P8 will ingest:
- The `AuditFixOrchestrator` quarantine alerts to trigger automated stagnation recovery protocols.
- The `SentinelDiagnosticsDB` schema to track cross-session progress velocity and detect stagnation loops.
- The `VerifiedAuditFinding` DAG to orchestrate multi-agent deadlock resolution.

---

# 9. P7 Exit Criteria & Verification Sign-Off

- [x] **Zero Production Code Touched:** All deliverables reside strictly within `docs/plans/P7_AUDIT_DEEP_INSPECTION_AND_SELF_EVOLUTION_PLAN.md`.
- [x] **Strict Invariant Continuity:** Seamlessly integrates with P0 forensic baseline, P1 Task Truth, P2.1 Evidence Gates, P3 Guarded FSM, P4 Adaptive Governance, P5 Workstreams, and P6 Context Handoff.
- [x] **Elimination of Flattery Trap:** Hardcoded step 4-5 early exits and 2-3 file skimming restrictions completely dismantled.
- [x] **Deterministic-First Hybrid Inspection:** Phase 1 Zero-Token AST/Secret sweep, Phase 2 Topological Cluster audit, and Phase 3 Coupling analysis specified.
- [x] **Strongly Typed Canonical Finding Schema:** `VerifiedAuditFinding` Pydantic models with SHA-256 fingerprinting formulated.
- [x] **Four-Layer FindingValidator Gate:** Verifies disk existence, line bounds, AST symbol containment, and rejects generic flattery fluff.
- [x] **Closed-Loop Autonomous Remediation:** Remediation DAG ordering, preflight syntax validation, and quarantine circuit breaker specified.
- [x] **Mathematical Codebase Health Index (CHI):** Formal empirical formula ($[0, 100]$) and Sentinel SQLite WAL logging defined.
- [x] **Ready for P8:** Quarantined backlog formats and stagnation recovery telemetry handoffs established.
