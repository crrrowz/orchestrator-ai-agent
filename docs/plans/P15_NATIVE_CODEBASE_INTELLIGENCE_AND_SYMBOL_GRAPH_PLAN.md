# PLAN 15: NATIVE CODEBASE INTELLIGENCE & SYMBOL GRAPH SYSTEM
## High-Performance Symbol Graph, Inverted AST Indices, Cross-File Dependency Invariants & Zero-Token Navigation

---

### Executive Metadata
- **Document ID:** `ORAGAI-PLAN-15-CODE-INTELLIGENCE`
- **Classification:** Enterprise Architectural Blueprint & Production Implementation Plan
- **Scope:** Zero-Token Repository Orientation, Incremental Inverted Symbol Index, Deep Call/Import Graph Analysis, AST Invariant & Anti-Stub Verification, Polyglot Integration, and Graft CLI Engine Wiring
- **Target Seam:** `orchestrator/ports/driven/intelligence_port.py`, `orchestrator/analysis/code_intel/`, `orchestrator/adapters/intelligence/`
- **Governing Standard:** Hexagonal Architecture (Ports & Adapters), Inversion of Control (IoC), Zero Stubs, Incremental Execution (`oragai-incremental-execution/SKILL.md`)

---

## 1. Problem Statement & Architectural Gap

While phases P0 through P14 established the Hexagonal Core, Guarded FSM, Strangler Seams, and Polyglot Drivers, ORAGAI still suffers from significant code intelligence limitations identified in the 360° Forensic Analysis:

1. **Context Window Inflation & Token Bleed:**
   - Without an incremental symbol index, agents read whole files or arbitrarily clamped windows (250 LOC / 12,000 characters).
   - Multi-file tasks force huge contexts into the prompt, rapidly exhausting context budgets ($\mathcal{B}_{\text{tokens}}$) and degrading reasoning quality.
2. **Graft CLI Decoupling & Fragility:**
   - `GraftContextProvider` (`orchestrator/analysis/graft_context.py`) is an ad-hoc utility rather than a formal driven hexagonal port.
   - When Graft is missing or fails on Windows, fallback behavior degrades silently to raw file reading without structured structural graphs.
3. **Absence of Unified Cross-File Symbol Knowledge:**
   - Current symbol outline extraction (`orchestrator/ports/driven/language_port.py`) is isolated per-file.
   - There is no in-memory or persisted SQLite graph mapping caller-callee relationships, class inheritance hierarchies, interface implementations, or blast-radius propagation across files.
4. **Shallow Impact Analysis for Refactoring & Edits:**
   - Changes to core interfaces (e.g. `VCSPort`, `FSMState`, `Requirement`) are evaluated in isolation without automatic blast-radius calculation.

---

## 2. Target Architecture & Hexagonal Placement

The Native Code Intelligence system is implemented strictly behind driven ports conforming to Hexagonal Architecture:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           ORAGAI CONTROL & GOVERNANCE                             │
│       (GuardedFSMEngine, TaskTruthGraph, ReviewWorkstream, AuditWorkstream)       │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │          DRIVEN PORT: ICodeIntelligencePort       │
                │   (orchestrator/ports/driven/intelligence_port.py)│
                └─────────────────────────┬─────────────────────────┘
                                          │
            ┌─────────────────────────────┴─────────────────────────────┐
            ▼                                                           ▼
┌──────────────────────────────────────────┐  ┌──────────────────────────────────────────┐
│   NativeAstSymbolIndexAdapter            │  │        GraftCliIntelligenceAdapter       │
│   (orchestrator/adapters/intelligence/   │  │   (orchestrator/adapters/intelligence/   │
│    ast_index_adapter.py)                 │  │    graft_adapter.py)                     │
│   • SQLite WAL Symbol & Call Graph Store │  │   • Subprocess Bridge to Graft CLI       │
│   • Tarjan SCC Circular Import Guard     │  │   • Fast Repository Skeletonization      │
│   • Incremental Merkle Hash Re-indexing  │  │   • Callers / Impact Blast Radius Engine │
└──────────────────────────────────────────┘  └──────────────────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### 3.1 Port Protocol: `ICodeIntelligencePort`
Location: `orchestrator/ports/driven/intelligence_port.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Set, runtime_checkable

@dataclass(frozen=True)
class SymbolLocation:
    file_path: str
    symbol_name: str
    kind: str  # "class", "function", "method", "interface", "type_alias"
    line_start: int
    line_end: int
    docstring: Optional[str]
    parameters: List[str]
    return_type: Optional[str]

@dataclass(frozen=True)
class BlastRadiusReport:
    target_symbol: str
    affected_files: List[str]
    direct_callers: List[SymbolLocation]
    transitive_callers_count: int
    risk_score: float  # 0.0 (isolated) to 1.0 (core breaking change)

@runtime_checkable
class ICodeIntelligencePort(Protocol):
    def index_workspace(self, workspace: Path, force: bool = False) -> None:
        ...
    def find_symbol(self, symbol_name: str) -> List[SymbolLocation]:
        ...
    def get_symbol_skeleton(self, file_path: str) -> str:
        ...
    def get_call_graph(self, symbol_name: str, direction: str = "in") -> List[SymbolLocation]:
        ...
    def compute_blast_radius(self, modified_files: List[str]) -> BlastRadiusReport:
        ...
    def detect_circular_dependencies(self) -> List[List[str]]:
        ...
```

### 3.2 Native Inverted Symbol Index: `NativeAstSymbolIndexAdapter`
Location: `orchestrator/adapters/intelligence/ast_index_adapter.py`
- Uses SQLite with WAL mode (`.oragai/code_intel.db`) to cache AST nodes, symbol definitions, and import bindings.
- Uses file content SHA-256 hashes to re-parse only modified or added files.
- Integrates with `ILanguageDriver` mesh (`orchestrator/ports/driven/language_port.py`) to parse Python, Rust, Go, TypeScript/JS, and C/C++.
- Guarantees `<50ms` symbol queries and `<200ms` blast radius computation without external dependencies.

### 3.3 Graft Hybrid Adapter: `GraftCliIntelligenceAdapter`
Location: `orchestrator/adapters/intelligence/graft_adapter.py`
- Seamlessly probes for `graft` or `graft.ps1` in PATH.
- If Graft is present, delegates `graft skeleton`, `graft callers`, and `graft blast` directly for sub-millisecond execution.
- If Graft is absent, falls back deterministically to `NativeAstSymbolIndexAdapter` without crashing or throwing unhandled exceptions.

---

## 4. Invariants & Verification Plan

1. **Zero-Token Symbol Discovery Invariant:**
   - Symbol lookups and signature extractions must run offline with 0 LLM tokens consumed.
2. **Zero Regressions Invariant:**
   - All 520 baseline tests must continue to pass (100% green).
3. **Cycle-Free Codebase Invariant:**
   - Static analysis must assert 0 circular imports across all `orchestrator` packages using Tarjan's SCC algorithm.
4. **Anti-Stub Invariant:**
   - Code intelligence indexer must flag any `# TODO`, `raise NotImplementedError`, or empty stubs in indexed files.

---

## 5. Execution Bites Breakdown

- **BITE-P15-01:** Define `ICodeIntelligencePort` protocol and domain models in `orchestrator/ports/driven/intelligence_port.py`.
- **BITE-P15-02:** Implement `NativeAstSymbolIndexAdapter` in `orchestrator/adapters/intelligence/ast_index_adapter.py` with SQLite WAL store and Merkle change detection.
- **BITE-P15-03:** Refactor `GraftContextProvider` into `GraftCliIntelligenceAdapter` implementing `ICodeIntelligencePort`.
- **BITE-P15-04:** Wire Code Intelligence into `ContextSynthesisWorkstream` (`orchestrator/workstreams/context/synthesizer.py`) for automatic targeted context injection.
- **BITE-P15-05:** Verification test suite `tests/test_code_intelligence_p15.py` validating symbol lookup, blast radius, and Graft fallback.
