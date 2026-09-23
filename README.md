# Antigravity Multi-Agent Orchestrator

A skill-driven Multi-Agent Software Development Orchestration System powered by the **OpenHands Software Agent SDK** (`openhands-sdk`).

Coordinates specialized AI agents through structured pipelines, with role-based skill enforcement, automated test loops, independent cross-model review, and Git integration.

---

## Architecture

```
                             USER TASK
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                      ORCHESTRATOR                           │
 │     Coordinates lifecycle, state, git, & skill injection    │
 └──────┬──────────────┬──────────────┬──────────────┬─────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
  │ ARCHITECT │  │ DEVELOPER │  │  TESTER   │  │ REVIEWER  │
  │  Agent    │  │   Agent   │  │   Agent   │  │   Agent   │
  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
 ┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐
 │ SKILL:      ││ SKILLS:     ││ SKILL:      ││ SKILL:      │
 │architectural││clean-python-││pytest-      ││code-review- │
 │decomposition││architecture││rigorous-    ││standards    │
 │             ││systematic-  ││testing      ││             │
 │             ││debugging    ││             ││             │
 └─────────────┘└─────────────┘└─────────────┘└─────────────┘
```

---

## Built-In Architectural Skills (`.agents/skills/`)

| Skill | Role | Purpose |
|---|---|---|
| `clean-python-architecture` | Developer | Enforces Python 3.12+ modern typing, clean architecture, zero stubs/placeholders. |
| `systematic-debugging` | Developer | Methodical root-cause analysis on test failures without guesswork. |
| `pytest-rigorous-testing` | Tester | AAA test pattern, edge cases, boundaries, deterministic fixtures, failure diagnostics. |
| `code-review-standards` | Reviewer | Security audit, performance analysis, strict approval rubric. |
| `architectural-decomposition`| Architect | Requirements breakdown into specifications, contracts, and implementation steps. |

---

## Commands

```bash
# Verify skills discovery
uv run python -m orchestrator.main --list-skills

# Run test suite
uv run pytest -v

# Run Dev-Test pipeline
uv run python -m orchestrator.main "Build module X with tests"

# Run Full 4-Agent pipeline
uv run python -m orchestrator.main "Build module X" --mode full
```
