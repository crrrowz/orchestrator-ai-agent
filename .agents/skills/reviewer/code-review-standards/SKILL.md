---
name: code-review-standards
description: Independent code review rubric. Evaluates security, correctness, backward compatibility, performance, and adherence to clean architecture principles.
triggers:
  - review
  - critique
  - audit
  - inspect
---

# Code Review Standards

## 1. Zero-Tolerance Violations (Automatic REJECT)
- Security: `shell=True` with dynamic strings, path traversal (`../`), hardcoded credentials.
- Dead/Stub Code: `pass`, `TODO`, `raise NotImplementedError`, unused imports, leftover debug prints.
- Fragility: Unhandled exceptions on critical paths, missing type annotations.

## 2. Mandatory Verdict Output
Every review MUST conclude with:
```
VERDICT: [APPROVED | REJECTED]
REASONING:
- <Concrete observation 1>
- <Concrete observation 2>
REQUIRED_FIXES:
1. <Actionable fix with exact file and line reference>
```

## 3. Windows & PowerShell Rules
- Execute inspection commands without bash operators (`|`, `&&`, `;`).
