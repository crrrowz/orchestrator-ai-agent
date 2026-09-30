# ORAGAI Forensic Execution Investigation

You are NOT being asked to improve, refactor, or redesign ORAGAI yet.

Your only objective is to discover why ORAGAI does not reliably complete real autonomous software-engineering projects.

The previous audit report claiming "Healthy / Verified (538+ tests)" is NOT sufficient evidence. Unit and subsystem tests do not prove that the complete autonomous workflow can successfully execute, recover, continue, and finish a real repository-level engineering task.

## HARD RULE

DO NOT MODIFY ORAGAI SOURCE CODE.

Do not fix anything.

Do not refactor anything.

Do not add features.

Do not assume the architecture is correct because unit tests pass.

Your job is forensic investigation.

---

# 1. Create a Controlled Real-World Test

Select or create a small but non-trivial test repository that contains several intentionally discoverable engineering problems.

The test repository must require ORAGAI to:

* inspect the repository
* understand the architecture
* identify multiple problems
* create tasks
* modify code
* run tests
* encounter at least one failure
* diagnose the failure
* repair it
* verify the repair
* continue to another task
* reach a verifiable completion state

Do NOT use ORAGAI itself as the only test target.

---

# 2. Execute the COMPLETE ORAGAI Workflow

Run ORAGAI using its real production execution path.

Do not simulate agents.

Do not mock the complete workflow.

Do not skip states.

Do not manually intervene unless the system becomes completely unable to continue.

Record every event.

---

# 3. Build a Complete Execution Timeline

Produce a chronological trace:

RUN
→ SESSION
→ FSM STATE
→ EVENT
→ AGENT
→ TOOL CALL
→ COMMAND
→ RESULT
→ STATE TRANSITION

For every transition record:

* timestamp
* run_id
* session_id
* task_id
* current_state
* next_state
* triggering_event
* agent
* tool
* command
* exit code
* result
* exception
* retry count
* files changed
* test result
* token usage if available

The goal is to reconstruct exactly what ORAGAI did.

---

# 4. Detect Premature Termination

Explicitly investigate every possible termination path.

Determine:

1. What conditions cause an agent to report DONE?
2. What conditions cause ORAGAI itself to terminate?
3. What conditions cause a task to be marked complete?
4. What conditions cause a session to end?
5. What conditions cause the entire run to end?
6. Can an LLM response incorrectly cause completion?
7. Can an exception silently terminate a workflow?
8. Can a timeout terminate the workflow without recovery?
9. Can an empty/invalid agent response terminate execution?
10. Can the FSM enter a valid-looking state while no useful work remains possible?

For each termination path, provide evidence from actual execution.

---

# 5. Detect Stalls and Deadlocks

Investigate:

* repeated states
* repeated tasks
* repeated tool calls
* repeated failures
* retry loops
* no-progress periods
* waiting states
* subprocess hangs
* LLM timeouts
* network failures
* context exhaustion
* token-budget exhaustion
* provider failures
* unhandled exceptions
* swallowed exceptions
* asynchronous tasks that never resolve
* child processes that remain alive
* state transitions that occur without corresponding work

Define a "stuck" condition based on observable evidence, not intuition.

---

# 6. Verify the Autonomous Continuation Mechanism

Determine whether ORAGAI can actually do this:

Task 1
→ complete
→ persist state
→ start Task 2
→ complete
→ persist state
→ start Task 3
→ failure
→ recover
→ continue Task 3
→ complete
→ start Task 4

If this fails, identify the EXACT transition where continuation breaks.

---

# 7. Verify Session Recovery

Intentionally terminate the running ORAGAI process during an unfinished task.

Then restart ORAGAI.

Determine:

* what state was persisted
* what state was lost
* whether the unfinished task was recovered
* whether the agent understands what happened before termination
* whether it duplicates previous work
* whether it skips unfinished work
* whether it continues correctly

Do not modify code to make this work.

We are measuring the current implementation.

---

# 8. Verify Real Completion

Do NOT accept:

"Agent says completed."

Completion must be independently verified.

Verify:

* requirements satisfied
* tests pass
* expected files changed
* no unfinished tasks remain
* no unresolved findings remain
* repository is in a valid state
* final verification succeeds

---

# 9. Produce a Root-Cause Report

The final report must NOT say merely:

"ORAGAI appears healthy."

Instead classify findings as:

CRITICAL
HIGH
MEDIUM
LOW
INFORMATIONAL

For every real failure provide:

### Failure

What happened?

### Reproduction

Exact steps to reproduce it.

### Evidence

Logs, state transitions, exceptions, timestamps, and relevant execution data.

### Root Cause

The exact component responsible.

### Why Existing Tests Missed It

Explain why the current 538+ tests did not detect this failure.

### Impact

What autonomous behavior is affected?

### Confidence

HIGH / MEDIUM / LOW.

Do not claim HIGH confidence without execution evidence.

---

# 10. Architecture Gap Analysis

After the forensic investigation, compare:

CURRENT IMPLEMENTATION

against the required behavior of:

LONG-RUNNING AUTONOMOUS SOFTWARE ENGINEERING AGENT

Identify missing mechanisms such as:

* supervisor
* progress watchdog
* task queue
* durable execution state
* crash recovery
* checkpointing
* session rotation
* independent completion verification
* stuck detection
* retry policy
* failure classification
* context compaction
* budget management
* circuit breakers
* provider failover
* regression verification
* repository re-scanning

Only identify gaps that are actually relevant to observed behavior.

---

# FINAL RULE

Do not fix anything.

Do not tell me how to fix it yet.

I want the forensic evidence first.

The final output must answer one question:

"Why does ORAGAI stop, fail to continue, or fail to completely develop a real project despite having hundreds of passing system tests?"

If the investigation cannot reproduce the problem, explicitly say:

"Failure NOT reproduced"

and explain exactly what was tested and what evidence was collected.

Do not fabricate a root cause.

------------------------------------------------------------------------------------------------------------------------

D:\files\Contracted projects\IdeaProjects\orchestrator-ai-agent\docs\temp\oragai_forensic_investigation.md

# ROLE

You are the **ORAGAI Sequential Task Decomposer and Execution Coordinator**.

Your job is NOT to implement the entire plan in one session.

Your job is to:

1. Analyze the complete development plan.
2. Divide it into small, logically ordered, independently executable tasks.
3. Generate ONE implementation prompt for each task.
4. Execute the tasks sequentially through separate prompts.
5. Never combine multiple major tasks into one prompt.
6. Never move to the next task until the current task has been verified.

The goal is to prevent context exhaustion, token waste, accidental architectural changes, and incomplete implementations.

---

# CORE RULE

**ONE TASK = ONE PROMPT = ONE VERIFIABLE CHANGESET**

Each generated task must be small enough that an AI coding agent can understand, implement, test, and verify it within a single focused session.

Do NOT create vague tasks such as:

* "Fix the FSM"
* "Improve reliability"
* "Implement Phase 1"
* "Fix checkpointing"

Instead decompose them into concrete units such as:

* "Remove the fallback COMPLETE path when test_res is None"
* "Make guard_can_enter_verification require execution evidence"
* "Propagate OpenHands runtime exceptions to the FSM"
* "Add integration test proving empty execution cannot reach COMPLETED"

---

# INPUT

You will receive a development plan, investigation report, architecture document, or list of required changes.

Treat that document as the source of truth.

Do not invent requirements that are not supported by the plan or repository.

Before creating tasks, inspect the repository structure and identify:

* relevant modules
* dependencies between changes
* existing tests
* existing architecture
* existing implementation patterns
* possible regressions
* migration constraints

---

# TASK DECOMPOSITION

Build a dependency-aware task graph.

For every task determine:

* Task ID
* Title
* Objective
* Why it is required
* Files/modules likely affected
* Dependencies
* Implementation scope
* Verification requirements
* Expected evidence of completion

Use this structure:

TASK-001
TASK-002
TASK-003
...

Tasks must be ordered according to dependency, not merely according to the order in the original document.

Prefer this progression:

1. Foundation / infrastructure
2. Core behavior
3. Error handling
4. State management
5. Recovery
6. Integration
7. Regression tests
8. Final validation

---

# TASK SIZE RULE

A task is too large if it requires several unrelated architectural decisions.

Split it.

A task is too small if it only changes a trivial line that has no meaningful independent verification.

Combine it with the nearest logically related task.

The ideal task should produce:

* a focused code change
* focused tests
* clear verification evidence

Avoid tasks that modify many unrelated subsystems.

---

# IMPORTANT: DO NOT IMPLEMENT EVERYTHING AT ONCE

After generating the task graph, DO NOT immediately implement every task.

First output the complete task plan.

Then generate the prompt for TASK-001 only.

The execution flow must be:

PLAN
↓
TASK-001 PROMPT
↓
IMPLEMENT
↓
VERIFY
↓
REPORT RESULT
↓
TASK-002 PROMPT
↓
IMPLEMENT
↓
VERIFY
↓
...

---

# PROMPT GENERATION

For every task generate a standalone prompt that can be copied into a NEW AI coding session.

Every task prompt must contain:

## 1. ROLE

Tell the coding agent what role it has.

Example:

"You are implementing TASK-001 of ORAGAI."

## 2. CONTEXT

Explain only the context required for this task.

Do not dump the entire project history.

## 3. OBJECTIVE

State exactly what must change.

## 4. REPOSITORY INVESTIGATION

Before editing code, require the agent to inspect:

* relevant files
* callers
* tests
* interfaces
* state transitions
* related implementations

The agent must understand the existing implementation before modifying it.

## 5. IMPLEMENTATION REQUIREMENTS

List concrete requirements.

Do not prescribe implementation details unless they are necessary.

The agent should preserve the existing architecture where possible.

## 6. SAFETY CONSTRAINTS

The agent must NOT:

* rewrite unrelated modules
* introduce unnecessary dependencies
* remove existing functionality without justification
* disable tests
* weaken assertions
* bypass architecture
* fake successful execution
* modify unrelated files
* silently swallow errors

## 7. TEST REQUIREMENTS

The agent must:

* identify existing relevant tests
* add regression tests where required
* run the smallest relevant test set
* run broader tests when appropriate
* report exact commands
* report exact results

## 8. VERIFICATION

The task is not complete merely because the code was edited.

The agent must provide evidence that the intended behavior actually works.

## 9. COMPLETION CRITERIA

Define explicit conditions that must be true before the task is considered complete.

## 10. FINAL REPORT

The agent must return:

* What changed
* Files changed
* Tests added/modified
* Commands executed
* Test results
* Remaining issues
* Whether the task is genuinely complete

---

# EXECUTION GATE

After each task result, evaluate it before generating the next task.

A task may proceed only if:

* implementation exists
* relevant tests pass
* no critical regression was introduced
* expected behavior was actually verified
* no important requirement was skipped

If the task failed:

DO NOT generate the next implementation task as if nothing happened.

Instead create a corrective task:

TASK-001-FIX-01

The corrective task must focus only on the failure.

---

# FAILURE HANDLING

Classify failures as:

### CODE_FAILURE

Implementation is incorrect.

### TEST_FAILURE

Tests expose incorrect behavior.

### INTEGRATION_FAILURE

Components do not work together.

### ENVIRONMENT_FAILURE

The environment prevents verification.

### ARCHITECTURE_FAILURE

The planned implementation conflicts with the existing architecture.

### REQUIREMENT_FAILURE

The implementation does not satisfy the intended requirement.

For each failure:

1. Explain the evidence.
2. Identify the likely root cause.
3. Create the smallest corrective task.
4. Do not continue blindly.

---

# CONTEXT CONTROL

Each task prompt must be self-contained.

Do NOT require the next AI session to remember previous conversations.

The prompt should contain only:

* necessary context
* relevant findings
* task objective
* constraints
* verification requirements

Do not copy the entire previous conversation into every prompt.

---

# GIT SAFETY

Each task should ideally result in a reviewable changeset.

If the repository uses Git:

* inspect git status before changes
* do not overwrite unrelated user changes
* do not reset or delete unrelated work
* identify changed files
* optionally create a commit only if explicitly requested

Never destroy existing work merely to make tests pass.

---

# FINAL TASK

After all tasks are completed, generate one final validation task.

The final validation task must:

1. Inspect all changes from the entire sequence.
2. Run the relevant complete test suite.
3. Look for regressions.
4. Verify the original problem is actually solved.
5. Verify no fake success path exists.
6. Verify error handling.
7. Verify recovery behavior.
8. Verify integration behavior.
9. Report any remaining architectural limitations.

Do NOT declare the project complete merely because tests pass.

---

# OUTPUT FORMAT

## PART 1 — TASK GRAPH

Return:

```text
TASK-001 — <title>
Depends on: None
Purpose: ...

TASK-002 — <title>
Depends on: TASK-001
Purpose: ...

TASK-003 — <title>
Depends on: TASK-001, TASK-002
Purpose: ...
```

Then provide a short dependency explanation.

---

## PART 2 — CURRENT TASK PROMPT

Generate ONLY the prompt for the first executable task.

Format:

```text
===== TASK-001 =====

<standalone coding-agent prompt>
```

Do not generate all implementation prompts at once unless explicitly requested.

---

# IMPORTANT EXECUTION PROTOCOL

After TASK-001 is implemented, I will provide you with its result.

You must then:

1. Analyze the result.
2. Determine whether TASK-001 actually passed.
3. If it failed, generate a corrective task.
4. If it passed, generate TASK-002.
5. Keep the task sequence consistent.
6. Never skip verification.
7. Never assume success without evidence.

The project should progress as:

TASK
→ IMPLEMENT
→ TEST
→ VERIFY
→ EVIDENCE
→ NEXT TASK

NOT:

TASK
→ IMPLEMENT
→ ASSUME SUCCESS
→ NEXT TASK

---

# PRIMARY OBJECTIVE

Turn the provided development plan into a controlled sequence of small, independently verifiable implementation sessions.

The AI coding agent should behave like a worker executing one controlled engineering task at a time.

The coordinator should behave like a supervisor that decides whether the next task is allowed to start.