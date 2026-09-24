---
name: system-unification-audit
description: System-wide codebase consolidation, architectural audit, and responsibility unification protocol. Enforces "One responsibility -> One owner -> One implementation -> One source of truth", state isolation, unified security boundaries, and systematic zero-regression discovery.
triggers:
  - audit
  - unification
  - consolidation
  - refactor
  - architecture
  - dependency-map
  - state-ownership
---

# Antigravity — System Unification & Consolidation Audit Protocol

## 1. Prime Directive

> **One responsibility → One owner → One implementation → One source of truth**

Preserve the existing architecture and operational behavior without superficial reductions or over-abstraction. Every architectural change must possess an explicit rationale.

Core concepts that must remain intact:
* **Orchestrator Engine & FSM Lifecycle**
* **Agent Roles & Dynamic Skill Injection**
* **BudgetGuard (Dual USD + Token Cap Guard)**
* **Git Isolation & Worktree Safety**
* **Pipeline Hierarchy** (Dev-Test, Full, Audit, Audit-Fix)
* **HITL / Approval Gates & Human Intervention Channel**
* **Telemetry, Session Logs, and Project-Partitioned Diagnostics**
* **Persistent Memory & Vector/Context Stores**
* **CLI Entry Points & Verification Flags**

---

## 2. Six-Phase Audit & Refactoring Execution Standard

### Phase 1: Architecture Discovery (Zero Code Modifications)
Map the entire codebase systematically before touching any implementation:
1. Trace the end-to-end dependency pipeline:
   ```text
   CLI → Orchestrator → Pipeline Core → Agents → Skills → Tools → Workspace/Git/LLM → Telemetry/Memory
   ```
2. Identify:
   * **Creation Ownership**: Which component instantiates which object?
   * **State Ownership**: Who owns, modifies, or reads state?
   * **Hidden Couplings**: Where are circular dependencies, unstated imports, or mutable globals?
   * **Duplicate Implementations**: Where do multiple modules perform the same responsibility?
3. Produce discovery artifacts strictly under `docs/`:
   * `docs/ARCHITECTURE_MAP.md`
   * `docs/DUPLICATION_MAP.md`
   * `docs/STATE_OWNERSHIP.md`
   * `docs/DEPENDENCY_MAP.md`

### Phase 2: Target Architecture & Migration Plan
Draft the migration blueprint before executing changes:
* Specify `Current → Problem → Target → Migration` for every affected subsystem.
* Produce `docs/TARGET_ARCHITECTURE.md` and `docs/REFACTOR_PLAN.md`.

### Phase 3: Foundation Unification
Refactor core foundational models first:
* **Configuration**: Single source of truth (`OrchestratorConfig`); unify env var resolution, defaults, and LLM factory methods.
* **State Taxonomy**: Isolate Run State, Agent State, Pipeline State, Telemetry, and Persistent Memory.
* **Error Taxonomy**: Define distinct exception types (`ConfigurationError`, `ValidationError`, `SecurityError`, `ToolExecutionError`, `AgentExecutionError`, `PipelineError`, `BudgetError`, `CancellationError`). Ban silent `except Exception: return None`.

### Phase 4: Infrastructure & Tooling
* **Workspace Boundary**: Unify path security:
  ```text
  Normalize → Resolve → Validate Confinement → Permission Check → Execute
  ```
* **Terminal Safety**: Eliminate `shell=True` on dynamic user/agent input; enforce parameterized execution (`shell=False`) with strict token allowlist validation.
* **GitOps**: Centralize all Git operations (diff, branch, commit, rollback, checkpoint) into `GitOps`; forbid inline ad-hoc Git executions in pipelines.
* **Telemetry**: Unify event pipeline (`Events → Session Logs → Reports → Metrics`). No duplicate logging stores.

### Phase 5: Pipeline Consolidation
* Establish a lean `PipelineCore` containing only shared lifecycle logic:
  ```text
  Initialize → Preflight → Budget Check → Workspace Prep → Execute → Observe → Validate → Finalize → Persist Telemetry → Cleanup
  ```
* Subclass/specialize `DevTestPipeline`, `FullPipeline`, and `AuditPipeline` cleanly without cross-contaminating role-specific logic into the core.

### Phase 6: Dead Code Elimination & Cleanup
* Eliminate unused functions, classes, compatibility shims, duplicate constants, and abandoned imports.
* Validate with AST analysis and dynamic test coverage. Never delete solely based on substring search.

---

## 3. State Ownership Invariants

1. **Zero Run-to-Run Leakage**: State must never persist from one pipeline run into another.
2. **Fresh Recorders**: `TelemetryRecorder` and `SessionLogStore` must start clean or be explicitly reset per execution.
3. **Explicit Dependency Injection**: Forbid mutable global state; pass dependencies explicitly through constructors or method signatures.
4. **No Foreign Private Mutation**: Never mutate private attributes (`_attribute`) of external library objects to alter lifecycle.

---

## 4. Quality & Safety Verification Standard

Execute safety verification at every phase transition:
1. **Fast Regression**:
   ```bash
   uv run pytest -q
   ```
2. **Full Test Suite & CLI Integrity**:
   ```bash
   uv run pytest tests/ -v
   uv run python -m orchestrator.main --list-skills
   uv run python -m orchestrator.main --check-config
   ```
3. **Static Lint & Format**:
   ```bash
   uv run ruff check .
   ```

---

## 5. Audit Deliverable Report Template

Every audit concludes with a structured report saved strictly to `docs/AUDIT_REPORT.md` (no markdown files permitted in repository root):

```markdown
# Antigravity Consolidation Audit Report

## 1. Executive Summary & Code Metrics
| Dimension | Before | Target / After | Delta |
|---|---|---|---|
| Total Python Files | ... | ... | ... |
| Total LOC | ... | ... | ... |
| Duplicate Implementations | ... | ... | ... |
| Global / Leaked State Sites | ... | ... | ... |
| Security Boundary Exceptions | ... | ... | ... |

## 2. Duplicate Responsibilities & Ownership Resolution
- **Configuration**: ...
- **Agent/LLM Creation**: ...
- **Workspace & Terminal Operations**: ...
- **Git Operations**: ...
- **Telemetry & Logging**: ...

## 3. State Ownership & Concurrency Matrix
- Run State vs Pipeline State vs Persistent Memory isolation verified.

## 4. Security Hardening Verification
- Parameterized execution (`shell=False`) verified.
- Path normalization & confinement verified.
- Sensitive environment redaction verified.

## 5. Intentionally Not Merged (Justified Separation)
- List components kept separate with explicit technical justifications.

## 6. Remaining Technical Debt & Priority Matrix
- [CRITICAL | HIGH | MEDIUM | LOW] items with file and line references.
```
