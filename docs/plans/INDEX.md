# ORAGAI Target Strategic Plans & Master Architecture Index

This directory contains the forward-looking, active architectural specifications and implementation blueprints for the **ORAGAI (Orchestrator-AI-Agent)** multi-agent autonomous engineering factory.

Historical implementation plans (P0 through P14) covering the Hexagonal Core, Guarded FSM, Strangler Fig migration, Benchmark Engine, and Polyglot Driver Mesh have been successfully implemented, verified, and sealed in code (with 520 automated tests passing).

The active plans define the next generation of native capabilities derived from forensic analysis of the codebase, modern code intelligence architectures (e.g. Graft, Graphite, CodeRabbit), and continuous quality governance:

---

## Active Target Architecture Plans

### 1. [Plan 15: Native Codebase Intelligence & Symbol Graph System](P15_NATIVE_CODEBASE_INTELLIGENCE_AND_SYMBOL_GRAPH_PLAN.md)
- **Document ID:** `ORAGAI-PLAN-15-CODE-INTELLIGENCE`
- **Domain:** Codebase Understanding, AST Indexing & Structural Blast Radius
- **Key Capabilities:**
  - Zero-token offline repository orientation and symbol resolution.
  - SQLite WAL inverted symbol and call graph index.
  - Sub-second blast radius calculation for affected symbols and downstream callers.
  - Hexagonal `ICodeIntelligencePort` with hybrid `GraftCliIntelligenceAdapter` and fallback `NativeAstSymbolIndexAdapter`.
  - Tarjan's SCC cycle detector for circular import defense.

### 2. [Plan 16: Native Change Management & Stacked Diffs System](P16_NATIVE_CHANGE_MANAGEMENT_AND_STACKED_DIFFS_PLAN.md)
- **Document ID:** `ORAGAI-PLAN-16-STACKED-DIFFS`
- **Domain:** GitOps, Stacked Branches & Conflict Classification
- **Key Capabilities:**
  - Multi-milestone stacked branch DAG (`IStackedVCSPort`).
  - Topological rebase orchestration and automated descendant restacking.
  - AST-driven semantic conflict classifier (distinguishing trivial syntax/imports from structural breaking changes).
  - Virtual pre-merge simulation queue ensuring zero broken main-line builds.

### 3. [Plan 17: Native AI Code Review & Automated PR Gate Engine](P17_NATIVE_AI_CODE_REVIEW_AND_PR_GATE_PLAN.md)
- **Document ID:** `ORAGAI-PLAN-17-CODE-REVIEW-PR-GATE`
- **Domain:** Quality Assurance, Security Boundaries & Pull Request Automation
- **Key Capabilities:**
  - Multi-tier PR Review Gate (`IPRGatePort`) combining zero-token deterministic hard gates with senior AI reviewer agent.
  - Entropy and secret leak detection (API keys, private tokens).
  - Universal anti-stub enforcement (`# TODO`, `pass`, `NotImplementedError`, `todo!()`).
  - Semantic AST hunk classification (additive, modifying, breaking).
  - Interactive contributor action checklists and automated GitHub PR commenting.

### 4. [Plan 18: End-to-End Autonomous Evolution, Doc Sync & MCP Server](P18_AUTONOMOUS_EVOLUTION_DOC_SYNC_AND_MCP_SERVER_PLAN.md)
- **Document ID:** `ORAGAI-PLAN-18-STRATEGIC-CONVERGENCE`
- **Domain:** Self-Healing Loops, Codebase Health & Model Context Protocol
- **Key Capabilities:**
  - Closed-loop autonomous remediation: converting architectural audit findings into executable `TaskTruthGraph` requirements.
  - Continuous Codebase Health Index ($\Delta\text{CHI} \ge 0.0$) gating with automatic GitOps rollback.
  - Continuous Documentation-Code Sync Engine preventing documentation drift across releases.
  - High-performance `oragai-sre-mcp` server exposing zero-token AST, Graft, polyglot, and review tools to external agent ecosystems.

---

## Incremental Execution Protocol
All implementations of these plans follow the established governance protocol documented in `oragai-incremental-execution/SKILL.md`:
- Atomic, bite-sized tasks with explicit acceptance criteria.
- Mandatory pre-flight syntax checks and zero-stub invariant verification.
- Zero regressions across the 520 baseline test suite.
