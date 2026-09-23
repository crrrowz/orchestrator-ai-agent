---
name: systematic-debugging
description: Systematic root cause analysis protocol. Fixes test failures and runtime errors methodically without introducing regressions or guess-and-check patches.
triggers:
  - fix
  - debug
  - error
  - failure
  - traceback
---

# Systematic Debugging Protocol

## 1. Triage Protocol
1. **Read the Full Traceback**: Identify the exact line number, exception type, and variable values at the point of failure.
2. **Reproduce Minimally**: Run the single failing test in isolation before making any edits.
3. **Hypothesis Formulation**: Formulate a concrete hypothesis explaining *why* the failure occurred. Never change code randomly hoping it passes.

## 2. Surgical Repair
- Address the root cause in the source code or test fixture, not just a superficial symptom.
- Check surrounding edge cases: if an `IndexError` occurred on empty list, check if other callers pass empty collections.
- Ensure all other existing tests still pass.

## 3. Regression Prevention
- If the bug was not caught by an existing test, add a regression test that specifically reproduces the failure before declaring victory.
