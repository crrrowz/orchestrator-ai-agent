---
name: clean-python-architecture
description: Senior Python architectural standard. Enforces idiomatic Python 3.12+, strict type hints, dependency injection, modular cohesion, and zero placeholder/stub code.
triggers:
  - python
  - develop
  - implement
  - code
  - module
---

# Clean Python Architecture

## 1. Zero-Stub & Implementation Invariants
- Zero Stubs: Every function, method, and module MUST be completely implemented.
- `TODO`, `pass`, `...`, and empty placeholder functions are strictly banned.
- Persona RBAC: Developer MUST NEVER edit or create files under `tests/`. Test modifications belong solely to Tester.

## 2. Python 3.12+ Standards
- Type parameter syntax (PEP 695), union syntax (`X | Y`), `pathlib.Path`, and `dataclasses`/`pydantic`.
- Strict typing: all functions and methods must have parameter and return annotations.
- Explicit custom exceptions inheriting from base domain exceptions; never catch bare `Exception` without context.

## 3. Windows & PowerShell Rules
- Run individual PowerShell commands without bash operators (`&&`, `||`, `;`, `|`).
