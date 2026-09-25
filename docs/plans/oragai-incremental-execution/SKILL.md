
---
name: oragai-incremental-execution
description: "Graft-aware, evidence-driven incremental execution and governance engine for ORAGAI. Executes the canonical P1-P14 architecture across independent conversations using atomic architectural bites, persistent execution state, Graft topology intelligence, contract-first verification, RBAC sandboxing, AST virtualization, regression protection, zero-token preflight checks, evidence gates, and safe recovery."
triggers:
  - oragai-dev
  - execute-plan
  - incremental-dev
  - build-oragai
  - implement-milestone
  - plan-execution
---

# ORAGAI Incremental Execution & Architecture Governance

## 1. PURPOSE & ARCHITECTURAL SCOPE

This skill serves as the deterministic execution, coordination, and governance engine for **ORAGAI**.

It does NOT replace:
* Canonical plans in `docs/plans/P0-P14`[cite: 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14]
* Approved Architectural Decision Records (ADRs)[cite: 2]
* Graft Codebase Topology Engine[cite: 2]
* GitOps Repository Isolation[cite: 2]
* Project test infrastructure (244 baseline invariant tests)[cite: 2]

Its explicit responsibility is to transform approved architectural plans into bounded, cryptographically verified, and independently executable **Atomic Bites** across stateless agent conversations[cite: 1, 8].

A conversation is ephemeral; the repository, Git history, `TaskTruthGraph`, and cryptographic evidence are permanent[cite: 3, 4, 7].

---

## 2. SOURCE-OF-TRUTH HIERARCHY

When determining implementation scope and verifying completion, adhere strictly to this precedence:

1. `docs/plans/P0-P14` — Canonical architectural intent and invariants[cite: 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14].
2. Current repository code — Implementation ground-truth[cite: 2].
3. Existing test suites — Behavioral contracts (244 passing baseline)[cite: 2].
4. `TaskTruthGraph` & Persistent execution state (`.orchestrator_state.json` / `docs/execution/`) — Active requirements and milestone DAG[cite: 3, 5].
5. Cryptographic Evidence Packages (`CanonicalEvidence`, SHA-256 digests) — Previously proven facts[cite: 4, 8].
6. Git working tree & Checkpoint commits — Verified historical states[cite: 5, 10].
7. Graft Engine — Structural relationships, call graphs, and blast-radius topology[cite: 2].
8. Agent reasoning — Transient execution assistance only[cite: 2].

The agent MUST NOT treat conversational context, LLM assumptions, or unverified claims as authoritative[cite: 2, 4].

---

## 3. CORE ARCHITECTURAL INVARIANTS

Every execution session MUST strictly satisfy these non-negotiable system invariants:

1. **The 244-Test Invariant Gate:** Existing baseline tests must remain 100% passing (`244 passed`). A single regression halts execution immediately[cite: 2, 13, 14].
2. **False Completion Barrier ($FCR \equiv 0.000$):** An Atomic Bite or task MUST NEVER be marked `COMPLETED` based merely on process exit code `0` or conversation step exhaustion without deterministic evidence satisfying all mandatory Acceptance Criteria[cite: 2, 4, 13].
3. **Strict Persona RBAC Sandboxing:** 
   * `Developer` role is STRICTLY FORBIDDEN from modifying `tests/`[cite: 2, 7].
   * `Tester` role is STRICTLY FORBIDDEN from modifying production source code outside `tests/`[cite: 2, 7].
   * `Architect` and `Reviewer` roles are strictly read-only for production code[cite: 2, 7].
4. **Zero-Stub Invariant:** Production implementations must NEVER contain `# TODO`, `# FIXME`, `pass`, `...`, or `raise NotImplementedError` in public interfaces. Stubs cause immediate rejection by `ASTGuard`[cite: 2, 7].
5. **No Monkey-Patching (`sdk_patch.py` Banned):** All OpenHands SDK integrations must strictly use official public extension points (`ToolDefinition`, `ToolExecutor`, `EventStream`)[cite: 12].
6. **Cross-Conversation Recovery:** Every bite must be fully recoverable from repository state alone without requiring previous chat transcripts[cite: 7, 8].

---

## 4. ATOMIC BITE DEFINITION

The atomic execution unit is an **Atomic Bite**.

An Atomic Bite is the smallest coherent architectural change that:
* Fulfills a discrete slice of a `TaskMilestone` from `TaskTruthGraph`[cite: 3, 7].
* Possesses explicit boundaries and unambiguous Acceptance Criteria (Given-When-Then)[cite: 3].
* Can be independently verified via automated tests or deterministic AST checks[cite: 3, 4].
* Can be atomically rolled back via GitOps in $<5$ seconds[cite: 10, 14].
* Emits a cryptographically sealed `CrossAgentHandoffPayload`[cite: 7, 8].

Architectural coherence defines atomicity, NOT file count[cite: 7].

---

## 5. SESSION START PROTOCOL (STATE RECONSTRUCTION)

Every new conversation MUST reconstruct its operating state before executing any tool or code action:

```text
1. Read active plan in docs/plans/.
2. Inspect persistent execution state (docs/execution/state.json or TaskTruthGraph).
3. Discover current test baseline via local zero-token check.
4. Verify working tree status (git status, last verified commit hash).
5. Query Graft topology for affected module neighborhoods.
6. Verify whether previous evidence is FRESH or STALE via composite SHA-256 digest.
7. Identify unverified requirements or active blockers.
8. Select exactly ONE dependency-ready Atomic Bite.

```

If state is ambiguous or contradictory:

```text
STOP
→ Run PreFlightGuard syntax and import sweep
→ Reconstruct TaskTruthGraph
→ Proceed ONLY when state is deterministically grounded

```

---

## 6. EXECUTION LIFECYCLE (THE 12-GATE PROTOCOL)

Every Atomic Bite strictly follows this deterministic state progression:

```text
DISCOVER (Graft & AST Mapping)
   ↓
GROUND (Identify active ACs & target symbols)
   ↓
SLICE (Define bounded Atomic Bite)
   ↓
PRECONDITION GATE (Dependencies & Interfaces verified)
   ↓
CONTRACT (Micro-TDD: Red failing test authored by Tester)
   ↓
IMPLEMENT (Developer authors complete logic; tests/ locked by RBAC)
   ↓
PREFLIGHT (Zero-token py_compile & ASTGuard syntax check)
   ↓
VERIFY (Run targeted pytest suite; capture compact trace)
   ↓
EVIDENCE (Generate SHA-256 bound CanonicalEvidence)
   ↓
COMPLETION GATE (TaskTruthSemanticQueries validation)
   ↓
PERSIST STATE (Update TaskTruthGraph & SQLite WAL)
   ↓
CHECKPOINT (Atomic Git commit: feat(bite): ...)

```

---

## 7. ROLE OF GRAFT & CONTEXT SYNTHESIS

Use Graft to minimize token expenditure and avoid blind repository exploration:

* Use `graft map` to discover module cluster boundaries.


* Use `graft skeleton <file>` for class and method signatures.


* Use `graft callers <symbol>` to calculate downstream blast radius.



### Context Synthesis Tiers (P6 Integration)

Prompts must strictly adhere to priority tiers without truncation of critical intent:

* **Tier 0 (Immutable):** Task Intent, Acceptance Criteria, RBAC Scope, and Invariants.


* **Tier 1 (High):** Compacted Pytest Diagnostics ($\le 800$ tokens) and Upstream Handoff Envelope.


* **Tier 2 (Medium):** Target symbol implementations and AST-folded neighbor signatures.


* **Tier 3 (Elastic):** Graft architecture map and distilled lessons learned.



---

## 8. TOOLING, SANDBOXING & WINDOWS RESILIENCE

All file and terminal actions must pass through the hardened sandbox:

### File Virtualization (P9)

* Files $>250$ LOC must NOT be clamped bluntly.


* Use `operation="outline"` to inspect structure at zero token cost.


* Use `operation="symbol"` for exact, lossless class/function extraction.


* Use `operation="read"` with `offset_line` and `limit_lines` for windowed reading.


* File writes must execute via atomic temporary file swap (`os.replace`) with syntax check pre-commit.



### Terminal Security & Windows NT Subprocess Protection (P9)

* NEVER use bash-specific pipes (`|`) or dangerous operators (`&&`, `;`, `||`, ```).


* Use grammar-validated commands: only allowlisted producers (e.g. `Get-Content`, `pytest`) piped into allowlisted consumers (e.g. `Select-String`) are permitted.


* Subprocesses must run with `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, and isolated environment dictionaries stripped of API keys and credentials.



---

## 9. CONTRACT-FIRST DEVELOPMENT (MICRO-TDD)

For behavioral modifications:

1. **RED:** Author or update isolated tests in `tests/test_*.py` asserting expected Acceptance Criteria. Confirm test failure or symbol absence.


2. **GREEN:** Implement production logic in target source files. Zero stubs allowed.


3. **REFACTOR:** Run zero-token AST syntax validation and execute tests to confirm green status.



TDD is strictly enforced for functional changes; it must not be faked for pure documentation, configuration, or packaging updates.

---

## 10. PREFLIGHT & DETERMINISTIC ZERO-TOKEN FIRST

Before invoking expensive LLM turns or running multi-module test suites:

1. Run local zero-token syntax compilation:


```bash
python -m py_compile <modified_files>

```


2. Run local AST symbol and stub inspection.


3. Run targeted single-node tests before broad regression sweeps.



---

## 11. PROGRESS DETECTION & STAGNATION CONTROL (P8)

Track progress across the 4-dimensional velocity vector:


$$\vec{V} = \langle V_{\text{code}}, V_{\text{verif}}, V_{\text{evid}}, V_{\text{defect}} \rangle$$

* $V_{\text{code}}$: Structural AST diff excluding whitespace and comments.


* $V_{\text{verif}}$: Net delta of passed versus failed test node IDs.


* $V_{\text{evid}}$: Net verified Acceptance Criteria.


* $V_{\text{defect}}$: Net resolved static/audit findings.



### Stagnation & Oscillation Interception

* **Cycle Detection:** If state fingerprints exhibit period $p \in [1, 5]$ oscillation ($A \to B \to A$), STOP CODING immediately.


* **4-Tier Strategy Mutation:**
1. *Tier 1:* Prompt steering with anti-oscillation diff comparison.


2. *Tier 2:* Target decomposition (split active bite into sub-atomic tasks).


3. *Tier 3:* Tool constriction (disable terminal; enforce AST file patch only).


4. *Tier 4:* Model elevation to Tier-1 frontier reasoning.





---

## 12. COMPLETION GATES & EVIDENCE PERSISTENCE

An Atomic Bite is marked `COMPLETE` if and only if ALL criteria evaluate to `True`:

```text
[ ] Mandatory Requirements in TaskTruthGraph satisfied (TCR == 1.0)[cite: 3, 13]
[ ] Discrete Acceptance Criteria proven by passing test nodes[cite: 3, 4]
[ ] Zero syntax errors via PreFlightGuard[cite: 1, 4]
[ ] Zero stubs (pass, TODO, NotImplementedError) detected by ASTGuard[cite: 2, 7]
[ ] 244-test baseline regression suite is 100% green[cite: 2, 13]
[ ] Workspace composite SHA-256 digest matches evidence record[cite: 4, 8]
[ ] Codebase Health Index (CHI) is non-decreasing (ΔCHI >= 0.0)[cite: 9, 13]
[ ] CrossAgentHandoffPayload cryptographically sealed[cite: 7, 8]
[ ] Git checkpoint commit created: feat(bite): <Title> [hash: <sha>][cite: 5, 7]

```

If any mandatory gate fails, status is `BLOCKED` or `FAILED`. Never declare completion through conversational assertion.

---

## 13. REQUIRED BITE COMPLETION RECORD

At the conclusion of every verified bite, append this structured record to `docs/execution/progress.md`:

```markdown
### Bite Record: <BITE-ID> - <Title>
- **Plan Reference:** <P-Phase, ID Milestone Section,>[cite: 3, 7]
- **Target Files & Symbols:** <List AST and modified of paths symbols>[cite: 7]
- **Acceptance Criteria Verified:** <List AC IDs of satisfied>[cite: 3, 4]
- **Test Evidence:** `<test_file.py>::<test_node>` (Exit code: 0, Duration: <X>s)[cite: 4]
- **PreFlight Status:** SYNTAX_CLEAN (Composite SHA-256: `<hash>`)[cite: 1, 4]
- **Baseline Invariant:** 244/244 PASSED (0 Regressions)[cite: 2, 13]
- **PER 2.0 Score:** <Progress Score> (<Classification: THRIVING/MAKING_PROGRESS>)[cite: 10]
- **Checkpoint Commit:** `<commit_sha>`[cite: 5, 7]
- **Remaining Blockers / Next Eligible Bite:** <Next Bite ID None or>[cite: 3, 7]

```

---

## 14. FINAL GOVERNING PRINCIPLE

```text
VERIFIED TRUTH  over  CONVERSATION ASSERTIONS[cite: 2, 4]
DETERMINISTIC GATES  over  HEURISTIC TRUST[cite: 2, 4]
ATOMIC PERSISTENCE  over  EPHEMERAL MEMORY[cite: 7, 8]
STRUCTURAL COHERENCE  over  SUPERFICIAL CHURN[cite: 10]

```

The entire implementation and governance lifecycle must always remain **100% recoverable, verifiable, and enforceable directly from the repository itself.**