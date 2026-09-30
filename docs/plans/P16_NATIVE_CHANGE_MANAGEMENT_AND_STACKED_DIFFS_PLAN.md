# PLAN 16: NATIVE CHANGE MANAGEMENT & STACKED DIFFS SYSTEM
## High-Precision Stacked Branches, Dependency-Aware Restacking, Rebase Conflict Classification & Merge Queue Engine

---

### Executive Metadata
- **Document ID:** `ORAGAI-PLAN-16-STACKED-DIFFS`
- **Classification:** Enterprise Architectural Blueprint & Production Implementation Plan
- **Scope:** Native Stacked Branch DAG, Dependency-Aware Rebase Orchestration, Upstream Restacking, Git Conflict Classification, Milestone-to-Stack Mapping, and Deterministic Merge Queue Engine
- **Target Seam:** `orchestrator/ports/driven/stacked_vcs_port.py`, `orchestrator/vcs/stacked/`, `orchestrator/adapters/vcs/stacked_adapter.py`
- **Governing Standard:** Hexagonal Architecture (Ports & Adapters), Inversion of Control (IoC), Non-destructive GitOps, Incremental Execution (`oragai-incremental-execution/SKILL.md`)

---

## 1. Problem Statement & Architectural Gap

As documented in the *ORAGAI Native Code Intelligence & Review System* analysis, modern multi-agent systems fail catastrophically when attempting large, monolithic changes across multiple modules:

1. **Monolithic PR & Branch Bloat:**
   - Currently, `GitOps` and `GitOpsAdapter` (`orchestrator/adapters/vcs/git_adapter.py`) only support a single working branch with atomic milestone commits and hard resets (`git reset --hard`).
   - Complex engineering tasks involving 5–10 milestones produce massive, unreviewable diffs on a single branch.
2. **Absence of Branch Lineage & Ancestry Tracking:**
   - Milestones in `MilestoneDAG` (`orchestrator/workstreams/milestone_dag/`) exist only in memory as ephemeral execution nodes.
   - When upstream milestone code changes or fails review, there is no mechanism to propagate rebases or restack dependent downstream work without manual intervention or corrupting the Git tree.
3. **Destructive Conflict Resolution:**
   - Standard Git rebase or merge operations fail abruptly on conflicts. ORAGAI lacks an automated conflict classifier to differentiate between semantic conflicts (renamed methods, import alterations) and trivial syntactic whitespace/comment clashes.
4. **Merge Serialization Bottleneck:**
   - Without a dependency-aware Merge Queue, PRs cannot be validated against their projected target states before integration, leading to broken master branches and test regressions.

---

## 2. Target Architecture & Hexagonal Placement

The Native Change Management system introduces stacked diffs as a first-class citizen in ORAGAI's Hexagonal Architecture:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           ORAGAI CONTROL & GOVERNANCE                             │
│         (MilestoneDAGDispatcher, GuardedFSMEngine, TaskTruthGraph)                │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │          DRIVEN PORT: IStackedVCSPort             │
                │   (orchestrator/ports/driven/stacked_vcs_port.py) │
                └─────────────────────────┬─────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │             GitStackedDiffAdapter                 │
                │   (orchestrator/adapters/vcs/stacked_adapter.py)   │
                │   • Stacked Branch DAG (Parent/Child Lineage)     │
                │   • Dependency-Aware Restack Orchestrator         │
                │   • AST & Semantic Conflict Classifier           │
                │   • Virtual Pre-Merge Simulation Queue            │
                └───────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### 3.1 Port Protocol: `IStackedVCSPort`
Location: `orchestrator/ports/driven/stacked_vcs_port.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Protocol, runtime_checkable

class ConflictSeverity(str, Enum):
    TRIVIAL_SYNTAX = "TRIVIAL_SYNTAX"
    IMPORT_ORDER = "IMPORT_ORDER"
    SEMANTIC_SIGNATURE = "SEMANTIC_SIGNATURE"
    STRUCTURAL_DESTRUCTIVE = "STRUCTURAL_DESTRUCTIVE"

@dataclass(frozen=True)
class StackedBranchNode:
    branch_name: str
    milestone_id: str
    parent_branch: Optional[str]
    commit_sha: str
    is_rebased: bool
    is_merged: bool

@dataclass(frozen=True)
class ConflictAnalysis:
    file_path: str
    severity: ConflictSeverity
    conflicting_symbols: List[str]
    auto_resolvable: bool
    proposed_resolution: Optional[str]

@runtime_checkable
class IStackedVCSPort(Protocol):
    def initialize_stack(self, base_branch: str) -> None:
        ...
    def create_stacked_branch(self, branch_name: str, milestone_id: str, parent_branch: str) -> StackedBranchNode:
        ...
    def get_stack_topology(self) -> List[StackedBranchNode]:
        ...
    def restack_descendants(self, root_branch: str) -> List[str]:
        ...
    def analyze_conflicts(self, source_branch: str, target_branch: str) -> List[ConflictAnalysis]:
        ...
    def queue_for_merge(self, branch_name: str, test_command: str) -> bool:
        ...
```

### 3.2 Stack Topology & Branch DAG Engine
Location: `orchestrator/vcs/stacked/dag.py`
- Tracks branch lineage persisted in `.oragai/stacked_branches.json`.
- Maps each milestone from `MilestoneDAG` to an isolated, atomic Git branch (e.g. `oragai/task-42/m01-models`, `oragai/task-42/m02-ports`, `oragai/task-42/m03-adapter`).
- Validates that child branches cleanly inherit from parent branches without diverging histories.

### 3.3 Dependency-Aware Restack Orchestrator
Location: `orchestrator/vcs/stacked/restacker.py`
- When a parent branch receives modifications (e.g. following a code review fix or audit finding), the `RestackOrchestrator` computes the topological sort of all descendant branches.
- Uses `git rebase --onto` under programmatic guard controls to fast-forward descendants.
- Emits pre-rebase checkpoint snapshots so any failure can be aborted cleanly (`git rebase --abort`) with zero repository state corruption.

### 3.4 Conflict Classifier & Autonomous Resolver
Location: `orchestrator/vcs/stacked/conflict_classifier.py`
- Parses Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
- Categorizes conflicts:
  - `TRIVIAL_SYNTAX` / `IMPORT_ORDER`: Automatically resolved via AST normalization and alphabetical sorting without agent intervention.
  - `SEMANTIC_SIGNATURE`: Injected into the Review/Developer workstream with localized AST diffs for targeted agent resolution.
  - `STRUCTURAL_DESTRUCTIVE`: Halts automated restack and requests human or higher-tier architectural guidance.

---

## 4. Invariants & Verification Plan

1. **Non-Destructive GitOps Invariant:**
   - Any failed rebase or merge operation must automatically revert to its clean pre-flight checkpoint SHA.
2. **Topological Ordering Invariant:**
   - Descendant branches cannot be rebased before their direct parent branch has passed all cryptographic evidence and test gates.
3. **Zero Test Regression Across Stacks:**
   - Every stacked branch must independently pass the full project test suite (`pytest`) before merge queue qualification.
4. **Baseline Invariant:**
   - All 520 baseline tests must remain green with zero regressions.

---

## 5. Execution Bites Breakdown

- **BITE-P16-01:** Implement `IStackedVCSPort` protocol and domain models in `orchestrator/ports/driven/stacked_vcs_port.py`.
- **BITE-P16-02:** Develop `StackedBranchDAG` engine in `orchestrator/vcs/stacked/dag.py` with JSON metadata persistence.
- **BITE-P16-03:** Implement `RestackOrchestrator` and safe rebase transaction management in `orchestrator/vcs/stacked/restacker.py`.
- **BITE-P16-04:** Implement AST-driven `ConflictClassifier` in `orchestrator/vcs/stacked/conflict_classifier.py`.
- **BITE-P16-05:** Implement `GitStackedDiffAdapter` in `orchestrator/adapters/vcs/stacked_adapter.py`.
- **BITE-P16-06:** Comprehensive verification suite `tests/test_stacked_diffs_p16.py` verifying stack creation, restacking, and conflict recovery.
