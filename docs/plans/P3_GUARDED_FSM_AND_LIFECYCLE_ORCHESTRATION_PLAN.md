# P3 — GUARDED FSM & LIFECYCLE ORCHESTRATION PLAN

> **Document Type:** Canonical Systems Architecture & Lifecycle Orchestration Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Software Architect, State Machine Engineer, & Autonomous Agent Orchestration Specialist  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md`, `docs/plans/P1_TASK_TRUTH_AND_REQUIREMENT_MODEL_PLAN.md`, `docs/plans/P2_EVIDENCE_AND_COMPLETION_GATES_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Design Phase:** P3 (Specification & Guarded Lifecycle Engine — Zero Production Code Modified)

---

# 1. Executive Summary

This specification establishes the canonical **Guarded Finite State Machine (FSM) & Lifecycle Orchestration Architecture** for the **ORAGAI** multi-agent software engineering system.

In previous phases:
* **P0 (Forensic Baseline):** Identified the critical pathology where ORAGAI conflated *Resource Governance* (token limits, step ceilings, timeouts) with *Work Governance* (requirements, acceptance criteria, verified completion), resulting in premature task termination, shallow audits, and passive state transitions.
* **P1 (Task Truth Model):** Established the immutable, graph-based representation of user intent: $\text{Task} \to \text{Requirements} \to \text{Acceptance Criteria} \to \text{Milestones} \to \text{Evidence}$.
* **P2.1 (Evidence & Completion Gates):** Formulated the canonical evidence taxonomy, cryptographic content hashing (SHA-256), multi-dimensional state tracking (`ImplementationState`, `VerificationState`, `BlockingState`), the 14-step deterministic `evaluate_task_completion()` algorithm, and the read-only `TaskTruthSemanticQueries` semantic query contract.

### The Mission of P3
P3 bridges the gap between semantic truth and dynamic runtime execution. It completely replaces the legacy passive dictionary router (`PipelineStateMachine`) and five disjoint procedural scripts (`dev_test_loop.py`, `full_pipeline.py`, `audit_pipeline.py`, `audit_fix_pipeline.py`, `documentation_pipeline.py`) with a single, unified, event-driven **Guarded FSM Engine (`GuardedFSMEngine`)**.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ORAGAI RUNTIME                                        │
│                                                                                         │
│   ┌───────────────────────────┐                     ┌───────────────────────────────┐   │
│   │    Guarded FSM Engine     │   Semantic Queries  │  Task Truth & Evidence Engine │   │
│   │          (P3)             │ ──────────────────> │            (P2.1)             │   │
│   │                           │                     │                               │   │
│   │  • Event-Driven Router    │ <────────────────── │  • TaskTruthGraph             │   │
│   │  • Transition Guards      │  Structured Decision│  • CriterionEvidencePolicies  │   │
│   │  • Recovery Loops         │ (COMPLETE/INCOMPLETE│  • SHA-256 Identity Hash      │   │
│   │  • Execution Inversion    │  /FAILED/BLOCKED)   │  • CompletionGate             │   │
│   └─────────────┬─────────────┘                     └───────────────────────────────┘   │
│                 │                                                                       │
│                 │ Bounded Execution Delegation (IoC)                                    │
│                 ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                     OpenHands SDK Runtime (v1.49.4)                             │   │
│   │                                                                                 │   │
│   │   [Architect]       [Developer]       [Tester]       [Reviewer]       [Auditor]     │   │
│   │   (Ephemeral)       (Ephemeral)       (Ephemeral)    (Ephemeral)     (Ephemeral)    │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. The P2.1 $\to$ P3 Handoff & Boundary Separation

The foundational architectural invariant governing P3 is **Absolute Separation of Concerns**:

$$\text{The FSM engine does NOT evaluate code, ASTs, test traces, diffs, or SHA-256 hashes directly.}$$

The FSM is the **Driver & Coordinator**; P2.1 is the **Sensor Suite & Source of Truth**.

### Interface Contract
The FSM consumes the pure, side-effect-free interface `TaskTruthSemanticQueries` defined in P2.1:

```python
class TaskTruthSemanticQueries:
    """Read-only semantic interface consumed exclusively by P3 transition guards."""

    @staticmethod
    def can_enter_testing(graph: "TaskTruthGraph") -> bool:
        """True if all mandatory requirements have ImplementationState == IMPLEMENTED."""
        mandatory = [r for r in graph.requirements if r.is_mandatory]
        return len(mandatory) > 0 and all(
            r.implementation_state == ImplementationState.IMPLEMENTED for r in mandatory
        )

    @staticmethod
    def can_enter_review(graph: "TaskTruthGraph", workspace: Path) -> bool:
        """True if testing passed for all test-governed criteria and syntax is clean."""
        preflight_ok, _ = PreFlightGuard.check_syntax(workspace)
        return preflight_ok and TaskTruthSemanticQueries.can_enter_testing(graph)

    @staticmethod
    def can_complete(graph: "TaskTruthGraph", workspace: Path) -> bool:
        """True if CompletionGate evaluates to COMPLETE."""
        decision = evaluate_task_completion(graph, workspace)
        return decision.is_complete

    @staticmethod
    def must_block(graph: "TaskTruthGraph", workspace: Path) -> bool:
        """True if CompletionGate evaluates to BLOCKED."""
        decision = evaluate_task_completion(graph, workspace)
        return decision.status == CompletionStatus.BLOCKED

    @staticmethod
    def must_clarify(graph: "TaskTruthGraph", workspace: Path) -> bool:
        """True if CompletionGate evaluates to AMBIGUOUS."""
        decision = evaluate_task_completion(graph, workspace)
        return decision.status == CompletionStatus.AMBIGUOUS
```

### Invariant Rules
1. **No Evidence Logic in Guards:** An FSM Guard may check `queries.can_complete(graph, workspace)` or `queries.can_enter_review(graph, workspace)`, but must never compute hashes, parse regex strings, or read raw pytest terminal buffers.
2. **No State Mutation via Resource Exhaustion:** Running out of steps (`ConvRunResult.completed = True` or step ceiling hit) must emit `AGENT_YIELDED` with execution payload, prompting the FSM to evaluate semantic completion rather than falsely mutating phase status to `COMPLETED`.
3. **Deterministic Guard Execution:** Guard predicates are boolean functions with zero side effects. They either permit a transition or reject it, raising structured telemetry incidents upon illegal attempts.

---

# 3. Forensic Analysis of Current Pipeline Deficiencies

A comprehensive forensic audit of the existing pipeline implementations reveals five major architectural pathologies:

| Subsystem / File | Source Location | Current Behavioral Reality | Pathological Impact | P3 Architectural Remedy |
| :--- | :--- | :--- | :--- | :--- |
| **Passive Enum Router** | `orchestrator/pipeline/state_machine.py:L28-93` | `PipelineStateMachine` checks only `target in ALLOWED_TRANSITIONS[current]`. | Transitions occur without verifying whether code was written, compiled, or tested. | **Guard Predicates** embedded in transition rules that query P2.1 semantic gates before state changes. |
| **Buried Procedural Logic** | `orchestrator/pipeline/full_pipeline.py:L1-792`, `dev_test_loop.py:L1-397` | Hardcoded procedural `if/elif/else` statements manually create conversations, loop iterations, and handle errors. | Massive code duplication across 5 pipelines; high divergence in error handling and logging. | **Unified GuardedFSMEngine** executing configurable `LifecycleProfile` definitions over a single state graph. |
| **Early Exit Trap** | `orchestrator/pipeline/dev_test_loop.py:L277-280` | `if test_result.status == TestExecutionStatus.PASSED: tests_passed = True; break` | Development loop breaks immediately on single pytest pass, ignoring missing requirements. | Loop termination governed strictly by `CompletionDecision.status == COMPLETE`. |
| **Phantom `COMPLETED` State** | `orchestrator/pipeline/base_pipeline.py:L56, L353-370` | `ConvRunResult.completed = True` by default when `conv.run()` exits. | Step exhaustion or token timeouts silently register as successful stage completion. | **Execution Loop Inversion (IoC)**: OpenHands agent yields execution; FSM inspects P2.1 truth before advancing. |
| **Violent Process Abortion** | `orchestrator/pipeline/base_pipeline.py:L304-324` | Background thread calls `conv.interrupt()` when token budget hits 28% without file write. | Destroys agent reasoning context mid-stream, corrupting state and preventing clean recovery. | **Bounded Delegation & Yielding**: Tasks assigned in discrete chunks with explicit turn budgets; no kill threads. |
| **Fragmented Checkpoints** | `orchestrator/pipeline/checkpoint.py:L9-21` | `.orchestrator_state.json` stores string list of completed phase names (`["architect", "developer"]`). | Resuming a task restores phase names but loses all requirement status, evidence hashes, and DAG progress. | **FSMCheckpoint**: Full serialization of `FSMState`, `TaskTruthGraph`, active milestone, and workspace snapshot. |

---

# 4. Unified FSM State Taxonomy & Architecture

The Guarded FSM replaces fragmented pipelines with 11 discrete, mathematically defined states:

```
                                  ┌──────────────┐
                                  │     INIT     │
                                  └──────┬───────┘
                                         │ PREFLIGHT_PASSED
                                         ▼
                                  ┌──────────────┐
                        ┌─────────┤  PREFLIGHT   ├─────────┐
                        │         └──────┬───────┘         │
                        │ PREFLIGHT_FAIL │                 │ PREFLIGHT_FAIL
                        ▼                │ PREFLIGHT_OK    ▼
                 ┌─────────────┐         │          ┌─────────────┐
                 │   BLOCKED   │         │          │   FAILED    │
                 └──────▲──────┘         │          └──────▲──────┘
                        │                ▼                 │
                        │         ┌──────────────┐         │
                        │         │   PLANNING   │         │
                        │         └──────┬───────┘         │
                        │                │ PLAN_GENERATED  │
                        │                ▼                 │
                        │      ┌──────────────────┐        │
                        │ ┌───>│  IMPLEMENTATION  │        │
                        │ │    └─────────┬────────┘        │
                        │ │              │ AGENT_YIELDED   │
                        │ │              ▼                 │
                        │ │    ┌──────────────────┐        │
                        │ │    │   VERIFICATION   │        │
                        │ │    └─────────┬────────┘        │
                        │ │              │ VERIFICATION_DONE
                        │ │              ▼                 │
                        │ │    ┌──────────────────┐        │
                        │ └───-┤    RESOLUTION    ├────────┘
                        │      └─────────┬────────┘ (MAX_RETRIES)
                        │                │ VERIFIED_ALL
                        │                ▼
                        │         ┌──────────────┐
                        │         │    REVIEW    │
                        │         └──────┬───────┘
                        │                │ REVIEW_APPROVED
                        │                ▼
                        │         ┌──────────────┐
                        └─────────┤  COMPLETED   │
                         CRITICAL └──────────────┘
```

### State Definitions

```python
from enum import Enum
from typing import Set


class FSMState(str, Enum):
    """Discrete lifecycle states of the Guarded FSM Engine."""

    INIT = "INIT"
    """Workspace initialization, configuration loading, and environment discovery."""

    PREFLIGHT = "PREFLIGHT"
    """Zero-token static validation (syntax check, adapter detection, baseline importability)."""

    PLANNING = "PLANNING"
    """Architect agent generates requirement decomposition, acceptance criteria, and Milestone DAG."""

    IMPLEMENTATION = "IMPLEMENTATION"
    """Developer / Fixer agent authors or modifies source code for active milestone."""

    VERIFICATION = "VERIFICATION"
    """Deterministic static checks, pytest runs, and P2.1 evidence gate evaluation."""

    RESOLUTION = "RESOLUTION"
    """Intelligent failure triage, remediation routing, and progress stagnation analysis."""

    REVIEW = "REVIEW"
    """Independent architectural and security assessment by Reviewer / Auditor agent."""

    BLOCKED = "BLOCKED"
    """Execution halted due to environmental failure, missing credentials, or human intervention requirement."""

    AMBIGUOUS = "AMBIGUOUS"
    """Execution halted due to conflicting requirements or impossible acceptance criteria."""

    COMPLETED = "COMPLETED"
    """Terminal state: Task verified complete by CompletionGate; atomic Git commit executed."""

    FAILED = "FAILED"
    """Terminal state: Unrecoverable error, invariant violation, or retry limit exhaustion."""

    ABORTED = "ABORTED"
    """Terminal state: User cancellation or external controller abort signal."""
```

---

# 5. Event-Driven Lifecycle & Payload Contracts

State transitions are driven strictly by strongly typed **Pipeline Events**. Direct state mutation without an event is impossible.

### Event Domain Model

```python
"""Pipeline Event schema for Guarded FSM."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class EventType(str, Enum):
    """Discrete event types triggering state transitions."""

    # Initialization & Preflight
    START_TASK = "START_TASK"
    PREFLIGHT_PASSED = "PREFLIGHT_PASSED"
    PREFLIGHT_FAILED = "PREFLIGHT_FAILED"

    # Planning
    PLAN_GENERATED = "PLAN_GENERATED"
    PLAN_REJECTED = "PLAN_REJECTED"
    REPLAN_TRIGGERED = "REPLAN_TRIGGERED"

    # Implementation
    MILESTONE_STARTED = "MILESTONE_STARTED"
    AGENT_YIELDED = "AGENT_YIELDED"

    # Verification
    VERIFICATION_REQUESTED = "VERIFICATION_REQUESTED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"

    # Resolution & Recovery
    REMEDIATION_ROUTED = "REMEDIATION_ROUTED"
    STAGNATION_DETECTED = "STAGNATION_DETECTED"
    RETRIES_EXHAUSTED = "RETRIES_EXHAUSTED"

    # Review
    REVIEW_REQUESTED = "REVIEW_REQUESTED"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    REVIEW_REJECTED = "REVIEW_REJECTED"

    # Edge & Terminal
    HUMAN_INTERVENTION_REQUIRED = "HUMAN_INTERVENTION_REQUIRED"
    HUMAN_INPUT_RECEIVED = "HUMAN_INPUT_RECEIVED"
    CRITICAL_ERROR = "CRITICAL_ERROR"
    ABORT_REQUESTED = "ABORT_REQUESTED"


class AgentExecutionOutcome(str, Enum):
    """Detailed outcome classification from an OpenHands agent yield."""

    NATURAL_COMPLETION = "NATURAL_COMPLETION"
    STEP_LIMIT_REACHED = "STEP_LIMIT_REACHED"
    TOKEN_LIMIT_REACHED = "TOKEN_LIMIT_REACHED"
    TOOL_ERROR = "TOOL_ERROR"
    STAGNANT_DIFF = "STAGNANT_DIFF"
    INTERRUPTED = "INTERRUPTED"


@dataclass(frozen=True)
class PipelineEvent:
    """Immutable event payload processed by the GuardedFSMEngine."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.START_TASK
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    source_phase: FSMState = FSMState.INIT
    active_milestone_id: Optional[str] = None
    execution_outcome: Optional[AgentExecutionOutcome] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
```

---

# 6. Deterministic Transition Matrix & Guard Predicates

The transition matrix defines all allowable state transitions, along with their mandatory Guard Predicates and Action Hooks.

### Canonical Transition Matrix

```
┌─────────────────┬─────────────────────────────┬───────────────────────────────────────────┬─────────────────┐
│ Source State    │ Trigger Event               │ Guard Predicate (via P2.1 & Context)      │ Target State    │
├─────────────────┼─────────────────────────────┼───────────────────────────────────────────┼─────────────────┤
│ INIT            │ START_TASK                  │ workspace_exists()                        │ PREFLIGHT       │
│ PREFLIGHT       │ PREFLIGHT_PASSED            │ PreFlightGuard.check_syntax() == True     │ PLANNING        │
│ PREFLIGHT       │ PREFLIGHT_PASSED (Direct)   │ skip_planning == True                     │ IMPLEMENTATION  │
│ PREFLIGHT       │ PREFLIGHT_FAILED            │ is_unrecoverable() == True                │ FAILED          │
│ PREFLIGHT       │ PREFLIGHT_FAILED            │ requires_human() == True                  │ BLOCKED         │
│ PLANNING        │ PLAN_GENERATED              │ TaskTruthGraph has valid requirements     │ IMPLEMENTATION  │
│ PLANNING        │ PLAN_REJECTED               │ replan_attempts < max_replan              │ PLANNING        │
│ PLANNING        │ PLAN_REJECTED               │ replan_attempts >= max_replan             │ FAILED          │
│ IMPLEMENTATION  │ AGENT_YIELDED               │ can_enter_testing(graph) == True          │ VERIFICATION    │
│ IMPLEMENTATION  │ AGENT_YIELDED               │ yield_outcome == STEP_LIMIT_REACHED       │ VERIFICATION    │
│ IMPLEMENTATION  │ CRITICAL_ERROR              │ fatal_exception == True                   │ FAILED          │
│ VERIFICATION    │ VERIFICATION_COMPLETED      │ CompletionDecision.status == COMPLETE     │ REVIEW          │
│ VERIFICATION    │ VERIFICATION_COMPLETED      │ CompletionDecision.status == COMPLETE     │ COMPLETED       │
│                 │                             │   (if review disabled in profile)         │                 │
│ VERIFICATION    │ VERIFICATION_COMPLETED      │ CompletionDecision.status == INCOMPLETE   │ RESOLUTION      │
│ VERIFICATION    │ VERIFICATION_COMPLETED      │ CompletionDecision.status == FAILED       │ RESOLUTION      │
│ VERIFICATION    │ VERIFICATION_COMPLETED      │ CompletionDecision.status == BLOCKED      │ BLOCKED         │
│ VERIFICATION    │ VERIFICATION_COMPLETED      │ CompletionDecision.status == AMBIGUOUS    │ AMBIGUOUS       │
│ RESOLUTION      │ REMEDIATION_ROUTED          │ attempts < max_fix_attempts               │ IMPLEMENTATION  │
│ RESOLUTION      │ REPLAN_TRIGGERED            │ architectural_conflict == True            │ PLANNING        │
│ RESOLUTION      │ STAGNATION_DETECTED         │ zero_diff_progress == True                │ RESOLUTION      │
│ RESOLUTION      │ RETRIES_EXHAUSTED           │ attempts >= max_fix_attempts              │ FAILED          │
│ REVIEW          │ REVIEW_APPROVED             │ ReviewerVerdict == APPROVED               │ COMPLETED       │
│ REVIEW          │ REVIEW_REJECTED             │ review_fixes_pending == True              │ RESOLUTION      │
│ BLOCKED         │ HUMAN_INPUT_RECEIVED        │ human_unblocked == True                   │ PREFLIGHT       │
│ AMBIGUOUS       │ REPLAN_TRIGGERED            │ ambiguity_clarified == True               │ PLANNING        │
│ * (Any State)   │ ABORT_REQUESTED             │ controller.should_abort() == True         │ ABORTED         │
└─────────────────┴─────────────────────────────┴───────────────────────────────────────────┴─────────────────┘
```

### Mathematical Guard Specifications

```python
"""Transition Guard definitions for GuardedFSMEngine."""

from pathlib import Path
from typing import Callable, Optional
from orchestrator.analysis.schemas import CompletionDecision, CompletionStatus
from orchestrator.guards.preflight import PreFlightGuard
from orchestrator.pipeline.fsm.events import PipelineEvent
from orchestrator.pipeline.fsm.states import FSMState


class FSMGuards:
    """Pure, side-effect-free transition guard predicates."""

    @staticmethod
    def guard_preflight_passed(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that workspace passes static syntax compilation and importability."""
        clean, _ = PreFlightGuard.check_syntax(context.workspace_path)
        return clean

    @staticmethod
    def guard_plan_valid(context: "FSMContext", event: PipelineEvent) -> bool:
        """Verify that Architect produced at least one mandatory requirement and milestone."""
        graph = context.task_truth_graph
        if not graph:
            return False
        mandatory_reqs = [r for r in graph.requirements if r.is_mandatory]
        return len(mandatory_reqs) > 0 and len(context.milestone_dag) > 0

    @staticmethod
    def guard_can_enter_verification(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that implementation phase yielded cleanly or reached step budget."""
        # Verification must ALWAYS run after implementation to gather empirical evidence
        return True

    @staticmethod
    def guard_can_enter_review(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that all milestone criteria pass and code is syntactically sound."""
        return TaskTruthSemanticQueries.can_enter_review(
            context.task_truth_graph, context.workspace_path
        )

    @staticmethod
    def guard_can_complete(context: "FSMContext", event: PipelineEvent) -> bool:
        """Verify that CompletionGate returned COMPLETE."""
        return TaskTruthSemanticQueries.can_complete(
            context.task_truth_graph, context.workspace_path
        )

    @staticmethod
    def guard_must_block(context: "FSMContext", event: PipelineEvent) -> bool:
        """Verify if execution encountered an unrecoverable blocking condition."""
        return TaskTruthSemanticQueries.must_block(
            context.task_truth_graph, context.workspace_path
        )

    @staticmethod
    def guard_must_clarify(context: "FSMContext", event: PipelineEvent) -> bool:
        """Verify if requirements or criteria are contradictory or ambiguous."""
        return TaskTruthSemanticQueries.must_clarify(
            context.task_truth_graph, context.workspace_path
        )

    @staticmethod
    def guard_can_retry_remediation(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that iteration count has not exceeded maximum configured retries."""
        return context.iteration_count < context.config.max_fix_iterations

    @staticmethod
    def guard_retries_exhausted(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that iteration count has reached or exceeded maximum retries."""
        return context.iteration_count >= context.config.max_fix_iterations
```

---

# 7. Execution Loop Inversion (IoC over OpenHands SDK)

### The Legacy Problem (P0)
In the legacy implementation, ORAGAI launched long-lived conversations (`conv.run()`) and relied on an asynchronous watchdog thread (`_start_token_monitor`) that forcibly invoked `conv.interrupt()` if token or turn limits were approached. This destroyed LLM context, truncated half-written files, and frequently locked the workspace. Furthermore, when OpenHands finished turns naturally, `ConvRunResult.completed` defaulted to `True`, creating the illusion of task completion.

### The Inversion of Control Solution
Under P3, **the FSM is the absolute supervisor; OpenHands is an ephemeral, bounded sub-worker.**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        GuardedFSMEngine (Master)                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                       1. Create Bounded Conversation
                       (Max Turns: N, Scoped Prompt)
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   OpenHands Conversation Worker                        │
│                                                                        │
│   • Executes tool actions (Read, Edit, Write, Terminal)               │
│   • Runs until:                                                        │
│       (a) Natural completion statement                                 │
│       (b) Exact turn limit reached                                     │
│       (c) Tool execution exception                                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                        2. Yields Control & Telemetry
                        (AGENT_YIELDED Event)
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        GuardedFSMEngine (Master)                       │
│                                                                        │
│   3. Captures SHA-256 Workspace Snapshot                               │
│   4. Evaluates P2.1 Evidence Gates (TaskTruthSemanticQueries)          │
│   5. Decides Next State:                                               │
│       • VERIFICATION -> RESOLUTION -> IMPLEMENTATION (if incomplete)   │
│       • REVIEW -> COMPLETED (if verified)                              │
│       • FAILED (if budget/retries exhausted)                           │
└────────────────────────────────────────────────────────────────────────┘
```

### Turn-Bounded Execution Protocol
1. **Scope Bounding:** Each conversation run is initialized with a strict, task-specific turn cap (e.g., 6 turns per milestone attempt) via `Conversation(agent, workspace, max_turns=6)`.
2. **Clean Yielding:** The conversation loop terminates naturally when turns are exhausted or the agent stops. No background thread kills the process.
3. **Structured Yield Capture:** The engine captures the `ConvRunResult` and transforms it into an `AGENT_YIELDED` pipeline event containing:
   - Raw tokens consumed and LLM cost.
   - Files modified during the turn.
   - Final agent output text.
   - Outcome flag (`NATURAL_COMPLETION`, `STEP_LIMIT_REACHED`, `TOOL_ERROR`).
4. **Zero State Mutation:** The yield event *never* marks the task complete. The FSM immediately routes the workflow to `VERIFICATION` to evaluate empirical evidence against P2.1 gates.

---

# 8. Intelligent Recovery & Remediation Routing (`RESOLUTION` State)

The `RESOLUTION` state is the central intelligence hub for non-linear recovery. When `VERIFICATION` concludes with an unsatisfied gate, the FSM transitions to `RESOLUTION` to determine the precise recovery vector:

```
                               ┌───────────────────────────┐
                               │     RESOLUTION STATE      │
                               └─────────────┬─────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               │                             │                             │
    [INCOMPLETE REQUIREMENTS]        [TEST/SYNTAX FAILURE]         [STAGNANT PROGRESS]
               │                             │                             │
               ▼                             ▼                             ▼
    Delta-Injected Developer       Failure-Trace Developer        Escalation Protocol
    • Injects unsatisfied ACs      • Extracts pytest traceback    • Trips circuit breaker
    • Preserves prior context      • ASTGuard error report        • Prevents token loop
    • Bounded turn budget          • Targets specific fix         • Transitions to FAILED
               │                             │                             │
               └──────────────────────┬──────┴─────────────────────────────┘
                                      │
                                      ▼
                        Route to IMPLEMENTATION State
```

### The 4 Recovery Dispatchers

#### 1. Incomplete Requirements Recovery (Missing Evidence)
* **Trigger:** `CompletionDecision.status == INCOMPLETE` and `missing_evidence` exists, but tests/syntax are passing.
* **Diagnosis:** Developer stopped prematurely or hit turn limit without addressing all acceptance criteria.
* **Remediation Action:**
  - Construct a **Delta Requirement Prompt** listing exclusively the unsatisfied Acceptance Criteria and unfulfilled Milestones.
  - Re-engage Developer in `IMPLEMENTATION` with clear scope: *"The previous iteration implemented X, but AC-002 and AC-003 remain unaddressed. Focus exclusively on implementing these criteria."*

#### 2. Test & Syntax Failure Recovery (Explicit Errors)
* **Trigger:** `CompletionDecision.status == FAILED` with failed test cases or PreFlight syntax violations.
* **Diagnosis:** Code modifications introduced regressions, syntax errors, or failing assertions.
* **Remediation Action:**
  - Extract the parsed pytest failure diagnostics (`PytestOutputParser`) or `ASTGuard` violation details.
  - Format a compact **Failure Trace Prompt** containing the failing test name, assertion error line, and minimal traceback.
  - Route Developer in **Fix Mode** targeting only the failing modules.

#### 3. Stagnation & Oscillation Circuit Breaker
* **Trigger:** Two consecutive iterations produce identical SHA-256 workspace hashes ($\Delta \text{Diff} == 0$), or alternating test failures occur ($A \text{ fails} \to B \text{ fails} \to A \text{ fails}$).
* **Diagnosis:** Agent is trapped in a reasoning loop, making ineffective modifications or hallucinating fixes.
* **Remediation Action:**
  - Increment `stagnation_counter`.
  - If `stagnation_counter >= 2`, trigger a **Prompt Strategy Mutation** (injecting architectural hints or simplifying the objective).
  - If stagnation continues, trip the circuit breaker and transition to `FAILED` or `BLOCKED` to protect token budget.

#### 4. Ambiguity & Re-Planning Recovery
* **Trigger:** `CompletionDecision.status == AMBIGUOUS` or requirement conflict identified.
* **Diagnosis:** Acceptance criteria are contradictory, dependencies are circular, or requirements cannot be satisfied in the current architecture.
* **Remediation Action:**
  - Suspend execution workers.
  - Transition to `AMBIGUOUS`.
  - Invoke Architect agent to perform a **Plan Revision** (`PLAN_REJECTED` $\to$ `PLANNING`), or escalate to `HumanInterventionChannel`.

---

# 9. Milestone DAG Orchestration & Subtask Lifecycle

For non-trivial tasks (BM-02, BM-03, BM-06), the FSM integrates directly with the `MilestoneDAG` to execute work incrementally rather than in a monolithic sweep.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Milestone DAG Engine                                  │
│                                                                                         │
│   ┌───────────────────┐        ┌───────────────────┐        ┌───────────────────┐       │
│   │   Milestone 1     │ ─────> │   Milestone 2     │ ─────> │   Milestone 3     │       │
│   │ (Base Data Types) │        │ (Service Logic)   │        │ (CLI & Adapter)   │       │
│   └─────────┬─────────┘        └─────────┬─────────┘        └─────────┬─────────┘       │
│             │                            │                            │                 │
│             ▼                            ▼                            ▼                 │
│    [Milestone Sub-FSM]          [Milestone Sub-FSM]          [Milestone Sub-FSM]        │
│    • Implementation             • Implementation             • Implementation           │
│    • Verification (Gate 1)      • Verification (Gate 2)      • Verification (Final)     │
│    • Snapshot Hash 1            • Snapshot Hash 2            • Review & Full Gate       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Milestone Sub-Lifecycle Rules
1. **Topological Ordering:** Milestones are resolved into a directed acyclic graph using Kahn's algorithm (`MilestoneParser.resolve_execution_order`).
2. **Milestone Isolation:** Each milestone is executed within a dedicated FSM cycle (`IMPLEMENTATION` $\to$ `VERIFICATION` $\to$ `RESOLUTION`).
3. **Progressive Gating:** Milestone $N+1$ cannot begin until Milestone $N$:
   - Has all associated Acceptance Criteria marked `VERIFIED`.
   - Passes PreFlight syntax verification (`check_syntax() == True`).
   - Produces a valid, non-empty SHA-256 workspace snapshot hash.
4. **Milestone Checkpointing:** After each milestone succeeds, an atomic checkpoint is persisted, caching completed milestones so a failure in Milestone 3 does not force re-implementing Milestone 1.

---

# 10. Unified Checkpoint & Resume Architecture

The legacy `.orchestrator_state.json` stored an unstructured dictionary with string phase names. P3 introduces a comprehensive, cryptographically verified checkpoint schema: `FSMCheckpoint`.

### Checkpoint Domain Schema

```python
"""FSM Checkpoint and State Serialization Schema."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MilestoneStateSnapshot(BaseModel):
    """Execution state of a single milestone."""

    milestone_id: str
    title: str
    is_completed: bool = False
    verified_criteria_ids: List[str] = Field(default_factory=list)
    output_hash: Optional[str] = None


class FSMCheckpoint(BaseModel):
    """Complete, recoverable snapshot of the ORAGAI execution state."""

    run_id: str
    task_description: str
    profile_name: str
    current_state: str
    state_history: List[str] = Field(default_factory=list)
    active_milestone_id: Optional[str] = None
    milestones: List[MilestoneStateSnapshot] = Field(default_factory=list)
    task_truth_graph_json: Optional[str] = None
    workspace_root_hash: str
    iteration_count: int = 1
    total_cost_usd: float = 0.0
    total_tokens_consumed: int = 0
    saved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### Zero-Token Safe Resume Protocol
When invoked with `--resume`:
1. **Load Checkpoint:** Read `.orchestrator_state.json` from workspace root.
2. **Verify Cryptographic Fingerprint:** Calculate current SHA-256 hash of workspace source files. If the hash does not match `workspace_root_hash`, warn the user of working-tree drift and invalidate stale evidence.
3. **Reconstruct TaskTruthGraph:** Restore the `TaskTruthGraph` and requirement states directly from `task_truth_graph_json`.
4. **Fast-Forward FSM:** Initialize `GuardedFSMEngine` at the checkpointed `current_state`, with all previously verified milestones preserved as `COMPLETED`.
5. **Resume Execution:** Dispatch the next uncompleted milestone immediately without re-running previous agent turns.

---

# 11. Profile-Driven Pipeline Synthesis

Rather than maintaining five distinct pipeline classes with duplicated boilerplate, the `GuardedFSMEngine` executes a **`LifecycleProfile`**.

```python
"""Lifecycle Profile definitions for GuardedFSMEngine."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set
from orchestrator.pipeline.fsm.states import FSMState


class PipelineMode(str, Enum):
    DEV_TEST = "dev-test"
    FULL = "full"
    AUDIT = "audit"
    AUDIT_FIX = "audit-fix"
    DOCS = "docs"


@dataclass(frozen=True)
class LifecycleProfile:
    """Configuration profile defining active states and rules for an execution mode."""

    mode: PipelineMode
    allowed_states: Set[FSMState]
    enable_planning: bool = True
    enable_review: bool = True
    enable_git_commit: bool = True
    max_fix_iterations: int = 5
    default_agent_turn_limit: int = 8


# Canonical Profiles
PROFILES = {
    PipelineMode.DEV_TEST: LifecycleProfile(
        mode=PipelineMode.DEV_TEST,
        allowed_states={
            FSMState.INIT,
            FSMState.PREFLIGHT,
            FSMState.IMPLEMENTATION,
            FSMState.VERIFICATION,
            FSMState.RESOLUTION,
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.BLOCKED,
            FSMState.ABORTED,
        },
        enable_planning=False,
        enable_review=False,
        enable_git_commit=True,
        max_fix_iterations=3,
        default_agent_turn_limit=8,
    ),
    PipelineMode.FULL: LifecycleProfile(
        mode=PipelineMode.FULL,
        allowed_states={
            FSMState.INIT,
            FSMState.PREFLIGHT,
            FSMState.PLANNING,
            FSMState.IMPLEMENTATION,
            FSMState.VERIFICATION,
            FSMState.RESOLUTION,
            FSMState.REVIEW,
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.BLOCKED,
            FSMState.AMBIGUOUS,
            FSMState.ABORTED,
        },
        enable_planning=True,
        enable_review=True,
        enable_git_commit=True,
        max_fix_iterations=5,
        default_agent_turn_limit=10,
    ),
    PipelineMode.AUDIT: LifecycleProfile(
        mode=PipelineMode.AUDIT,
        allowed_states={
            FSMState.INIT,
            FSMState.PREFLIGHT,
            FSMState.IMPLEMENTATION,  # Auditor Agent execution
            FSMState.VERIFICATION,  # Finding schema validation
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.ABORTED,
        },
        enable_planning=False,
        enable_review=False,
        enable_git_commit=False,
        max_fix_iterations=1,
        default_agent_turn_limit=15,
    ),
    PipelineMode.AUDIT_FIX: LifecycleProfile(
        mode=PipelineMode.AUDIT_FIX,
        allowed_states={
            FSMState.INIT,
            FSMState.PREFLIGHT,
            FSMState.PLANNING,  # Finding prioritization
            FSMState.IMPLEMENTATION,  # Fixer agent
            FSMState.VERIFICATION,  # Re-audit & pytest
            FSMState.RESOLUTION,
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.ABORTED,
        },
        enable_planning=True,
        enable_review=False,
        enable_git_commit=True,
        max_fix_iterations=4,
        default_agent_turn_limit=8,
    ),
}
```

---

# 12. Benchmark Verification Walkthroughs (BM-01 to BM-08)

The Guarded FSM design is evaluated against the 8 canonical system benchmarks established in P0:

### BM-01: Single-File Bug Fix
* **Scenario:** Off-by-one error in `token_governance.py`.
* **Legacy Pathology:** Developer wrote partial fix, ran single test, `exit_code == 0` tripped premature exit, leaving edge cases broken.
* **Guarded FSM Trace:**
  1. `INIT` $\to$ `PREFLIGHT` $\to$ `IMPLEMENTATION`.
  2. Developer fixes error and yields (`AGENT_YIELDED`).
  3. `VERIFICATION` runs `evaluate_task_completion()`.
  4. `CompletionGate` detects that edge-case acceptance criterion `AC-002` (boundary check at 0%) has no passing test evidence.
  5. Status is `INCOMPLETE`. FSM transitions: `VERIFICATION` $\to$ `RESOLUTION` $\to$ `IMPLEMENTATION`.
  6. Developer is prompted with delta prompt to add tests for `AC-002`.
  7. Developer implements boundary test; `VERIFICATION` evaluates `COMPLETE`.
  8. FSM transitions to `COMPLETED` and commits.

### BM-02: Multi-File Feature
* **Scenario:** Adding JWT authentication across 4 files (`auth.py`, `middleware.py`, `config.py`, `models.py`).
* **Legacy Pathology:** Developer hit turn limit on file 2; `ConvRunResult.completed = True` masked unfinished work as success.
* **Guarded FSM Trace:**
  1. `PLANNING` generates Milestone DAG (MS-1: Models, MS-2: Auth Service, MS-3: Middleware).
  2. MS-1 implemented and verified. Checkpoint saved.
  3. MS-2 Developer hits turn limit (`STEP_LIMIT_REACHED`). Yields control.
  4. `VERIFICATION` queries P2.1: `ImplementationState == IN_PROGRESS`.
  5. `RESOLUTION` dispatches continuation turn for MS-2 with remaining files.
  6. MS-2 and MS-3 complete and verify sequentially.
  7. Final `CompletionGate` returns `COMPLETE`. FSM routes to `REVIEW` $\to$ `COMPLETED`.

### BM-03: Architectural Refactor
* **Scenario:** Decoupling `SessionLogStore` from direct SQLite writes into repository pattern.
* **Legacy Pathology:** Developer added `pass` stubs to satisfy imports; tests passed, code merged broken.
* **Guarded FSM Trace:**
  1. Developer writes new interfaces with `pass` stubs.
  2. `VERIFICATION` runs PreFlight and ASTGuard invariant check.
  3. `ASTGuard` detects banned `pass` stub in public class method.
  4. `evaluate_task_completion()` returns `FAILED (INVARIANT_VIOLATION)`.
  5. FSM transitions: `VERIFICATION` $\to$ `RESOLUTION` $\to$ `IMPLEMENTATION` with exact AST violation trace.
  6. Developer replaces stubs with complete implementations.
  7. Refactor passes full test suite and AST audit $\to$ `REVIEW` $\to$ `COMPLETED`.

### BM-04: Deep Codebase Audit
* **Scenario:** Security and architectural audit of entire repository.
* **Legacy Pathology:** Prompt forced Auditor to exit at step 4 after reading 2 files.
* **Guarded FSM Trace:**
  1. `LifecycleProfile.AUDIT` assigns 15-turn bounded budget.
  2. `IMPLEMENTATION` executes Auditor across all workspace clusters.
  3. Auditor yields finding report.
  4. `VERIFICATION` validates each finding using `FindingValidator` (file existence, line bounds, proof snippet).
  5. If findings pass validation $\to$ `COMPLETED` (Report saved). If hallucinated paths detected $\to$ `RESOLUTION` filters invalid findings.

### BM-05: Audit-Fix Pipeline
* **Scenario:** Automated remediation of 3 CRITICAL security findings.
* **Legacy Pathology:** Fixer repaired finding 1 but broke test suite; pipeline exited declaring success.
* **Guarded FSM Trace:**
  1. `PLANNING` extracts 3 findings and creates prioritized fix DAG.
  2. Finding 1 fixed. `VERIFICATION` detects regression in existing test suite.
  3. `RESOLUTION` routes back to `IMPLEMENTATION` with pytest regression output.
  4. Finding 1 fix refined until regression resolves.
  5. Findings 2 and 3 remediated sequentially.
  6. Final re-audit confirms 0 CRITICAL findings remain and full test suite passes $\to$ `COMPLETED`.

### BM-06: New Subsystem Implementation
* **Scenario:** Creating new `CloudResilienceMesh` adapter from scratch.
* **Legacy Pathology:** Missing requirements in prompts caused Developer to invent incompatible APIs.
* **Guarded FSM Trace:**
  1. `PLANNING` generates formal requirements with type signatures and Acceptance Criteria.
  2. Architectural review gate approves `PLAN.md`.
  3. Developer implements subsystem according to plan.
  4. Tester creates parameterized test suite covering all ACs.
  5. `VERIFICATION` confirms 100% AC-to-test mapping.
  6. `REVIEW` agent reviews compact diff against architecture specs $\to$ `COMPLETED`.

### BM-07: Cross-Platform Windows/POSIX CLI
* **Scenario:** Terminal execution involving Windows paths and pipe syntax.
* **Legacy Pathology:** Command interceptor banned all pipe `|` characters, breaking subshell commands.
* **Guarded FSM Trace:**
  1. `PREFLIGHT` identifies OS environment as Windows NT.
  2. Adapter normalizes terminal execution commands for PowerShell/cmd.
  3. Developer implements CLI command.
  4. `VERIFICATION` executes runtime CLI tests in workspace sandbox.
  5. Behavioral assertions pass $\to$ `COMPLETED`.

### BM-08: Stagnation & Failure Recovery
* **Scenario:** Complex bug where Developer repeats identical failing edits.
* **Legacy Pathology:** Infinite loop until token budget completely drained.
* **Guarded FSM Trace:**
  1. Iteration 1 fails pytest. Iteration 2 produces identical diff hash.
  2. `RESOLUTION` detects `zero_diff_progress == True` and increments `stagnation_counter`.
  3. Iteration 3 repeats failure.
  4. `RESOLUTION` trips circuit breaker (`RETRIES_EXHAUSTED` / `STAGNATION_DETECTED`).
  5. FSM safely transitions to `FAILED`, persists complete diagnostic checkpoint, and halts without wasting further budget.

---

# 13. Strangler Fig Migration Strategy

To guarantee that the **244 passing unit tests** are preserved and zero regressions are introduced, the transition to the Guarded FSM is executed in four strictly decoupled phases:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               Strangler Fig Rollout Phases                              │
│                                                                                         │
│   Phase 1: Shadow Engine Implementation                                                 │
│   • Construct `orchestrator/pipeline/fsm/` subpackage (States, Events, Engine)          │
│   • 100% isolated unit test coverage for all transitions and guards                     │
│                                                                                         │
│   Phase 2: Profile Validation & CLI Interception                                        │
│   • CLI `--mode dev-test` and `--mode full` wired to `GuardedFSMEngine`                 │
│   • Legacy pipelines preserved as fallback under `--legacy-pipeline` flag               │
│                                                                                         │
│   Phase 3: Migration of Audit, Audit-Fix, and Docs                                      │
│   • Port `AuditPipeline`, `AuditFixPipeline`, `DocumentationPipeline` to Profiles       │
│   • Validate against all 8 system benchmarks                                            │
│                                                                                         │
│   Phase 4: Deprecation & Cleanup                                                        │
│   • Remove legacy `dev_test_loop.py`, `full_pipeline.py`, `state_machine.py`            │
│   • Promote `GuardedFSMEngine` to default orchestrator core                             │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 14. Target Module Structure & Class Contracts

```
orchestrator/pipeline/
├── fsm/
│   ├── __init__.py          # Public exports (GuardedFSMEngine, FSMState, PipelineEvent)
│   ├── engine.py            # GuardedFSMEngine core lifecycle runner
│   ├── states.py            # FSMState enum and state metadata
│   ├── events.py            # PipelineEvent, EventType, AgentExecutionOutcome
│   ├── transitions.py       # TransitionRule, TransitionMatrix, TransitionResult
│   ├── guards.py            # FSMGuards (Pure boolean predicates querying P2.1)
│   ├── profiles.py          # LifecycleProfile, PipelineMode definitions
│   └── checkpoint.py        # FSMCheckpoint and FSMCheckpointManager
├── milestone_dag.py         # Enhanced Milestone DAG parser
├── reviewer_parser.py       # Reviewer verdict parsing
└── base_pipeline.py         # Shared telemetry, git ops, and visualizer bindings
```

### Core Engine Interface Contract (`orchestrator/pipeline/fsm/engine.py`)

```python
"""Guarded Finite State Machine Engine core implementation contract."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.control import HumanChannel, PipelineController
from orchestrator.pipeline.fsm.checkpoint import FSMCheckpointManager
from orchestrator.pipeline.fsm.events import EventType, PipelineEvent
from orchestrator.pipeline.fsm.guards import FSMGuards
from orchestrator.pipeline.fsm.profiles import LifecycleProfile, PipelineMode
from orchestrator.pipeline.fsm.states import FSMState
from orchestrator.pipeline.fsm.transitions import (
    TransitionMatrix,
    TransitionResult,
)


class GuardedFSMEngine:
    """Deterministic, event-driven state machine orchestrating agent lifecycles."""

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        profile: LifecycleProfile,
        workspace_path: Optional[Path] = None,
        controller: Optional[PipelineController] = None,
        human_channel: Optional[HumanChannel] = None,
    ):
        self.config = config
        self.skill_manager = skill_manager
        self.profile = profile
        self.workspace_path = (workspace_path or config.workspace_path).resolve()
        self.controller = controller or PipelineController()
        self.human_channel = human_channel

        self.current_state: FSMState = FSMState.INIT
        self.state_history: List[FSMState] = [FSMState.INIT]
        self.iteration_count: int = 0
        self.transition_matrix = TransitionMatrix.build_default()

    def process_event(self, event: PipelineEvent) -> TransitionResult:
        """Evaluate active guards and execute state transition for an incoming event.

        Raises ValueError if transition is illegal or guard predicate rejects event.
        """
        rule = self.transition_matrix.get_rule(
            self.current_state, event.event_type
        )
        if not rule:
            raise ValueError(
                f"No transition rule defined for State '{self.current_state}' on Event '{event.event_type}'."
            )

        # Check state allowance in active profile
        if rule.target_state not in self.profile.allowed_states:
            raise ValueError(
                f"Target state '{rule.target_state}' is disallowed under profile '{self.profile.mode}'."
            )

        # Evaluate Guard Predicate
        guard_fn = rule.guard
        if guard_fn and not guard_fn(self._build_context(), event):
            return TransitionResult(
                success=False,
                current_state=self.current_state,
                target_state=rule.target_state,
                rejection_reason=f"Guard predicate '{guard_fn.__name__}' failed.",
            )

        # Execute On-Exit Action
        if rule.on_exit:
            rule.on_exit(self._build_context(), event)

        # Apply Transition
        old_state = self.current_state
        self.current_state = rule.target_state
        self.state_history.append(self.current_state)

        # Execute On-Entry Action
        if rule.on_entry:
            rule.on_entry(self._build_context(), event)

        # Checkpoint State
        FSMCheckpointManager.save_checkpoint(self._build_context())

        return TransitionResult(
            success=True,
            current_state=self.current_state,
            target_state=rule.target_state,
            previous_state=old_state,
        )

    def run(self, task_description: str) -> Dict[str, Any]:
        """Execute full event-driven lifecycle to terminal conclusion."""
        # Initial event dispatch
        self.process_event(
            PipelineEvent(
                event_type=EventType.START_TASK, source_phase=FSMState.INIT
            )
        )

        while not self.is_terminal():
            # Run state handler and generate next event
            next_event = self._execute_state_handler(self.current_state)
            self.process_event(next_event)

        return self._finalize_run()

    def is_terminal(self) -> bool:
        """Return True if active state is COMPLETED, FAILED, or ABORTED."""
        return self.current_state in (
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.ABORTED,
        )
```

---

# 15. P3 Exit Criteria Checklist

- [x] Complete FSM state taxonomy (11 states) formally defined.
- [x] Pure semantic separation maintained: FSM queries `TaskTruthSemanticQueries` (P2.1) without computing code/evidence logic.
- [x] Strongly typed `PipelineEvent` and `EventType` domain models specified.
- [x] Deterministic Transition Matrix with exact Guard Predicates and Action Hooks established.
- [x] Inversion of Control (IoC) over OpenHands SDK designed (turn-bounded execution, no violent interrupt threads).
- [x] 4 intelligent recovery loops (`INCOMPLETE`, `FAILED`, `STAGNATION`, `AMBIGUOUS`) specified in `RESOLUTION` state.
- [x] Milestone DAG progressive gating and checkpointing specified.
- [x] Cryptographically validated `FSMCheckpoint` schema designed for zero-token safe resume.
- [x] Unified `LifecycleProfile` mechanism replacing 5 legacy pipeline scripts.
- [x] All 8 canonical system benchmarks (BM-01 to BM-08) verified against the FSM lifecycle.
- [x] 4-phase Strangler Fig migration strategy preserving the 244-test safety net defined.
- [x] Zero production code modified during this design phase.

---

# 16. Handoff Contract for P4 (Adaptive Governance & Token Budgets)

P3 provides the architectural framework for state orchestration. It establishes the following operating contract for **P4 (Adaptive Resource Governance & Dynamic Step Allocation)**:

1. **State-Aware Resource Allocation:** P4 will allocate token and turn budgets dynamically based on `FSMState` and milestone complexity (e.g., higher budget for `PLANNING` on complex tasks, micro-budgets for `RESOLUTION` fixes).
2. **Yield Outcome Consumption:** P4 will consume `AgentExecutionOutcome` telemetry to adjust budget curves in real time.
3. **Monetary Circuit Breaker Integration:** P4 will hook into `FSMGuards` to trip transitions to `BLOCKED` or `FAILED` when dollar thresholds are reached.

---

# 17. Final Architectural Verdict

The **P3 Guarded FSM & Lifecycle Orchestration Plan** provides a mathematically rigorous, event-driven, and fault-tolerant orchestration core. It permanently eliminates the passive enum routing, premature loop terminations, and procedural fragility of the legacy system while cleanly integrating with P1 Task Truth and P2.1 Evidence Gates.
