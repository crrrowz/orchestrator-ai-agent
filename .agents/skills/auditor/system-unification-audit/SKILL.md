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

# System Unification Audit

## 1. Prime Directive
- One responsibility -> One owner -> One implementation -> One source of truth.
- Low-Token Discovery: run `graft map` and `graft skeleton` instead of bulk file reads.

## 2. Invariants & Isolation
- State Isolation: telemetry, session logs, and persistent memory must never leak across runs.
- Unified Boundaries: enforce parameterized commands (`shell=False`) and workspace path confinement.
- Zero Stubs: flag any unhandled stubs or dead code paths.

## 3. Required Output Artifacts
- Save verified structured findings to `docs/audit_findings.json`.
- Write the comprehensive audit report strictly to `docs/AUDIT_REPORT.md`.
