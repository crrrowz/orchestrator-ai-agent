---
name: code-review-standards
description: Independent code review rubric. Evaluates security, correctness, backward compatibility, performance, and adherence to clean architecture principles.
triggers:
  - review
  - critique
  - audit
  - inspect
---

# Code Review & Architectural Audit Rubric

## 1. Zero Tolerance Issues (Automatic REJECT)
- **Security Vulnerabilities**:
  - Command injection (`shell=True` with unvalidated user input)
  - Path traversal (`../` vulnerabilities in file access)
  - Hardcoded secrets, keys, or passwords
- **Logical Flaws**:
  - Unhandled exceptions in critical paths
  - Infinite loops or unconstrained recursion
  - Unsynchronized shared state across async tasks/threads
- **Dead/Stub Code**:
  - Functions containing only `pass` or `raise NotImplementedError`
  - Unused imports and leftover debugging statements (`print`, `breakpoint`)

## 2. Quality Evaluation Matrix
- **Correctness (40%)**: Does the implementation satisfy all requirements and pass all tests?
- **Robustness (25%)**: Are edge cases handled? Are type contracts respected?
- **Maintainability (20%)**: Is code clean, readable, modular, and self-documenting?
- **Performance (15%)**: Are algorithm time/space complexities optimal? No unnecessary allocations.

## 3. Verdict Output Format
Every review MUST conclude with:
```
VERDICT: [APPROVED | REJECTED]
REASONING:
- <Key finding 1>
- <Key finding 2>
REQUIRED_FIXES:
1. <Specific actionable fix with file and line context>
```
