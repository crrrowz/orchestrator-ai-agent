---
name: architectural-decomposition
description: Senior Architect methodology. Decomposes high-level requirements into formal specifications, dependency trees, and incremental implementation phases.
triggers:
  - plan
  - architect
  - design
  - decompose
  - specification
---

# Architectural Decomposition Methodology

## 1. Goal
Transform an ambiguous, natural language user request into a clear, verifiable, step-by-step engineering plan.

## 2. Decomposition Steps
1. **Scope Definition**:
   - Explicit inputs, outputs, invariants, and constraints.
   - Non-goals (what is out of scope for this task).
2. **Component Architecture**:
   - Identify modules, classes, and public interfaces.
   - Detail data flow and dependency graph.
3. **Execution Steps**:
   - Step 1: Base data structures and domain exceptions.
   - Step 2: Core business logic / service layer.
   - Step 3: Tool / API / Storage integration.
   - Step 4: Comprehensive test suite matching the specifications.

## 3. Deliverable Format (`PLAN.md`)
The Architect outputs a structured specification containing:
- Module filepaths to be created or modified
- Exact function signatures and contracts
- Test strategy and test case outline
- Invariants that the Tester and Reviewer must enforce
