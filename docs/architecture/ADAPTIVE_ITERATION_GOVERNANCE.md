# 🧭 Adaptive Iteration Governance Layer Architecture Specification

## Overview

The **Adaptive Iteration Governance Layer** establishes an authoritative, evidence-driven supervisor over autonomous agent turn execution in ORAGAI. It eliminates the fragile paradigm of static iteration counters (e.g. `base_turns = 10 -> STOP`) in favor of dynamic task-aware budgeting, real-time progress observation, chaos detection, stagnation mitigation, and empirical verification gates.

---

## 🏛️ Architectural Separation of Concerns

```text
    ┌──────────────────────────────────────────────┐
    │                 LLM Agent                    │
    │         (Produces actions & work)            │
    └──────────────────────┬───────────────────────┘
                           │ Actions / Events
                           ▼
    ┌──────────────────────────────────────────────┐
    │              Progress Monitor                │
    │        (Observes what actually happened)     │
    └──────────────────────┬───────────────────────┘
                           │ Metrics & Telemetry
                           ▼
    ┌──────────────────────────────────────────────┐
    │             Iteration Governor               │
    │       (Evaluates execution trajectory)       │
    └──────────────────────┬───────────────────────┘
                           │ Authoritative Decisions
                           ▼
    ┌──────────────────────────────────────────────┐
    │                 ORAGAI FSM                   │
    │        (Owns authoritative system state)     │
    └──────────────────────┬───────────────────────┘
                           │ State Validation
                           ▼
    ┌──────────────────────────────────────────────┐
    │             Verification Gate                │
    │   (Determines completion evidence exists)    │
    └──────────────────────────────────────────────┘
```

* **Agents produce work**: The agent remains an executor of tools (files, terminal, linters).
* **Governance evaluates progress**: The governor evaluates velocity, error bursts, and repetition.
* **Verification evaluates evidence**: Tests, syntax, and mutated files decide completion.
* **The FSM owns lifecycle state**: State transitions remain deterministic and cryptographic.

---

## 📦 Core Subsystems (`orchestrator/governance/`)

### 1. Data Models (`models.py`)
* `GovernanceAction`:
  * `CONTINUE`: Execution is healthy and proceeding towards goals.
  * `EXTEND_BUDGET`: Agent is actively mutating code and requires more turns.
  * `CHANGE_STRATEGY`: Agent is in an error burst or exploration churn; directive injected.
  * `REPLAN_TASK`: Recurring cycles or deadlocks requiring architectural breakdown.
  * `PAUSE_BLOCK`: Human intervention required.
  * `RETRY`: Transient failure eligible for targeted retry.
  * `FAIL`: Budget exhausted without progress or critical violations.
  * `VERIFY_COMPLETION`: Turn completed naturally with verified artifacts.
* `ExecutionHealth`: `HEALTHY`, `PROGRESSING`, `CHAOTIC`, `STAGNANT`, `CYCLING`, `EXHAUSTED`, `BLOCKED`, `CRITICAL_FAILURE`.
* `TaskCategory`: 11 engineering disciplines: `ARCHITECTURE`, `IMPLEMENTATION`, `DEBUGGING`, `TESTING`, `REVIEW`, `AUDIT`, `REFACTORING`, `RESEARCH`, `DOCUMENTATION`, `SECURITY`, `CODE_GENERATION`.

### 2. Task-Aware Budget Allocator (`budget_allocator.py` & `governance_policy.py`)
Dynamically tailors turn budgets rather than applying universal arbitrary limits:
* Classifies task domain from prompt semantics, mode, and assigned role.
* Allocates calibrated bounds (`initial_turns`, `min_turns`, `max_extension_turns`, `max_total_ceiling_turns`).
* Scales initial turns proportionally with task complexity.

### 3. Real-Time Progress Monitor (`progress_monitor.py` & `progress_metrics.py`)
* Synchronously monitors all `ActionEvent` and `ObservationEvent` emissions via `OpenHandsTelemetryBridge`.
* Classifies action intent (`is_mutation`, `is_read`, `is_terminal`, `is_error`).
* Computes real-time execution metrics:
  * `mutation_velocity = mutations / total_steps`
  * `error_rate = errors / total_steps`
  * `repetition_score`: Frequency ratio of most repeated commands.
  * `action_diversity_score`: Entropy of distinct tool operations.
  * `consecutive_stagnant_steps`: Trailing steps without code modifications.

### 4. Chaos Detector (`chaos_detector.py`)
Detects erratic or thrashing agent streams before budget exhaustion:
* **Error Bursts**: Triggers when $\ge 3$ consecutive tool or terminal actions fail.
* **Error Density**: Triggers when $>60\%$ of actions fail in a sliding window ($W=6$).
* **Failing Command Repetition**: Intercepts identical commands that fail repeatedly (e.g. invalid flags, missing binaries).
* **Action**: Emits `CHANGE_STRATEGY` with precise remediation directives.

### 5. Stagnation Detector (`stagnation_detector.py`)
* **Exploration Exhaustion**: Detects when an agent consumes $\ge 7$ turns solely reading files without modifying any target files.
* **Repetitive Read Loops**: Detects when identical files are read $\ge 3$ times.
* **Action**: Instructs the agent to cease reading and initiate code mutations.

### 6. Checkpoint Evaluator (`checkpoint_evaluator.py`)
Evaluates execution trajectory at periodic intervals and upon turn yields:
* **Evidence-Based Extensions**: If an agent hits the turn envelope limit but demonstrates active code mutations ($V_{\text{mut}} > 0$) with low error rates ($E_{\text{rate}} < 0.40$), extends budget up to the ceiling.
* **Zero False Completion Barrier**: If an agent claims natural completion on a coding task without mutating any files, completion is rejected and a corrective directive is issued.

---

## 🛡️ FSM and Verification Gate Integration

In `orchestrator/pipeline/fsm/engine.py`:
1. `_handle_implementation()`:
   * Dynamically requests initial budget from `iteration_governor.allocate_initial_budget()`.
   * Passes `progress_monitor` into the OpenHands runtime bridge.
   * Evaluates the yield via `iteration_governor.evaluate_turn_yield()`.
   * Automatically injects any `governance_directive` into the prompt for subsequent turns.
2. `_handle_verification()`:
   * Evaluates `governance_decision`. If governance blocked the turn (`FAIL`, `CHAOTIC`, `EXHAUSTED`), verification immediately fails closed.
   * Eliminates the False Completion loophole: pre-existing passing tests cannot mask an uncompleted or stagnant turn.

---

## 🧪 Verification Matrix

| Test Suite | Assertions | Status |
|---|---|:---:|
| `test_task_aware_category_inference` | Multi-category domain classification | ✅ PASS |
| `test_task_budget_allocation_scaling` | Complexity-proportional turn allocation | ✅ PASS |
| `test_progress_monitor_and_metrics` | Step telemetry & metric calculation | ✅ PASS |
| `test_chaos_detector_error_burst` | 3-consecutive error burst detection | ✅ PASS |
| `test_stagnation_detector_exploration_exhaustion` | 7-turn read-only exhaustion | ✅ PASS |
| `test_stagnation_detector_repetition_loop` | Read loops $\ge 3$ detected | ✅ PASS |
| `test_budget_extension_on_active_mutations` | Turn extension on active progress | ✅ PASS |
| `test_governance_blocks_chaotic_session` | Strategy change on chaotic bursts | ✅ PASS |
| `test_fsm_engine_integrates_iteration_governor` | FSM integration & directive injection | ✅ PASS |
| **Full Repository Regression Suite** | **565 total unit, FSM & pipeline tests** | ✅ **565/565 PASS** |
