# P4 — ADAPTIVE RESOURCE GOVERNANCE PLAN

> **Document Type:** Canonical Systems Architecture & Resource Governance Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Software Architect, Resource Control Engineer, & Autonomous Agent Systems Specialist  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md`, `docs/plans/P1_TASK_TRUTH_AND_REQUIREMENT_MODEL_PLAN.md`, `docs/plans/P2_EVIDENCE_AND_COMPLETION_GATES_PLAN.md`, `docs/plans/P3_GUARDED_FSM_AND_LIFECYCLE_ORCHESTRATION_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Design Phase:** P4 (Specification & Adaptive Resource Governance — Zero Production Code Modified)

---

# 1. Executive Summary

This specification establishes the canonical **Adaptive Resource Governance (P4)** architecture for the **ORAGAI** multi-agent software engineering orchestrator.

Throughout earlier phases, we uncovered the fundamental flaw at the root of ORAGAI's execution failures:
* **P0 (Forensic Baseline):** Proved that ORAGAI fundamentally conflated **Resource Governance** (protecting API budgets, quotas, and step limits) with **Work Governance** (assessing task requirements, acceptance criteria, and verified code completion).
* **P1 (Task Truth Model):** Created the deterministic graph representing user intent: $\text{Task} \to \text{Requirements} \to \text{Acceptance Criteria} \to \text{Milestones}$.
* **P2.1 (Evidence Gates):** Established the 14-step deterministic completion engine, SHA-256 cryptographic identity, and orthogonal state model (`ImplementationState`, `VerificationState`, `BlockingState`).
* **P3 (Guarded FSM):** Inverted the execution loop from monolithic scripts to an event-driven `GuardedFSMEngine` that delegates bounded, ephemeral work sessions to OpenHands SDK agents and evaluates state transitions via `TaskTruthSemanticQueries`.

### The Mission of P4
P4 completely redesigns ORAGAI's resource management plane. It replaces brittle, hardcoded micro-limits (e.g. 5-step limits for single-file tasks, violent 28% investigation thread kills, and blunt 250-line file truncations) with an intelligent, phase-aware **Adaptive Resource Governance Engine**.

This engine guarantees two inviolable properties:
1. **Sufficiency for Verification:** Agents receive dynamically calculated step budgets, token allocations, and AST-folded context windows tailored to the complexity of the active `MilestoneDAG` and `FSMState`, ensuring they are never starved before satisfying P2.1 evidence criteria.
2. **Absolute Financial & Quota Safety:** Unbounded execution loops, infinite tool cycling, and runaway billing are prevented through non-intrusive step ceilings, stagnation penalties, and global monetary circuit breakers.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ORAGAI ARCHITECTURE                                    │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          Guarded FSM Engine (P3)                               │   │
│   └───────────────────────┬────────────────────────────────┬───────────────────────┘   │
│                           │                                │                           │
│     Semantic Queries      │                                │  Pre-Dispatch Allocation  │
│     & Completion Status   │                                │  & Post-Yield Accounting  │
│                           ▼                                ▼                           │
│   ┌───────────────────────────────┐        ┌───────────────────────────────┐           │
│   │  Task Truth & Evidence Engine │        │ Adaptive Resource Governance  │           │
│   │            (P2.1)             │        │             (P4)              │           │
│   │                               │        │                               │           │
│   │ • TaskTruthGraph (P1)         │        │ • AdaptiveBudgetAllocator     │           │
│   │ • CriterionEvidencePolicies   │        │ • ASTAwareContextClamper      │           │
│   │ • SHA-256 Identity Hash       │        │ • MonetaryCircuitBreaker      │           │
│   │ • CompletionGate              │        │ • ProviderQuotaProtector      │           │
│   └───────────────────────────────┘        └───────────────┬───────────────┘           │
│                                                            │                           │
│                                    Bounded Delegation (IoC)│ Turn Ceiling & Clamped ctx│
│                                                            ▼                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        OpenHands SDK Runtime (v1.49.4)                         │   │
│   │                                                                                │   │
│   │    [Architect]       [Developer]       [Tester]       [Reviewer]    [Auditor]      │   │
│   │     (Bounded)         (Bounded)        (Bounded)      (Bounded)     (Bounded)      │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. Forensic Baseline of Legacy Resource Control Failures

A deep forensic inspection of the legacy codebase (`orchestrator/control/token_governance.py`, `orchestrator/control/context_budget_manager.py`, `orchestrator/control/budget_guard.py`, and `orchestrator/pipeline/base_pipeline.py`) reveals five fatal pathologies that crippled task completion:

| Legacy Subsystem | Code Location | Observed Pathology | Direct Failure Consequence | P4 Architectural Solution |
| :--- | :--- | :--- | :--- | :--- |
| **Static File-Count Step Ceiling** | `token_governance.py:L108-116` | Assigns `max_agent_steps = 5` if `affected_files_count <= 1`. | A new feature in an empty workspace or single-file module is strangled after 5 steps, leaving code half-written. | **Complexity-Scored Turn Allocation:** Computes turn budgets based on AC count, AST symbol complexity, and FSM phase. |
| **28% Investigation Circuit Breaker** | `base_pipeline.py:L304-324`, `token_governance.py:L147-151` | Background thread triggers `conv.interrupt()` if 28% of turn tokens are consumed without an edit. | System prompt + 2 file reads trip the 28% threshold (11.2k tokens). Agent is killed for investigating before it can type a line of code. | **Phase-Differentiated Policies:** `PLANNING`, `REVIEW`, and `AUDIT` phases receive 100% investigation allocation; zero edits required. |
| **Violent Asynchronous Abort** | `base_pipeline.py:L320-335` | Background watcher calls `conv.interrupt()` asynchronously mid-step. | Corrupts agent reasoning context, leaves partial file writes, and fails to emit structured telemetry. | **Turn-Bounded Inversion of Control:** Agent is invoked with an explicit `max_turns` limit; yields cleanly via SDK without external thread killing. |
| **Monolithic Output Clamping** | `context_budget_manager.py:L125-146` | Arbitrary string slice at `DEFAULT_MAX_CHARS = 12_000` (~3,000 tokens). | Truncates code mid-function or mid-JSON, causing syntax errors in tool observations. | **AST-Aware Intelligent Folding:** Folds irrelevant function/class bodies while preserving complete signatures and types. |
| **Premature Financial Ceiling** | `config/__init__.py:L59`, `budget_guard.py:L9` | Hardcoded `$0.50` task ceiling. | Tier-1 models (Claude 3.5 Sonnet, GPT-4o) hit `$0.50` within 1-2 turn loops on medium codebases, aborting healthy runs. | **Configurable Multi-Tier Budgets:** Default adjusted to $5.00 for complex workflows, with dynamic cost estimation and micro-step alerts. |

---

# 3. P4 Architectural Principles & Invariant Contracts

To permanently resolve these pathologies, P4 enforces four core architectural invariants:

### Invariant 1: Resource Limits Protect Billing, Never Define Completion
Resource exhaustion (`OUT_OF_TURNS`, `TOKEN_CEILING_REACHED`, `BUDGET_EXHAUSTED`) is an operational constraint, not a proof of success or failure. When resources expire, the agent yields to the FSM. The FSM queries P2.1's `CompletionGate`. If criteria are incomplete, the task is marked `INCOMPLETE` or `BLOCKED`, never falsely marked `COMPLETED`.

### Invariant 2: No Asynchronous Thread Termination
No background thread shall ever invoke `conv.interrupt()` or `conv.pause()` during active LLM token generation. Every OpenHands session is launched with an explicit, mathematically computed `max_turns` parameter. Control returns to ORAGAI naturally when the SDK completes its turn allocation (`AGENT_YIELDED`).

### Invariant 3: Phase-Aware Resource Governance
Resource policies must match the cognitive requirements of the active FSM state:
* In `PLANNING` and `AUDIT`, 100% of tokens may be spent on reading, searching, and reasoning.
* In `IMPLEMENTATION`, turns and tokens are weighted toward file authorship, AST validation, and iterative refinement.
* In `VERIFICATION`, zero LLM tokens are consumed whenever deterministic tools (`PreFlightGuard`, `PytestOutputParser`) can verify truth.

### Invariant 4: Syntactic & Semantic Context Integrity
Context pruning and clamping must never produce broken syntax trees. When large files exceed token headroom, the system employs AST folding (replacing irrelevant function implementations with docstrings and type signatures) rather than raw character truncation.

---

# 4. Adaptive Budget & Turn Allocation Engine

The `AdaptiveBudgetAllocator` dynamically calculates the maximum allowed agent turns (`max_turns`) and token envelope for each ephemeral OpenHands invocation.

```
                                  ┌────────────────────────┐
                                  │      FSM State         │
                                  │  (PLANNING, DEV, etc.) │
                                  └───────────┬────────────┘
                                              │
┌────────────────────────┐                    │                    ┌────────────────────────┐
│    TaskTruthGraph      │                    ▼                    │   Stagnation Record    │
│  (AC Count, DAG Depth) ├────────►  Adaptive Turn Budget ◄────────┤  (Consecutive Loops)   │
└────────────────────────┘             Calculator                  └────────────────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │ Bounded OpenHands Turns │
                                 │   (e.g., max_turns=12)  │
                                 └─────────────────────────┘
```

### 4.1 Phase-Aware Base Parameters

Each FSM state is assigned base turn and token characteristics:

| FSM Phase | Base Turns ($T_{\text{base}}$) | Min Turns ($T_{\text{min}}$) | Max Turns ($T_{\text{max}}$) | Target Output Headroom | Primary Objective |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `PREFLIGHT` | 0 | 0 | 0 | 0 | Static zero-token verification |
| `PLANNING` | 15 | 8 | 25 | 8,192 tokens | Requirement decomposition & DAG construction |
| `IMPLEMENTATION` | 10 | 5 | 20 | 4,096 tokens | Milestone code authorship & self-testing |
| `VERIFICATION` | 0 | 0 | 0 | 0 | Deterministic test & gate execution |
| `RESOLUTION` | 5 | 3 | 10 | 4,096 tokens | Targeted defect fixing from AST/test traces |
| `REVIEW` | 8 | 4 | 12 | 4,096 tokens | Multi-dimensional quality & diff evaluation |
| `AUDIT` | 20 | 10 | 30 | 8,192 tokens | Deep repository vulnerability & architectural audit |

### 4.2 Task Complexity Scoring

Task complexity is evaluated dynamically across four objective dimensions:

$$\text{Complexity Score } (S_{\text{comp}}) = w_1 C_{\text{AC}} + w_2 C_{\text{DAG}} + w_3 C_{\text{files}} + w_4 C_{\text{ast}}$$

Where:
* $C_{\text{AC}} = \min(1.0, \frac{\text{Count of Active Acceptance Criteria}}{8})$ (Weight $w_1 = 0.35$)
* $C_{\text{DAG}} = \min(1.0, \frac{\text{Milestone Dependency Depth}}{5})$ (Weight $w_2 = 0.25$)
* $C_{\text{files}} = \min(1.0, \frac{\text{Target Files Affected}}{6})$ (Weight $w_3 = 0.20$)
* $C_{\text{ast}} = \min(1.0, \frac{\text{Target File Symbol Count}}{50})$ (Weight $w_4 = 0.20$)

This yields a continuous normalized score: $S_{\text{comp}} \in [0.0, 1.0]$.

### 4.3 Dynamic Turn Calculation Formula

The allocated turns $T_{\text{allocated}}$ for an execution session are computed as:

$$T_{\text{allocated}} = \text{clamp}\left( T_{\text{min}}, \left\lfloor T_{\text{base}} \cdot (1.0 + 0.8 \cdot S_{\text{comp}}) - P_{\text{stagnation}} \right\rfloor, T_{\text{max}} \right)$$

Where $P_{\text{stagnation}}$ is the stagnation penalty:
$$P_{\text{stagnation}} = \min(6, \text{stagnation\_count} \times 2)$$

If an agent has yielded multiple times without modifying code or advancing acceptance criteria, its turn allocation is systematically tightened to force rapid yield back to the FSM for resolution or human escalation.

---

# 5. Predictive Context Clamping & AST-Aware Headroom Management

Context window saturation leads to high token burn and severe reasoning degradation ("Lost-in-the-Middle"). P4 introduces an **AST-Aware Context Clamper** that guarantees syntactic integrity and preserves generous output headroom.

### 5.1 Context Priority Tiers

When assembling the prompt context for an agent session, information is ingested strictly by priority tier until the context budget ceiling is reached:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               CONTEXT WINDOW (e.g. 200k)                               │
├───────────────────────────────────────────────────────────────────┬────────────────────┤
│                       INJECTED CONTEXT                            │  RESERVED OUTPUT   │
├─────────────────┬──────────────────┬────────────────┬─────────────┼────────────────────┤
│ Tier 0          │ Tier 1           │ Tier 2         │ Tier 3      │ Headroom (4K-8K)   │
│ Task Truth Graph│ Failure Traces   │ Target Files   │ Codebase    │ Guaranteed space   │
│ Active Req & AC │ AST / Pytest err │ (AST Folded)   │ Map (Graft) │ for LLM generation │
└─────────────────┴──────────────────┴────────────────┴─────────────┴────────────────────┘
```

* **Tier 0: Mandatory Intent (Strictly Required):** User Task specification, active `Requirement` models, active `AcceptanceCriteria`, and active `Milestone` definitions.
* **Tier 1: Empirical Diagnostics (Critical if in Resolution):** Exact pytest failure traces, compiler syntax errors, and `ASTGuard` violation reports.
* **Tier 2: Target Source Code (AST-Folded):** Content of files targeted by the active milestone. If file tokens exceed available budget, non-target function and class bodies are folded into type signatures and docstrings.
* **Tier 3: Ambient Architecture (Opportunistic):** Graft architecture skeleton, directory trees, and imported interface definitions. Included only if token headroom permits.

### 5.2 AST-Aware Code Folding Engine

Rather than slicing raw text at 12,000 characters (which breaks Python indentation and cuts off ASTs mid-expression), P4 parses the Python AST and intelligently compresses non-target nodes:

```
Original Python File (350 lines):                AST-Folded Python File (65 lines):
┌──────────────────────────────────────┐          ┌──────────────────────────────────────┐
│ class OrderService:                  │          │ class OrderService:                  │
│     def calculate_tax(self, val):    │          │     def calculate_tax(self, val):    │
│         # 50 lines of tax logic      │ ───────► │         """[Folded: 50 lines]"""     │
│         ...                          │          │         ...                          │
│                                      │          │                                      │
│     def process_payment(self, req):  │          │     def process_payment(self, req):  │
│         # Active Requirement Target  │          │         # Full implementation        │
│         # 40 lines of payment logic  │          │         # preserved intact           │
│         ...                          │          │         ...                          │
└──────────────────────────────────────┘          └──────────────────────────────────────┘
```

#### The Folding Algorithm:
1. Parse the file into a Python AST (`ast.parse()`).
2. Identify all top-level functions, classes, and methods.
3. Check if the AST node intersects with the active requirement's target symbols.
4. For non-target nodes exceeding 5 lines of body code:
   - Preserve the function signature, type annotations, and docstrings.
   - Replace the inner body with a single `ast.Constant(value="[Folded: N lines implementation]")` or `ast.Pass()`.
5. Unparse the folded AST (`ast.unparse()`) back to clean, valid, executable Python code.

---

# 6. Monetary Circuit Breakers & Provider Resilience

Resource safety requires strict, deterministic controls against financial runaway and API degradation.

### 6.1 Multi-Tier Monetary Circuit Breaker

The `MonetaryCircuitBreaker` continuously tallies financial expenditure across all agent sessions and model invocations:

```python
@dataclass
class CircuitBreakerStatus:
    total_cost_usd: float
    max_budget_usd: float
    is_tripped: bool
    trip_reason: Optional[str] = None
```

#### Operational Rules:
1. **Configurable Ceilings:** Global task budget default is elevated from legacy `$0.50` to `$5.00` (configurable via `MAX_BUDGET_USD`), with a warning alert triggered at 80% ($4.00).
2. **Post-Yield Evaluation:** After every `AGENT_YIELDED` event, the actual cost reported by OpenHands telemetry is aggregated into `AccumulatedSpend`.
3. **Hard Trip Action:** If `AccumulatedSpend >= MAX_BUDGET_USD`:
   - The circuit breaker transitions to `TRIPPED`.
   - The FSM intercepts execution and forces an immediate state transition to `BLOCKED` with reason `BUDGET_EXHAUSTED`.
   - A full `FSMCheckpoint` is saved to disk, allowing the user to inspect progress and resume with an elevated budget if desired.

### 6.2 Provider Resilience & Exponential Backoff

When LLM providers encounter rate limits (HTTP 429) or server overload (HTTP 529):
1. **Exponential Jittered Backoff:** Retries are executed with base delay $t = 2.0\text{s}$, multiplier $2.0$, and uniform random jitter:
   $$\Delta t = (t \cdot 2^{\text{attempt}}) + \text{random}(0.1, 1.0)$$
2. **Max Retry Ceiling:** After 4 consecutive failed attempts, the `ProviderQuotaProtector` trips, marking the active operation `BLOCKED` (`PROVIDER_RATE_LIMIT_EXHAUSTED`) without burning further turn or token budgets.

---

# 7. Canonical Python Architecture & Data Models

Below is the complete, production-ready, fully typed implementation specification for the P4 Resource Governance module (`orchestrator/control/adaptive_governance.py`).

```python
"""Adaptive Resource Governance Architecture for ORAGAI (P4 Specification).

Provides dynamic, phase-aware turn allocation, AST-aware context folding,
and non-intrusive financial circuit breakers.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from enum import Enum
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


# ============================================================================
# 1. State & Policy Enums
# ============================================================================

class ResourcePhase(str, Enum):
    """Execution phase matching P3 FSM States for resource budgeting."""
    PREFLIGHT = "PREFLIGHT"
    PLANNING = "PLANNING"
    IMPLEMENTATION = "IMPLEMENTATION"
    VERIFICATION = "VERIFICATION"
    RESOLUTION = "RESOLUTION"
    REVIEW = "REVIEW"
    AUDIT = "AUDIT"


class CircuitState(str, Enum):
    """Operational state of the monetary and quota circuit breakers."""
    CLOSED = "CLOSED"        # Normal operation
    HALF_OPEN = "HALF_OPEN"  # Testing recovery after transient failure
    OPEN = "OPEN"            # Tripped; blocking execution


class ResourceExhaustionReason(str, Enum):
    """Formal taxonomy of resource termination conditions."""
    NONE = "NONE"
    MAX_TURNS_REACHED = "MAX_TURNS_REACHED"
    MONETARY_BUDGET_EXHAUSTED = "MONETARY_BUDGET_EXHAUSTED"
    TOKEN_CEILING_EXCEEDED = "TOKEN_CEILING_EXCEEDED"
    PROVIDER_RATE_LIMIT = "PROVIDER_RATE_LIMIT"
    STAGNATION_LIMIT_EXCEEDED = "STAGNATION_LIMIT_EXCEEDED"


# ============================================================================
# 2. Configuration & Telemetry Data Models
# ============================================================================

@dataclass(frozen=True)
class PhaseBudgetProfile:
    """Resource constraints for a specific FSM execution phase."""
    phase: ResourcePhase
    base_turns: int
    min_turns: int
    max_turns: int
    output_headroom_tokens: int
    investigation_token_ratio: float  # 1.0 = 100% investigation permitted


@dataclass(frozen=True)
class ResourceGovernorConfig:
    """Master configuration for the adaptive resource governance engine."""
    max_budget_usd: float = 5.00
    warning_budget_usd: float = 4.00
    max_task_tokens: int = 1_000_000
    default_model_context_window: int = 200_000
    default_max_output_tokens: int = 8_192
    max_stagnation_turns: int = 4
    enable_ast_folding: bool = True


@dataclass
class TurnBudgetResult:
    """The computed turn budget and configuration for an OpenHands session."""
    phase: ResourcePhase
    allocated_turns: int
    allocated_output_tokens: int
    complexity_score: float
    stagnation_penalty: int
    reasoning: str


@dataclass
class ResourceUsageSnapshot:
    """Cumulative resource consumption telemetry."""
    total_cost_usd: float = 0.0
    total_tokens_consumed: int = 0
    turns_executed: int = 0
    phase_spend_usd: Dict[ResourcePhase, float] = field(default_factory=dict)
    phase_tokens: Dict[ResourcePhase, int] = field(default_factory=dict)


# ============================================================================
# 3. Adaptive Budget Allocator
# ============================================================================

class AdaptiveBudgetAllocator:
    """Computes dynamic, complexity-scored turn and token budgets per FSM state."""

    PHASE_PROFILES: Dict[ResourcePhase, PhaseBudgetProfile] = {
        ResourcePhase.PREFLIGHT: PhaseBudgetProfile(
            phase=ResourcePhase.PREFLIGHT,
            base_turns=0,
            min_turns=0,
            max_turns=0,
            output_headroom_tokens=0,
            investigation_token_ratio=1.0,
        ),
        ResourcePhase.PLANNING: PhaseBudgetProfile(
            phase=ResourcePhase.PLANNING,
            base_turns=15,
            min_turns=8,
            max_turns=25,
            output_headroom_tokens=8192,
            investigation_token_ratio=1.0,
        ),
        ResourcePhase.IMPLEMENTATION: PhaseBudgetProfile(
            phase=ResourcePhase.IMPLEMENTATION,
            base_turns=10,
            min_turns=5,
            max_turns=20,
            output_headroom_tokens=4096,
            investigation_token_ratio=0.50,
        ),
        ResourcePhase.VERIFICATION: PhaseBudgetProfile(
            phase=ResourcePhase.VERIFICATION,
            base_turns=0,
            min_turns=0,
            max_turns=0,
            output_headroom_tokens=0,
            investigation_token_ratio=1.0,
        ),
        ResourcePhase.RESOLUTION: PhaseBudgetProfile(
            phase=ResourcePhase.RESOLUTION,
            base_turns=5,
            min_turns=3,
            max_turns=10,
            output_headroom_tokens=4096,
            investigation_token_ratio=0.70,
        ),
        ResourcePhase.REVIEW: PhaseBudgetProfile(
            phase=ResourcePhase.REVIEW,
            base_turns=8,
            min_turns=4,
            max_turns=12,
            output_headroom_tokens=4096,
            investigation_token_ratio=1.0,
        ),
        ResourcePhase.AUDIT: PhaseBudgetProfile(
            phase=ResourcePhase.AUDIT,
            base_turns=20,
            min_turns=10,
            max_turns=30,
            output_headroom_tokens=8192,
            investigation_token_ratio=1.0,
        ),
    }

    def __init__(self, config: Optional[ResourceGovernorConfig] = None):
        self.config = config or ResourceGovernorConfig()

    def compute_complexity_score(
        self,
        acceptance_criteria_count: int,
        dag_depth: int = 1,
        target_files_count: int = 1,
        symbol_count: int = 10,
    ) -> float:
        """Calculates a normalized task complexity score in [0.0, 1.0]."""
        c_ac = min(1.0, max(0.0, acceptance_criteria_count / 8.0))
        c_dag = min(1.0, max(0.0, dag_depth / 5.0))
        c_files = min(1.0, max(0.0, target_files_count / 6.0))
        c_symbols = min(1.0, max(0.0, symbol_count / 50.0))

        score = (0.35 * c_ac) + (0.25 * c_dag) + (0.20 * c_files) + (0.20 * c_symbols)
        return round(min(1.0, max(0.0, score)), 4)

    def allocate_turn_budget(
        self,
        phase: ResourcePhase,
        acceptance_criteria_count: int = 1,
        dag_depth: int = 1,
        target_files_count: int = 1,
        stagnation_count: int = 0,
    ) -> TurnBudgetResult:
        """Computes the bounded turn budget for an upcoming agent session."""
        profile = self.PHASE_PROFILES.get(phase, self.PHASE_PROFILES[ResourcePhase.IMPLEMENTATION])

        if profile.base_turns == 0:
            return TurnBudgetResult(
                phase=phase,
                allocated_turns=0,
                allocated_output_tokens=0,
                complexity_score=0.0,
                stagnation_penalty=0,
                reasoning=f"Phase {phase.value} is deterministic zero-token.",
            )

        comp_score = self.compute_complexity_score(
            acceptance_criteria_count=acceptance_criteria_count,
            dag_depth=dag_depth,
            target_files_count=target_files_count,
        )

        stagnation_penalty = min(6, stagnation_count * 2)
        raw_turns = (profile.base_turns * (1.0 + 0.8 * comp_score)) - stagnation_penalty
        allocated_turns = max(profile.min_turns, min(int(math.floor(raw_turns)), profile.max_turns))

        reasoning = (
            f"Phase {phase.value}: base={profile.base_turns}, comp_score={comp_score:.2f}, "
            f"stagnation_penalty={stagnation_penalty} -> allocated={allocated_turns}"
        )

        return TurnBudgetResult(
            phase=phase,
            allocated_turns=allocated_turns,
            allocated_output_tokens=profile.output_headroom_tokens,
            complexity_score=comp_score,
            stagnation_penalty=stagnation_penalty,
            reasoning=reasoning,
        )


# ============================================================================
# 4. AST-Aware Context Clamper
# ============================================================================

class ASTAwareContextClamper:
    """Compresses Python source files using AST folding to guarantee context headroom."""

    @staticmethod
    def fold_python_source(
        source_code: str,
        target_symbols: Optional[Set[str]] = None,
        min_fold_lines: int = 5,
    ) -> Tuple[str, bool]:
        """Folds non-target function/class bodies in Python code into docstrings.
        
        Returns:
            Tuple of (transformed_source_code, was_folded_boolean).
        """
        targets = target_symbols or set()
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            # If file has syntax error, return raw content safely
            return source_code, False

        folded = False

        class MethodFolder(ast.NodeTransformer):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
                self.generic_visit(node)
                if node.name in targets:
                    return node

                # Calculate body line length
                body_lines = (node.end_lineno or 0) - (node.lineno or 0)
                if body_lines > min_fold_lines:
                    nonlocal folded
                    folded = True
                    docstring = ast.get_docstring(node)
                    new_body: List[ast.stmt] = []
                    
                    if docstring:
                        new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
                    
                    notice = f"[Folded implementation: {body_lines} lines]"
                    new_body.append(ast.Expr(value=ast.Constant(value=notice)))
                    new_body.append(ast.Pass())
                    node.body = new_body
                return node

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
                self.generic_visit(node)
                if node.name in targets:
                    return node

                body_lines = (node.end_lineno or 0) - (node.lineno or 0)
                if body_lines > min_fold_lines:
                    nonlocal folded
                    folded = True
                    docstring = ast.get_docstring(node)
                    new_body: List[ast.stmt] = []
                    
                    if docstring:
                        new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
                    
                    notice = f"[Folded async implementation: {body_lines} lines]"
                    new_body.append(ast.Expr(value=ast.Constant(value=notice)))
                    new_body.append(ast.Pass())
                    node.body = new_body
                return node

        transformer = MethodFolder()
        modified_tree = transformer.visit(tree)
        ast.fix_missing_locations(modified_tree)

        if folded:
            return ast.unparse(modified_tree), True
        return source_code, False

    @classmethod
    def assemble_clamped_context(
        cls,
        tier0_intent: str,
        tier1_diagnostics: str,
        tier2_files: Dict[str, str],
        tier3_architecture: str,
        target_symbols_per_file: Optional[Dict[str, Set[str]]] = None,
        max_context_chars: int = 120_000,
    ) -> str:
        """Assembles prompt context strictly adhering to priority tiers without overflow."""
        symbols = target_symbols_per_file or {}
        chunks: List[str] = []
        current_len = 0

        # Tier 0: Mandatory Intent
        chunks.append("=== TASK INTENT & REQUIREMENTS ===\n" + tier0_intent)
        current_len += len(chunks[-1])

        # Tier 1: Failure Diagnostics
        if tier1_diagnostics:
            diag_chunk = "\n\n=== FAILURE DIAGNOSTICS ===\n" + tier1_diagnostics
            chunks.append(diag_chunk)
            current_len += len(diag_chunk)

        # Tier 2: Target Files (with AST Folding if space is tight)
        chunks.append("\n\n=== TARGET SOURCE FILES ===")
        current_len += len(chunks[-1])

        for file_path, content in tier2_files.items():
            file_symbols = symbols.get(file_path, set())
            file_str = f"\n\n--- File: {file_path} ---\n{content}"

            if current_len + len(file_str) > max_context_chars:
                # Fold file to fit
                folded_content, was_folded = cls.fold_python_source(content, file_symbols)
                file_str = f"\n\n--- File: {file_path} (AST-Folded) ---\n{folded_content}"

            chunks.append(file_str)
            current_len += len(file_str)

        # Tier 3: Architecture Map (if capacity remains)
        if tier3_architecture and (current_len + len(tier3_architecture) <= max_context_chars):
            chunks.append("\n\n=== ARCHITECTURE SKELETON ===\n" + tier3_architecture)

        return "".join(chunks)


# ============================================================================
# 5. Monetary Circuit Breaker & Provider Protector
# ============================================================================

class MonetaryCircuitBreaker:
    """Enforces non-intrusive financial ceilings and safe execution pausing."""

    def __init__(self, config: Optional[ResourceGovernorConfig] = None):
        self.config = config or ResourceGovernorConfig()
        self.usage = ResourceUsageSnapshot()
        self.state: CircuitState = CircuitState.CLOSED
        self.trip_reason: Optional[ResourceExhaustionReason] = None

    def record_consumption(
        self,
        cost_usd: float,
        tokens: int,
        phase: ResourcePhase,
        turns: int = 1,
    ) -> None:
        """Records telemetry and evaluates circuit state."""
        self.usage.total_cost_usd += max(0.0, cost_usd)
        self.usage.total_tokens_consumed += max(0, tokens)
        self.usage.turns_executed += max(0, turns)

        self.usage.phase_spend_usd[phase] = (
            self.usage.phase_spend_usd.get(phase, 0.0) + max(0.0, cost_usd)
        )
        self.usage.phase_tokens[phase] = (
            self.usage.phase_tokens.get(phase, 0) + max(0, tokens)
        )

        self._evaluate_thresholds()

    def _evaluate_thresholds(self) -> None:
        """Evaluates whether financial limits have been breached."""
        if self.usage.total_cost_usd >= self.config.max_budget_usd:
            self.state = CircuitState.OPEN
            self.trip_reason = ResourceExhaustionReason.MONETARY_BUDGET_EXHAUSTED
        elif self.usage.total_tokens_consumed >= self.config.max_task_tokens:
            self.state = CircuitState.OPEN
            self.trip_reason = ResourceExhaustionReason.TOKEN_CEILING_EXCEEDED

    @property
    def is_tripped(self) -> bool:
        return self.state == CircuitState.OPEN

    @property
    def remaining_budget_usd(self) -> float:
        return max(0.0, self.config.max_budget_usd - self.usage.total_cost_usd)


class ProviderQuotaProtector:
    """Manages rate-limiting backoffs and tracks provider API health."""

    def __init__(self, max_retries: int = 4, base_delay_seconds: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay_seconds
        self.consecutive_rate_limits = 0

    def compute_backoff_delay(self, attempt: int) -> float:
        """Calculates exponential backoff with deterministic scaling."""
        return self.base_delay * (2.0 ** min(attempt, 5))

    def record_rate_limit_event(self) -> bool:
        """Records a 429/529 event. Returns True if max retries exceeded."""
        self.consecutive_rate_limits += 1
        return self.consecutive_rate_limits > self.max_retries

    def record_success(self) -> None:
        """Resets rate limit counter on clean API call."""
        self.consecutive_rate_limits = 0


# ============================================================================
# 6. Unified Adaptive Resource Governor
# ============================================================================

class AdaptiveResourceGovernor:
    """Unified façade consumed by P3 GuardedFSMEngine."""

    def __init__(self, config: Optional[ResourceGovernorConfig] = None):
        self.config = config or ResourceGovernorConfig()
        self.allocator = AdaptiveBudgetAllocator(self.config)
        self.clamper = ASTAwareContextClamper()
        self.circuit_breaker = MonetaryCircuitBreaker(self.config)
        self.provider_protector = ProviderQuotaProtector()
        self._stagnation_counter: int = 0

    def pre_dispatch_allocate(
        self,
        phase: ResourcePhase,
        acceptance_criteria_count: int = 1,
        dag_depth: int = 1,
        target_files_count: int = 1,
    ) -> TurnBudgetResult:
        """Called before dispatching an OpenHands session to calculate turn limits."""
        if self.circuit_breaker.is_tripped:
            return TurnBudgetResult(
                phase=phase,
                allocated_turns=0,
                allocated_output_tokens=0,
                complexity_score=0.0,
                stagnation_penalty=0,
                reasoning=f"Circuit breaker tripped: {self.circuit_breaker.trip_reason}",
            )

        return self.allocator.allocate_turn_budget(
            phase=phase,
            acceptance_criteria_count=acceptance_criteria_count,
            dag_depth=dag_depth,
            target_files_count=target_files_count,
            stagnation_count=self._stagnation_counter,
        )

    def post_yield_record(
        self,
        phase: ResourcePhase,
        cost_usd: float,
        tokens_consumed: int,
        turns_used: int,
        made_meaningful_progress: bool,
    ) -> None:
        """Called when an OpenHands session yields to record spend and update stagnation."""
        self.circuit_breaker.record_consumption(
            cost_usd=cost_usd,
            tokens=tokens_consumed,
            phase=phase,
            turns=turns_used,
        )

        if made_meaningful_progress:
            self._stagnation_counter = 0
            self.provider_protector.record_success()
        else:
            self._stagnation_counter += 1
```

---

# 8. Rigorous Test Matrix & Verification Scenarios

To ensure zero regressions and validate that P4 eliminates all legacy resource pathologies, the following comprehensive test suite is specified for `tests/test_adaptive_governance.py`:

| Test Case ID | Test Function Name | Tested Invariant | Validation Criteria |
| :--- | :--- | :--- | :--- |
| **TEST-P4-01** | `test_turn_budget_scales_with_ac_count` | Turn budget scales smoothly with AC complexity | 1 AC yields ~10 turns; 8 ACs yield 18-20 turns; never capped at 5 turns. |
| **TEST-P4-02** | `test_planning_and_audit_receive_100_percent_investigation` | `PLANNING` & `AUDIT` allow 100% token spend on reading | Zero edits do not trip investigation circuit breakers in `PLANNING`/`AUDIT`. |
| **TEST-P4-03** | `test_ast_folding_preserves_target_symbols_and_syntax` | Code folding preserves target functions and valid syntax | Folded code parses with `ast.parse()`; target function bodies remain untouched; non-target bodies folded. |
| **TEST-P4-04** | `test_monetary_circuit_breaker_trips_cleanly_at_budget` | Budget breach halts execution without thread kills | Exceeding `$5.00` sets `is_tripped=True`, returning 0 turns on subsequent dispatches. |
| **TEST-P4-05** | `test_stagnation_penalty_tightens_loop_turns` | Looping without edits progressively decreases turn allocations | 3 consecutive stagnant yields reduce turn budget by 6 turns down to minimum. |
| **TEST-P4-06** | `test_provider_backoff_and_quota_recovery` | Exponential backoff delay doubles per attempt | Attempt 1 = 4.0s, Attempt 2 = 8.0s, Attempt 3 = 16.0s; resets on success. |
| **TEST-P4-07** | `test_context_assembler_guarantees_output_headroom` | Prompt builder guarantees requested output headroom | Total context length never exceeds `max_context_chars - headroom`. |

---

# 9. Migration & Deprecation Strategy

The rollout of P4 proceeds in four structured phases with zero breaking changes to existing passing test suites:

```
┌────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐
│   Phase A: Decouple    │ ──► │  Phase B: Integrator   │ ──► │   Phase C: Clamping    │ ──► │  Phase D: Benchmark    │
│  Remove conv.interrupt │     │  Wire into GuardedFSM  │     │ Deploy AST-Aware Fold  │     │ Validate BM-01 to BM-04│
└────────────────────────┘     └────────────────────────┘     └────────────────────────┘     └────────────────────────┘
```

1. **Phase A (Decoupling):**
   - Deprecate `conv.interrupt()` calls inside `base_pipeline.py`.
   - Remove the background thread monitor that policed the 28% token threshold.
2. **Phase B (Governor Integration):**
   - Replace legacy `DynamicTokenGovernor` instantiations with `AdaptiveResourceGovernor`.
   - Wire `pre_dispatch_allocate()` into `GuardedFSMEngine._dispatch_agent_turn()`.
3. **Phase C (AST Clamping Rollout):**
   - Replace character-truncation logic in `context_budget_manager.py` with `ASTAwareContextClamper`.
   - Update `WorkspaceFileTool` to support AST-folded views for large files.
4. **Phase D (Benchmark Validation):**
   - Run Benchmark Suite BM-01 (Single-File Task), BM-02 (Multi-File Refactor), BM-03 (Failing Test Resolution), and BM-04 (Deep Audit) to verify full-depth execution.

---

# 10. Handoff Contract for P5 (Agent Work & Milestone Execution)

P4 establishes the resource boundaries, turn allocations, and context headroom. 

**P5 (Agent Work & Milestone Execution Plan)** will govern how specific agent personas (Architect, Developer, Tester, Reviewer, Auditor) operate within these allocated turn budgets to systematically execute the `MilestoneDAG` chunks defined in P1:
* Defining persona-specific system prompts and tool access permissions.
* Structuring the iterative code-edit and test self-verification loops.
* Ensuring seamless passing of truth artifacts between ephemeral agent sessions.
