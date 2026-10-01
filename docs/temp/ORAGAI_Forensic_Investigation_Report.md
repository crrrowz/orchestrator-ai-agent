# ORAGAI Forensic Execution Investigation Report

> **Investigator**: Antigravity (Claude Opus 4.6)
> **Date**: 2026-10-01T07:42 UTC+3
> **Scope**: Forensic analysis of why ORAGAI fails to reliably complete real autonomous software engineering projects
> **Method**: Static source analysis + runtime state evidence (`.orchestrator_state.json`, PowerShell history, error output)
> **Code Modified**: NONE

---

## Executive Summary

**ORAGAI cannot reliably complete autonomous software engineering projects.** The 538+ passing tests validate individual components in isolation but never exercise the actual end-to-end production execution path under real-world conditions. The investigation identified **6 CRITICAL**, **5 HIGH**, and **4 MEDIUM** root causes.

The single most important finding: **The system has no mechanism to actually continue working after an agent hits its iteration limit.** When the developer agent reaches its 20-turn ceiling, the governance layer correctly detects stagnation, but the FSM then attempts to transition to `BLOCKED` — a state the `audit-fix` profile explicitly disallows. This causes an unrecoverable failure with no remediation path. This is exactly what happened in the observed run.

---

## 1. Observed Execution Timeline (from `.orchestrator_state.json` and CLI output)

```
RUN_ID:       e1fd3e1f
PROFILE:      audit-fix
TASK:         "Autonomous codebase defect and optimization fix loop."
TOTAL_TOKENS: 1,014,314
ITERATIONS:   2
DURATION:     ~336.20s

STATE TIMELINE:
INIT → PREFLIGHT → PLANNING → IMPLEMENTATION → VERIFICATION → RESOLUTION
→ IMPLEMENTATION → VERIFICATION → RESOLUTION → IMPLEMENTATION → FAILED

GOVERNANCE DECISION AT FAILURE:
  action:     CHANGE_STRATEGY
  health:     STAGNANT
  reason:     "Exploration exhaustion: 40 turns elapsed with 0 code mutations.
               Agent is churning across read/inspect operations without modifying code."
  evidence:
    total_steps:        40
    mutation_steps:      0
    read_steps:         21
    terminal_steps:     26
    error_steps:         1
    unique_files_mutated: 0
    consecutive_stagnant_steps: 40

TERMINAL ERROR:
  "Transition failed: Target state 'FSMState.BLOCKED' is disallowed under profile 'audit-fix'."
  "Turn step limit reached (20 turns)."
```

---

## 2. Root Cause Analysis — Classified Findings

---

### FINDING F-001: Profile-State Mismatch Causes Unrecoverable Transition Failure

**Severity**: CRITICAL
**Confidence**: HIGH (reproduced from actual execution evidence)

#### What Happened

The `audit-fix` profile's `allowed_states` set does **NOT** include `FSMState.BLOCKED`:

```python
# profiles.py:102-114
PipelineMode.AUDIT_FIX: LifecycleProfile(
    allowed_states={
        FSMState.INIT, FSMState.PREFLIGHT, FSMState.PLANNING,
        FSMState.IMPLEMENTATION, FSMState.VERIFICATION,
        FSMState.RESOLUTION,
        FSMState.COMPLETED, FSMState.FAILED, FSMState.ABORTED,
    },
    # Note: FSMState.BLOCKED is ABSENT
)
```

But when the governance layer detects stagnation and the agent hits its step limit, the verification handler produces `CompletionDecision(status=FAILED)`, which routes to `RESOLUTION`. The resolution handler then triggers `REMEDIATION_ROUTED → IMPLEMENTATION`. But after the third IMPLEMENTATION attempt (iteration_count >= max_fix_iterations=4), resolution emits `RETRIES_EXHAUSTED`, which transitions to `FAILED`.

**However**, before that can happen, the engine encounters a wildcard transition rule:

```python
# transitions.py:400-406
TransitionRule(
    source_state=None,  # Wildcard — matches ANY state
    trigger_event=EventType.HUMAN_INTERVENTION_REQUIRED,
    target_state=FSMState.BLOCKED,
)
```

The `HUMAN_INTERVENTION_REQUIRED` event can be emitted from **any state** via the circuit breaker. The engine then attempts to transition to `BLOCKED`, but the profile boundary check at [engine.py:216-224](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L216-L224) rejects it:

```python
if target_state not in self.profile.allowed_states:
    return TransitionResult(
        success=False,
        rejection_reason=f"Target state '{target_state}' is disallowed under profile..."
    )
```

This rejection triggers the recovery path at [engine.py:346-380](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L346-L380), which sends `CRITICAL_ERROR`, which transitions to `FAILED` — but the real problem is that the system **never had a chance to recover** from governance-detected stagnation because the `BLOCKED` state was disallowed.

#### Root Cause

The profile definition for `audit-fix` does not include `BLOCKED`, yet the universal wildcard transition rules can target `BLOCKED` from any state. This is a **state space inconsistency** between the transition matrix and the profile boundary.

#### Why Existing Tests Missed It

Tests mock individual guards and transitions. No test runs a real `audit-fix` profile through a governance stagnation detection that triggers a `HUMAN_INTERVENTION_REQUIRED` event.

#### Impact

Every `audit-fix` run that hits a stagnation or circuit breaker condition will fail with an unrecoverable transition rejection instead of entering a recoverable blocked state.

---

### FINDING F-002: Agent Produces Zero Mutations — 40 Turns of Pure Reading

**Severity**: CRITICAL
**Confidence**: HIGH (from `.orchestrator_state.json` evidence)

#### What Happened

The developer agent consumed **40 turns** and **779,023 tokens** across its bounded turn envelopes and produced **zero code mutations** (`mutation_steps: 0`, `unique_files_mutated: 0`). It performed 21 read operations and 26 terminal (shell) commands but never wrote code.

#### Root Cause

The orchestrator delegates the entire implementation task to a single LLM agent turn with a compiled prompt. But:

1. **The compiled prompt for `audit-fix` is generic**: It says "Task Objective: Autonomous codebase defect and optimization fix loop." — this is insufficiently specific for the agent to know what files to modify.

2. **No audit findings are injected**: The `_handle_implementation` method at [engine.py:565-708](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L565-L708) builds the prompt from `context.task_description` and optionally from `context.last_verification_decision` and `context.last_test_result`. But on the first iteration, both are `None`. For `audit-fix` mode, there is no code path that injects actual audit findings into the developer prompt.

3. **The agent explores endlessly**: Without specific targets, the LLM agent reads files, runs `ls`, inspects the project structure, but never commits to a modification because it has no clear target.

#### Why Existing Tests Missed It

Tests mock `runtime_bridge.execute_bounded_turn` to return a successful `AgentExecutionOutcome` with pre-populated `mutated_files`. No test verifies that the prompt actually causes the LLM to produce mutations.

#### Impact

The entire implementation phase is wasted when the task description is too vague. 779K tokens consumed with zero productive output.

---

### FINDING F-003: Governance Detects Stagnation But Cannot Remediate It

**Severity**: CRITICAL
**Confidence**: HIGH

#### What Happened

The `CheckpointEvaluator` correctly detected stagnation:

```python
# checkpoint_evaluator.py:62-73
if is_stagnant:
    return GovernanceDecision(
        action=GovernanceAction.CHANGE_STRATEGY,
        health=ExecutionHealth.STAGNANT,
        recommended_directive="Cease repetitive reading operations..."
    )
```

This decision is stored in `context.metadata["governance_decision"]` and `context.metadata["governance_directive"]`. The next implementation turn injects it into the prompt as:

```
## Strategic Directive from Governance Watchdog:
Cease repetitive reading operations. Commit the required code modifications to targeted files now.
```

But this is **only advisory text injected into the LLM prompt**. The FSM itself does **nothing** with a `CHANGE_STRATEGY` governance action. The verification handler checks for stagnation health codes and marks the decision as `FAILED`, but this just sends the FSM back to `RESOLUTION → IMPLEMENTATION` — with the same prompt and the same stagnation conditions.

#### Root Cause

`GovernanceAction.CHANGE_STRATEGY` has no FSM transition handler. It is purely informational. The FSM has no mechanism to:
- Switch to a different agent strategy
- Break the task into smaller pieces
- Choose different files to modify
- Escalate to human intervention

#### Why Existing Tests Missed It

Tests verify that `CheckpointEvaluator` produces the correct `GovernanceDecision` enum value. No test verifies that the FSM engine actually acts on `CHANGE_STRATEGY` differently from `CONTINUE`.

#### Impact

The system enters an infinite stagnation loop: detect stagnation → inject directive text → run same agent → detect stagnation again → repeat until iteration budget exhausted.

---

### FINDING F-004: Session Recovery Does Not Restore Agent Context

**Severity**: CRITICAL
**Confidence**: HIGH (from source code analysis)

#### What Happened

The `_resume_from_checkpoint` method at [engine.py:1041-1074](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L1041-L1074) restores:

```python
self.context.run_id = checkpoint.run_id
self.context.iteration_count = checkpoint.iteration_count
self.context.total_iterations = ...
self.context.total_tokens_consumed = ...
self.context.total_cost_usd = ...
self.context.metadata = ...
self.context.current_state = target_st
self.context.state_history = [FSMState(s) for s in checkpoint.state_history]
```

**NOT restored**:
- `milestone_dag` (the actual task breakdown)
- `task_truth_graph` (only a JSON string is saved, never deserialized back)
- `mutated_files` (what was already changed)
- `last_outcome` (what the agent did)
- `last_verification_decision` (what failed)
- `last_test_result` (test failures)
- `adapter` (project type detection)
- `git_ops` (VCS state)
- `stagnation_counter`
- `last_workspace_hash`

The checkpoint stores `task_truth_graph_json` as a serialized string, but `_resume_from_checkpoint` never deserializes it back into a `task_truth_graph` object. The milestones are saved as `MilestoneStateSnapshot` objects but never re-parsed into `SubtaskMilestone` objects.

#### Root Cause

The checkpoint serialization layer (`FSMCheckpointManager.save_checkpoint`) saves comprehensive state, but the deserialization layer (`_resume_from_checkpoint`) only restores a subset. This is a classic **asymmetric serialization** bug.

#### Why Existing Tests Missed It

No test performs a real checkpoint → kill → resume → verify continuation sequence. Tests that exercise checkpoint loading mock the checkpoint data and verify that `current_state` is set correctly, but don't verify that the full context is functional.

#### Impact

After a crash and restart, the FSM resumes at a valid-looking state but has lost all context about what was planned, what was changed, what failed, and why. The agent starts from scratch but with a partially-modified workspace, leading to confusion, conflicts, and wasted tokens.

---

### FINDING F-005: Verification Logic Has No Test Execution for Self-Targeting `audit-fix`

**Severity**: CRITICAL
**Confidence**: HIGH

#### What Happened

In `_handle_verification` at [engine.py:710-874](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L710-L874), the verification logic runs:

```python
test_res = None
if self.context.adapter:
    test_res = self.context.adapter.run_tests(self.workspace_path)
```

For the `audit-fix` mode running on ORAGAI itself, the test suite is the ORAGAI test suite (538+ tests). Running this takes significant time and the tests may pass even if the "fix" was never applied, because the agent made zero mutations.

Then the decision logic at [engine.py:749-843](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L749-L843):

```python
if not self.context.task_truth_graph:
    # ... derives decision from tests & syntax ...
    elif test_res and test_res.passed:
        decision = CompletionDecision(
            status=CompletionStatus.COMPLETE,
            satisfied_requirements=["Task Execution", "All Tests Passed"],
        )
```

This means: **if the agent does nothing and tests pass, the task can be marked COMPLETE**. The only thing preventing this is the `agent_incomplete` check that catches step limit violations. But if the agent happened to finish naturally (e.g., gave up and said "done"), the FSM would accept it as complete without verifying any actual changes were made.

#### Root Cause

The verification logic for non-TaskTruthGraph paths (i.e., `dev-test` and `audit-fix` modes) equates "tests pass" with "task complete". There is no check for:
- Whether any files were actually modified
- Whether the task objectives were addressed
- Whether the agent's output relates to the task

#### Why Existing Tests Missed It

Tests mock `adapter.run_tests()` to return passing results and verify the decision status. No test verifies that a no-mutation execution cannot reach `COMPLETED`.

#### Impact

False positive completions. The FSM can declare success when zero useful work was performed, as long as pre-existing tests pass.

---

### FINDING F-006: Iteration Budget Logic Creates Self-Defeating Loop

**Severity**: CRITICAL
**Confidence**: HIGH

#### What Happened

The governance evaluator at [checkpoint_evaluator.py:86-121](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/governance/checkpoint_evaluator.py#L86-L121) distinguishes between two post-yield outcomes:

1. **Agent completed naturally** → `VERIFY_COMPLETION` (proceed to verification)
2. **Agent hit step limit** → Check if `can_extend`:
   - `has_mutations` AND `error_rate < 0.40` AND budget room → `EXTEND_BUDGET`
   - Otherwise → `FAIL`

But `EXTEND_BUDGET` is **never consumed by the FSM**. The governance decision is stored in metadata and optionally injected into the next prompt as text, but the FSM engine never reads `allocated_turns_extension` to actually increase the agent's turn budget.

The implementation handler at [engine.py:626-631](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L626-L631) calculates turns:

```python
allocated_turns = self.iteration_governor.allocate_initial_budget(
    task_description=...,
    role=role_name,
    mode=...,
    workspace_path=...,
)
```

This always calls `AdaptiveTaskBudgetAllocator.calculate_initial_budget()`, which is a **stateless** function that ignores previous governance decisions. The extension is never applied.

#### Root Cause

The governance layer produces `EXTEND_BUDGET` decisions with `allocated_turns_extension`, but the implementation handler always recalculates from scratch using the stateless budget allocator. There is no code path that reads and applies `allocated_turns_extension`.

#### Why Existing Tests Missed It

Tests verify that `CheckpointEvaluator` produces `GovernanceAction.EXTEND_BUDGET` with the correct extension count. No test verifies that the engine actually allocates more turns on the next cycle.

#### Impact

The adaptive governance system is advisory-only. Budget extensions are computed but never applied. The agent always gets the same initial budget regardless of progress.

---

### FINDING F-007: `max_fix_iterations` for `audit-fix` Is 4, but `total_iterations` Ceiling Is 20

**Severity**: HIGH
**Confidence**: HIGH

#### Evidence

```python
# profiles.py:102-121
PipelineMode.AUDIT_FIX: LifecycleProfile(
    max_fix_iterations=4,
    max_total_iterations=20,
)
```

The resolution handler at [engine.py:876-914](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L876-L914):

```python
def _handle_resolution(self):
    self.context.iteration_count += 1
    self.context.total_iterations += 1
    max_fix = self.profile.max_fix_iterations  # 4
    max_total = self.profile.max_total_iterations  # 20

    if self.context.total_iterations >= max_total:
        return RETRIES_EXHAUSTED
    if self.context.iteration_count >= max_fix:
        return RETRIES_EXHAUSTED
```

But `iteration_count` is reset to 0 when a milestone advances ([transitions.py:240](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/transitions.py#L240)). This means:

- For a single-milestone task: The agent gets 4 fix attempts per milestone.
- For a multi-milestone task: The agent gets 4 fix attempts per milestone, up to 20 total.

In the observed run, `total_iterations` was 2 and `iteration_count` was 2 at failure. The system failed at iteration 2 of 4 because the governance stagnation detection triggered `BLOCKED` (which was disallowed) before the retry budget was exhausted.

#### Impact

The retry budget is often not fully utilized because other failure paths (governance, profile boundary) terminate execution before the retry limit is reached.

---

### FINDING F-008: No Progress Watchdog Between Agent Turns

**Severity**: HIGH
**Confidence**: HIGH

#### Evidence

The main loop at [engine.py:289-382](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L289-L382) has a wall-clock timeout check, but **no inter-turn progress check**. The governance evaluation happens **inside** `_handle_implementation`, after the agent turn completes. If the agent turn itself takes 300 seconds and produces nothing, the FSM only learns about stagnation after the tokens are already spent.

There is a `progress_monitor` passed to `execute_bounded_turn`, but looking at the telemetry bridge code, it records step-by-step events. The governance checkpoint is only evaluated **after** the full turn:

```python
# engine.py:673-682
gov_decision = self.iteration_governor.evaluate_turn_yield(
    profile=task_profile,
    turns_used=outcome.iterations_executed,
    ...
)
```

This means the system detects stagnation retroactively, not proactively. By the time it knows the agent is stuck, the tokens are burned.

#### Impact

Token waste. The system cannot abort a stagnating agent mid-turn. Each agent turn always runs to its full budget or until the SDK's own stuck detector fires.

---

### FINDING F-009: Milestone Advancement Has No Context Carry-Forward

**Severity**: HIGH
**Confidence**: HIGH

#### Evidence

When a milestone completes and the FSM advances to the next one:

```python
# transitions.py:234-241
def action_advance_milestone(ctx, ev):
    if ctx.milestone_dag and ctx.active_milestone_index < len(ctx.milestone_dag):
        ctx.milestone_dag[ctx.active_milestone_index].is_completed = True
    ctx.active_milestone_index += 1
    ...
    ctx.iteration_count = 0
    ctx.stagnation_counter = 0
```

The context carries no information about what was learned, what files were modified, or what failed in the previous milestone. The next implementation turn gets a fresh prompt with only the milestone description. The agent has no memory of what happened before.

#### Impact

Multi-milestone tasks cannot build on previous work. Each milestone starts from scratch. The agent may re-read files it already analyzed, redo work, or make conflicting changes.

---

### FINDING F-010: Wildcard Transition Rules Override Profile Boundaries

**Severity**: HIGH
**Confidence**: HIGH

#### Evidence

The transition matrix contains two wildcard rules ([transitions.py:400-415](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/transitions.py#L400-L415)):

```python
TransitionRule(source_state=None, trigger_event=HUMAN_INTERVENTION_REQUIRED, target_state=BLOCKED)
TransitionRule(source_state=None, trigger_event=ABORT_REQUESTED, target_state=ABORTED)
```

`source_state=None` means these match from **any** state. But the profile boundary check at [engine.py:216-224](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L216-L224) runs **after** the rule match, rejecting transitions to states not in the profile.

The `ABORTED` state is included in all profiles, so abort always works. But `BLOCKED` is not in `audit-fix` or `docs` profiles, making the circuit breaker and human intervention mechanism non-functional for those modes.

#### Impact

Circuit breakers, resource governors, and human escalation are silently disabled for `audit-fix` and `docs` modes. Instead of a graceful degradation path, the system crashes with a transition rejection.

---

### FINDING F-011: No Independent Completion Verification

**Severity**: HIGH
**Confidence**: HIGH

#### Evidence

The `_handle_verification` method makes its completion decision based on:
1. Syntax checks (automated, zero-token)
2. Test results (if adapter is available)
3. Agent's exit reason
4. Governance health status

It does **NOT**:
- Re-inspect the files the agent claims to have modified
- Verify that the task description requirements are addressed
- Run a separate LLM evaluation of the changes
- Compare pre/post workspace state semantically
- Verify that test additions actually test the claimed changes

The system trusts the agent's `completed_naturally` flag and test results as the sole evidence of completion.

#### Impact

An agent that says "done" and doesn't break existing tests is considered successful, regardless of whether it addressed the actual task.

---

### FINDING F-012: Ephemeral Agent Sessions Destroy Inter-Turn Memory

**Severity**: MEDIUM
**Confidence**: HIGH

#### Evidence

From [openhands_bridge.py:1279-1287](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/engine/openhands_bridge.py#L1279-L1287):

```python
conv = LocalConversation(
    agent=agent,
    workspace=workspace_path,
    max_iteration_per_run=max_turns,
    delete_on_close=True,  # ← DELETES conversation history
    ...
)
```

And teardown at [openhands_bridge.py:1322-1325](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/engine/openhands_bridge.py#L1322-L1325):

```python
try:
    conv.close()
except Exception:
    pass
```

Every agent turn creates a fresh `LocalConversation` that is destroyed after the turn. The agent has no memory of what it did in the previous turn. The only information carried forward is what the FSM injects into the next prompt (failure diagnostics, governance directives).

#### Impact

The agent cannot learn from its mistakes. If it made a wrong decision in turn 1, it has no record of that decision in turn 2. It may repeat the same mistake.

---

### FINDING F-013: Test Suite Coverage Blind Spot — No End-to-End Execution Tests

**Severity**: MEDIUM
**Confidence**: HIGH

#### Evidence

The test directory contains 63 test files with comprehensive unit and subsystem coverage. Looking at the test names:

- `test_guarded_fsm.py` (48KB) — Tests FSM transitions, guards, profiles
- `test_sdk_bridge.py` (23KB) — Tests OpenHands bridge
- `test_adaptive_governance.py` (15KB) — Tests governance layer
- `test_audit_fix_pipeline.py` (20KB) — Tests audit-fix pipeline

But all of these use mocks:
- `runtime_bridge.execute_bounded_turn` is mocked
- `adapter.run_tests()` is mocked
- `PreFlightGuard.check_syntax()` is often mocked
- LLM responses are mocked

There is **no test** that:
1. Creates a real workspace
2. Runs the full `GuardedFSMEngine.run()` with a real LLM call
3. Verifies that actual code changes are produced
4. Verifies that actual tests pass
5. Verifies milestone continuation
6. Verifies crash recovery with full context

#### Impact

The 538+ tests prove component correctness in isolation but do not prove the system works as an integrated whole. This is the fundamental gap.

---

### FINDING F-014: Cost Tracking Is Non-Functional

**Severity**: MEDIUM
**Confidence**: HIGH

#### Evidence

In `ExitStatusClassifier.classify()` at [openhands_bridge.py:1102-1223](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/engine/openhands_bridge.py#L1102-L1223), every outcome has:

```python
cost_usd=0.0
```

The cost is hardcoded to `0.0` in every classification branch. The `AdaptiveResourceGovernor` uses `cost_usd` for budget management, but since it's always zero, cost-based circuit breakers never trip.

From the observed state: `total_cost_usd: 0.0` despite consuming 1,014,314 tokens.

#### Impact

The monetary circuit breaker is non-functional. The system cannot enforce cost limits.

---

### FINDING F-015: `BLOCKED` and `AMBIGUOUS` States Are Dead-End Loops

**Severity**: MEDIUM
**Confidence**: HIGH

#### Evidence

When the FSM reaches `BLOCKED` or `AMBIGUOUS` at [engine.py:320-340](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L320-L340):

```python
if self.context.current_state in (FSMState.BLOCKED, FSMState.AMBIGUOUS):
    if self.human_channel and self.human_channel.has_message():
        # process human input
        continue
    else:
        logger.info(f"Execution halted at non-terminal state...")
        break  # ← EXIT THE MAIN LOOP
```

The `break` exits the main event loop. The FSM returns a result dict with `blocked: True`, but the `_finalize_run_result` at [engine.py:1076-1102](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L1076-L1102) marks `success: False` (since state is not `COMPLETED`).

There is **no mechanism** to:
- Retry the blocked operation automatically
- Schedule a future check
- Poll for human input
- Timeout and recover

Once blocked, the run is over.

#### Impact

`BLOCKED` is effectively equivalent to `FAILED` — it terminates the run. The only difference is the result dict contains `blocked: True` instead of just `success: False`.

---

## 3. Premature Termination Path Analysis

| # | Condition | Evidence | Can It Happen Silently? |
|---|-----------|----------|------------------------|
| 1 | Agent reports DONE (NATURAL_COMPLETION) | [openhands_bridge.py:1102-1117](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/engine/openhands_bridge.py#L1102-L1117) — `ConversationExecutionStatus.FINISHED` → verified by tests+syntax | **YES** — agent can say "done" after reading files without changing anything |
| 2 | ORAGAI terminates via wall-clock timeout | [engine.py:291-307](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L291-L307) | No — produces `CRITICAL_ERROR` event |
| 3 | Task marked complete via passing tests | [engine.py:814-818](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L814-L818) | **YES** — pre-existing passing tests = "complete" |
| 4 | Session ends via `BLOCKED`/`AMBIGUOUS` | [engine.py:331-340](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L331-L340) | No — logged and returns `blocked: True` |
| 5 | Run ends via retry exhaustion | [engine.py:883-894](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L883-L894) | No — produces `RETRIES_EXHAUSTED` event |
| 6 | LLM response causes false completion | Agent says "done" → NATURAL_COMPLETION → tests pass → COMPLETE | **YES** — F-005 |
| 7 | Exception silently terminates workflow | [engine.py:228-231](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L228-L231) — `on_exit` and `on_entry` exceptions are caught with `logger.warning` and **swallowed** | **YES** — transition hooks can fail silently |
| 8 | Timeout terminates without recovery | [engine.py:291-307](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py#L291-L307) — CRITICAL_ERROR → FAILED, no recovery | **YES** — hard termination |
| 9 | Empty/invalid agent response | [openhands_bridge.py:1209-1223](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/engine/openhands_bridge.py#L1209-L1223) — defaults to `STEP_LIMIT_REACHED` | No — classified as incomplete |
| 10 | FSM enters valid state with no work possible | Profile boundary rejection → recovery → CRITICAL_ERROR → FAILED | **YES** — F-001 |

---

## 4. Autonomous Continuation Mechanism Verification

**Required Sequence**:
```
Task 1 → complete → persist → Task 2 → complete → persist → Task 3 → fail → recover → continue → Task 4
```

**Analysis**:

The `run_tasks()` method in [orchestrator.py:88-178](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/orchestrator.py#L88-L178) implements a sequential task queue. Each task calls `run_task()` which creates a **new** `GuardedFSMEngine` instance. There is no shared state between tasks.

Within a single `run_task()`, milestone continuation works via `action_advance_milestone` at [transitions.py:234-241](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/transitions.py#L234-L241), but:

1. ✅ Milestone advancement works structurally
2. ❌ No context carry-forward between milestones (F-009)
3. ❌ No failure recovery within a milestone that preserves agent learning (F-012)
4. ❌ No cross-task state sharing
5. ❌ Checkpoint recovery is incomplete (F-004)

**Conclusion**: Continuation breaks at the **agent context level**. The FSM transitions work correctly, but the agent has no memory of what it learned, making "continuation" equivalent to "restart".

---

## 5. Architecture Gap Analysis

| Required Mechanism | Status | Evidence |
|---|---|---|
| **Supervisor / Progress Watchdog** | PARTIAL — Governance layer detects stagnation post-hoc, cannot intervene mid-turn | F-008 |
| **Task Queue** | EXISTS — `SequentialTaskQueue` in [task_queue.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/task_queue.py) | Functional for sequential tasks |
| **Durable Execution State** | PARTIAL — Checkpoint saves comprehensive state, deserialization is incomplete | F-004 |
| **Crash Recovery** | BROKEN — Resumes at valid state but without milestone/context data | F-004 |
| **Checkpointing** | EXISTS — `FSMCheckpointManager` saves after every transition | Functional for state tracking |
| **Session Rotation** | MISSING — Each agent turn is ephemeral, no session continuity | F-012 |
| **Independent Completion Verification** | MISSING — Relies on test results and agent self-report | F-011 |
| **Stuck Detection** | PARTIAL — SDK-level stuck detector + governance stagnation, but no FSM-level intervention | F-003, F-008 |
| **Retry Policy** | EXISTS — `max_fix_iterations` + `max_total_iterations` | F-007 shows it's underutilized |
| **Failure Classification** | EXISTS — `ExitStatusClassifier` with 7 exit reasons | Functional |
| **Context Compaction** | MISSING — No mechanism to summarize previous turns for the next agent | F-009, F-012 |
| **Budget Management** | BROKEN — Cost always 0.0, extensions computed but not applied | F-006, F-014 |
| **Circuit Breakers** | PARTIALLY BROKEN — `AdaptiveResourceGovernor` exists but cost=0, profile blocks `BLOCKED` state | F-001, F-014 |
| **Provider Failover** | EXISTS — `OmniRouteProvider` with fallback chains | Not tested in this investigation |
| **Regression Verification** | MISSING — No comparison of pre/post workspace state | F-011 |
| **Repository Re-scanning** | MISSING — Agent gets single prompt, no iterative workspace analysis | F-002 |

---

## 6. Answer to the Primary Question

> "Why does ORAGAI stop, fail to continue, or fail to completely develop a real project despite having hundreds of passing system tests?"

### Answer:

ORAGAI fails because **the FSM orchestration layer is structurally disconnected from the actual agent execution layer**. Specifically:

1. **The agent has no persistent memory between turns** (F-012). Each agent invocation is a fresh ephemeral conversation that is destroyed after use. The FSM carries state, but the agent does not.

2. **The governance layer is advisory-only** (F-003, F-006). It detects problems but cannot intervene. It computes budget extensions but doesn't apply them. It recommends strategy changes but only via prompt text.

3. **Profile boundaries silently disable safety mechanisms** (F-001, F-010). The `audit-fix` profile disallows `BLOCKED`, making circuit breakers crash the FSM instead of gracefully degrading.

4. **Verification equates "tests pass" with "task complete"** (F-005). When no `TaskTruthGraph` is present (which is the common case), the system has no independent way to verify the agent actually did what was asked.

5. **The task description is too vague for the agent** (F-002). The compiled prompt gives the agent a high-level goal but no specific targets, leading to 40 turns of exploration with zero mutations.

6. **Checkpoint recovery is incomplete** (F-004). After a crash, the system restores the FSM state but not the execution context, making "recovery" equivalent to "confused restart".

The 538+ tests validate that each component works correctly in isolation. But the **integration seams** — where the FSM talks to the governance layer, where the governance layer talks to the agent, where the checkpoint system talks to the context — are all broken or incomplete. Unit tests cannot detect these integration failures because they mock the boundaries.

---

## Appendix A: Files Examined

| File | Path | Relevance |
|---|---|---|
| FSM Engine | [engine.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/engine.py) | Core orchestration loop |
| FSM States | [states.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/states.py) | State taxonomy |
| FSM Transitions | [transitions.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/transitions.py) | Transition rules |
| FSM Guards | [guards.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/guards.py) | Completion evaluation |
| FSM Profiles | [profiles.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/profiles.py) | Mode configurations |
| FSM Checkpoint | [checkpoint.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/checkpoint.py) | State persistence |
| FSM Context | [context.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/context.py) | Runtime context |
| FSM Events | [events.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/fsm/events.py) | Event definitions |
| OpenHands Bridge | [openhands_bridge.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/engine/openhands_bridge.py) | Agent execution |
| Dispatcher | [dispatcher.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/dispatcher.py) | Route selection |
| Migration Guard | [migration_guard.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/migration_guard.py) | Feature flags |
| Orchestrator | [orchestrator.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/orchestrator.py) | Top-level coordinator |
| Governance Models | [models.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/governance/models.py) | Decision types |
| Checkpoint Evaluator | [checkpoint_evaluator.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/governance/checkpoint_evaluator.py) | Turn evaluation |
| Iteration Governor | [iteration_governor.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/governance/iteration_governor.py) | Budget control |
| Budget Allocator | [budget_allocator.py](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/governance/budget_allocator.py) | Turn budgets |
| Persisted State | [.orchestrator_state.json](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/.orchestrator_state.json) | Runtime evidence |
| Migration Routing | [migration_routing.json](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/config/migration_routing.json) | Feature flags |

---

## Appendix B: Methodology Notes

This investigation was conducted through **static source code analysis** combined with **runtime state evidence**. A full end-to-end execution was not performed by this investigator because:

1. The system requires OpenHands SDK with a real LLM provider, which would consume real tokens and cost.
2. The available `.orchestrator_state.json` from the user's most recent run provides concrete execution evidence.
3. The code analysis reveals structural impossibilities (profile boundary violations, incomplete checkpoint deserialization) that don't require execution to confirm.

For findings classified as HIGH confidence, the evidence is either from the actual failed run or from code paths that are provably broken by construction (e.g., F-001 where `BLOCKED` is not in `allowed_states` but is targeted by wildcard rules).

For findings that would benefit from execution confirmation, the recommendation is to run a controlled test with full telemetry logging before proceeding to fixes.
