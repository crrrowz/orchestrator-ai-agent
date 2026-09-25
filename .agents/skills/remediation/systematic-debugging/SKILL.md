---
name: systematic-debugging
description: Systematic root cause analysis protocol. Fixes test failures and runtime errors methodically without introducing regressions or guess-and-check patches.
triggers:
  - fix
  - debug
  - error
  - failure
  - traceback
  - remedy
---

# Systematic Debugging Protocol (Remediation)

## 1. Triage & Root Cause Invariants
- Read the complete traceback: identify file, line number, exception type, and stack frame.
- Reproduce minimally with a single test execution before editing source files.
- Formulate an explicit hypothesis; never apply random or speculative edits.

## 2. Surgical Repair & Verification
- Fix the root cause in the affected subsystem.
- In remediation mode, ensure both code and tests align with target invariants.
- Verify adjacent edge cases (empty inputs, `None` values, boundary types).

## 3. Windows & PowerShell Rules
- Execute commands via native PowerShell syntax without bash pipes (`|`) or chaining (`&&`).
