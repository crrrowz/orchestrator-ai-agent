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

# Clean Python Architecture Standard

## 1. Core Principles
- **No Stubs / No Placeholders**: Every function, method, and module MUST be completely implemented. Never output `# TODO: implement later` or `pass` in production code.
- **Python 3.12+ Modern Idioms**: Use PEP 695 type parameter syntax, modern union syntax (`X | Y`), pattern matching where appropriate, and standard library modules (`pathlib`, `typing`, `dataclasses`).
- **Strict Typing**: All function signatures MUST include type annotations for arguments and return types. Use `typing.Annotated`, `typing.Protocol`, and `pydantic.BaseModel` where validation is required.
- **Explicit Separation of Concerns**:
  - Domain models (pure data/entities)
  - Service layer (business logic, orchestration)
  - Adapter / Tool layer (I/O, filesystem, external APIs)
  - Ports / Protocols for loose coupling

## 2. Error Handling & Robustness
- Never catch generic `Exception` without re-raising or logging with structured context.
- Define custom domain exceptions inheriting from a base project exception.
- Fail early: Validate preconditions at entry points.

## 3. Immutability & Data Design
- Prefer immutable data structures (`dataclass(frozen=True)` or Pydantic `frozen=True`) for value objects.
- Separate reads from writes (Command-Query Separation).
- Keep functions pure and side-effect free whenever feasible.
