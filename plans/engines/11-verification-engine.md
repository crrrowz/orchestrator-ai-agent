# Engine Plan 11: Verification Engine

## 1. Objective
Design an independent, evidence-based Verification Engine that validates task completion through deterministic test execution, static analysis, architectural conformance, security scans, and evidence gates rather than agent claims.

## 2. Current Architecture Involved
- `orchestrator/ci/` (`verifier.py`, `evidence_gate.py`, `root_cause.py`, `analyzer.py`, `pytest_parser.py`)
- `orchestrator/analysis/audit/` (`engine.py`, `scanner.py`, `validator.py`)
- `orchestrator/workstreams/review/` (`diff_verifier.py`, `evaluator.py`)

## 3. Problem
Verification logic is split across CI modules and audit scripts. It lacks a unified verification rubric, standardized evidence bundle formats, and the ability to register custom verification suites dynamically.

## 4. Proposed Design
Implement `VerificationEngine`:
- **Evidence Bundle Protocol**: Requires agents to provide verifiable artifacts (Test logs, Git diffs, AST parse trees, Static analysis reports) before completion is evaluated.
- **Pluggable Verifier Suites**: Modular verification providers:
  - `PyTestVerifier`: Parses test execution results, assertion counts, and coverage metrics.
  - `StaticAuditVerifier`: Scans for security vulnerabilities, syntax errors, and style violations.
  - `ArchitecturalVerifier`: Enforces module boundary invariants and dependency directions (Graft integration).
  - `DiffVerifier`: Verifies git diff relevance against the assigned task scope.
- **Verification Gate & Rubric**: Computes a deterministic composite completion score; rejects completion if evidence is missing or fails criteria.

## 5. Files/Components Affected
- `orchestrator/engines/verification/engine.py`
- `orchestrator/engines/verification/models.py`
- `orchestrator/engines/verification/rubric.py`
- `orchestrator/engines/verification/verifiers/` (`pytest_verifier.py`, `audit_verifier.py`, `arch_verifier.py`, `diff_verifier.py`)
- `orchestrator/engines/verification/evidence_gate.py`

## 6. Interfaces/Contracts
```python
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"

class VerificationDefect(BaseModel):
    category: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None

class VerificationReport(BaseModel):
    task_id: str
    status: VerificationStatus
    score: float  # 0.0 - 1.0
    passed: bool
    defects: List[VerificationDefect] = Field(default_factory=list)
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    feedback_for_agent: str = ""

class IVerifier(ABC):
    @abstractmethod
    async def verify(self, workspace_path: str, task_context: Dict[str, Any]) -> VerificationReport: ...

class IVerificationEngine(IEngine):
    def register_verifier(self, name: str, verifier: IVerifier) -> None: ...
    async def verify_task(self, task_id: str, verifiers: Optional[List[str]] = None) -> VerificationReport: ...
```

## 7. Data Flow
Agent signals task completion -> Verification Engine collects evidence bundle -> Dispatches registered verifiers concurrently -> Verifiers inspect tests, diffs, AST, and security -> Aggregates results into `VerificationReport` -> If `PASSED`, Graph Engine transitions to complete; if `FAILED`, structured feedback is routed back to Developer agent.

## 8. State Transitions
`COLLECTING_EVIDENCE -> VERIFYING -> AGGREGATING_SCORES -> VERIFIED_SUCCESS / REJECTED_WITH_DEFECTS`.

## 9. Error Handling
Test runner crashes or parse failures are treated as verification failures with `CRITICAL` defects, preventing false-positive task completions.

## 10. Migration Strategy
Port existing `CIVerifier` and `AuditEngine` into native verifiers under `orchestrator/engines/verification/verifiers/`.

## 11. Tests
- Clean pass verification tests on passing test suites.
- Defect extraction and feedback generation tests on broken code.
- Boundary violation tests on invalid cross-module imports.

## 12. Acceptance Criteria
- Zero task completion without verifiable evidence.
- Structured, actionable defect reports returned on failure.

## 13. Dependencies
Depends on Core Engine, Tool Engine, Event Engine. Blocks Graph Engine.

## 14. Risks
Flaky tests causing false verification failures; mitigated by automatic test re-run filters for non-deterministic test suites.

## 15. Rollback Strategy
Fallback to `orchestrator/ci/verifier.py`.
