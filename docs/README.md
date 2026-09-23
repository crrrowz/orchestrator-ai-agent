# Antigravity Multi-Agent Orchestrator

A skill-driven Multi-Agent Software Development Orchestration System powered by the **OpenHands Software Agent SDK** (`openhands-sdk v1.49.4`).

Coordinates specialized AI agents (Architect, Developer, Tester, Reviewer, Auditor) across structured pipelines with role-based skill enforcement, automated test loops, pre-execution cost estimation, zero-token preflight gatekeepers, Git safety isolation, and interactive TUI telemetry.

---

## Architecture Overview

```
                                 USER TASK / SPEC FILE
                                           │
                                           ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                           ORCHESTRATOR ENGINE                                    │
 │    Lifecycle, FSM State Machine, Git Isolation, BudgetGuard, Skill Injection     │
 └──────┬──────────────┬──────────────┬──────────────┬──────────────┬───────────────┘
        │              │              │              │              │
        ▼              ▼              ▼              ▼              ▼
  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
  │ ARCHITECT │  │ DEVELOPER │  │  TESTER   │  │ REVIEWER  │  │  AUDITOR  │
  │   Agent   │  │   Agent   │  │   Agent   │  │   Agent   │  │   Agent   │
  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
        │              │              │              │              │
        ▼              ▼              ▼              ▼              ▼
 ┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐
 │ SKILL:      ││ SKILLS:     ││ SKILL:      ││ SKILL:      ││ SKILL:      │
 │architectural││clean-python-││pytest-      ││code-review- ││code-audit-  │
 │decomposition││architecture││rigorous-    ││standards    ││heuristics   │
 │graft-arch-  ││systematic-  ││testing      ││             ││             │
 │intelligence ││debugging    ││             ││             ││             │
 └─────────────┘└─────────────┘└─────────────┘└─────────────┘└─────────────┘
```

---

## Quick Start

### 1. Environment Setup

```bash
cd orchestrator-ai-agent

# Install dependencies with uv
uv sync

# Configure environment variables
cp .env.example .env
```

Edit `.env` and provide your OpenRouter API key:
```env
OPENROUTER_API_KEY=sk-or-v1-...
```

### 2. Verify Setup (0-Token)

```bash
# Check discovered skills
uv run python -m orchestrator.main --list-skills

# Run preflight configuration audit
uv run python -m orchestrator.main --check-config

# Run test suite (64 unit & integration tests)
uv run pytest -q
```

---

## Execution Modes (`--mode`)

The orchestrator supports three primary pipeline modes:

| Mode | Flag | Agents Involved | Best For |
|---|---|---|---|
| **Dev-Test** *(Default)* | `--mode dev-test` | Developer + Tester | Fast TDD development, single features, bug fixes, script generation. |
| **Full Architecture** | `--mode full` | Architect + Developer + Tester + Reviewer | End-to-end applications, multi-file modules, structured milestone plans. |
| **Codebase Audit** | `--mode audit` | AST Static Analysis + Auditor Agent | Deep security review, dead code detection, architectural critique. |

---

## CLI Reference & Flags

### Syntax

```bash
uv run python -m orchestrator.main [TASK] [OPTIONS]
```

### Arguments & Options

#### 1. Task Specification
- **Inline Text Prompt**:
  ```bash
  uv run python -m orchestrator.main "Build an in-memory sliding window rate limiter"
  ```
- **Task from Specification File**:
  You can pass a `.md` or `.txt` file directly as the task argument:
  ```bash
  uv run python -m orchestrator.main ./specs/feature_auth.md --mode full
  ```

#### 2. Pipeline Control
- `--mode {dev-test,full,audit}`: Choose pipeline execution engine.
- `--workspace PATH`: Target directory for code generation. Defaults to `workspace/` inside orchestrator.
- `--resume`: Resume execution from the last checkpoint (`.orchestrator_state.json`), skipping completed phases.

#### 3. Budget & Cost Safety
- `--estimate`: **Zero-token pre-flight cost projection**. Analyzes the task, computes expected token burns per agent role, and displays a formatted cost table without invoking any LLMs:
  ```bash
  uv run python -m orchestrator.main "Build OAuth2 service" --mode full --estimate
  ```
- `--no-memory`: Disables cross-run historical memory retrieval to minimize prompt token burn.

#### 4. Human-in-the-Loop (HITL)
- `--interactive`, `-i`: Activates interactive CLI checkpoints allowing you to guide the agents, request plan edits, or abort.
- `--approval-gates GATES`: Comma-separated list of checkpoints requiring manual approval before proceeding:
  - `after_architect`: Review `PLAN.md` before developer implementation begins.
  - `after_developer`: Review code before test runs.
  - `before_commit`: Inspect git diff before auto-committing to branch.
  ```bash
  uv run python -m orchestrator.main "Refactor DB" --mode full --approval-gates after_architect,before_commit
  ```

#### 5. Diagnostics & Visualization
- `--logs`: Launches the interactive TUI log explorer to inspect step-by-step agent thoughts, tool actions, and terminal outputs:
  ```bash
  # View latest global session
  uv run python -m orchestrator.main --logs

  # View latest session for a specific project workspace
  uv run python -m orchestrator.main --logs --workspace ./workspace/my-service
  ```
- `--self-audit`: Runs an offline heuristic analysis on past diagnostic runs (`diagnostics/reports/`) to discover recurring failure patterns.
- `--verbose`, `-v`: Detailed streaming of agent thoughts, prompts, and tool parameters.
- `--quiet`, `-q`: Minimalist console output showing only phase transitions and final status.

---

## Workspace Management & Isolation

By default, all generated code, files, and Git branches are isolated inside:
```
orchestrator-ai-agent/workspace/
```

To run the orchestrator against an existing project outside this directory:
```bash
uv run python -m orchestrator.main "Add input validation" --workspace /path/to/my-repo
```

- **Git Isolation**: The orchestrator automatically creates an isolated Git branch (`agent/<task-slug>-<timestamp>`) so your working branch is never modified directly.
- **Path Confinement**: Agent tool execution is strictly confined to the target workspace to prevent accidental edits to parent directories.

---

## Telemetry, Logs & Auto-Pruning

Diagnostics and run telemetry are automatically managed under `diagnostics/`:

```
diagnostics/
├── reports/                 # JSON execution reports (auto-pruned to last 20)
│   └── run_<timestamp>.json
├── logs/
│   ├── latest_session.json  # Global pointer to most recent session
│   └── <project_slug>/      # Project-isolated session history (keeps last 10)
│       ├── latest_session.json
│       └── session_<timestamp>.json
└── memory/                  # Cross-run conversational knowledge
```

- **FIFO Report Pruning**: The system automatically retains only the latest `MAX_RETAINED_REPORTS` (default: 20) in `diagnostics/reports/`, deleting obsolete reports on finalize.
- **Project Partitioning**: Each target workspace gets its own isolated log directory preventing multi-project collisions.

---

## Environment Variables Reference (`.env`)

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | *(Required)* | OpenRouter API Key for agent LLM inference. |
| `DEFAULT_MODEL` | `openrouter/anthropic/claude-3.5-sonnet` | Default model across all agent roles. |
| `ARCHITECT_MODEL` | `openrouter/anthropic/claude-3.5-sonnet` | Specialized model for architectural decomposition. |
| `DEVELOPER_MODEL` | `openrouter/anthropic/claude-3.5-sonnet` | Model for code generation and refactoring. |
| `TESTER_MODEL` | `openrouter/anthropic/claude-3.5-sonnet` | Model for pytest test suite creation. |
| `REVIEWER_MODEL` | `openrouter/anthropic/claude-3.5-sonnet` | Model for independent security/code review. |
| `AUDITOR_MODEL` | `openrouter/anthropic/claude-3.5-sonnet` | Model for codebase auditing (`--mode audit`). |
| `WORKSPACE_PATH` | `./workspace` | Default path for code generation. |
| `MAX_ITERATIONS` | `4` | Maximum TDD test/fix loops before stopping. |
| `MAX_BUDGET_USD` | `0.50` | Hard spending limit per pipeline run. |
| `MAX_TOKENS_PER_CALL` | `4096` | Max output tokens per LLM invocation. |
| `CIRCUIT_BREAKER_THRESHOLD` | `2` | Consecutive identical test failures before abort. |
| `MAX_RETAINED_REPORTS` | `20` | Max JSON telemetry reports retained in `diagnostics/reports/`. |
| `AUTO_COMMIT` | `true` | Auto-commit changes to task branch upon test pass. |
| `ENABLE_MEMORY` | `true` | Enable cross-run knowledge persistence. |
| `VERBOSITY` | `normal` | Output detail (`quiet`, `normal`, `verbose`). |

---

## Testing & Quality Assurance

Run the comprehensive test suite verifying SDK tools, circuit breaker, FSM states, reviewer parser, and log rotation:

```bash
uv run pytest tests/ -v
```

All 64 tests run offline using mocks without consuming API credits.
