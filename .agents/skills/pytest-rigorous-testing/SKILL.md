---
name: pytest-rigorous-testing
description: Senior testing protocol. Enforces isolated unit tests, edge-case coverage, deterministic fixtures, parameterization, and actionable test failure diagnostics.
triggers:
  - test
  - pytest
  - unittest
  - verify
  - assert
---

# Pytest Rigorous Testing Protocol

## 1. Test Architecture
- **AAA Pattern**: Structure every test explicitly into:
  1. `Arrange`: Set up inputs, mocks, and fixtures.
  2. `Act`: Invoke the target method/function.
  3. `Assert`: Verify outputs, state changes, and side effects.
- **Isolation**: Tests must never depend on execution order or shared mutable state. Use temporary directories (`tmp_path`) for file operations.
- **Determinism**: No network calls or non-deterministic time/random sources in unit tests. Use `unittest.mock` or pytest `monkeypatch`.

## 2. Coverage Requirements
- **Happy Path**: Typical successful scenarios with boundary inputs.
- **Edge Cases**:
  - Empty inputs (`""`, `[]`, `{}`, `None`)
  - Boundary limits (0, negative numbers, max integer, large payloads)
  - Malformed or invalid input types
- **Failure Modes**: Explicitly assert that expected exceptions are raised using `pytest.raises(CustomException)`.

## 3. Parametrization
- Use `@pytest.mark.parametrize` to avoid repetitive test code and test matrices cleanly.

## 4. Diagnostics on Failure
- Write descriptive assertion messages or rely on pytest's introspection with clear variable naming.
- Ensure output can be parsed directly by downstream agents to locate and repair bugs immediately.
