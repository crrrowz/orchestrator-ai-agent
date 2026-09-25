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

# Architectural Decomposition

## 1. Low-Token Discovery
- Run `graft map` to orient on directory clusters and hotspots before inspecting files.
- Use `graft skeleton <filepath>` to check public interface signatures with minimal token overhead.
- Never perform unbounded whole-file reads across the codebase.

## 2. Specification Deliverable (`PLAN.md`)
Every architecture plan MUST provide:
1. Target filepaths to create or modify.
2. Explicit function signatures, type annotations, and dataclass/Pydantic models.
3. Component dependency ordering:
   - Phase 1: Domain models and custom exceptions.
   - Phase 2: Core service logic.
   - Phase 3: Adapters, I/O tools, and CLI wiring.
   - Phase 4: Test specifications.
4. Non-goals and structural invariants.

## 3. Windows & PowerShell Rules
- Execute commands as standalone calls without bash pipes (`|`) or chaining (`&&`, `;`).
