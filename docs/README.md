# ORAGAI

> **Autonomous Multi-Agent Orchestration & Self-Healing Engineering.**  
> *(Orchestrated Resilient Autonomous Generative AI)*

**ORAGAI** is a high-performance, autonomous multi-agent software engineering framework powered by the **OpenHands Software Agent SDK** (`openhands-sdk v1.49.4`), `.agents/skills/` specification, and zero-token codebase intelligence (via Graft).

---

## 🌟 System Overview

```
                                  USER TASK / SPEC FILE
                                            │
                                            ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                           ORAGAI CONTROL PLANE (Python 3.12+)                    │
 │  FSM State Machine (12 Phases) │ ContextManager │ DynamicTokenGovernor           │
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
 │ SKILLS:     ││ SKILLS:     ││ SKILL:      ││ SKILLS:     ││ SKILLS:     │
 │architectural││clean-python-││pytest-      ││code-review- ││code-review- │
 │decomposition││architecture││rigorous-    ││standards    ││standards    │
 │api-design   ││systematic-  ││testing      ││security-    ││security-    │
 │contract     ││debugging    ││             ││audit        ││hardening    │
 │graft-arch   ││docker-devops││             ││             ││graft-arch   │
 └─────────────┘└─────────────┘└─────────────┘└─────────────┘└─────────────┘
                                      │
                                      ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                      COGNITIVE SENTINEL & SRE MESH                               │
 │ ASTGuard (<15ms), SelfHealingEngine, CloudResilienceMesh, SQLite WAL Diagnostics │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```text
.
├── orchestrator/
│   ├── adapters/            # Polyglot Project Adapters (Python, Node, Generic)
│   ├── agents/              # Role Agent Factories (Architect, Developer, Tester, Reviewer, Auditor, Documentation)
│   ├── analysis/            # Pytest parsing, Graft context, Finding validators
│   ├── cli/                 # CLI handlers, argparse routing, interactive wizard
│   ├── config/              # Pydantic schemas, cascading JSON/.env loaders
│   ├── context/             # ContextManager, prompt builder, modular injectors
│   ├── control/             # TokenGovernor, BudgetGuard, HumanInterventionChannel
│   ├── core/                # Config, constants, exceptions, typing protocols
│   ├── guards/              # Zero-token preflight syntax & importability guards
│   ├── llm/                 # LLMManager, factory, pricing, model normalization
│   ├── memory/              # Cross-run persistent conversation memory
│   ├── pipeline/            # 5 Pipelines (DevTestLoop, FullPipeline, AuditPipeline, AuditFixPipeline, DocumentationPipeline)
│   ├── rendering/           # Rich diff renderer, terminal styling, report generators
│   ├── sentinel/            # Cognitive Sentinel: ASTGuard, SelfHealing, CloudMesh, DiagnosticsDB
│   ├── skills/              # Skill manager, compressor, resolver, registry
│   ├── tools/               # RBAC workspace file and parameterized terminal tools
│   ├── ui/                  # SessionLogStore, OrchestratorLiveVisualizer, InteractiveLogExplorer
│   └── vcs/                 # GitOps isolation, branching, diffs, checkpointing
├── tests/                   # Comprehensive Test Modules (469 Passing Tests)
├── docs/                    # Operational and architectural documentation (DOCKER_GUIDE.md, etc.)
├── Dockerfile               # Multi-stage container definition (Dev & Prod)
├── docker-compose.yml       # Dev environment, CLI runner, and test container services
└── pyproject.toml           # Project dependencies & build configuration
```

---

## 🚀 Quick Start

ORAGAI can be run either via **Docker** (recommended for isolated, reproducible Linux execution) or **locally** using Python and `uv`.

---

### 🐳 1. Getting Started with Docker (Recommended)

ORAGAI provides first-class Docker support for both **Local Docker Engines** (Docker Desktop on Windows/macOS/Linux) and **Remote Docker Engines** (Debian VM / Remote Server via SSH Context).

#### Quick Commands
```bash
# 1. Configure environment secrets
cp .env.example .env

# 2. Build the development image (dependencies pre-cached)
docker build --target development -t oragai:dev .

# 3. Verify configuration offline (0 API tokens consumed)
docker run --rm --env-file .env oragai:dev python -m orchestrator.main --check-config

# 4. Run test suite inside Linux container
docker run --rm oragai:dev pytest tests/ -v

# 5. Execute an orchestration task
docker run --rm -it --env-file .env oragai:dev python -m orchestrator.main "Build a rate limiter" --mode dev-test
```

> 📖 **Comprehensive Docker Documentation:**  
> For in-depth architectural details, Local vs Remote VM workflows, live bind-mounting, Docker Compose, Dev Containers, context switching, and dangling image cleanup (`dangling=true`), see the complete **[Docker Architecture & Operations Guide](DOCKER_GUIDE.md)**.

---

### 💻 2. Local Installation (Without Docker)

If you prefer to run directly on your host machine without containers:

#### Requirements
- Python `3.12+`
- `uv` (recommended) or `pip`
- Git

```bash
# Install dependencies with uv
uv sync

# Verify configuration offline
uv run python -m orchestrator.main --check-config

# Run test suite
uv run python -m pytest tests/ -q

# Execute an orchestration task
uv run python -m orchestrator.main "Build a rate limiter" --mode dev-test
```

---

## ⚡ Execution Modes (`--mode`)

1. **`--mode dev-test` (Default)**: Developer + Tester iterative TDD loop.
2. **`--mode full`**: 4-Agent Pipeline coordinating Architect (creates `PLAN.md`), Developer (Milestone DAG), Tester (Pytest), and Reviewer (Independent Verdict).
3. **`--mode audit`**: Zero-token AST/linter inspection + Auditor agent producing structured `docs/audit_findings.json` and `docs/AUDIT_REPORT.md`.
4. **`--mode audit-fix`**: Continuous scan-remediate-verify self-healing loop directly on workspace working tree without Git operations.
5. **`--mode docs`**: Documentation agent authoring and updating repository documentation.

---

## 🛡️ Cognitive Sentinel & SRE Mesh

- **`--sentinel-status`**: Displays live Sentinel diagnostics, auto-healed incident counts, and cloud circuit breaker statuses.
- **`--sentinel-heal [PATH]`**: Offline zero-token AST syntax audit and automated import repair.
- **`--sentinel-test-mesh`**: Probes cloud fallback chain readiness across OpenRouter, Gemini, Groq, Anthropic, and OpenAI.

---

## 🧪 Testing & Verification

The test suite contains **469 automated tests** covering:
- OpenHands SDK tool protocol compliance (`WorkspaceFileTool`, `WorkspaceTerminalTool`).
- Circuit breaker state machines and semantic failure deduplication.
- Dynamic token governance and phase allocation (`TokenPhase`).
- Cognitive Sentinel supervision, AST guarding, and self-healing.
- Project log rotation and multi-workspace partitioning.
- Cross-platform Windows & Linux subprocess execution and sandbox path virtualization.

```bash
# Inside Docker (Recommended)
docker run --rm oragai:dev pytest tests/ -v

# Or locally with uv
uv run python -m pytest tests/ -v
```

All 469 tests pass deterministically across Linux containers and Windows.
