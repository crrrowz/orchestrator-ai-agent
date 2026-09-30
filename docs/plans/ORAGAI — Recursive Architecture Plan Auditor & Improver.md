# ORAGAI — Recursive Architecture Plan Auditor & Improver

## Mission

You are NOT creating the ORAGAI architecture plans from scratch.

The architecture plans already exist.

Your mission is to perform a **deep recursive architectural audit of the existing planning system**, discover what was overlooked, underestimated, incorrectly designed, overly coupled, duplicated, ambiguous, impossible to implement, or missing entirely, and then improve the plans.

Every time this prompt is executed, the planning system must become more complete, more internally consistent, more implementable, and more resilient.

This is an **iterative architecture improvement process**.

The current plans must NEVER be assumed to be correct merely because they already exist.

---

# CORE PRINCIPLE

Treat the existing plans as:

> A hypothesis about the future architecture — NOT the truth.

Your job is to attack that hypothesis.

Search aggressively for:

```text
Missing architecture
Missing responsibilities
Missing interfaces
Missing states
Missing failure modes
Missing dependencies
Missing data flows
Missing lifecycle rules
Missing security boundaries
Missing persistence
Missing recovery
Missing concurrency behavior
Missing observability
Missing testing strategy
Missing migration strategy
Hidden coupling
Circular dependencies
Duplicate responsibilities
Contradictory decisions
Impossible assumptions
Over-engineering
Under-engineering
```

Do NOT optimize for making the plans look complete.

Optimize for discovering what is actually missing.

---

# IMPORTANT CONSTRAINT

This is a PLANNING-ONLY operation.

DO NOT:

* modify application source code
* implement the proposed architecture
* refactor production code
* delete production files
* execute migration
* claim that planned architecture is implemented

You MAY modify the architecture planning documents.

---

# ITERATION MODEL

Every time this prompt runs, perform a new architectural improvement cycle.

Conceptually:

```text
Existing Plans
      ↓
Architecture Reconstruction
      ↓
Independent Criticism
      ↓
Gap Discovery
      ↓
Contradiction Detection
      ↓
Failure Analysis
      ↓
Completeness Analysis
      ↓
Implementation Feasibility Analysis
      ↓
Plan Improvement
      ↓
Cross-Plan Consistency Check
      ↓
Final Architecture Re-Audit
      ↓
Improved Plans
```

Do NOT simply append another section to the existing plans.

Improve the actual plans.

---

# PHASE 0 — PLAN INVENTORY

First discover all existing planning files.

Do not assume the previous expected structure still exists.

Inspect:

```text
plans/
```

and all nested directories.

Build an inventory:

```text
plan
purpose
status
dependencies
covered architecture
missing architecture
last known quality issues
```

Identify:

```text
duplicate plans
obsolete plans
conflicting plans
orphan plans
plans with no dependencies
plans referenced but missing
plans that reference nonexistent components
```

---

# PHASE 1 — RECONSTRUCT THE REAL CURRENT SYSTEM

Do NOT rely only on the plans.

Inspect the actual ORAGAI source code.

The source code is the ground truth for the CURRENT architecture.

Compare:

```text
CURRENT CODE
vs
CURRENT PLANS
```

Find:

```text
Plan says X
Code actually does Y
```

These discrepancies must be recorded.

Create/update:

```text
plans/00-current-architecture.md
```

with factual architecture derived from the repository.

---

# PHASE 2 — RECONSTRUCT THE TARGET ARCHITECTURE

Read ALL existing target architecture plans together.

Do not inspect them independently only.

Build a mental/system-level model:

```text
Core
 ↓
Components
 ↓
Graph
 ↓
Engines
 ↓
Agents
 ↓
Tools
 ↓
Skills
 ↓
Memory
 ↓
Execution
 ↓
Governance
 ↓
Verification
 ↓
Events
 ↓
Plugins
 ↓
UI
```

Then ask:

> Does this architecture actually form one coherent system?

Look specifically for:

```text
circular dependencies
ownership ambiguity
shared mutable state
cross-layer leakage
god objects
god engines
hidden global state
duplicate orchestration
conflicting lifecycle ownership
```

---

# PHASE 3 — ADVERSARIAL ARCHITECTURE REVIEW

Attack the architecture as if you were trying to break it.

Ask:

### What happens if:

```text
Agent crashes?
Tool crashes?
Model unavailable?
Network disappears?
Provider times out?
Model returns malformed output?
Tool returns malformed output?
Agent loops?
Agent repeats actions?
Agent becomes confused?
Agent runs out of iterations?
Agent runs out of tokens?
Task becomes larger than expected?
Task becomes smaller than expected?
Task is impossible?
Task has conflicting requirements?
Two agents modify the same file?
Two tasks run simultaneously?
A process crashes?
ORAGAI restarts?
Machine restarts?
Database becomes unavailable?
Checkpoint becomes corrupted?
Plugin is incompatible?
Skill dependency is missing?
Graph contains a cycle?
Graph node hangs?
Graph execution partially succeeds?
Verification disagrees with agent?
Governor makes a wrong decision?
LLM Governor hallucinates?
Memory contains stale information?
Context becomes too large?
A previous execution left dirty state?
Migration is interrupted?
User changes configuration during execution?
```

For every relevant failure:

```text
Who detects it?
Who owns the state?
Who decides what happens?
Where is the decision recorded?
How does execution recover?
How is duplicate work prevented?
How is the task eventually completed or failed?
```

If the plans do not answer these questions, they are incomplete.

---

# PHASE 4 — THE "WHAT DID WE FORGET?" AUDIT

Search systematically for entire architectural domains that are missing.

Audit at minimum:

## Runtime

```text
process lifecycle
startup
shutdown
restart
crash recovery
graceful cancellation
timeouts
resource limits
```

## Concurrency

```text
parallel agents
parallel tools
race conditions
locking
resource contention
task isolation
file conflicts
state conflicts
```

## Persistence

```text
project state
task state
execution state
checkpoint state
agent state
graph state
configuration
history
recovery
migration
```

## Security

```text
tool permissions
filesystem boundaries
command execution
secrets
API keys
plugin trust
skill trust
sandboxing
agent isolation
network permissions
```

## Observability

```text
logs
metrics
traces
events
execution timeline
cost tracking
token tracking
failure tracking
decision history
audit trail
```

## Configuration

```text
defaults
overrides
environment variables
project configuration
agent configuration
workflow configuration
runtime configuration
versioning
validation
```

## Versioning

```text
components
plugins
skills
models
workflow schemas
configuration schemas
state migrations
```

## Extensibility

```text
plugin discovery
registration
loading
validation
compatibility
dependency resolution
uninstallation
upgrade
rollback
```

## Networking

```text
provider failure
timeouts
retries
rate limits
streaming
connection pooling
offline behavior
```

## Data contracts

```text
schemas
serialization
validation
version compatibility
backward compatibility
error contracts
event contracts
```

## Developer Experience

```text
CLI
configuration
debugging
local development
testing
plugin development
skill development
workflow authoring
```

## UI

```text
state synchronization
live execution
error display
editing
validation
undo/redo
persistence
workflow versioning
```

## Testing

```text
unit
integration
contract
end-to-end
failure injection
property testing
concurrency
recovery
migration
plugin compatibility
```

## Deployment

```text
local
Docker
server
distributed execution
configuration
secrets
storage
upgrades
rollback
```

If any domain is relevant but absent, create or improve a plan for it.

---

# PHASE 5 — COMPONENT CONTRACT AUDIT

For EVERY major component determine:

```text
Identity
Lifecycle
Inputs
Outputs
Configuration
State
Persistence
Dependencies
Capabilities
Permissions
Errors
Timeouts
Events
Telemetry
Versioning
Testing
Extension
```

Do not accept:

```text
"Component handles execution."
```

as sufficient.

Define exactly:

```text
What does it own?
What does it NOT own?
Who calls it?
What does it call?
What state may it mutate?
What state must remain external?
```

This is essential to prevent future architectural coupling.

---

# PHASE 6 — ENGINE BOUNDARY AUDIT

For every Engine ask:

```text
Why does this engine exist?
What responsibility does it own?
What responsibility does it explicitly NOT own?
What depends on it?
What does it depend on?
Can it be independently tested?
Can it be replaced?
Can it run without the UI?
Can it run without a specific LLM?
Can it run without another engine?
```

If two engines own overlapping responsibilities:

```text
MERGE
or
REDRAW BOUNDARY
```

If an engine exists only because the plan expects it to exist:

```text
REMOVE IT
```

Do not create architecture for architecture's sake.

---

# PHASE 7 — GRAPH EXECUTION AUDIT

Treat the workflow graph as a real execution system.

Verify that plans define:

```text
node lifecycle
edge semantics
input validation
output validation
conditional execution
branching
loops
cycles
parallelism
join semantics
failure propagation
retry
timeout
cancellation
checkpointing
resume
partial execution
dynamic graph modification
versioning
```

Ask:

> Can this graph actually execute a large autonomous software project without hidden orchestration logic outside the graph?

If not, identify what is missing.

---

# PHASE 8 — AGENT LIFECYCLE AUDIT

Define the complete lifecycle:

```text
CREATED
↓
CONFIGURED
↓
READY
↓
STARTED
↓
EXECUTING
↓
WAITING
↓
PAUSED
↓
REPLANNING
↓
RETRYING
↓
COMPLETED
↓
FAILED
↓
CANCELLED
```

Adjust according to the actual architecture.

For each transition define:

```text
trigger
owner
preconditions
state mutation
events
recovery
```

Pay particular attention to:

```text
iteration exhaustion
agent yield
natural completion
tool failure
model failure
context overflow
stagnation
```

---

# PHASE 9 — GOVERNANCE AUDIT

Critically inspect the Adaptive Governance design.

Do NOT assume:

```text
Governor = LLM
```

is sufficient.

Determine how governance handles:

```text
iterations
tokens
time
cost
progress
stagnation
chaos
retries
budget extension
task decomposition
strategy changes
resource exhaustion
```

Define which decisions are:

```text
DETERMINISTIC
vs
HEURISTIC
vs
LLM-ASSISTED
```

Any LLM decision must have:

```text
evidence
structured output
validation
confidence
fallback
```

---

# PHASE 10 — VERIFICATION AUDIT

Attack the completion system.

Ask:

> What prevents ORAGAI from falsely declaring a project complete?

Test conceptual scenarios:

```text
Agent says done but code incomplete
Tests pass but requirement missing
No code changed
Wrong files changed
Tests were not executed
Tests are unrelated
Partial implementation
Broken integration
Missing documentation
Hidden regression
Agent stops at iteration limit
Agent crashes after making changes
Agent produces an invalid report
```

Define evidence requirements.

Completion must be based on task-specific evidence.

---

# PHASE 11 — DATA FLOW AUDIT

Trace important data across the entire system:

```text
Task
↓
Planner
↓
Graph
↓
Agent
↓
Context
↓
Model
↓
Tool
↓
Result
↓
Progress
↓
Governance
↓
Verification
↓
Final State
```

For every transition identify:

```text
data structure
schema
owner
serialization
validation
persistence
events
```

Look for:

```text
implicit data
global state
hidden context
duplicated state
state reconstruction
```

---

# PHASE 12 — STATE OWNERSHIP AUDIT

For every important state variable determine exactly one owner.

Examples:

```text
task state
agent state
execution state
budget state
graph state
verification state
project state
```

If two systems can independently modify the same authoritative state:

```text
ARCHITECTURAL RISK
```

Redesign ownership.

---

# PHASE 13 — LEGACY / MIGRATION AUDIT

Inspect every legacy and migration mechanism in the current repository.

Determine:

```text
Why does it exist?
Who still uses it?
Can it coexist with the target architecture?
When can it be removed?
What prevents removal?
```

The target architecture must not accidentally preserve obsolete architecture forever.

---

# PHASE 14 — PLAN CONSISTENCY CHECK

Read ALL plans together.

Search for contradictions such as:

```text
Engine A owns X
Engine B also owns X

Component API says input A
Another plan expects input B

Graph supports feature X
Execution Engine cannot execute X

Plugin system expects dynamic loading
Core assumes static registration

Governor can replan
Task Engine cannot mutate tasks

Verification requires evidence
Execution never stores evidence
```

Create:

```text
plans/architecture-consistency-report.md
```

Fix contradictions directly in the relevant plans.

---

# PHASE 15 — IMPLEMENTATION FEASIBILITY

Pretend you are the AI agent that must implement these plans.

Try to answer:

```text
Where do I start?

What file do I modify first?

What interface do I implement?

What depends on it?

How do I test it?

How do I migrate existing behavior?

How do I know the task is finished?
```

If you cannot answer these questions from the plans:

> The plans are NOT implementation-ready.

Improve them.

---

# PHASE 16 — PLAN GRANULARITY AUDIT

Find plans that are too large.

For example:

```text
"Implement Execution Engine"
```

may need to become:

```text
Execution contracts
Execution context
Execution lifecycle
Tool dispatch
Agent loop
Checkpointing
Recovery
Telemetry
Testing
Integration
```

Split large plans when necessary.

Also find plans that are unnecessarily fragmented.

Merge them when fragmentation creates overhead without architectural value.

---

# PHASE 17 — PLAN DEPENDENCY VALIDATION

Build the actual dependency graph.

Detect:

```text
missing dependency
circular dependency
implicit dependency
incorrect execution order
parallelizable work
blocked work
```

Update:

```text
plans/00-plan-index.md
```

---

# PHASE 18 — RED TEAM REVIEW

Act as five different experts independently:

### Architect

Look for structural problems.

### Distributed Systems Engineer

Look for:

```text
concurrency
recovery
state
race conditions
partial failure
```

### AI Agent Engineer

Look for:

```text
agent loops
context
tool usage
planning
reasoning failures
```

### Security Engineer

Look for:

```text
permissions
sandboxing
secrets
untrusted plugins
command execution
```

### Reliability Engineer

Look for:

```text
stagnation
timeouts
crashes
recovery
observability
false success
```

Each perspective must produce findings.

Then reconcile them.

---

# PHASE 19 — COMPLETENESS MATRIX

Create:

```text
plans/completeness-matrix.md
```

Track:

| Domain       | Planned | Detailed | Testable | Implementable | Missing |
| ------------ | ------- | -------- | -------- | ------------- | ------- |
| Core         |         |          |          |               |         |
| Graph        |         |          |          |               |         |
| Agents       |         |          |          |               |         |
| Models       |         |          |          |               |         |
| Tools        |         |          |          |               |         |
| Skills       |         |          |          |               |         |
| Memory       |         |          |          |               |         |
| Tasks        |         |          |          |               |         |
| Execution    |         |          |          |               |         |
| Governance   |         |          |          |               |         |
| Verification |         |          |          |               |         |
| Events       |         |          |          |               |         |
| Plugins      |         |          |          |               |         |
| UI           |         |          |          |               |         |
| Security     |         |          |          |               |         |
| Persistence  |         |          |          |               |         |
| Concurrency  |         |          |          |               |         |
| Recovery     |         |          |          |               |         |
| Testing      |         |          |          |               |         |
| Deployment   |         |          |          |               |         |

Do NOT mark something complete merely because a file exists.

A domain is complete only when the architecture explains:

```text
responsibility
interfaces
state
failure
testing
integration
```

---

# PHASE 20 — IMPROVE THE PLANS

Now modify the planning documents.

For every discovered issue:

```text
FIX
SPLIT
MERGE
EXPAND
REMOVE
REORDER
```

Do not merely create a report saying something is wrong.

If the correction belongs inside an existing plan, update that plan.

If it requires a new plan, create it.

---

# PHASE 21 — SECOND-PASS SELF-AUDIT

After improving the plans:

STOP.

Pretend the improved plans were written by another AI.

Run the entire audit again mentally.

Ask:

```text
What could still be missing?
What did the previous audit assume?
What new contradictions did our changes introduce?
Did we create unnecessary complexity?
Did we duplicate responsibilities?
Did we accidentally preserve legacy coupling?
```

Perform another gap analysis.

Fix newly discovered issues.

---

# PHASE 22 — DIMINISHING RETURNS CHECK

Do NOT endlessly invent architecture.

Determine whether another iteration would likely discover meaningful architectural improvements.

Classify:

```text
MAJOR GAPS REMAIN
MODERATE GAPS REMAIN
MINOR GAPS REMAIN
ARCHITECTURE STABLE
```

If stable, do not create artificial work.

---

# FINAL REQUIRED OUTPUT

At the end produce:

## 1. Improvement Summary

```text
Previous plan quality:
New plan quality:

Major improvements:
...
```

Do NOT use arbitrary scores unless backed by explicit criteria.

---

## 2. Newly Discovered Problems

For every issue:

```text
Problem
Why previous plans missed it
Architectural impact
Correction
Affected plans
```

---

## 3. Plans Modified

```text
file
change
reason
```

---

## 4. Plans Created

```text
file
purpose
dependency
```

---

## 5. Plans Removed/Merged

Explain why.

---

## 6. Remaining Risks

List architectural uncertainties that still require investigation.

---

## 7. Completeness Matrix

Update:

```text
plans/completeness-matrix.md
```

---

## 8. Final Dependency Graph

Update:

```text
plans/00-plan-index.md
```

---

# MOST IMPORTANT RULE

Never assume that:

> "The previous AI already handled this."

Instead ask:

> "What would an expert discover that the previous AI probably forgot?"

Then investigate it.

---

# ANTI-SUPERFICIALITY RULE

You are NOT allowed to improve the plans by simply:

```text
adding more text
adding more bullet points
adding more filenames
adding more generic requirements
```

An improvement is valid only if it produces at least one of:

```text
new architectural discovery
removed ambiguity
resolved contradiction
defined missing interface
defined missing state
defined missing failure mode
defined missing lifecycle
defined missing dependency
defined missing recovery
defined missing security boundary
defined missing persistence
defined missing testing strategy
simplified unnecessary architecture
improved implementation order
improved migration safety
```

---

# FINAL PRINCIPLE

The goal is not to produce the longest architecture plan.

The goal is to produce the architecture plan that leaves the **fewest hidden assumptions for the implementation agent to discover later**.

Every execution of this prompt must therefore attempt to find the things that previous planning iterations failed to see.

This process is recursive:

```text
Plans
  ↓
Attack Plans
  ↓
Find Blind Spots
  ↓
Improve Plans
  ↓
Attack Again
  ↓
Find New Blind Spots
  ↓
Improve Again
  ↓
...
  ↓
Architecture Stabilizes
```

Do not implement the architecture.

Improve the plans.
