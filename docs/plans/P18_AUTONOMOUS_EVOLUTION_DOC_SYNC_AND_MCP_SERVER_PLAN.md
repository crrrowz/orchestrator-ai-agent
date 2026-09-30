# PLAN 18: END-TO-END AUTONOMOUS CODEBASE EVOLUTION & STRATEGIC CONVERGENCE
## Self-Directed Architectural Healing, Monotonic Codebase Health (CHI), Enterprise Documentation Sync & OpenSpace MCP Federation

---

### Executive Metadata
- **Document ID:** `ORAGAI-PLAN-18-STRATEGIC-CONVERGENCE`
- **Classification:** Enterprise Architectural Blueprint & Production Implementation Plan
- **Scope:** Autonomous Architectural Drift Correction, Codebase Health Index (CHI) Feedback Loops, Forensic Documentation-Code Synchronization, OpenSpace Cloud/Local Skills Federation, and SRE MCP Server Deployment
- **Target Seam:** `orchestrator/evolution/`, `orchestrator/governance/gates/completion_gate.py`, `docs/reports/`
- **Governing Standard:** Monotonic Codebase Health ($\Delta\text{CHI} \ge 0.0$), Zero Drift, Self-Sustaining Autonomous Evolution, Incremental Execution (`oragai-incremental-execution/SKILL.md`)

---

## 1. Problem Statement & Architectural Gap

The *360° Architectural Assessment*, *Forensic Performance Analysis*, and recent *Documentation Drift Report* demonstrate that autonomous agents introduce gradual entropy unless constrained by closed-loop feedback:

1. **Passive Evolution vs. Closed-Loop Healing:**
   - The evolution subsystem (`orchestrator/evolution/auditor.py`) generates static telemetry and findings, but does not autonomously execute remediation tasks into the `GuardedFSMEngine` to fix detected defects.
2. **Documentation-Code Drift Divergence:**
   - As new subsystems were added (Domain, Ports, Polyglot, Benchmarks), documentation drifted significantly (18 drifts identified in `docs/reports/DOCUMENTATION_DRIFT_REPORT.md`).
   - There is no automated pre-commit or CI gate to continuously detect documentation-to-code divergence.
3. **Unexercised OpenSpace Skill Federation:**
   - OpenSpace capabilities (local and cloud skills) exist in the environment, but ORAGAI's internal skill manager does not automatically discover, benchmark, and evolve skills through task feedback loops.
4. **Standalone MCP Server Gap:**
   - While ORAGAI possesses proprietary, zero-token AST analysis, Graft graph intelligence, and pre-flight compilers, these high-value tools are locked inside CLI monoliths rather than exposed as an enterprise Model Context Protocol (MCP) server for external agent ecosystems.

---

## 2. Target Architecture & Hexagonal Placement

The Strategic Convergence subsystem closes the loop between observation, evolution, and documentation:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           ORAGAI MONITORED REPOSITORY                             │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                    CONTINUOUS ARCHITECTURAL SENTINEL & AUDITOR                    │
│      • Computes Codebase Health Index (CHI: 0.00 to 100.00)                       │
│      • Forensic Documentation Drift Verifier (DocSync Protocol)                   │
│      • OpenSpace Dynamic Skill Discovery & Capability Mapping                     │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                    CLOSED-LOOP AUTONOMOUS REMEDIATION ENGINE                      │
│      • Generates TaskTruthGraph Requirements for Structural Invariant Violations │
│      • Dispatches Red-Green-Refactor Loops via GuardedFSMEngine                   │
│      • Verifies Post-Remediation $\Delta\text{CHI} \ge 0.0$                       │
│      • Synchronizes API Reference & Architecture Markdown Artifacts               │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │          HIGH-PERFORMANCE MCP SERVER              │
                │              `oragai-sre-mcp`                     │
                │   Exposes: ASTGuard, GraftMap, PolyglotCompactor, │
                │   PRReviewGate, and HealthEvaluator via JSON-RPC  │
                └───────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### 3.1 Codebase Health Index (CHI) Engine
Location: `orchestrator/workstreams/audit/chi_calculator.py`
- Formula:
  $$\text{CHI} = 100.0 - (W_{\text{crit}} \cdot N_{\text{crit}} + W_{\text{high}} \cdot N_{\text{high}} + W_{\text{med}} \cdot N_{\text{med}} + W_{\text{stub}} \cdot N_{\text{stub}} + W_{\text{drift}} \cdot N_{\text{drift}})$$
- Enforces the **Monotonic Health Invariant**: Any task run where $\Delta\text{CHI} < 0.0$ automatically trips the `RollbackControllerPort`, reverting Git working tree to the pre-task Merkle checkpoint.

### 3.2 Continuous Documentation-Code Sync Engine
Location: `orchestrator/workstreams/audit/doc_sync.py`
- Continuously audits:
  - CLI commands and options in `orchestrator/cli/` vs. `README.md`
  - Exported port protocols in `orchestrator/ports/` vs. `docs/architecture/API_REFERENCE.md`
  - Configuration models in `orchestrator/core/config.py` vs. `docs/guides/CONFIG_REFERENCE.md`
  - Test suites and test counts vs. documentation claims
- Automatically generates updated markdown sections or flags blocking drift issues in `PRGate`.

### 3.3 OpenSpace & SRE MCP Server (`oragai-sre-mcp`)
Location: `orchestrator/mcp/server.py`
- Implements standard Model Context Protocol (MCP) over `stdio` and SSE.
- Exposes native tools to IDEs, Antigravity, and external LLM runners:
  - `oragai_ast_guard`: Zero-token syntax & anti-stub inspection.
  - `oragai_graft_map`: Sub-second codebase orientation and hub detection.
  - `oragai_polyglot_check`: Cross-language syntax and test compaction.
  - `oragai_review_diff`: Semantic AI and AST diff review.
  - `oragai_compute_chi`: Immediate codebase health scoring.

---

## 4. Invariants & Verification Plan

1. **Monotonic Health Invariant ($\Delta\text{CHI} \ge 0.0$):**
   - No code modification can be committed or merged if it lowers the overall repository CHI score.
2. **Zero Documentation Drift Invariant:**
   - Documentation audits must report 0 CRITICAL and 0 HIGH drifts against the living codebase.
3. **Hermetic MCP Server Invariant:**
   - The MCP server must communicate strictly through typed protocols, never leak unhandled exceptions, and execute tool calls in under 50ms for local static checks.
4. **Baseline Invariant:**
   - 100% pass rate across all existing 520 baseline tests.

---

## 5. Execution Bites Breakdown

- **BITE-P18-01:** Implement `DocSyncEngine` in `orchestrator/workstreams/audit/doc_sync.py` enforcing continuous alignment between code and docs.
- **BITE-P18-02:** Wire `DocSyncEngine` into `PRGate` and `AuditWorkstream` as a deterministic hard gate.
- **BITE-P18-03:** Implement `ClosedLoopRemediationDispatcher` in `orchestrator/evolution/remediation_dispatcher.py` to auto-schedule fixes for detected findings.
- **BITE-P18-04:** Implement `oragai-sre-mcp` server in `orchestrator/mcp/server.py` exposing core intelligence and verification tools.
- **BITE-P18-05:** Comprehensive verification suite `tests/test_strategic_convergence_p18.py`.
