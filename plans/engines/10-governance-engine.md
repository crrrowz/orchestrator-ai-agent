# Engine Plan 10: Adaptive Governance Engine

## 1. Objective
Design an Adaptive Governance Engine combining deterministic metrics, AST guards, token/budget limits, stagnation/velocity detection, chaos analysis, and circuit breakers into a multi-tiered safety and control layer.

## 2. Current Architecture Involved
- `orchestrator/control/token_governance.py`
- `orchestrator/control/budget_guard.py`
- `orchestrator/control/context_budget_manager.py`
- `orchestrator/control/adaptive/` (`governor.py`, `clamper.py`, `allocator.py`, `circuit_breaker.py`)
- `orchestrator/governance/` (`stagnation_detector.py`, `chaos_detector.py`, `checkpoint_evaluator.py`)
- `orchestrator/sentinel/` (`supervisor.py`, `self_healing.py`, `heuristics.py`, `diagnostics_db.py`)

## 3. Problem
Governance logic is currently scattered across three disconnected packages (`orchestrator/control/`, `orchestrator/governance/`, and `orchestrator/sentinel/`), resulting in duplicated state tracking, inconsistent circuit breaker tripping, and lack of a unified decision pipeline.

## 4. Proposed Design
Implement `GovernanceEngine` unifying all safety, budget, and trajectory controls:
- **Unified Policy Pipeline**: Evaluates every execution turn and state transition against Deterministic Metrics + Execution Evidence + Graph State + Optional LLM Trajectory Reasoning.
- **Budget & Token Governor**: Enforces token ceilings, dollar cost caps, rate limits, and dynamic budget extensions for productive agents.
- **Stagnation & Velocity Monitor**: Detects cyclic oscillation, repetitive file edits, semantic stagnation, and zero-progress loops.
- **Chaos & Drift Detector**: Detects out-of-scope edits, mass file deletions, and unintended codebase drift.
- **Circuit Breaker & Self-Healing**: Deterministically trips execution on threshold violations and triggers self-healing or rollback routines via Sentinel Diagnostics DB.

```text
       Execution Telemetry & Turn State
                       │
                       ▼
         ┌───────────────────────────┐
         │     Governance Engine     │
         └─────────────┬─────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                 ▼
[Budget/Token]   [Stagnation/Chaos]  [AST/Security]
     │                 │                 │
     └─────────────────┬─────────────────┘
                       │
                       ▼
             Deterministic Verdict
  ├── CONTINUE (Proceed to next step)
  ├── EXTEND_BUDGET (Productive progress detected)
  ├── REPLAN (Stagnation detected; trigger Task Engine)
  ├── RETRY (Transient failure; apply mutation)
  ├── DECOMPOSE (Task scope too broad)
  ├── VERIFY (Ready for independent verification)
  └── HALT (Circuit breaker tripped / Hard budget exceeded)
```

## 5. Files/Components Affected
- `orchestrator/engines/governance/engine.py`
- `orchestrator/engines/governance/models.py`
- `orchestrator/engines/governance/budget/` (`token_guard.py`, `cost_guard.py`, `rate_limiter.py`)
- `orchestrator/engines/governance/detectors/` (`stagnation.py`, `chaos.py`, `oscillation.py`)
- `orchestrator/engines/governance/guards/` (`ast_guard.py`, `command_guard.py`)
- `orchestrator/engines/governance/circuit_breaker.py`
- `orchestrator/engines/governance/sentinel_db.py`

## 6. Interfaces/Contracts
```python
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class GovernanceVerdict(str, Enum):
    CONTINUE = "continue"
    EXTEND_BUDGET = "extend_budget"
    REPLAN = "replan"
    RETRY = "retry"
    DECOMPOSE = "decompose"
    VERIFY = "verify"
    HALT = "halt"

class GovernanceDecision(BaseModel):
    verdict: GovernanceVerdict
    reason: str
    budget_adjustment_tokens: int = 0
    budget_adjustment_usd: float = 0.0
    suggested_action: Optional[str] = None
    metrics_snapshot: Dict[str, Any] = Field(default_factory=dict)

class IGovernanceEngine(IEngine):
    async def evaluate_turn(self, agent_name: str, telemetry: Dict[str, Any], context: Dict[str, Any]) -> GovernanceDecision: ...
    async def check_command_safety(self, command: str) -> bool: ...
    def record_anomaly(self, anomaly_type: str, details: Dict[str, Any]) -> None: ...
```

## 7. Data Flow
Execution Engine dispatches turn telemetry -> Governance Engine parallel evaluates Budget, Stagnation, Chaos, and Security -> Aggregates deterministic metrics into `GovernanceDecision` -> If `CONTINUE`, loop proceeds; if `REPLAN`/`RETRY`/`HALT`, signals Graph Engine to execute corrective edge.

## 8. State Transitions
`MONITORING -> WARNING -> STAGNATION_DETECTED / BUDGET_EXHAUSTED -> CIRCUIT_BROKEN -> SELF_HEALING / HALTED`.

## 9. Error Handling
Governance failures never fail silently; all anomalies and circuit trips are persisted to `sentinel_mesh.db` and broadcast via Event Engine.

## 10. Migration Strategy
Consolidate `orchestrator/control/` and `orchestrator/sentinel/` into `orchestrator/engines/governance/`, retaining backwards compatibility shims.

## 11. Tests
- Stagnation detector oscillation tests on synthetic repetitive edits.
- Hard token ceiling trip tests.
- Chaos detector tests on out-of-scope file modifications.
- AST guard syntax and dangerous node detection tests.

## 12. Acceptance Criteria
- 100% deterministic governance decision engine (non-reliant on pure LLM self-evaluation).
- Sub-5ms evaluation latency per turn.
- Unified diagnostics logging to Sentinel SQLite database.

## 13. Dependencies
Depends on Core Engine, Event Engine. Blocks Execution Engine and Graph Engine.

## 14. Risks
False positives in stagnation detection during long multi-step refactorings; mitigated by tracking semantic AST diffs rather than naive line counts.

## 15. Rollback Strategy
Fallback to `orchestrator/control/adaptive/governor.py`.
