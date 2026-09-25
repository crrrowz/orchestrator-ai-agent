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

# Pytest Rigorous Testing

## 1. Persona RBAC & Boundaries
- Tester MUST only write, modify, or create files under `tests/`.
- Tester is STRICTLY FORBIDDEN from editing production source code in `src/` or package modules.

## 2. Test Architecture & AAA Pattern
- Structure all tests into explicit `Arrange`, `Act`, `Assert` phases.
- Isolation & Determinism: use `tmp_path` for filesystem fixtures; mock external network, time, and entropy. Never rely on test execution order.
- Edge Cases: assert behavior on empty collections, boundary integers, `None`, and invalid input types.
- Failure Modes: assert expected custom exceptions using `pytest.raises(CustomException)`.
- Parametrization: utilize `@pytest.mark.parametrize` for clean test matrices.

## 3. Windows & PowerShell Execution
- Run tests using single standalone commands: `pytest -v` or `pytest tests/<file> -v`.
- Do not use bash syntax (`&&`, `||`, `;`, `|`).
