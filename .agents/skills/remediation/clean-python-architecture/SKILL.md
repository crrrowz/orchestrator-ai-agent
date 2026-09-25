---
name: clean-python-architecture
description: Senior Python architectural standard. Enforces idiomatic Python 3.12+, strict type hints, dependency injection, modular cohesion, and zero placeholder/stub code.
triggers:
  - python
  - develop
  - implement
  - code
  - module
  - remediate
---

# Clean Python Architecture (Remediation)

## 1. Zero-Stub & Remediation Invariants
- Zero Stubs: Every repaired function, method, and module MUST be completely implemented.
- `TODO`, `pass`, `...`, and empty placeholder functions are strictly banned.
- Persona RBAC: Remediation focuses on production source code and MUST NOT edit `tests/` to hide failing assertions.
- Surgical Edits: Apply localized diffs addressing the finding without destabilizing surrounding code.

## 2. Python 3.12+ Standards
- Type parameter syntax (PEP 695), union syntax (`X | Y`), `pathlib.Path`, and `dataclasses`/`pydantic`.
- Strict typing: all functions and methods must have parameter and return annotations.
- Explicit custom exceptions; never catch bare `Exception` without context.

## 3. Windows & PowerShell Rules
- Run individual PowerShell commands without bash operators (`&&`, `||`, `;`, `|`).
