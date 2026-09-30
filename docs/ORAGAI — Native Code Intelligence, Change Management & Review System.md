# ORAGAI — Native Code Intelligence, Change Management & Review System

## Capability Analysis + Architecture + Implementation Planning Prompt

## ROLE

You are a Principal Software Architect, Senior Code Intelligence Engineer, Git Internals Engineer, AI Agent Systems Architect, and Software Quality Engineer.

Your task is NOT to install, integrate, wrap, call, or depend on Graphite or CodeRabbit.

Your task is to analyze the existing ORAGAI codebase and design how ORAGAI itself can natively implement the most valuable capabilities represented by:

* Graphite
* CodeRabbit

You must treat these products only as **capability references and architectural inspiration**.

Do NOT copy proprietary implementation details.
Do NOT reproduce proprietary source code.
Do NOT make ORAGAI dependent on their APIs or services unless explicitly requested later.
Do NOT assume their internal implementation.
Instead, identify the underlying engineering capabilities and design an original implementation suitable for ORAGAI.

---

# PRIMARY OBJECTIVE

Analyze the COMPLETE ORAGAI repository first.

Then determine:

1. What capabilities ORAGAI already has.
2. What capabilities are partially implemented.
3. What capabilities are missing.
4. Which Graphite-like capabilities are technically appropriate for ORAGAI.
5. Which CodeRabbit-like capabilities are technically appropriate for ORAGAI.
6. Which capabilities should NOT be implemented and why.
7. Where each capability belongs inside the existing architecture.
8. What architectural changes are required.
9. What new modules, services, interfaces, models, state machines, storage, Git operations, analyzers, agents, and tests are required.
10. How to implement everything incrementally without destabilizing the existing system.

The result must be a **repository-specific engineering plan**, not a generic explanation.

---

# IMPORTANT CONSTRAINT

DO NOT MODIFY CODE.

This phase is analysis and planning only.

Do not create files.
Do not edit files.
Do not refactor files.
Do not implement features.

Your final output must be the implementation blueprint that another development phase can execute.

---

# PHASE 0 — REPOSITORY DISCOVERY

Before designing anything, inspect the repository deeply.

Understand:

* Project structure
* Python package structure
* Entry points
* CLI
* Configuration
* Agents
* Agent lifecycle
* FSM/state machine
* Context management
* Token management
* DynamicTokenGovernor
* Evidence Gates
* Graft integration
* Skills
* OpenHands integration
* Git handling
* Existing branch/commit/PR functionality
* Testing infrastructure
* Logging
* Error handling
* Persistence
* Data models
* Pydantic models
* Async/sync architecture
* External integrations
* Existing abstractions
* Existing extension points
* Existing TODOs
* Existing technical debt
* Existing architectural constraints

Search the entire repository.

Do not rely only on README files.

Trace important execution paths through the actual source code.

---

# PHASE 1 — CREATE AN ARCHITECTURAL MAP

Produce an accurate map of the current ORAGAI architecture.

Include:

```text
CLI
 ↓
Orchestrator
 ↓
FSM
 ↓
Agents
 ↓
Context / Evidence
 ↓
Developer
 ↓
Tester
 ↓
Reviewer
 ↓
Auditor
 ↓
Git
```

But do NOT assume this structure is correct.

Replace it with the actual architecture discovered from the repository.

For every major component identify:

* File
* Class/function
* Responsibility
* Inputs
* Outputs
* Dependencies
* State
* Side effects
* Extension points
* Problems
* Architectural risks

---

# PHASE 2 — CURRENT CAPABILITY INVENTORY

Create a capability matrix.

Use:

| Capability | Current State | Evidence | Location | Quality | Missing Pieces |
| ---------- | ------------- | -------- | -------- | ------- | -------------- |

Classify each capability as:

* NOT_IMPLEMENTED
* PARTIAL
* IMPLEMENTED
* STRONG
* UNKNOWN

Do not claim a capability exists unless the source code proves it.

---

# PHASE 3 — EXTRACT GRAPHITE-LIKE CAPABILITIES

Do not analyze Graphite as a product to integrate.

Decompose its useful engineering concepts into independent capabilities.

Analyze at minimum:

## Change Management

* Atomic changes
* Stacked changes
* Stacked branches
* Branch dependency graph
* Change ordering
* Change relationships
* Stack visualization model
* Stack synchronization
* Restacking
* Rebase orchestration
* Dependency-aware branch updates
* PR decomposition
* Small reviewable changes
* Change lineage
* Change ancestry
* Change state

## Git Intelligence

* Branch graph
* Commit graph
* Parent/child relationships
* Branch dependency detection
* Changed-file analysis
* Commit relationships
* Rebase planning
* Conflict detection
* Conflict classification
* Conflict resolution workflow
* Safe synchronization

## Review Workflow

* PR lifecycle
* Review states
* Reviewer states
* CI states
* Dependency-aware review
* Merge readiness
* Merge ordering
* Merge queue concepts

## Merge System

* Dependency-aware merge
* Queue management
* CI verification
* Merge preconditions
* Main branch protection
* Automatic rebase
* Conflict detection
* Merge validation
* Safe merge execution

## Workflow Analytics

* Review duration
* PR lifecycle
* Bottlenecks
* Failure rates
* Rework
* Review quality
* Agent productivity

For every capability determine:

1. Is it useful for ORAGAI?
2. Why?
3. Where should it live?
4. What ORAGAI components would use it?
5. What new abstractions are required?
6. What Git operations are required?
7. What state must be persisted?

---

# PHASE 4 — EXTRACT CODERABBIT-LIKE CAPABILITIES

Decompose CodeRabbit into engineering capabilities rather than product features.

Analyze at minimum:

## Repository Intelligence

* Repository understanding
* Codebase indexing
* Symbol discovery
* Symbol relationships
* File relationships
* Dependency graph
* Call graph
* Import graph
* Cross-file reasoning
* Context retrieval
* Impact analysis
* Change impact analysis

## Diff Intelligence

* Diff parsing
* File-level analysis
* Hunk-level analysis
* Changed-symbol detection
* Changed-function detection
* Change classification
* Change grouping
* Logical change detection

## Semantic Review

* Bug detection
* Logic analysis
* Edge-case detection
* Error handling analysis
* Concurrency analysis
* State-management analysis
* API contract analysis
* Performance analysis
* Maintainability analysis
* Code smell detection
* Refactoring suggestions

## Security Review

* Security-sensitive code detection
* Input validation
* Authentication paths
* Authorization paths
* Trust boundaries
* Sensitive sinks
* Data-flow analysis
* Secret detection
* Dependency risk
* Supply-chain risk
* Reachability analysis
* Security severity
* Confidence scoring

## Change Understanding

Design native equivalents of concepts such as:

* PR summary
* Walkthrough
* Change cohorts
* Logical change grouping
* Layered change representation
* Dependency-aware change ordering
* Sequence reasoning
* State-machine reasoning
* Architecture impact

Do not assume ORAGAI needs visual diagrams for every change.

Determine when a diagram would provide real value.

---

# PHASE 5 — CODE INTELLIGENCE ARCHITECTURE

Determine whether ORAGAI needs a persistent internal code intelligence layer.

Evaluate:

```text
Repository
    ↓
Parser
    ↓
AST
    ↓
Symbols
    ↓
Relationships
    ↓
Dependency Graph
    ↓
Semantic Index
    ↓
Impact Analysis
    ↓
Agent Context
```

Determine:

* What can be implemented with existing libraries?
* What should use language-native ASTs?
* What requires Tree-sitter or equivalent?
* What can be extracted statically?
* What requires AI reasoning?
* What should be cached?
* What should be recomputed?
* What should be persisted?

Design this specifically for ORAGAI.

---

# PHASE 6 — CHANGE GRAPH

Design a native ORAGAI Change Graph.

Determine the required entities.

For example:

```text
Repository
Branch
Commit
Change
File
Symbol
PR
Stack
Dependency
Review
Finding
Test
CI Run
```

Determine relationships such as:

```text
Branch -> contains -> Commit
Commit -> modifies -> File
File -> contains -> Symbol
Symbol -> calls -> Symbol
Change -> depends_on -> Change
PR -> contains -> Change
Review -> analyzes -> Change
Finding -> belongs_to -> Review
Test -> validates -> Change
```

Do not blindly use this model.

Modify it based on the actual ORAGAI architecture.

---

# PHASE 7 — REVIEW ENGINE

Design a native ORAGAI Review Engine.

It must distinguish:

```text
Static Analysis
AI Analysis
Test Evidence
Security Analysis
Architecture Analysis
Human/Agent Review
```

Determine how findings should be represented.

Design a Finding model containing only fields justified by the architecture.

Potential concepts:

* ID
* severity
* confidence
* category
* location
* symbol
* evidence
* explanation
* impact
* recommendation
* fixability
* source
* status
* related findings

Again, verify the correct design against ORAGAI.

---

# PHASE 8 — REVIEW PIPELINE

Design the lifecycle:

```text
Change Created
      ↓
Change Discovery
      ↓
Diff Analysis
      ↓
Repository Context
      ↓
Impact Analysis
      ↓
Static Analysis
      ↓
AI Review
      ↓
Security Review
      ↓
Test Evidence
      ↓
Architecture Review
      ↓
Finding Deduplication
      ↓
Finding Prioritization
      ↓
Review Result
      ↓
Fix / Reject / Approve
```

Determine where this fits into the existing ORAGAI FSM.

Do NOT create a second competing orchestration system if the existing FSM can support this.

Prefer extending existing abstractions over duplicating them.

---

# PHASE 9 — AGENT RESPONSIBILITY ANALYSIS

Analyze the existing agents:

* Project Manager
* Architect
* Developer
* Tester
* Reviewer
* Auditor

Determine which capabilities belong to which agent.

Pay particular attention to avoiding duplicated reasoning.

For example:

```text
Developer
    → implementation

Tester
    → behavioral evidence

Review Engine
    → technical findings

Reviewer
    → requirement + architecture judgment

Auditor
    → independent verification
```

Determine the correct boundaries from the actual repository.

---

# PHASE 10 — TOKEN ECONOMICS

This is critical.

ORAGAI already contains token-management concepts.

Design the system to minimize AI token usage.

Determine what can be performed without an LLM:

* Git graph analysis
* AST parsing
* symbol extraction
* dependency analysis
* diff parsing
* changed-file detection
* impact calculation
* test result parsing
* CI state
* conflict detection
* finding deduplication

Determine what actually requires AI.

Design:

```text
Cheap deterministic analysis
        ↓
Evidence extraction
        ↓
Targeted AI reasoning
        ↓
Final judgment
```

Do NOT send the entire repository to an LLM.

Identify:

* Context boundaries
* Retrieval strategy
* Evidence-first review
* Cache opportunities
* Incremental analysis
* Token budgets
* Dynamic escalation
* Model routing
* Review depth levels

Integrate with the existing DynamicTokenGovernor rather than creating another token system.

---

# PHASE 11 — GRAFT INTEGRATION

Analyze the current Graft usage.

Determine whether Graft should provide:

* Initial repository mapping
* Structural intelligence
* TODO discovery
* Code search
* Context extraction

Determine what ORAGAI should own natively.

Avoid duplicating Graft capabilities unnecessarily.

Define a clean boundary:

```text
Graft
    ↓
Codebase discovery / retrieval

ORAGAI
    ↓
Reasoning / orchestration / validation / lifecycle
```

Only use this boundary if the repository analysis confirms it is appropriate.

---

# PHASE 12 — EVIDENCE SYSTEM

ORAGAI's Evidence Gates are a major architectural asset.

Extend them where appropriate.

For every AI finding determine:

```text
Claim
 ↓
Evidence
 ↓
Verification
 ↓
Confidence
 ↓
Decision
```

A review finding should preferably be backed by:

* Code location
* Relevant symbol
* Relevant dependency
* Test result
* Static-analysis result
* Runtime evidence
* Git diff
* Architecture constraint

Determine which evidence types are actually available.

---

# PHASE 13 — AUTOFIX ARCHITECTURE

Analyze whether ORAGAI should support:

```text
Finding
 ↓
Fix Plan
 ↓
Developer Agent
 ↓
Patch
 ↓
Tests
 ↓
Re-review
```

Do not allow an AI reviewer to silently modify production code.

Design explicit state transitions.

Determine:

* Who can request a fix?
* Who performs it?
* Who tests it?
* Who reviews the fix?
* When is a fix considered complete?
* How are fix loops prevented from becoming infinite?

Integrate with the existing FSM.

---

# PHASE 14 — FAILURE AND LOOP CONTROL

Design protections against:

* Infinite fix loops
* Repeated findings
* False positives
* Oscillating fixes
* Reviewer disagreement
* Agent disagreement
* CI loops
* Token exhaustion
* Git conflicts
* Broken rebases
* Partial state
* Stale repository intelligence

Use ORAGAI's existing safeguards where possible.

---

# PHASE 15 — ARCHITECTURAL FIT

For every proposed capability identify:

```text
Existing Component
        ↓
Extension Point
        ↓
Required Change
        ↓
New Component (if necessary)
```

Prefer:

```text
Extend > Refactor > Replace > Rewrite
```

Do not recommend rewriting existing components unless there is strong repository evidence that the current architecture makes the capability impossible or unsafe.

---

# PHASE 16 — FILE-LEVEL IMPLEMENTATION PLAN

Produce a concrete implementation map.

For every required change:

| Priority | File | Component | Change | Reason | Dependencies | Risk |
| -------- | ---- | --------- | ------ | ------ | ------------ | ---- |

If a new file is required:

```text
path/to/new_file.py
Purpose:
Responsibilities:
Interfaces:
Dependencies:
```

Do not invent filenames that conflict with the repository's existing conventions.

---

# PHASE 17 — DOMAIN MODEL

Design required models.

Potential categories:

```text
Change
Stack
Branch
Commit
Dependency
Review
Finding
Evidence
Impact
Symbol
Relationship
AnalysisResult
FixPlan
ReviewDecision
MergeCandidate
```

For each model define:

* Purpose
* Required fields
* Relationships
* Lifecycle
* Persistence requirements

Only include models actually required.

---

# PHASE 18 — FSM INTEGRATION

Map the new functionality onto ORAGAI's existing FSM.

Produce:

```text
CURRENT STATE
      ↓
NEW CAPABILITY
      ↓
TRANSITION
      ↓
NEXT STATE
```

Explicitly identify:

* New states
* Modified states
* New transitions
* Failure transitions
* Retry transitions
* Approval transitions
* Escalation transitions

Avoid creating an independent FSM.

---

# PHASE 19 — TEST STRATEGY

Design tests before implementation.

Include:

## Unit Tests

* Git graph
* Change graph
* Diff parser
* Symbol extraction
* Dependency analysis
* Finding model
* Review engine
* Evidence engine

## Integration Tests

* Git repository
* Branch stack
* Rebase
* Conflict
* Review pipeline
* Agent interaction
* FSM transitions

## End-to-End Tests

Example:

```text
Task
 ↓
Implementation
 ↓
Stack
 ↓
Tests
 ↓
Review
 ↓
Finding
 ↓
Fix
 ↓
Re-test
 ↓
Re-review
 ↓
Approval
 ↓
Merge
```

Design deterministic fixtures wherever possible.

---

# PHASE 20 — SECURITY AND SAFETY

Analyze risks introduced by giving ORAGAI control over:

* Git
* Branches
* Commits
* Rebases
* Merges
* Code modifications
* Secrets
* CI
* External commands

Define:

* Permissions
* Sandboxing
* Confirmation boundaries
* Rollback
* Recovery
* Audit logs
* Immutable evidence
* Safe defaults

---

# PHASE 21 — PERFORMANCE

Estimate architectural impact.

Analyze:

* Repository size
* Number of files
* Number of symbols
* Graph size
* Indexing cost
* Incremental update cost
* Memory
* Disk
* Git operations
* LLM calls
* Token consumption
* Review latency

Design incremental computation wherever possible.

---

# PHASE 22 — IMPLEMENTATION ROADMAP

Produce an ordered roadmap.

Use phases similar to:

```text
P0 — Baseline / Architecture Stabilization
P1 — Git Intelligence
P2 — Change Graph
P3 — Repository Intelligence
P4 — Diff Intelligence
P5 — Review Engine
P6 — Evidence Integration
P7 — Security Analysis
P8 — Stacked Change Workflow
P9 — Autofix Loop
P10 — Merge Safety
P11 — Analytics
P12 — Optimization
```

But change these phases according to the actual repository.

Each phase must contain:

* Objective
* Prerequisites
* Files
* Components
* Interfaces
* Tests
* Risks
* Rollback strategy
* Completion criteria

---

# PHASE 23 — PRIORITIZATION

Do NOT simply implement every feature.

Classify proposed capabilities:

### TIER A

Core capabilities that materially improve ORAGAI.

### TIER B

Useful capabilities that should follow the core architecture.

### TIER C

Optional capabilities.

### NOT RECOMMENDED

Capabilities that create unnecessary complexity or duplicate existing ORAGAI functionality.

Do not rank individual political choices or unrelated topics; this classification is strictly technical prioritization within the software architecture.

---

# PHASE 24 — FINAL ARCHITECTURE

Produce the proposed architecture after implementation.

Show:

```text
                    ORAGAI
                       │
              ┌────────┴────────┐
              │                 │
        Orchestration      Intelligence
              │                 │
          FSM / Agents     Code Intelligence
              │                 │
       ┌──────┼──────┐     ┌────┼─────┐
       │      │      │     │    │     │
    Planner Developer Tester AST Graph Diff
       │      │      │     │    │     │
       └──────┼──────┘     └────┼─────┘
              │                 │
              └────────┬────────┘
                       │
                 Review Engine
                       │
             ┌─────────┼─────────┐
             │         │         │
          Security   Evidence   AI Review
             │         │         │
             └─────────┼─────────┘
                       │
                  Fix Pipeline
                       │
                  Git Engine
                       │
               Merge / Delivery
```

Replace this conceptual diagram with the architecture that actually fits the repository.

---

# PHASE 25 — GAP ANALYSIS

Create a final matrix:

| Capability | Graphite Concept | CodeRabbit Concept | ORAGAI Current State | Required | Implementation Location |
| ---------- | ---------------- | ------------------ | -------------------- | -------- | ----------------------- |

This becomes the master feature map.

---

# PHASE 26 — DO NOT OVERENGINEER

You must actively challenge your own recommendations.

For every major subsystem ask:

1. Can ORAGAI already do this?
2. Can an existing component be extended?
3. Can deterministic code solve it?
4. Does this actually require AI?
5. Does this increase token consumption?
6. Does this introduce another state machine?
7. Does this duplicate Graft?
8. Does this duplicate existing ORAGAI agents?
9. Does this increase maintenance substantially?
10. Is the capability worth its complexity?

Reject unnecessary architecture.

---

# FINAL DELIVERABLE

Your final report must contain exactly these sections:

# 1. Executive Summary

# 2. Current ORAGAI Architecture

# 3. Current Capability Inventory

# 4. Graphite Capability Mapping

# 5. CodeRabbit Capability Mapping

# 6. Capability Gap Matrix

# 7. Proposed Native ORAGAI Architecture

# 8. Code Intelligence Architecture

# 9. Change Graph Architecture

# 10. Review Engine Architecture

# 11. Evidence Architecture

# 12. Git / Stack / Merge Architecture

# 13. Agent Responsibility Changes

# 14. FSM Changes

# 15. Token & Context Optimization

# 16. Graft Boundary

# 17. Domain Models

# 18. File-Level Change Plan

# 19. Test Strategy

# 20. Security Model

# 21. Performance Model

# 22. Implementation Roadmap

# 23. Capability Prioritization

# 24. Risks & Mitigations

# 25. Final Target Architecture

# 26. Definition of Done

---

# CRITICAL RULES

1. Analyze before recommending.
2. Read actual source code.
3. Do not guess.
4. Do not modify code.
5. Do not install Graphite.
6. Do not install CodeRabbit.
7. Do not create a wrapper around either product.
8. Do not make ORAGAI dependent on either product.
9. Treat them as capability references.
10. Prefer native ORAGAI implementations.
11. Reuse existing ORAGAI architecture.
12. Avoid duplicate systems.
13. Prefer deterministic analysis before AI analysis.
14. Minimize LLM tokens.
15. Use evidence before reasoning.
16. Integrate with the existing FSM.
17. Integrate with DynamicTokenGovernor.
18. Integrate with the existing Evidence Gates.
19. Preserve Graft where it provides useful deterministic/retrieval capabilities.
20. Do not rewrite working components without strong evidence.
21. Every architectural recommendation must reference actual repository evidence.
22. Every proposed module must have a concrete responsibility.
23. Every implementation phase must have tests.
24. Every automated modification must have verification.
25. Every fix loop must have termination conditions.
26. Do not start implementation during this phase.

---

# FINAL QUESTION TO ANSWER

After completing the repository analysis, answer this explicitly:

> "If we wanted ORAGAI to natively provide the most valuable engineering capabilities represented by Graphite + CodeRabbit, what is the smallest coherent architecture that can achieve this without turning ORAGAI into an unnecessarily complex system?"

The answer must be based on the actual ORAGAI repository, not generic assumptions.
